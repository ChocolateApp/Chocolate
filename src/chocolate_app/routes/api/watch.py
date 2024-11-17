import os
import datetime
import pycountry
import subprocess

from typing import Any, Dict
from videoprops import get_video_properties
from flask import Blueprint, make_response, request, Response, abort

from chocolate_app.routes.api.auth import token_required
from chocolate_app.tables import (
    OthersVideos,
    Movies,
    Albums,
    Games,
    Books,
    Episodes,
    MediaPlayed,
    Series,
    Seasons,
    TVChannels,
)
from chocolate_app import (
    DB,
    VIDEO_CHUNK_LENGTH,
    AUDIO_CHUNK_LENGTH,
    FFMPEG_ARGS,
    VIDEO_CODEC,
    ARTEFACTS_PATH,
)
from chocolate_app.utils.utils import (
    generate_response,
    Codes,
    length_video,
    get_chunk_user_token,
    hash_string,
)
from chocolate_app.routes.api.medias import (
    movie_to_media,
    episode_to_media,
    other_to_media,
    album_to_media,
)


watch_bp = Blueprint("watch", __name__, url_prefix="/watch")

LOG_LEVEL = "error"


class PreviousLagInfo:
    def __init__(self, lag: float | int, lag_id: int) -> None:
        self.lag = lag
        self.lag_id = lag_id


VIDEO_PREVIOUS_LAG: Dict[str, PreviousLagInfo] = {}
AUDIO_PREVIOUS_LAG: Dict[str, PreviousLagInfo] = {}


def set_media_played(
    media_type: str, media_id: int, user_id: int, duration: str | float | int
) -> None:
    if isinstance(duration, str):
        duration = round(float(duration))
    elif isinstance(duration, float):
        duration = round(duration)

    media_played = MediaPlayed.query.filter_by(
        media_id=media_id, media_type=media_type, user_id=user_id
    ).first()
    if not media_played:
        media_played = MediaPlayed(
            media_id=media_id, media_type=media_type, user_id=user_id
        )
        DB.session.add(media_played)

    # get the current date as a Date object
    media_played.datetime = datetime.datetime.now()
    media_played.duration = duration

    if media_type == "show":
        episode_data = Episodes.query.filter_by(id=media_id).first()
        if not episode_data:
            return
        media_played.season_id = (
            Seasons.query.filter_by(tmdb_id=episode_data.season_id).first().id
        )
        media_played.serie_id = (
            Series.query.filter_by(tmdb_id=episode_data.serie_id).first().id
        )
        media_duration = length_video(episode_data.slug)
        if duration > media_duration * 0.9:
            # create a new entry in the table MediaPlayed for the next episode
            if not Episodes.query.filter_by(
                season_id=episode_data.season_id,
                number=episode_data.number + 1,
            ).first():
                print("There's no next episodes")
                return

            print("There's a next episodes")
            print(
                f"season_id: {episode_data.season_id} number: {episode_data.number+1}"
            )
            next_episode = Episodes.query.filter_by(
                season_id=episode_data.season_id,
                number=int(episode_data.number) + 1,
            ).first()

            if MediaPlayed.query.filter_by(
                media_id=next_episode.id, media_type="show", user_id=user_id
            ).first():
                return

            media_played_next = MediaPlayed(
                media_id=next_episode.id, media_type="show", user_id=user_id
            )
            media_played_next.datetime = datetime.datetime.now()
            media_played_next.duration = 0
            media_played_next.serie_id = media_played.serie_id
            media_played_next.season_id = media_played.season_id
            media_played.datetime = media_played.datetime - datetime.timedelta(
                seconds=5
            )
            DB.session.add(media_played_next)

    DB.session.commit()


