import math
import pandas as pd


def overlap(interval1, interval2):
    """
    Returns the total amount of overlap between two intervals in the format of (x,y)

    Example:
        input:      (0,10) , (5,10)
        returns:    5
    """
    return max(0, min(interval1[1], interval2[1]) - max(interval1[0], interval2[0]))


def sum_timestamps(timestamps):
    """
    Get the total number of seconds out of a list with timestamps formatted like: (start,end)
    """
    result = 0
    for start, end in timestamps:
        result += end - start

    return result


# matches two lists of (starttime,endtime) detections and outputs the relevancy variables
def match_detections_precision_recall(detected, ground_truth, verbose=False):
    """
    Compares the detections and ground truth lists of timestamps and calculates
    and outputs precision and recall scores based on the comparison.
    """

    total_relevant_seconds = sum_timestamps(ground_truth)
    total_detected_seconds = sum_timestamps(detected)
    relevant_detected_seconds = 0

    for start, end in ground_truth:
        for i, (start_d, end_d) in enumerate(detected):

            if abs(start - start_d) < 2:
                start_d = start
            if abs(end - end_d) < 2:
                end_d = end

            relevant = overlap((start, end), (start_d, end_d))
            relevant_detected_seconds += relevant

    return total_relevant_seconds, total_detected_seconds, relevant_detected_seconds


def merge_consecutive_timestamps(timestamps):
    """
    Merges consecutive timestamps in a list if they're less than 2 seconds apart
    Example: [(0,5), (5,10), (20,30)] gets combined into [(0,10),[20,30]
    """
    result = []
    i = 0
    while i < len(timestamps):
        (start, end) = timestamps[i]

        # check if we're not already at the last element
        if i < len(timestamps) - 1:
            (start_next, end_next) = timestamps[i + 1]
            # merge if less than 2 seconds apart
            if abs(end - start_next) < 2:
                result.append((start, end_next))
                i += 1
            else:
                result.append((start, end))

        else:
            result.append((start, end))

        i += 1

    return result


def to_seconds(time):
    """
    Converts string of format hh:mm:ss to total number of seconds
    """
    if time == "None":
        return -1
    try:
        hours = int(time.split(":")[0])
        minutes = int(time.split(":")[1])
        seconds = int(float(time.split(":")[2]))
        return hours * 60 * 60 + minutes * 60 + seconds
    except:
        if math.isnan(time):
            return -1


def get_skippable_timestamps_by_filename(filename, df):
    """
    Looks in the supplied pandas dataframe to extract the annotations for the
    given filename.
    """
    result = []
    try:
        row = df.loc[df["filename"] == filename].to_dict(orient="records")[0]

        if not row["recap_start"] == -1:
            result.append((row["recap_start"], row["recap_end"]))
        if not row["openingcredits_start"] == -1:
            result.append((row["openingcredits_start"], row["openingcredits_end"]))
        if not row["preview_start"] == -1:
            result.append((row["preview_start"], row["preview_end"]))
        if not row["closingcredits_start"] == -1:
            result.append((row["closingcredits_start"], row["closingcredits_end"]))
    except Exception as e:
        raise Exception(
            f"Something went wrong when getting the annotations for: {filename} \n Make sure the annotations are there in the correct format"
        )

    return merge_consecutive_timestamps(result)


def get_annotations(filename):
    """
    Gets the annotations file as a pandas dataframe.
    """
    annotations = pd.read_csv(filename).dropna(how="all")

    # convert the timestamp strings to regular seconds
    annotations["recap_start"] = annotations["recap_start"].apply(to_seconds)
    annotations["recap_end"] = annotations["recap_end"].apply(to_seconds)
    annotations["openingcredits_end"] = annotations["openingcredits_end"].apply(
        to_seconds
    )
    annotations["openingcredits_start"] = annotations["openingcredits_start"].apply(
        to_seconds
    )
    annotations["preview_start"] = annotations["preview_start"].apply(to_seconds)
    annotations["preview_end"] = annotations["preview_end"].apply(to_seconds)
    annotations["closingcredits_end"] = annotations["closingcredits_end"].apply(
        to_seconds
    )
    annotations["closingcredits_start"] = annotations["closingcredits_start"].apply(
        to_seconds
    )

    return annotations
