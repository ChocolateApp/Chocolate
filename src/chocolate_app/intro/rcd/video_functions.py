import cv2
import ffmpeg
import mimetypes
import os


def file_is_video(video_fn):
    """
    Checks if the given file path actually is a video file
    """
    file_type = mimetypes.guess_type(video_fn)[0]
    return file_type is not None and file_type.startswith("video")


def get_framerate(video_fn):
    """
    Return the video framerate given a video filename
    """
    video = cv2.VideoCapture(video_fn)
    return video.get(cv2.CAP_PROP_FPS)


def resize(input, output, resize_width):
    """
    Resizes a video with ffmpeg
    """
    video2 = cv2.VideoCapture(input)
    framecount = int(video2.get(cv2.CAP_PROP_FRAME_COUNT))

    if framecount > 0:
        stream = ffmpeg.input(input)
        if resize_width == 224:
            stream = ffmpeg.filter(stream, "scale", w=224, h=224)
        else:
            stream = ffmpeg.filter(stream, "scale", w=resize_width, h="trunc(ow/a/2)*2")
        stream = ffmpeg.output(stream, output)
        try:
            with open(os.devnull, "w") as devnull:
                ffmpeg.run(stream, stdout=devnull, stderr=devnull)
        except FileNotFoundError:
            raise Exception("ffmpeg not found, make sure ffmpeg is in the PATH")
    else:
        raise Exception(f"Something is wrong with the video file: {input}")