def get_media_slug(media_id: int, media_type: str) -> str | None:
    if media_type == "show":
        return Episodes.query.filter_by(id=media_id).first().slug
    elif media_type == "movie":
        return Movies.query.filter_by(id=media_id).first().slug
    elif media_type == "other":
        return OthersVideos.query.filter_by(id=media_id).first().slug
    elif media_type == "album":
        return Albums.query.filter_by(id=media_id).first().slug
    elif media_type == "game":
        return Games.query.filter_by(id=media_id).first().slug
    elif media_type == "book":
        return Books.query.filter_by(id=media_id).first().slug
    return None


def generate_m3u8(media: Any) -> Response:
    media_id = media["id"]
    media_type = media["type"]

    video_path = get_media_slug(media_id, media_type)

    if not video_path:
        return generate_response(Codes.MEDIA_NOT_FOUND, True)

    video_properties = get_video_properties(video_path)
    height = int(video_properties["height"])
    width = int(video_properties["width"])
    m3u8_file = "#EXTM3U\n#EXT-X-VERSION:3\n"

    m3u8_file += generate_caption_media(video_path, media_id, media_type) + "\n"
    audio = "\n"
    audio = generate_audio_streams_media(video_path, media_id, media_type)
    audio += "\n"
    m3u8_file += audio
    qualities = [144, 240, 360, 480, 720, 1080]
    quality_to_codec = {
        144: "avc1.6e000c",
        240: "avc1.6e0015",
        360: "avc1.6e001e",
        480: "avc1.6e001f",
        720: "avc1.6e0020",
        1080: "avc1.6e0032",
    }

    file = []
    for quality in qualities:
        if quality < height:
            new_width = int(quality)
            new_height = int(float(width) / float(height) * new_width)
            new_height += new_height % 2
            m3u8_line = f"#EXT-X-STREAM-INF:BANDWIDTH={int((new_width*new_height)/4)},"

            m3u8_line += f'CODECS="{quality_to_codec[int(quality)]}",RESOLUTION={new_height}x{new_width},SUBTITLES="subs",AUDIO="audio"\n/api/watch/video_media/{quality}/{media_type}/{media_id}.m3u8\n'
            file.append(m3u8_line)
    last_line = f"#EXT-X-STREAM-INF:BANDWIDTH={int((width*height)/4)},"

    codec = "avc1.6e0033"

    if height in quality_to_codec:
        codec = quality_to_codec[height]

    last_line += f'CODECS="{codec}",RESOLUTION={width}x{height},SUBTITLES="subs",AUDIO="audio"\n/api/watch/video_media/default/{media_type}/{media_id}.m3u8'
    file.append(last_line)
    file_str = "".join(file)
    m3u8_file += file_str
    response = make_response(m3u8_file)

    response.headers.set("Content-Type", "vnd.apple.mpegURL")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{media_id}_{media_type}.m3u8"
    )

    return response


def generate_caption_media(
    video_path: str, media_id: int | str, media_type: str
) -> str:
    caption_command = [
        "ffprobe",
        "-loglevel",
        "error",
        "-select_streams",
        "s",
        "-show_entries",
        "stream=index:stream_tags=language",
        "-of",
        "csv=p=0",
        video_path,
    ]
    caption_pipe = subprocess.Popen(caption_command, stdout=subprocess.PIPE)

    if not caption_pipe or not caption_pipe.stdout:
        abort(404)

    caption_response = caption_pipe.stdout.read().decode("utf-8")
    caption_response = caption_response.split("\n")

    all_captions = []

    caption_response.pop()

    for line in caption_response:
        line = line.rstrip()
        language = line.split(",")[1]
        new_language = pycountry.languages.get(alpha_2=language)
        index = line.split(",")[0]
        try:
            title_name = line.split(",")[2]

            try:
                title_name = title_name.split(" : ")[0]
                subtitle_type = title_name.split(" : ")[1]
            except Exception:
                title_name = title_name
                subtitle_type = "Unknown"

        except Exception:
            title_name = new_language
        subtitle_type = "Unknown"
        if subtitle_type.lower() != "pgs":
            if not new_language:
                new_language = language

            all_captions.append(
                {
                    "index": index,
                    "languageCode": language,
                    "language": new_language,
                    "url": f"/api/watch/caption/{media_id}_{media_type}_{index}.m3u8",
                    "name": title_name,
                }
            )

    string = ""
    for caption in all_captions:
        string += f'#EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subs",NAME="{caption["language"]}",DEFAULT=NO,FORCED=NO,URI="{caption["url"]}",LANGUAGE="{caption["languageCode"]}"\n'

    return string


