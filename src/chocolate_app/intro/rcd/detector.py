import os
import itertools
import operator
import numpy as np
import pickle
import faiss
import pathlib
import datetime
from natsort import natsorted, ns

from chocolate_app import ARTEFACTS_PATH

# internal imports
from . import featurevectors
from . import video_functions
from . import evaluation


def max_two_values(d):
    """
    a) create a list of the dict's keys and values;
    b) return the two keys with the max values
    """
    v = list(d.values())
    k = list(d.keys())
    result1 = k[v.index(max(v))]
    del d[result1]

    v = list(d.values())
    k = list(d.keys())
    result2 = k[v.index(max(v))]
    return [result1, result2]


def fill_gaps(sequence, lookahead):
    """
    Given a list consisting of 0's and 1's , fills up the gaps between 1's
    if the gap is smaller than the lookahead.

    Example:
        input: [0,0,1,0,0,0,0,1,0,0] with lookahead=6
       output: [0,0,1,1,1,1,1,1,0,0]
    """

    i = 0
    change_needed = False
    look_left = 0
    while i < len(sequence):
        look_left -= 1
        if change_needed and look_left < 1:
            change_needed = False
        if sequence[i]:
            if change_needed:
                for k in to_change:
                    sequence[k] = True
            else:
                change_needed = True
            look_left = lookahead
            to_change = []
        else:
            if change_needed:
                to_change.append(i)
        i += 1
    return sequence


def get_two_longest_timestamps(timestamps):
    """
    Returns the two longest time intervals given a list of time intervals

    Example:
        input: [(0,10) , (0,5) , (20,21)]
        returns: [(0,10), (0,5)]
    """
    # if size is smaller or equal to 2, return immediately
    if len(timestamps) <= 2:
        return timestamps

    d = {}
    for start, end in timestamps:
        d[(start, end)] = end - start

    return max_two_values(d)


def to_time_string(seconds):
    """
    Given seconds in integer format, returns a string in the format hh:mm:ss (example: 01:30:45)
    """
    return str(datetime.timedelta(seconds=seconds))


def query_episodes_with_faiss(videos, vectors_dir):
    """
    Given a vector with the video file names and the directory
    where the corresponding vectors files reside. This function will
    query each set of episode feature vectors on all of the other feature vectors.
    It will return the distances to the best match found on each frame.

    returns:
        A list with tuples consisting of:
        (video_file_name, [list with all distances best match on each frame])
    """
    vector_files = []
    for video in videos:
        file_name, extension = os.path.splitext(video)
        file_name = os.path.basename(file_name)
        file_name = f"{file_name}{extension}.p"
        vector_files.append(file_name)

    vectors = []

    # the lengths of each vector, will be used to query each episode
    lengths = []

    # concatenate all the vectors into a single list multidimensional array
    for f in vector_files:
        episode_vectors = np.array(
            pickle.load(open(f"{ARTEFACTS_PATH}/{f}", "rb")), np.float32
        )
        lengths.append(episode_vectors.shape[0])
        vectors.append(episode_vectors)

    vectors = np.vstack(vectors)

    results = []
    for i, length in enumerate(lengths):
        i += 1
        s = sum(lengths[: i - 1])
        e = sum(lengths[:i])

        # query consists of one episode
        query = vectors[s:e]
        # rest of the feature vectors
        rest = np.append(vectors[:s], vectors[e:], axis=0)

        # build the faiss index, set vector size
        vector_size = query.shape[1]
        index = faiss.IndexFlatL2(vector_size)

        # add vectors of the rest of the episodes to the index
        index.add(rest)

        # we want to see k nearest neighbors
        k = 1
        # search with for matches with query
        scores, indexes = index.search(query, k)

        result = scores[:, 0]
        try:
            results.append((videos[i - 1], result))
        except:
            print(f"Error in query_episodes_with_faiss for idx {i-1}, result: {result}")

    return results