@watch_bp.route("/caption/<media_id>_<media_type>_<id>.m3u8", methods=["GET"])
def caption(media_id: int, media_type: str, id: int) -> Response:
    video_path = get_media_slug(media_id, media_type)

    if not video_path:
        return generate_response(Codes.MEDIA_NOT_FOUND, True)

    movie_duration = length_video(video_path) + 1

    m3u8_content = f"#EXTM3U\n#EXT-X-TARGETDURATION:{movie_duration}\n#EXT-X-VERSION:3\n\n#EXT-X-PLAYLIST-TYPE:VOD\n#EXTINF:{movie_duration},\n/api/watch/chunk_caption/{media_id}_{media_type}_{id}.vtt\n#EXT-X-ENDLIST"

    response = make_response(m3u8_content)
    response.headers.set("Content-Type", "vnd.apple.mpegURL")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set(
        "Content-Disposition",
        "attachment",
        filename=f"{media_id}_{media_type}_{id}.m3u8",
    )

    return response


@watch_bp.route("/chunk_caption/<media_id>_<media_type>_<id>.vtt", methods=["GET"])
def chunk_caption(media_id: int, media_type: str, id: int) -> Response:
    video_path = get_media_slug(media_id, media_type)

    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        LOG_LEVEL,
        "-i",
        video_path,
        "-map",
        f"0:{id}",
        "-f",
        "webvtt",
        "-",
    ]

    pipe = subprocess.Popen(command, stdout=subprocess.PIPE)

    if not pipe or not pipe.stdout:
        abort(404)

    data = pipe.stdout.read()

    response = make_response(data)
    response.headers.set("Content-Type", "text/vtt")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set(
        "Content-Disposition",
        "attachment",
        filename=f"{media_id}_{media_type}_{id}.vtt",
    )

    return response


def generate_audio_streams_media(
    movie_path: str, media_id: int | str, media_type: str
) -> str:
    caption_command = [
        "ffprobe",
        "-loglevel",
        "error",
        "-show_streams",
        "-select_streams",
        "a",
        "-show_entries",
        "stream=index,codec_name,channels:stream_tags=language,title,handler_name,codec_name",
        "-of",
        "csv=p=0",
        movie_path,
    ]

    audio_stream_pipe = subprocess.Popen(caption_command, stdout=subprocess.PIPE)

    if not audio_stream_pipe or not audio_stream_pipe.stdout:
        abort(404)

    audio_stream_response = audio_stream_pipe.stdout.read().decode("utf-8")
    audio_stream_response = audio_stream_response.split("\n")
    audio_stream_response.pop()

    audio_streams = []

    for line in audio_stream_response:
        line = line.rstrip().split(",")
        id = int(line[0]) - 1
        codec = line[1]
        channels = line[2]
        language = line[-1]
        new_language = pycountry.languages.get(alpha_2=language)
        if new_language is not None and new_language.name is not None:
            language = new_language.name

        type = line[-2]
        audio_stream_object = {
            "id": id,
            "codec": codec,
            "language": language,
            "type": type,
            "channels": channels,
        }
        audio_streams.append(audio_stream_object)

    audio_stream_string = ""
    for audio_stream in audio_streams:
        audio_stream_id = audio_stream["id"]
        audio_stream_language = audio_stream["language"]
        audio_stream_codec = audio_stream["codec"]
        audio_stream_type = audio_stream["type"]
        # audio_stream_channels = audio_stream["channels"]
        audio_stream_channels = 2
        audio_stream_url = (
            f"/api/watch/audio_media/{audio_stream_id}/{media_type}/{media_id}.m3u8"
        )
        audio_stream_string += f'#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="audio",CHANNELS="{audio_stream_channels}",NAME="{audio_stream_language} ({audio_stream_type})",DEFAULT=NO,AUTOSELECT=YES,URI="{audio_stream_url}",LANGUAGE="{audio_stream_language}",CODECS="{audio_stream_codec}"\n'

    return audio_stream_string