def detect(
    videos,
    feature_vector_function="CH",
    annotations=None,
    artifacts_dir=None,
    framejump=3,
    percentile=10,
    resize_width=144,
    video_start_threshold_percentile=20,
    video_end_threshold_seconds=15,
    min_detection_size_seconds=15,
):
    """
    The main function to call to detect recurring content. Resizes videos, converts to feature vectors
    and returns the locations of recurring content within the videos.

    arguments
    ---------
    videos : list
        Variable that should have the video file locations.
    annotations : str
        Location of the annotations.csv file, if annotations is given then it will evaluate the detections with the annotations.
    feature_vector_function : str
        Which type of feature vectors to use, options: ["CH", "CTM", "CNN"], default is color histograms (CH) because
        of balance between speed and accuracy. This default is defined in init.py.
    artifacts_dir : str
        Directory location where the artifacts should be saved. Default location is the location
        defined with the video_dir parameter.
    framejump : int
        The frame interval to use when sampling frames for the detection, a higher number means that less frames will be
        taken into consideration and will improve the processing time. But will probably cost accuracy.
    percentile : int
        Which percentile of the best matches will be taken into consideration as recurring content. A high percentile will
        means a higher recall, lower precision. A low percentile means a lower recall and higher precision.
    resize_width: int
        Width to which the videos will be resized. A lower number means higher processing speed but less accuracy and vice versa.
    video_start_threshold_percentile: int
        Percentage of the start of the video in which the detections will be marked as detections. As recaps and opening credits
        only occur at the first parts of video files, this parameter can alter that threshold. So putting 20 in here means that
        if we find recurring content in the first 20% of frames of the video, it will be marked as a detection. If it's detected
        later than 20%, then the detection will be ignored.
    video_end_threshold_seconds: int
        Number of seconds threshold in which the final detection at the end of the video should end for it to count.
        Putting 15 here means that a detection at the end of a video will only be marked as a detection if the detection ends
        in the last 15 seconds of the video.
    min_detection_size_seconds: int
        Minimal amount of seconds a detection should be before counting it as a detection. As credits & recaps & previews generally
        never consist of a few seconds, it's wise to pick at least a number higher than 10.

    returns
    -------
    dictionary
        dictionary with timestamp detections in seconds list for every video file name

       {"video_filename" : [(start1, end1), (start2, end2)],
        "video_filename2" :  [(start1, end1), (start2, end2)],
        ...
       }
    """

    # if feature vector function is CNN, change resize width
    if feature_vector_function == "CNN":
        resize_width = 224

    # define the static directory names
    resized_dir_name = f"resized{resize_width}"
    feature_vectors_dir_name = (
        f"{feature_vector_function}_feature_vectors_framejump{framejump}"
    )

    # the video files used for the detection
    videos = [f for f in videos if video_functions.file_is_video(f)]

    # make sure videos are sorted, use natural sort to correctly handle case of ep1 and ep10 in file names
    videos = natsorted(videos, alg=ns.IGNORECASE)

    for file in videos:
        file = file.replace("//", "/")

    # if artifacts dir is not set, then store artifacts in dir with videos
    if artifacts_dir is None:
        artifacts_dir = "artifacts/"

    # location of the vector directory
    vectors_dir = os.path.join(
        artifacts_dir, resized_dir_name, feature_vectors_dir_name
    )

    # if there's an annotations file, get the pandas format
    if annotations is not None:
        annotations = evaluation.get_annotations(annotations)

    for file in videos:
        # set the video path files
        file_full = file
        file_resized = os.path.join(artifacts_dir, resized_dir_name, file)

        # make sure folder of experimentname exists or create otherwise
        os.makedirs(os.path.dirname(file_resized), exist_ok=True)

        # if there is no resized video yet, then resize it
        if not os.path.isfile(file_resized):
            video_functions.resize(file_full, file_resized, resize_width)

        # from the resized video, construct feature vectors
        featurevectors.construct_feature_vectors(
            file_resized, feature_vectors_dir_name, feature_vector_function, framejump
        )

    # query the feature vectors of each episode on the other episodes
    results = query_episodes_with_faiss(videos, vectors_dir)

    # evaluation variables
    total_relevant_seconds = 0
    total_detected_seconds = 0
    total_relevant_detected_seconds = 0

    all_detections = {}
    for video, result in results:
        framerate = video_functions.get_framerate(os.path.join(video))
        threshold = np.percentile(result, percentile)

        # all the detections
        below_threshold = result < threshold
        # Merge all detections that are less than 10 seconds apart
        below_threshold = fill_gaps(below_threshold, int((framerate / framejump) * 10))

        # put all the indices where values are nonzero in a list of lists
        nonzeros = [
            [i for i, value in it]
            for key, it in itertools.groupby(
                enumerate(below_threshold), key=operator.itemgetter(1)
            )
            if key != 0
        ]

        detected_beginning = []
        detected_end = []

        # loop through all the detections taking start and endpoint into account
        for nonzero in nonzeros:
            start = nonzero[0]
            end = nonzero[-1]

            # result is in first video_start_threshold% of the video
            occurs_at_beginning = end < len(result) * (
                video_start_threshold_percentile / 100
            )
            # the end of this timestamp ends in the last video_end_threshold seconds
            ends_at_the_end = end > len(result) - video_end_threshold_seconds * (
                framerate / framejump
            )

            if end - start > (
                min_detection_size_seconds * (framerate / framejump)
            ) and (  # only count detection when larger than min_detection_size_seconds seconds
                occurs_at_beginning or ends_at_the_end
            ):  # only use results that are in first part or end at last seconds

                start = start / (framerate / framejump)
                end = end / (framerate / framejump)

                if occurs_at_beginning:
                    detected_beginning.append((start, end))
                elif ends_at_the_end:
                    detected_end.append((start, end))

        detected = get_two_longest_timestamps(detected_beginning) + detected_end

        # evaluation
        if annotations is not None:
            ground_truths = evaluation.get_skippable_timestamps_by_filename(
                video, annotations
            )
            relevant_seconds, detected_seconds, relevant_detected_seconds = (
                evaluation.match_detections_precision_recall(detected, ground_truths)
            )

            total_relevant_seconds += relevant_seconds
            total_detected_seconds += detected_seconds
            total_relevant_detected_seconds += relevant_detected_seconds

        all_detections[video] = detected

    return all_detections