@watch_bp.route(
    "/video_media/<quality>/<media_type>/<int:media_id>.m3u8", methods=["GET"]
)
def video_media(quality: str, media_type: str, media_id: int) -> Response:
    video_path = get_media_slug(media_id, media_type)

    if not video_path:
        return generate_response(Codes.MEDIA_NOT_FOUND, True)

    duration = length_video(video_path)

    file = f"#EXTM3U\n#EXT-X-VERSION:3\n\n#EXT-X-TARGETDURATION:{VIDEO_CHUNK_LENGTH}\n#EXT-X-MEDIA-SEQUENCE:1\n#EXT-X-PLAYLIST-TYPE:VOD\n"

    for i in range(0, int(duration), int(VIDEO_CHUNK_LENGTH)):
        extinf = float(VIDEO_CHUNK_LENGTH)

        if (duration - i) < VIDEO_CHUNK_LENGTH:
            extinf = duration - i

        file += "#EXT-X-DISCONTINUITY\n"
        file += f"#EXTINF:{extinf},\n/api/watch/video_chunk/{quality}/{media_type}/{media_id}/{(i // VIDEO_CHUNK_LENGTH) + 1}.ts\n"

    file += "#EXT-X-ENDLIST"

    response = make_response(file)
    response.headers.set("Content-Type", "vnd.apple.mpegURL")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set(
        "Content-Disposition",
        "attachment",
        filename=f"{media_id}_{media_type}_{quality}.m3u8",
    )

    return response


@watch_bp.route(
    "/audio_media/<int:audio_id>/<media_type>/<int:media_id>.m3u8", methods=["GET"]
)
def audio_media(audio_id: int, media_type: str, media_id: int) -> Response:
    video_path = get_media_slug(media_id, media_type)

    if not video_path:
        return generate_response(Codes.MEDIA_NOT_FOUND, True)

    duration = length_video(video_path)

    file = f"#EXTM3U\n#EXT-X-VERSION:3\n\n#EXT-X-TARGETDURATION:{AUDIO_CHUNK_LENGTH}\n#EXT-X-MEDIA-SEQUENCE:1\n#EXT-X-PLAYLIST-TYPE:VOD\n"

    for i in range(0, int(duration), int(AUDIO_CHUNK_LENGTH)):
        extinf = float(AUDIO_CHUNK_LENGTH)

        if (duration - i) < AUDIO_CHUNK_LENGTH:
            extinf = duration - i

        file += "#EXT-X-DISCONTINUITY\n"
        file += f"#EXTINF:{extinf},\n/api/watch/audio_chunk/{media_type}/{media_id}/{audio_id}/{(i // AUDIO_CHUNK_LENGTH) + 1}.ts\n"

    file += "#EXT-X-ENDLIST"

    response = make_response(file)
    response.headers.set("Content-Type", "vnd.apple.mpegURL")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set(
        "Content-Disposition",
        "attachment",
        filename=f"{media_id}_{media_type}_{audio_id}.m3u8",
    )

    return response


@watch_bp.route(
    "/video_chunk/<quality>/<media_type>/<int:media_id>/<int:idx>.ts", methods=["GET"]
)
@token_required
def video_chunk(
    current_user, quality: str, media_type: str, media_id: int, idx: int
) -> Response:
    video_path = get_media_slug(media_id, media_type)

    if not video_path:
        return generate_response(Codes.MEDIA_NOT_FOUND, True)

    seconds = (idx - 1) * VIDEO_CHUNK_LENGTH

    token = get_chunk_user_token(request)
    ip = request.remote_addr
    user_agent = request.headers.get("User-Agent")

    key = hash_string(f"{token}-{ip}-{user_agent}-{media_id}")

    if VIDEO_PREVIOUS_LAG.get(key) is None:
        VIDEO_PREVIOUS_LAG[key] = PreviousLagInfo(0, 0)

    time_start = str(datetime.timedelta(seconds=seconds + VIDEO_PREVIOUS_LAG[key].lag))
    if seconds + VIDEO_PREVIOUS_LAG[key].lag < 0:
        time_start = str(datetime.timedelta(seconds=0))

    command = []

    if quality == "default":
        command = [
            "ffmpeg",
            *FFMPEG_ARGS,
            "-hide_banner",
            "-loglevel",
            LOG_LEVEL,
            "-ss",
            time_start,
            "-t",
            str(VIDEO_CHUNK_LENGTH),
            "-i",
            video_path,
            "-c:v",
            VIDEO_CODEC,
            "-an",
            "-f",
            "mpegts",
            "-",
        ]
    else:
        video_properties = get_video_properties(video_path)
        width = video_properties["width"]
        height = video_properties["height"]
        new_width = int(float(quality))
        new_height = round(float(width) / float(height) * new_width)
        if (new_height % 2) != 0:
            new_height += 1

        command = [
            "ffmpeg",
            *FFMPEG_ARGS,
            "-hide_banner",
            "-loglevel",
            LOG_LEVEL,
            "-ss",
            time_start,
            "-t",
            str(VIDEO_CHUNK_LENGTH),
            "-i",
            video_path,
            "-c:v",
            VIDEO_CODEC,
            "-an",
            "-vf",
            f"scale={new_height}:{new_width}",
            "-f",
            "mpegts",
            "-",
        ]

    pipe = subprocess.Popen(command, stdout=subprocess.PIPE)

    if not pipe or not pipe.stdout:
        abort(404)

    data = pipe.stdout.read()

    temp_path = f"{ARTEFACTS_PATH}/{media_id}-{idx}.ts"

    with open(temp_path, "wb") as file:
        file.write(data)

    duration = length_video(temp_path)

    if os.path.exists(temp_path):
        os.remove(temp_path)

    VIDEO_PREVIOUS_LAG[key].lag = duration - (
        VIDEO_CHUNK_LENGTH - VIDEO_PREVIOUS_LAG[key].lag
    )
    if VIDEO_PREVIOUS_LAG[key].lag_id == idx - 1:
        VIDEO_PREVIOUS_LAG[key].lag = duration - (
            VIDEO_CHUNK_LENGTH - VIDEO_PREVIOUS_LAG[key].lag
        )
    else:
        VIDEO_PREVIOUS_LAG[key].lag = 0

    VIDEO_PREVIOUS_LAG[key].lag_id = idx

    current_time = request.headers.get("X-Current-Time")

    if current_time:
        set_media_played(
            media_type, media_id, current_user.id, round(float(current_time))
        )

    response = make_response(data)
    response.headers.set("Content-Type", "video/MP2T")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{media_id}-{idx}.ts"
    )

    return response


@watch_bp.route(
    "/audio_chunk/<media_type>/<int:media_id>/<int:audio_idx>/<int:idx>.ts",
    methods=["GET"],
)
def audio_chunk(media_type: str, media_id: int, audio_idx: int, idx: int) -> Response:
    global AUDIO_PREVIOUS_LAG

    token = get_chunk_user_token(request)
    ip = request.remote_addr
    user_agent = request.headers.get("User-Agent")

    key = hash_string(f"{token}-{ip}-{user_agent}-{media_id}")

    if AUDIO_PREVIOUS_LAG.get(key) is None:
        AUDIO_PREVIOUS_LAG[key] = PreviousLagInfo(0, 0)

    video_path = get_media_slug(media_id, media_type)

    seconds = (idx - 1) * AUDIO_CHUNK_LENGTH

    time_start = datetime.timedelta(seconds=seconds + AUDIO_PREVIOUS_LAG[key].lag)
    if seconds + AUDIO_PREVIOUS_LAG[key].lag < 0:
        time_start = datetime.timedelta(seconds=0)

    command = [
        "ffmpeg",
        *FFMPEG_ARGS,
        "-hide_banner",
        "-loglevel",
        LOG_LEVEL,
        "-ss",
        str(time_start),  # Start time of the segment
        "-t",
        str(AUDIO_CHUNK_LENGTH),  # End time of the segment
        "-i",
        video_path,  # Set output offset
        "-map",
        f"0:a:{audio_idx}",  # Select the audio stream
        "-ac",
        "2",  # Number of audio channels
        "-vn",  # Disable video
        "-f",
        "mp2",  # Output format for HLS
        "-",  # Send the result to stdout
    ]

    pipe = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if pipe is None or pipe.stdout is None:
        abort(404)

    data = pipe.stdout.read()

    temp_path = f"{ARTEFACTS_PATH}/{media_id}-{audio_idx}-{idx}.ts"

    with open(temp_path, "wb") as f:
        f.write(data)

    duration = length_video(temp_path)

    if os.path.exists(temp_path):
        os.remove(temp_path)

    if AUDIO_PREVIOUS_LAG[key].lag < 0:
        AUDIO_PREVIOUS_LAG[key].lag = duration - (
            VIDEO_CHUNK_LENGTH - AUDIO_PREVIOUS_LAG[key].lag
        )

    else:
        AUDIO_PREVIOUS_LAG[key].lag = 0

    AUDIO_PREVIOUS_LAG[key].lag_id = idx

    response = make_response(data)
    response.headers.set("Content-Type", "video/MP2T")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set(
        "Content-Disposition",
        "attachment",
        filename=f"{media_id}-{audio_idx}-{idx}.ts",
    )

    return response


@watch_bp.route("/media_played", methods=["POST"])
@token_required
def media_played(current_user) -> Response:
    """Set media as played"""
    data = request.get_json()

    if not data:
        return generate_response(Codes.MISSING_DATA, True)

    media_id = data.get("media_id")
    media_type = data.get("media_type")
    duration = data.get("duration")

    if not media_id or not media_type:
        return generate_response(Codes.MISSING_DATA, True)

    set_media_played(media_type, media_id, current_user.id, duration)

    return generate_response(Codes.SUCCESS, False)


@watch_bp.route("/<media_type>/<int:media_id>", methods=["GET"])
@token_required
def watch_media(current_user, media_type: str, media_id: int) -> Response:
    """Watch a media"""
    if media_type not in [
        "show",
        "movie",
        "album",
        "artist",
        "game",
        "book",
        "live-tv",
    ]:
        return generate_response(Codes.INVALID_MEDIA_TYPE, True)
    media = None
    if media_type == "show":
        media = episode_to_media(current_user.id, media_id)
    elif media_type == "movie":
        media = movie_to_media(current_user.id, media_id)
    elif media_type == "other":
        media = other_to_media(current_user.id, media_id)
    elif media_type == "album":
        media = album_to_media(current_user.id, media_id)
    elif media_type == "game":
        media = Games.query.filter_by(id=media_id).first()
    elif media_type == "book":
        media = Books.query.filter_by(id=media_id).first()
    elif media_type == "live-tv":
        media = TVChannels.query.filter_by(id=media_id).first()

    if not media:
        return generate_response(Codes.MEDIA_NOT_FOUND, True)

    if media_type == "show" or media_type == "movie" or media_type == "other":
        return generate_m3u8(media)

    return generate_response(Codes.INVALID_MEDIA_TYPE, True)
