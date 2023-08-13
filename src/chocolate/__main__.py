import datetime
import io
import json
import os
import platform
import re
import subprocess
import warnings
import zipfile
import rarfile
import PyPDF2
import logging
import git
import GPUtil
import pycountry
import requests
import sqlalchemy
import ebooklib

from time import localtime, mktime, time
from uuid import uuid4
from deep_translator import GoogleTranslator
from flask import (
    abort,
    jsonify,
    make_response,
    request,
    send_file,
    render_template,
)
from guessit import guessit
from PIL import Image
from ebooklib import epub
from pypresence import Presence
from tmdbv3api import TV, Movie, Person, TMDb, Search
from tmdbv3api.as_obj import AsObj
from unidecode import unidecode
from videoprops import get_video_properties

from . import create_app, get_dir_path, DB, LOGIN_MANAGER, tmdb, config, all_auth_tokens, ARGUMENTS
from .tables import *
from . import scans
from .utils.utils import path_join, generate_log, check_authorization, user_in_lib

app = create_app()
dir_path = get_dir_path()

with app.app_context():
    DB.create_all()

log = logging.getLogger("werkzeug")
log.setLevel(logging.DEBUG)

start_time = mktime(localtime())

with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=sqlalchemy.exc.SAWarning)

langs_dict = GoogleTranslator().get_supported_languages(as_dict=True)

@LOGIN_MANAGER.user_loader
def load_user(id):
    return Users.query.get(int(id))

try:
    repo = git.Repo(search_parent_directories=True)
    last_commit_hash = repo.head.object.hexsha[:7]
except:
    last_commit_hash = "xxxxxxx"
    
def translate(string):
    language = config["ChocolateSettings"]["language"]
    if language == "EN":
        return string
    translated = GoogleTranslator(source="english", target=language.lower()).translate(
        string
    )
    return translated

tmdb.language = config["ChocolateSettings"]["language"].lower()
tmdb.debug = True

movie = Movie()
show = TV()

error_message = True
client_id = "771837466020937728"

enabled_rpc = config["ChocolateSettings"]["discordrpc"]
if enabled_rpc == "true":
    try:
        RPC = Presence(client_id)
        RPC.connect()
    except Exception as e:
        enabled_rpc == "false"
        config.set("ChocolateSettings", "discordrpc", "false")
        with open(path_join(dir_path, "config.ini"), "w") as conf:
            config.write(conf)
searched_films = []
all_movies_not_sorted = []
searched_series = []
simple_data_series = {}

config_language = config["ChocolateSettings"]["language"]
with app.app_context():
    language_db = DB.session.query(Language).first()
    exists = DB.session.query(Language).first() is not None
    if not exists:
        new_language = Language(language="EN")
        DB.session.add(new_language)
        DB.session.commit()
    language_db = DB.session.query(Language).first()
    if language_db.language != config_language:
        DB.session.query(Movies).delete()
        DB.session.query(Series).delete()
        DB.session.query(Seasons).delete()
        DB.session.query(Episodes).delete()
        language_db.language = config_language
        DB.session.commit()

CHUNK_LENGTH = 5
CHUNK_LENGTH = int(CHUNK_LENGTH)

movies_genre = []
movie_extension = ""
websites_trailers = {
    "YouTube": "https://www.youtube.com/embed/",
    "Dailymotion": "https://www.dailymotion.com/video_movie/",
    "Vimeo": "https://vimeo.com/",
}

@app.after_request
def after_request(response):
    code_to_status = {
        100: "Keep the change, ya filthy animal",
        101: "I feel the need... the need for speed.",
        102: "There's a storm coming, Mr. Wayne.",
        103: "I'll be back.",
        200: "Everything is awesome!",
        201: "It's alive! It's alive!",
        202: "Challenge accepted!",
        203: "Non - Authoritative Information",
        204: "Nothing to see here.",
        205: "I feel the power of the reset.",
        206: "I've got a bad feeling about this... but only a part of it.",
        207: "Life is like a box of chocolates, you never know what you're gonna get... and sometimes you get multiple things at once.",
        208: "Already Reported",
        226: "IM Used",
        300: "Multiple Choices",
        301: "I'm going on an adventure!",
        302: "Found",
        303: "See Other",
        304: "Not Modified",
        305: "Use Proxy",
        306: "(Unused)",
        307: "Temporary Redirect",
        308: "Permanent Redirect",
        400: "Bad Request",
        401: "Unauthorized",
        402: "Payment Required",
        403: "You shall not pass",
        404: "Not Found",
        405: "Method Not Allowed",
        406: "Not Acceptable",
        407: "Proxy Authentication Required",
        408: "Request Timeout",
        409: "Conflict",
        410: "Gone",
        411: "Length Required",
        412: "Precondition Failed",
        413: "Payload Too Large",
        414: "URI Too Long",
        415: "Unsupported Media Type",
        416: "Range Not Satisfiable",
        417: "Expectation Failed",
        418: "I'm a teapot",
        420: "Enhance Your Calm",
        421: "Misdirected Request",
        422: "Unprocessable Entity",
        423: "Locked",
        424: "Failed Dependency",
        425: "Too Early",
        426: "Upgrade Required",
        428: "Precondition Required",
        429: "Too Many Requests",
        431: "Request Header Fields Too Large",
        451: "Unavailable For Legal Reasons",
        500: "Internal Server Error",
        501: "Not Implemented",
        502: "Bad Gateway",
        503: "Service Unavailable",
        504: "Gateway Timeout",
        505: "HTTP Version Not Supported",
        506: "Variant Also Negotiates",
        507: "Insufficient Storage",
        508: "Loop Detected",
        510: "Not Extended",
        511: "Network Authentication Required",

    }

    if response.status_code in code_to_status:
        generate_log(request, f"{response.status_code} - {code_to_status[response.status_code]}")
    else:
        generate_log(request, f"{response.status_code} - Unknown status code")

    return response

@app.route("/")
@app.route("/<path:path>")
def index(path=None):
    return render_template("index.html")

@app.route("/check_login", methods=["POST"])
def check_login():
    global all_auth_tokens
    token = request.get_json()["token"]
    if not token:
        generate_log(request, "ERROR")
        return jsonify({"status": "error"})

    token = "Bearer " + token

    if token not in all_auth_tokens.keys():
        generate_log(request, "ERROR")
        return jsonify({"status": "error"})

    user = Users.query.filter_by(name=all_auth_tokens[token]["user"]).first()
    return jsonify(
        {
            "status": "ok",
            "username": all_auth_tokens[token]["user"],
            "account_type": user.account_type,
            "account_id": user.id,
        }
    )


@app.route("/check_download")
def check_download():
    if config["ChocolateSettings"]["allowdownload"] == "true":
        return jsonify(True)
    return jsonify(False)


def length_video(path: str) -> float:
    seconds = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            path,
        ],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        return float(seconds.stdout)
    except:
        return 0


def get_gpu_info() -> str:
    if platform.system() == "Windows":
        return gpuname()
    elif platform.system() == "Darwin":
        return subprocess.check_output(
            ["/usr/sbin/sysctl", "-n", "machdep.cpu.brand_string"]
        ).strip()
    elif platform.system() == "Linux":
        return "impossible d'accéder au GPU"
    return ""


def gpuname() -> str:
    """Returns the model name of the first available GPU"""
    try:
        gpus = GPUtil.getGPUs()
    except:
        print(
            "Unable to detect GPU model. Is your GPU configured? Are you running with nvidia-docker?"
        )
        return "UNKNOWN"
    if len(gpus) == 0:
        raise ValueError("No GPUs detected in the system")
    return gpus[0].name

@app.route("/language_file")
def language_file():
    language = config["ChocolateSettings"]["language"]
    # if language not in the supported languages, or the file contain {}, return EN
    if not os.path.isfile(f"{dir_path}/static/lang/{language.lower()}.json") or "{}" in open(f"{dir_path}/static/lang/{language.lower()}.json", "r", encoding="utf-8").read():
        language = "EN"
        
    with open(f"{dir_path}/static/lang/{language.lower()}.json", "r", encoding="utf-8") as f:
        language = json.load(f)

    with open(f"{dir_path}/static/lang/EN.json", "r", encoding="utf-8") as f:
        en = json.load(f)
    
    for key in en:
        if key not in language:
            language[key] = en[key]
        
    return jsonify(language)


@app.route("/video_movie/<movie_id>.m3u8", methods=["GET"])
def create_m3u8(movie_id):
    movie = Movies.query.filter_by(id=movie_id).first()
    if not movie:
        abort(404)
    slug = movie.slug
    library = movie.library_name
    the_library = Libraries.query.filter_by(lib_name=library).first()
    path = the_library.lib_folder
    video_path = f"{path}/{slug}"
    duration = length_video(video_path)

    file = f"""#EXTM3U
#EXT-X-MEDIA-SEQUENCE:0
#EXT-X-TARGETDURATION:{CHUNK_LENGTH}\n\n"""

    for i in range(0, int(duration), CHUNK_LENGTH):
        file += f"""#EXTINF:{int(CHUNK_LENGTH)},\n/chunk_movie/{movie_id}-{(i // CHUNK_LENGTH) + 1}.ts\n"""

    file += """#EXT-X-ENDLIST"""

    response = make_response(file)
    response.headers.set("Content-Type", "application/x-mpegURL")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{movie_id}.m3u8"
    )

    return response


@app.route("/video_movie/<quality>/<movie_id>.m3u8", methods=["GET"])
def create_m3u8_quality(quality, movie_id):
    movie = Movies.query.filter_by(id=movie_id).first()
    slug = movie.slug
    library = movie.library_name
    the_library = Libraries.query.filter_by(lib_name=library).first()
    path = the_library.lib_folder
    video_path = f"{path}/{slug}"
    duration = length_video(video_path)
    file = f"""#EXTM3U
#EXT-X-MEDIA-SEQUENCE:0
#EXT-X-TARGETDURATION:{CHUNK_LENGTH}\n"""

    for i in range(0, int(duration), CHUNK_LENGTH):
        file += f"#EXTINF:{int(CHUNK_LENGTH)},\n/chunk_movie/{quality}/{movie_id}-{(i // CHUNK_LENGTH) + 1}.ts\n"

    file += """#EXT-X-ENDLIST"""

    response = make_response(file)
    response.headers.set("Content-Type", "application/x-mpegURL")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{movie_id}.m3u8"
    )

    return response


@app.route("/video_other/<hash>", methods=["GET"])
def create_other_m3u8(hash):
    other = OthersVideos.query.filter_by(video_hash=hash).first()
    slug = other.slug
    library = other.library_name
    the_library = Libraries.query.filter_by(lib_name=library).first()
    video_path = slug
    duration = length_video(video_path)
    file = f"""
#EXTM3U

#EXT-X-VERSION:4
#EXT-X-TARGETDURATION:{CHUNK_LENGTH}
#EXT-X-MEDIA-SEQUENCE:1
    """

    for i in range(0, int(duration), CHUNK_LENGTH):
        file += f"""
#EXTINF:{float(CHUNK_LENGTH)},
/chunk_other/{hash}-{(i // CHUNK_LENGTH) + 1}.ts
        """

    file += """
#EXT-X-ENDLIST"""

    response = make_response(file)
    response.headers.set("Content-Type", "application/x-mpegURL")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set("Content-Disposition", "attachment", filename=f"{hash}.m3u8")

    return response


@app.route("/video_other/<quality>/<hash>", methods=["GET"])
def create_other_m3u8_quality(quality, hash):
    other = OthersVideos.query.filter_by(video_hash=hash).first()
    slug = other.slug
    library = other.library_name
    the_library = Libraries.query.filter_by(lib_name=library).first()
    video_path = slug
    duration = length_video(video_path)
    file = f"""
#EXTM3U

#EXT-X-VERSION:4
#EXT-X-TARGETDURATION:{CHUNK_LENGTH}
#EXT-X-MEDIA-SEQUENCE:1
    """

    for i in range(0, int(duration), CHUNK_LENGTH):
        file += f"""
#EXTINF:{float(CHUNK_LENGTH)},
/chunk_other/{quality}/{hash}-{(i // CHUNK_LENGTH) + 1}.ts
        """

    file += """
#EXT-X-ENDLIST"""

    response = make_response(file)
    response.headers.set("Content-Type", "application/x-mpegURL")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set("Content-Disposition", "attachment", filename=f"{hash}.m3u8")

    return response


@app.route("/video_serie/<episode_id>", methods=["GET"])
def create_serie_m3u8(episode_id):
    episode = Episodes.query.filter_by(episode_id=episode_id).first()
    season = Seasons.query.filter_by(season_id=episode.season_id).first()
    serie = Series.query.filter_by(id=season.serie).first()
    library = serie.library_name
    the_library = Libraries.query.filter_by(lib_name=library).first()
    path = the_library.lib_folder
    episode_path = episode.slug
    episode_path = episode_path.replace("\\", "/")
    episode_path = f"{path}{episode_path}"
    duration = length_video(episode_path)
    file = f"""
#EXTM3U

#EXT-X-VERSION:4
#EXT-X-TARGETDURATION:{CHUNK_LENGTH}
#EXT-X-MEDIA-SEQUENCE:1
    """

    for i in range(0, int(duration), CHUNK_LENGTH):
        file += f"""
#EXTINF:{float(CHUNK_LENGTH)},
/chunk_serie/{episode_id}-{(i // CHUNK_LENGTH) + 1}.ts
        """

    file += """
#EXT-X-ENDLIST"""

    response = make_response(file)
    response.headers.set("Content-Type", "application/x-mpegURL")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set("Content-Disposition", "attachment", filename=f"{episode_id}")

    return response


@app.route("/video_serie/<quality>/<episode_id>", methods=["GET"])
def create_serie_m3u8_quality(quality, episode_id):
    episode = Episodes.query.filter_by(episode_id=episode_id).first()
    season = Seasons.query.filter_by(season_id=episode.season_id).first()
    serie = Series.query.filter_by(id=season.serie).first()
    library = serie.library_name
    the_library = Libraries.query.filter_by(lib_name=library).first()
    path = the_library.lib_folder
    episode_path = episode.slug
    episode_path = episode_path.replace("\\", "/")
    episode_path = f"{path}{episode_path}"
    duration = length_video(episode_path)
    file = f"""
#EXTM3U

#EXT-X-VERSION:4
#EXT-X-TARGETDURATION:{CHUNK_LENGTH}
#EXT-X-MEDIA-SEQUENCE:1
    """

    for i in range(0, int(duration), CHUNK_LENGTH):
        file += f"""
#EXTINF:{float(CHUNK_LENGTH)},
/chunk_serie/{quality}/{episode_id}-{(i // CHUNK_LENGTH) + 1}.ts
        """

    file += """
#EXT-X-ENDLIST"""

    response = make_response(file)
    response.headers.set("Content-Type", "application/x-mpegURL")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set("Content-Disposition", "attachment", filename=f"{episode_id}")

    return response


@app.route("/chunk_serie/<episode_id>-<int:idx>.ts", methods=["GET"])
def get_chunk_serie(episode_id, idx=0):
    seconds = (idx - 1) * CHUNK_LENGTH
    episode = Episodes.query.filter_by(episode_id=episode_id).first()
    season = Seasons.query.filter_by(season_id=episode.season_id).first()
    serie = Series.query.filter_by(id=season.serie).first()
    library = serie.library_name
    the_library = Libraries.query.filter_by(lib_name=library).first()
    path = the_library.lib_folder
    episode_path = episode.slug
    episode_path = episode_path.replace("\\", "/")
    episode_path = f"{path}{episode_path}"

    time_start = str(datetime.timedelta(seconds=seconds))
    time_end = str(datetime.timedelta(seconds=seconds + CHUNK_LENGTH))
    log_level_value = "error"
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        log_level_value,
        "-ss",
        time_start,
        "-to",
        time_end,
        "-i",
        episode_path,
        "-output_ts_offset",
        time_start,
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-b:a",
        "196k",
        "-ac",
        "2",
        "-f",
        "mpegts",
        "pipe:1",
    ]

    pipe = subprocess.Popen(command, stdout=subprocess.PIPE)

    response = make_response(pipe.stdout.read())
    response.headers.set("Content-Type", "video/MP2T")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{episode_id}-{idx}.ts"
    )

    return response


@app.route("/chunk_serie/<quality>/<episode_id>-<int:idx>.ts", methods=["GET"])
def get_chunk_serie_quality(quality, episode_id, idx=0):
    seconds = (idx - 1) * CHUNK_LENGTH
    episode = Episodes.query.filter_by(episode_id=episode_id).first()
    season = Seasons.query.filter_by(season_id=episode.season_id).first()
    serie = Series.query.filter_by(id=season.serie).first()
    library = serie.library_name
    the_library = Libraries.query.filter_by(lib_name=library).first()
    path = the_library.lib_folder
    episode_path = episode.slug
    episode_path = episode_path.replace("\\", "/")
    episode_path = f"{path}{episode_path}"

    time_start = str(datetime.timedelta(seconds=seconds))
    time_end = str(datetime.timedelta(seconds=seconds + CHUNK_LENGTH))
    video_properties = get_video_properties(episode_path)
    width = video_properties["width"]
    height = video_properties["height"]
    new_width = int(float(quality))
    new_height = round(float(width) / float(height) * new_width)
    if (new_height % 2) != 0:
        new_height += 1
    log_level_value = "error"

    bitrate = {
        "1080": "192k",
        "720": "192k",
        "480": "128k",
        "360": "128k",
        "240": "96k",
        "144": "64k",
    }

    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        log_level_value,
        "-ss",
        time_start,
        "-to",
        time_end,
        "-i",
        episode_path,
        "-output_ts_offset",
        time_start,
        "-c:v",
        "libx264",
        "-vf",
        f"scale={new_height}:{new_width}",
        "-c:a",
        "aac",
        "-b:a",
        bitrate[quality],
        "-ac",
        "2",
        "-f",
        "mpegts",
        "pipe:1",
    ]

    pipe = subprocess.Popen(command, stdout=subprocess.PIPE)

    response = make_response(pipe.stdout.read())
    response.headers.set("Content-Type", "video/MP2T")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{episode_id}-{idx}.ts"
    )

    return response


@app.route("/chunk_movie/<movie_id>-<int:idx>.ts", methods=["GET"])
def chunk_movie(movie_id, idx=0):
    seconds = (idx - 1) * CHUNK_LENGTH
    movie = Movies.query.filter_by(id=movie_id).first()
    slug = movie.slug
    library = movie.library_name
    the_library = Libraries.query.filter_by(lib_name=library).first()
    path = the_library.lib_folder
    video_path = f"{path}/{slug}"

    time_start = str(datetime.timedelta(seconds=seconds))
    time_end = str(datetime.timedelta(seconds=seconds + CHUNK_LENGTH))
    log_level_value = "error"

    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        log_level_value,
        "-ss",
        time_start,
        "-to",
        time_end,
        "-i",
        video_path,
        "-output_ts_offset",
        time_start,
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-b:a",
        "196k",
        "-ac",
        "2",
        "-f",
        "mpegts",
        "pipe:1",
    ]
    pipe = subprocess.Popen(command, stdout=subprocess.PIPE)

    response = make_response(pipe.stdout.read())
    response.headers.set("Content-Type", "video/MP2T")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{movie_id}-{idx}.ts"
    )

    return response


@app.route("/chunk_movie/<quality>/<movie_id>-<int:idx>.ts", methods=["GET"])
def get_chunk_quality(quality, movie_id, idx=0):
    seconds = (idx - 1) * CHUNK_LENGTH

    movie = Movies.query.filter_by(id=movie_id).first()
    slug = movie.slug
    library = movie.library_name
    the_library = Libraries.query.filter_by(lib_name=library).first()
    path = the_library.lib_folder
    video_path = f"{path}/{slug}"

    time_start = str(datetime.timedelta(seconds=seconds))
    time_end = str(datetime.timedelta(seconds=seconds + CHUNK_LENGTH))
    video_properties = get_video_properties(video_path)
    width = video_properties["width"]
    height = video_properties["height"]
    new_width = int(float(quality))
    new_height = round(float(width) / float(height) * new_width)
    while (new_height % 8) != 0:
        new_height += 1

    while (new_width % 8) != 0:
        new_width += 1

    a_bitrate = {
        "1080": "192k",
        "720": "192k",
        "480": "128k",
        "360": "128k",
        "240": "96k",
        "144": "64k",
    }

    a_bitrate = ((int(quality) - 144) / (1080 - 144)) * (192 - 64) + 64

    v_bitrate = ((int(quality) - 144) / (1080 - 144)) * (5000 - 1500) + 1500

    if v_bitrate < 1500:
        v_bitrate = 1500

    log_level_value = "error"
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        log_level_value,
        "-ss",
        time_start,
        "-to",
        time_end,
        "-i",
        video_path,
        "-output_ts_offset",
        time_start,
        "-c:v",
        "libx264",
        "-vf",
        f"scale={new_height}:{new_width}",
        "-c:a",
        "aac",
        "-b:a",
        f"{a_bitrate}k",
        "-ac",
        "2",
        "-f",
        "mpegts",
        "pipe:1",
    ]

    pipe = subprocess.Popen(command, stdout=subprocess.PIPE)

    response = make_response(pipe.stdout.read())
    response.headers.set("Content-Type", "video/MP2T")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{movie_id}-{idx}.ts"
    )

    return response


@app.route("/chunk_other/<hash>-<int:idx>.ts", methods=["GET"])
def get_chunk_other(hash, idx=0):
    seconds = (idx - 1) * CHUNK_LENGTH
    movie = OthersVideos.query.filter_by(video_hash=hash).first()
    video_path = movie.slug

    time_start = str(datetime.timedelta(seconds=seconds))
    time_end = str(datetime.timedelta(seconds=seconds + CHUNK_LENGTH))
    log_level_value = "error"

    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        log_level_value,
        "-ss",
        time_start,
        "-to",
        time_end,
        "-i",
        video_path,
        "-output_ts_offset",
        time_start,
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-b:a",
        "196k",
        "-ac",
        "2",
        "-f",
        "mpegts",
        "pipe:1",
    ]
    pipe = subprocess.Popen(command, stdout=subprocess.PIPE)

    response = make_response(pipe.stdout.read())
    response.headers.set("Content-Type", "video/MP2T")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{hash}-{idx}.ts"
    )

    return response


@app.route("/chunk_other/<quality>/<hash>-<int:idx>.ts", methods=["GET"])
def get_chunk_other_quality(quality, hash, idx=0):
    seconds = (idx - 1) * CHUNK_LENGTH
    movie = OthersVideos.query.filter_by(video_hash=hash).first()
    video_path = movie.slug

    time_start = str(datetime.timedelta(seconds=seconds))
    time_end = str(datetime.timedelta(seconds=seconds + CHUNK_LENGTH))
    video_properties = get_video_properties(video_path)
    width = video_properties["width"]
    height = video_properties["height"]
    new_width = int(float(quality))
    new_height = round(float(width) / float(height) * new_width)
    if (new_height % 2) != 0:
        new_height += 1

    bitrate = {
        "1080": "192k",
        "720": "192k",
        "480": "128k",
        "360": "128k",
        "240": "96k",
        "144": "64k",
    }

    log_level_value = "error"
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        log_level_value,
        "-ss",
        time_start,
        "-to",
        time_end,
        "-i",
        video_path,
        "-output_ts_offset",
        time_start,
        "-c:v",
        "libx264",
        "-vf",
        f"scale={new_height}:{new_width}",
        "-c:a",
        "aac",
        "-b:a",
        bitrate[quality],
        "-ac",
        "2",
        "-f",
        "mpegts",
        "pipe:1",
    ]

    pipe = subprocess.Popen(command, stdout=subprocess.PIPE)

    response = make_response(pipe.stdout.read())
    response.headers.set("Content-Type", "video/MP2T")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{hash}-{idx}.ts"
    )

    return response


@app.route("/chunk_caption/<index>/<movie_id>.vtt", methods=["GET"])
def chunk_caption(movie_id, index):
    movie = Movies.query.filter_by(id=movie_id).first()
    slug = movie.slug
    library = movie.library_name
    the_library = Libraries.query.filter_by(lib_name=library).first()
    path = the_library.lib_folder
    video_path = f"{path}/{slug}"
    extract_captions_command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        video_path,
        "-map",
        f"0:{index}",
        "-f",
        "webvtt",
        "pipe:1",
    ]
    extract_captions = subprocess.run(extract_captions_command, stdout=subprocess.PIPE)

    extract_captions_response = make_response(extract_captions.stdout)
    extract_captions_response.headers.set("Content-Type", "text/VTT")
    extract_captions_response.headers.set(
        "Content-Disposition", "attachment", filename=f"{index}/{movie_id}.vtt"
    )

    return extract_captions_response


@app.route("/captionMovie/<movie_id>_<id>.m3u8", methods=["GET"])
def caption_movie_by_id_to_m3_u8(movie_id, id):
    movie = Movies.query.filter_by(id=movie_id).first()
    duration = movie.duration
    duration = sum(x * int(t) for x, t in zip([3600, 60, 1], duration.split(":")))
    text = f"""
#EXTM3U
#EXT-X-TARGETDURATION:887
#EXT-X-VERSION:3
#EXT-X-MEDIA-SEQUENCE:1
#EXT-X-PLAYLIST-TYPE:VOD
#EXTINF:{float(duration)+1},
/chunk_caption/{id}/{movie_id}.vtt
#EXT-X-ENDLIST
    """
    response = make_response(text)
    response.headers.set("Content-Type", "application/x-mpegURL")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{movie_id}_{id}.m3u8"
    )

    return response



@app.route("/chunk_caption_serie/<language>/<index>/<episode_id>.vtt", methods=["GET"])
def chunk_caption_serie(language, index, episode_id):
    episode = Episodes.query.filter_by(episode_id=episode_id).first()
    season = Seasons.query.filter_by(season_id=episode.season_id).first()
    serie = Series.query.filter_by(id=season.serie).first()
    library = serie.library_name
    the_library = Libraries.query.filter_by(lib_name=library).first()
    path = the_library.lib_folder
    episode_path = episode.slug
    episode_path = episode_path.replace("\\", "/")
    video_path = f"{path}{episode_path}"

    extract_captions_command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        video_path,
        "-map",
        f"0:{index}",
        "-f",
        "webvtt",
        "pipe:1",
    ]

    extract_captions = subprocess.run(extract_captions_command, stdout=subprocess.PIPE)

    extract_captions_response = make_response(extract_captions.stdout)
    extract_captions_response.headers.set("Content-Type", "text/VTT")
    extract_captions_response.headers.set(
        "Content-Disposition",
        "attachment",
        filename=f"{language}/{index}/{episode_id}.vtt",
    )

    return extract_captions_response


@app.route("/get_language", methods=["GET"])
def get_language():
    language = config["ChocolateSettings"]["language"]
    return jsonify({"language": language})


@app.route("/get_all_movies/<library>", methods=["GET"])
def get_all_movies(library):
    token = request.headers.get("Authorization")
    check_authorization(request, token, library)
    generate_log(request, "SERVER")
    username = all_auth_tokens[token]["user"]

    movies = Movies.query.filter_by(library_name=library).all()
    the_lib = Libraries.query.filter_by(lib_name=library).first()
    user = Users.query.filter_by(name=username).first()

    movies_list = [movie.__dict__ for movie in movies]
    # get the user from the database
    # get the user type
    user_type = user.account_type
    for movie in movies_list:
        del movie["_sa_instance_state"]

    if user_type in ["Kid", "Teen"]:
        for movie in movies_list:
            if movie["adult"] == "True":
                movies_list.remove(movie)

    movies_list = sorted(movies_list, key=lambda k: k["real_title"].lower())

    return jsonify(movies_list)


@app.route("/get_all_books/<library>", methods=["GET"])
def get_all_books(library):
    token = request.headers.get("Authorization")
    check_authorization(request, token, library)
    generate_log(request, "SUCCESS")

    username = all_auth_tokens[token]["user"]
    books = Books.query.filter_by(library_name=library).all()
    books_list = [book.__dict__ for book in books]

    user = Users.query.filter_by(name=username).first()

    user_type = user.account_type
    for book in books_list:
        del book["_sa_instance_state"]

    books_list = sorted(books_list, key=lambda k: k["title"].lower())

    return jsonify(books_list)


@app.route("/get_all_playlists/<library>", methods=["GET"])
def get_all_playlists(library):
    token = request.headers.get("Authorization")
    check_authorization(request, token, library)
    generate_log(request, "SUCCESS")

    username = all_auth_tokens[token]["user"]
    user = Users.query.filter_by(name=username).first()
    user_id = user.id

    playlists = Playlist.query.filter(
        Playlist.user_id.like(f"%{user_id}%"), Playlist.library_name == library
    ).all()
    playlists_list = [playlist.__dict__ for playlist in playlists]

    for playlist in playlists_list:
        del playlist["_sa_instance_state"]

    playlists_list = sorted(playlists_list, key=lambda k: k["name"].lower())

    liked_music = MusicLiked.query.filter_by(user_id=user_id, liked="true").all()
    musics = ""
    for music in liked_music:
        music_id = music.music_id

        musics += f"{music_id},"
    musics = musics[:-1]

    if len(musics) > 0:
        playlists_list.insert(
            0,
            {
                "id": 0,
                "name": "Likes",
                "tracks": musics,
                "cover": "/static/img/likes.webp",
            },
        )

    return jsonify(playlists_list)


@app.route("/get_all_albums/<library>", methods=["GET"])
def get_all_albums(library):
    token = request.headers.get("Authorization")
    check_authorization(request, token, library)
    generate_log(request, "SUCCESS")

    albums = Album.query.filter_by(library_name=library).all()
    albums_list = [album.__dict__ for album in albums]

    for album in albums_list:
        del album["_sa_instance_state"]

    albums_list = sorted(albums_list, key=lambda k: k["name"].lower())

    return jsonify(albums_list)


@app.route("/get_all_artists/<library>", methods=["GET"])
def get_all_artists(library):
    token = request.headers.get("Authorization")
    check_authorization(request, token, library)
    generate_log(request, "SUCCESS")

    artists = Artist.query.filter_by(library_name=library).all()
    artists_list = [artist.__dict__ for artist in artists]

    for artist in artists_list:
        del artist["_sa_instance_state"]

    artists_list = sorted(artists_list, key=lambda k: k["name"].lower())

    return jsonify(artists_list)


@app.route("/get_all_tracks/<library>", methods=["GET"])
def get_all_tracks(library):
    token = request.headers.get("Authorization")
    check_authorization(request, token, library)
    generate_log(request, "SUCCESS")

    tracks = Track.query.filter_by(library_name=library).all()
    tracks_list = [track.__dict__ for track in tracks]

    for track in tracks_list:
        del track["_sa_instance_state"]
        try:
            album_name = Album.query.filter_by(id=track["album_id"]).first().name
            track["album_name"] = album_name
        except:
            track["album_name"] = None

        try:
            artist_name = Artist.query.filter_by(id=track["artist_id"]).first().name
            track["artist_name"] = artist_name
        except:
            track["artist_name"] = None

    tracks_list = sorted(tracks_list, key=lambda k: k["name"].lower())

    return jsonify(tracks_list)


@app.route("/get_album_tracks/<album_id>")
def get_album_tracks(album_id):
    token = request.headers.get("Authorization")

    try:
        user = all_auth_tokens[token]["user"]
        generate_log(request, "SUCCESS")
    except:
        generate_log(request, "ERROR")
        return jsonify({"error": "Invalid token"})

    user = Users.query.filter_by(name=user).first()
    user_id = user.id

    tracks = Track.query.filter_by(album_id=album_id).all()
    tracks_list = [track.__dict__ for track in tracks]

    artist = Artist.query.filter_by(id=tracks_list[0]["artist_id"]).first().name
    album = Album.query.filter_by(id=tracks_list[0]["album_id"]).first().name

    for track in tracks_list:
        del track["_sa_instance_state"]

        track["artist_name"] = artist
        track["album_name"] = album

        music_like = MusicLiked.query.filter_by(
            music_id=track["id"], user_id=user_id
        ).first()
        if music_like:
            track["liked"] = music_like.liked
        else:
            track["liked"] = False

    return jsonify(tracks_list)


@app.route("/get_playlist_tracks/<playlist_id>")
def get_playlist_tracks(playlist_id):
    token = request.headers.get("Authorization")

    try:
        user = all_auth_tokens[token]["user"]
        generate_log(request, "SUCCESS")
    except:
        generate_log(request, "ERROR")
        return jsonify({"error": "Invalid token"})

    user = Users.query.filter_by(name=user).first()
    user_id = user.id
    tracks_list = []
    if playlist_id != "0":
        # tracks = Playlist.query.filter(Playlist.user_id.like(f"%{user_id}%"), id=playlist_id).first()
        tracks = Playlist.query.filter(
            Playlist.user_id.like(f"%{user_id}%"), Playlist.id == playlist_id
        ).first()
        tracks = tracks.tracks.split(",")
        for track in tracks:
            track = Track.query.filter_by(id=track).first().__dict__

            del track["_sa_instance_state"]

            music_like = MusicLiked.query.filter_by(
                music_id=track["id"], user_id=user_id
            ).first()
            if music_like:
                track["liked"] = music_like.liked
            else:
                track["liked"] = False

            if "album_id" in track:
                album = Album.query.filter_by(id=track["album_id"]).first()
                if album:
                    track["album_name"] = album.name

            if "artist_id" in track:
                artist = Artist.query.filter_by(id=track["artist_id"]).first()
                if artist:
                    track["artist_name"] = artist.name

            tracks_list.append(track)
    else:
        likes = MusicLiked.query.filter_by(user_id=user_id, liked="true").all()
        for like in likes:
            track = Track.query.filter_by(id=like.music_id).first().__dict__

            del track["_sa_instance_state"]

            music_like = MusicLiked.query.filter_by(
                music_id=track["id"], user_id=user_id
            ).first()
            track["liked"] = music_like.liked
            track["liked_at"] = music_like.liked_at

            if "album_id" in track:
                album = Album.query.filter_by(id=track["album_id"]).first()
                track["album_name"] = album.name

            if "artist_id" in track:
                artist = Artist.query.filter_by(id=track["artist_id"]).first()
                track["artist_name"] = artist.name

            tracks_list.append(track)

        tracks_list = sorted(tracks_list, key=lambda k: k["liked_at"])

    return jsonify(tracks_list)


@app.route("/play_track/<id>/<user_id>", methods=["POST"])
def play_track(id, user_id):
    exists_in_music_played = MusicPlayed.query.filter_by(
        music_id=id, user_id=user_id
    ).first()
    play_count = 0
    if exists_in_music_played:
        exists_in_music_played.play_count = int(exists_in_music_played.play_count) + 1
        DB.session.commit()
        play_count = exists_in_music_played.play_count
    else:
        music_played = MusicPlayed(music_id=id, user_id=user_id, play_count=1)
        DB.session.add(music_played)
        DB.session.commit()
        play_count = music_played.play_count

    return jsonify(
        {
            "status": "success",
            "music_id": id,
            "user_id": user_id,
            "play_count": play_count,
        }
    )


@app.route("/like_track/<id>/<user_id>", methods=["POST"])
def like_track(id, user_id):
    exist_in_mucis_liked = MusicLiked.query.filter_by(
        music_id=id, user_id=user_id
    ).first()
    liked = False
    like_dict = {"true": "false", "false": "true"}
    if exist_in_mucis_liked:
        exist_in_mucis_liked.liked = like_dict[exist_in_mucis_liked.liked]
        liked = like_dict[exist_in_mucis_liked.liked]
        exist_in_mucis_liked.liked_at = time()
        DB.session.commit()
    else:
        music_liked = MusicLiked(
            music_id=id, user_id=user_id, liked="true", liked_at=time()
        )
        DB.session.add(music_liked)
        DB.session.commit()
        liked = music_liked.liked

    return jsonify(
        {"status": "success", "music_id": id, "user_id": user_id, "liked": liked}
    )


@app.route("/create_playlist", methods=["POST"])
def create_playlist():
    body = request.get_json()

    name = body["name"]
    user_id = body["user_id"]
    track_id = body["track_id"]
    library = body["library"]

    exists = Playlist.query.filter_by(
        name=name, user_id=user_id, library_name=library
    ).first()
    if exists:
        return jsonify({"status": "error", "error": "Playlist already exists"})
    track = Track.query.filter_by(id=track_id).first()
    duration = 0
    cover = track.cover
    cover = generate_playlist_cover(track_id)
    if not cover:
        cover = "ahaha"
    playlist = Playlist(
        name=name,
        user_id=user_id,
        tracks=f"{track_id}",
        library_name=library,
        duration=duration,
        cover=cover,
    )
    DB.session.add(playlist)
    DB.session.commit()

    return jsonify({"status": "success", "playlist_id": playlist.id})


def generate_playlist_cover(id):
    if type(id) == str or type(id) == int:
        id = int(id)
        track = Track.query.filter_by(id=id).first()
        cover = track.cover
        return cover
    elif type(id) == list:
        # prends les 4 premiers, si y en a moins ajoute le premier, le deuxieme, etc
        tracks = []
        id_to_append = 0
        for i in range(4):
            try:
                tracks.append(id[i])
            except:
                tracks.append(id[id_to_append])
                id_to_append += 1

        covers = []
        for track in tracks:
            track = Track.query.filter_by(id=track).first()

            covers.append(dir_path + track.cover)

        # fusionne les 4 covers en une image, dans chaque coin, enregistre et renvoie l'url
        im1 = Image.open(covers[0])
        im2 = Image.open(covers[1])
        im3 = Image.open(covers[2])
        im4 = Image.open(covers[3])

        im1 = im1.resize((200, 200))
        im2 = im2.resize((200, 200))
        im3 = im3.resize((200, 200))
        im4 = im4.resize((200, 200))

        im1 = im1.crop((0, 0, 100, 100))
        im2 = im2.crop((100, 0, 200, 100))
        im3 = im3.crop((0, 100, 100, 200))
        im4 = im4.crop((100, 100, 200, 200))

        im = Image.new("RGB", (200, 200))
        im.paste(im1, (0, 0))
        im.paste(im2, (100, 0))
        im.paste(im3, (0, 100))
        im.paste(im4, (100, 100))

        cover = f"/static/img/mediaImages/Playlist_{uuid4()}.webp"
        im.save(dir_path + cover, "WEBP")

        return cover


@app.route("/add_track_to_playlist", methods=["POST"])
def add_track_to_playlist():
    body = request.get_json()

    playlist_id = body["playlist_id"]
    track_id = body["track_id"]

    playlist = Playlist.query.filter_by(id=playlist_id).first()
    if playlist.tracks == "":
        playlist.tracks = track_id
    else:
        playlist.tracks += f",{track_id}"
    cover = generate_playlist_cover(playlist.tracks.split(","))
    playlist.cover = cover
    DB.session.commit()

    return jsonify(
        {"status": "success", "playlist_id": playlist_id, "track_id": track_id}
    )


@app.route("/get_track/<id>")
def get_track(id):
    track = Track.query.filter_by(id=id).first().slug

    return send_file(track)


@app.route("/get_album/<album_id>")
def get_album(album_id):
    generate_log(request, "SUCCESS")

    album = Album.query.filter_by(id=album_id).first()
    album_dict = album.__dict__
    del album_dict["_sa_instance_state"]

    artist = Artist.query.filter_by(id=album_dict["artist_id"]).first().name
    album_dict["artist_name"] = artist

    return jsonify(album_dict)


@app.route("/get_playlist/<playlist_id>")
def get_playlist(playlist_id):
    generate_log(request, "SUCCESS")
    token = request.headers.get("Authorization")
    user = all_auth_tokens[token]["user"]
    user = Users.query.filter_by(name=user).first()
    user_id = user.id

    if playlist_id != "0":
        playlist = Playlist.query.filter_by(id=playlist_id).first()
        playlist_dict = playlist.__dict__
        del playlist_dict["_sa_instance_state"]
    else:
        liked_music = MusicLiked.query.filter_by(user_id=user_id, liked="true").all()
        musics = ""
        for music in liked_music:
            music_id = music.music_id
            liked = music.liked
            musics += f"{music_id},"
        musics = musics[:-1]

        playlist_dict = {
            "id": 0,
            "name": "Likes",
            "tracks": musics,
            "cover": "/static/img/likes.webp",
        }

    return jsonify(playlist_dict)


@app.route("/get_artist/<artist_id>")
def get_artist(artist_id):
    generate_log(request, "SUCCESS")

    artist = Artist.query.filter_by(id=artist_id).first()
    artist_dict = artist.__dict__
    del artist_dict["_sa_instance_state"]

    return jsonify(artist_dict)


@app.route("/get_artist_albums/<artist_id>")
def get_artist_albums(artist_id):
    token = request.headers.get("Authorization")
    generate_log(request, "SUCCESS")

    albums = Album.query.filter_by(artist_id=artist_id).all()
    albums_list = [album.__dict__ for album in albums]

    for album in albums_list:
        del album["_sa_instance_state"]

    return jsonify(albums_list)


@app.route("/get_artist_tracks/<artist_id>")
def get_artist_tracks(artist_id):
    generate_log(request, "SUCCESS")

    tracks = Track.query.filter_by(artist_id=artist_id).all()
    tracks_list = [track.__dict__ for track in tracks]

    for track in tracks_list:
        del track["_sa_instance_state"]
        try:
            album_name = Album.query.filter_by(id=track["album_id"]).first().name
            track["album_name"] = album_name
        except:
            pass

        try:
            artist_name = Artist.query.filter_by(id=track["artist_id"]).first().name
            track["artist_name"] = artist_name
        except:
            pass

    return jsonify(tracks_list)

@app.route("/get_all_series/<library>", methods=["GET"])
def get_all_series(library):
    token = request.headers.get("Authorization")
    if token not in all_auth_tokens:
        abort(401)

    generate_log(request, "SUCCESS")

    username = all_auth_tokens[token]["user"]

    series = Series.query.filter_by(library_name=library).all()
    the_lib = Libraries.query.filter_by(lib_name=library).first()
    user = Users.query.filter_by(name=username).first()
    user_id = user.id
    user_in_the_lib = user_in_lib(user_id, the_lib)

    if not user_in_the_lib:
        abort(401)

    if series is None or user is None:
        abort(404)

    series_list = [serie.__dict__ for serie in series]

    user_type = user.account_type
    for serie in series_list:
        del serie["_sa_instance_state"]

    if user_type in ["Kid", "Teen"]:
        for serie in series_list:
            if serie["adult"] == "True":
                series_list.remove(serie)

    for serie in series_list:
        serie["seasons"] = get_seasons(serie["id"])

    series_list = sorted(series_list, key=lambda k: k["original_name"].lower())

    return jsonify(series_list)


def get_seasons(id):
    seasons = Seasons.query.filter_by(serie=id).all()
    seasons_list = [season.__dict__ for season in seasons]
    for season in seasons_list:
        del season["_sa_instance_state"]

    return seasons_list


def get_similar_movies(movie_id):
    global searched_films
    similar_movies_possessed = []
    movie = Movie()
    similar_movies = movie.recommendations(movie_id)
    for movie_info in similar_movies:
        movie_name = movie_info.title
        for movie in searched_films:
            if movie_name == movie:
                similar_movies_possessed.append(movie)
                break
    return similar_movies_possessed



@app.route("/get_movie_data/<movie_id>", methods=["GET"])
def get_movie_data(movie_id):
    exists = Movies.query.filter_by(id=movie_id).first() is not None
    if exists:
        movie = Movies.query.filter_by(id=movie_id).first().__dict__
        del movie["_sa_instance_state"]
        movie["similarMovies"] = get_similar_movies(movie_id)
        return jsonify(movie)
    else:
        abort(404)


@app.route("/get_other_data/<video_hash>", methods=["GET"])
def get_other_data(video_hash):
    exists = OthersVideos.query.filter_by(video_hash=video_hash).first() is not None
    if exists:
        other = OthersVideos.query.filter_by(video_hash=video_hash).first().__dict__
        del other["_sa_instance_state"]
        return jsonify(other)
    else:
        abort(404)


@app.route("/get_serie_data/<serie_id>", methods=["GET"])
def get_series_data(serie_id):
    exists = Series.query.filter_by(id=serie_id).first() is not None
    if exists:
        serie = Series.query.filter_by(id=serie_id).first().__dict__
        serie["seasons"] = get_serie_seasons(serie["id"])

        latest_episode_watched_db = LatestEpisodeWatched.query.filter_by(
            serie_id=serie_id
        ).first()
        if latest_episode_watched_db is not None:
            serie["latest_id"] = latest_episode_watched_db.episode_id
        else:
            serie["latest_id"] = None

        del serie["_sa_instance_state"]
        return jsonify(serie)
    else:
        abort(404)


def get_serie_seasons(id):
    seasons = Seasons.query.filter_by(serie=id).all()
    seasons_dict = {}
    for season in seasons:
        seasons_dict[season.season_number] = dict(season.__dict__)
        del seasons_dict[season.season_number]["_sa_instance_state"]
    return seasons_dict


def transform(obj):
    if isinstance(obj, AsObj):
        return str(obj)
    return obj.replace('"', '\\"')


@app.route("/edit_movie/<id>/<library>", methods=["GET", "POST"])
def edit_movie(id, library):
    if request.method == "GET":
        the_movie = Movies.query.filter_by(id=id, library_name=library).first()
        the_movie = the_movie.__dict__
        del the_movie["_sa_instance_state"]
        movie_name = guessit(the_movie["title"])["title"]
        file_title = the_movie["slug"]
        tmdb = TMDb()
        tmdb.language = config["ChocolateSettings"]["language"].lower()
        movie = Movie()
        movie_info = Search().movies(movie_name)
        movie_info = sorted(movie_info, key=lambda k: k["popularity"], reverse=True)

        real_movies = []
        for the_movie in movie_info:
            accepted_types = [str, int, list, dict, float, bool]
            the_movie = the_movie.__dict__
            for key in the_movie:
                if type(the_movie[key]) not in accepted_types:
                    the_movie[key] = str(the_movie[key])
            real_movies.append(the_movie)

        movies = {"movies": real_movies, "file_title": file_title}

        return jsonify(movies)

    new_movie_id = request.get_json()["new_id"]
    print(f"The id: {id} and the new id: {new_movie_id}")
    the_movie = Movies.query.filter_by(id=id, library_name=library).first()
    
    movie = Movie()
    movie_info = movie.details(new_movie_id)
    the_movie.id = new_movie_id
    the_movie.real_title = movie_info.title
    the_movie.description = movie_info.overview
    the_movie.note = movie_info.vote_average
    date = movie_info.release_date

    try:
        date = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError as e:
        date = "Unknown"
    except UnboundLocalError:
        date = "Unknown"

    the_movie.date = date

    bande_annonce = movie_info.videos.results

    bande_annonce_url = ""
    if len(bande_annonce) > 0:
        for video in bande_annonce:
            bande_annonce_type = video.type
            bande_annonce_host = video.site
            bande_annonce_key = video.key
            if bande_annonce_type == "Trailer":
                try:
                    bande_annonce_url = websites_trailers[bande_annonce_host] + bande_annonce_key
                    break
                except KeyError as e:
                    bande_annonce_url = "Unknown"
                    print(e)

    the_movie.bande_annonce_url = bande_annonce_url
    the_movie.adult = str(movie_info.adult)

    alternatives_names = []
    actual_title = movie_info.title
    characters = [" ", "-", "_", ":", ".", ",", "!", "'", "`", '"']
    empty = ""
    for character in characters:
        for character2 in characters:
            if character != character2:
                string_test = actual_title.replace(character, character2)
                alternatives_names.append(string_test)
                string_test = actual_title.replace(character2, character)
                alternatives_names.append(string_test)
                string_test = actual_title.replace(character, empty)
                alternatives_names.append(string_test)
                string_test = actual_title.replace(character2, empty)
                alternatives_names.append(string_test)

    official_alternative_names = movie.alternative_titles(movie_id=the_movie.id).titles
    if official_alternative_names is not None:
        for official_alternative_name in official_alternative_names:
            alternatives_names.append(official_alternative_name.title)

    alternatives_names = list(dict.fromkeys(alternatives_names))

    alternatives_names = ",".join(alternatives_names)

    the_movie.alternatives_names = alternatives_names

    the_movie.vues = str({})

    movie_genre = []
    genre = movie_info.genres
    for genre_info in genre:
        movie_genre.append(genre_info.name)
    movie_genre = jsonify(movie_genre)

    the_movie.genre = movie_genre
    casts = movie_info.casts.__dict__["cast"]
    
    the_cast = []
    for cast in casts:
        character_name = cast.character
        actor_id = cast.id
        actor_image = f"https://www.themoviedb.org/t/p/w600_and_h900_bestv2{cast.profile_path}"
        if not os.path.exists(f"{dir_path}/static/img/mediaImages/Actor_{actor_id}.webp"):
            with open(
                f"{dir_path}/static/img/mediaImages/Actor_{actor_id}.png", "wb"
            ) as f:
                f.write(requests.get(actor_image).content)
            try:
                img = Image.open(
                    f"{dir_path}/static/img/mediaImages/Actor_{actor_id}.png"
                )
                img = img.save(
                    f"{dir_path}/static/img/mediaImages/Actor_{actor_id}.webp", "webp"
                )
                os.remove(f"{dir_path}/static/img/mediaImages/Actor_{actor_id}.png")
            except Exception as e:
                os.rename(
                    f"{dir_path}/static/img/mediaImages/Actor_{actor_id}.png",
                    f"{dir_path}/static/img/mediaImages/Actor_{actor_id}.webp",
                )

        actor_image = f"/static/img/mediaImages/Actor_{actor_id}.webp"
        actor = [cast.name, character_name, actor_image, cast.id]
        if actor not in the_cast:
            the_cast.append(actor)
        else:
            break
        person = Person()
        p = person.details(cast.id)
        exists = Actors.query.filter_by(actor_id=cast.id).first() is not None
        if not exists:
            actor = Actors(
                name=cast.name,
                actor_image=actor_image,
                actor_description=p.biography,
                actor_birth_date=p.birthday,
                actor_birth_place=p.place_of_birth,
                actor_programs=f"{the_movie.id}",
                actor_id=actor_id,
            )
            DB.session.add(actor)
            DB.session.commit()
        elif exists and str(the_movie.id) not in Actors.query.filter_by(actor_id=cast.id).first().actor_programs:
            actor = Actors.query.filter_by(actor_id=cast.id).first()
            actor.actor_programs = f"{actor.actor_programs} {the_movie.id}"
            DB.session.commit()

    the_cast = jsonify(the_cast)
    the_movie.cast = the_cast

    movie_cover_path = f"https://image.tmdb.org/t/p/original{movie_info.poster_path}"
    banniere = f"https://image.tmdb.org/t/p/original{movie_info.backdrop_path}"

    try:
        os.remove(f"{dir_path}/static/img/mediaImages/{new_movie_id}_cover.webp")
    except FileNotFoundError:
        pass
    try:
        os.remove(f"{dir_path}/static/img/mediaImages/{new_movie_id}_cover.png")
    except FileNotFoundError:
        pass
    with open(f"{dir_path}/static/img/mediaImages/{new_movie_id}_cover.png", "wb") as f:
        f.write(requests.get(movie_cover_path).content)
    try:
        img = Image.open(f"{dir_path}/static/img/mediaImages/{new_movie_id}_cover.png")
        img.save(f"{dir_path}/static/img/mediaImages/{new_movie_id}_cover.webp", "webp")
        os.remove(f"{dir_path}/static/img/mediaImages/{new_movie_id}_cover.png")
        movie_cover_path = f"/static/img/mediaImages/{new_movie_id}_cover.webp"
    except:
        os.rename(
            f"{dir_path}/static/img/mediaImages/{new_movie_id}_cover.png",
            f"{dir_path}/static/img/mediaImages/{new_movie_id}_cover.webp",
        )
        movie_cover_path = "/static/img/broken.webp"
    try:
        os.remove(f"{dir_path}/static/img/mediaImages/{new_movie_id}_Banner.webp")
    except FileNotFoundError:
        pass
    with open(
        f"{dir_path}/static/img/mediaImages/{new_movie_id}_Banner.png", "wb"
    ) as f:
        f.write(requests.get(banniere).content)
    if movie_info.backdrop_path == None:
        banniere = f"https://image.tmdb.org/t/p/original{movie_info.backdrop_path}"
        if banniere != "https://image.tmdb.org/t/p/originalNone":
            with open(
                f"{dir_path}/static/img/mediaImages/{new_movie_id}_Banner.png", "wb"
            ) as f:
                f.write(requests.get(banniere).content)
        else:
            banniere = "/static/img/broken.webp"
    try:
        img = Image.open(f"{dir_path}/static/img/mediaImages/{new_movie_id}_Banner.png")
        img.save(
            f"{dir_path}/static/img/mediaImages/{new_movie_id}_Banner.webp", "webp"
        )
        os.remove(f"{dir_path}/static/img/mediaImages/{new_movie_id}_Banner.png")
        banniere = f"/static/img/mediaImages/{new_movie_id}_Banner.webp"
    except:
        os.rename(
            f"{dir_path}/static/img/mediaImages/{new_movie_id}_Banner.png",
            f"{dir_path}/static/img/mediaImages/{new_movie_id}_Banner.webp",
        )
        banniere = "/static/img/brokenBanner.webp"

    the_movie.cover = movie_cover_path
    the_movie.banner = banniere
    DB.session.commit()

    return jsonify({"status": "success"})


@app.route("/edit_serie/<id>/<library>", methods=["GET", "POST"])
def edit_serie(id, library):
    if request.method == "GET":
        serie = (
            Series.query.filter_by(id=id, library_name=library)
            .first()
            .__dict__
        )

        del serie["_sa_instance_state"]
        serie_name = serie["original_name"]
        tmdb = TMDb()
        tmdb.language = config["ChocolateSettings"]["language"].lower()
        series = TV()
        serie_info = Search().tv_shows(serie_name)
        serie_info = sorted(serie_info, key=lambda k: k["popularity"], reverse=True)

        real_series = []
        for the_serie in serie_info:
            accepted_types = [str, int, list, dict, float, bool]
            the_serie = the_serie.__dict__
            for key in the_serie:
                if type(the_serie[key]) not in accepted_types:
                    the_serie[key] = str(the_serie[key])
            real_series.append(the_serie)

        data = {
            "series": real_series,
            "folder_title": serie["original_name"],
        }

        return jsonify(data, default=transform, indent=4)

    elif request.method == "POST":
        serie_id = request.get_json()["new_id"]
        the_serie = Series.query.filter_by(
            id=id, library_name=library
        ).first()

        if the_serie.id == serie_id:
            return jsonify({"status": "success"})

        all_seasons = Seasons.query.filter_by(serie=serie_id).all()
        for season in all_seasons:
            cover = f"{dir_path}{season.season_cover_path}"
            try:
                os.remove(cover)
            except FileNotFoundError:
                pass
            episodes = Episodes.query.filter_by(season_id=season.season_number).all()
            for episode in episodes:
                cover = f"{dir_path}{episode.episode_cover_path}"
                os.remove(cover)
                DB.session.delete(episode)
            DB.session.delete(season)
        DB.session.commit()

        tmdb = TMDb()
        tmdb.language = config["ChocolateSettings"]["language"].lower()
        show = TV()
        details = show.details(serie_id)
        res = details

        name = details.name
        serie_cover_path = f"https://image.tmdb.org/t/p/original{res.poster_path}"
        banniere = f"https://image.tmdb.org/t/p/original{res.backdrop_path}"
        if not os.path.exists(
            f"{dir_path}/static/img/mediaImages/{serie_id}_Cover.webp"
        ):
            with open(
                f"{dir_path}/static/img/mediaImages/{serie_id}_Cover.png", "wb"
            ) as f:
                f.write(requests.get(serie_cover_path).content)

            img = Image.open(f"{dir_path}/static/img/mediaImages/{serie_id}_Cover.png")
            img = img.save(
                f"{dir_path}/static/img/mediaImages/{serie_id}_Cover.webp", "webp"
            )
            os.remove(f"{dir_path}/static/img/mediaImages/{serie_id}_Cover.png")
        else:
            os.remove(f"{dir_path}/static/img/mediaImages/{serie_id}_Cover.webp")
            with open(
                f"{dir_path}/static/img/mediaImages/{serie_id}_Cover.png", "wb"
            ) as f:
                f.write(requests.get(serie_cover_path).content)

            img = Image.open(f"{dir_path}/static/img/mediaImages/{serie_id}_Cover.png")
            img = img.save(
                f"{dir_path}/static/img/mediaImages/{serie_id}_Cover.webp", "webp"
            )
            os.remove(f"{dir_path}/static/img/mediaImages/{serie_id}_Cover.png")

        if not os.path.exists(
            f"{dir_path}/static/img/mediaImages/{serie_id}_Banner.webp"
        ):
            with open(
                f"{dir_path}/static/img/mediaImages/{serie_id}_Banner.png", "wb"
            ) as f:
                f.write(requests.get(banniere).content)

            img = Image.open(f"{dir_path}/static/img/mediaImages/{serie_id}_Banner.png")
            img = img.save(
                f"{dir_path}/static/img/mediaImages/{serie_id}_Banner.webp", "webp"
            )
            os.remove(f"{dir_path}/static/img/mediaImages/{serie_id}_Banner.png")
        else:
            os.remove(f"{dir_path}/static/img/mediaImages/{serie_id}_Banner.webp")
            with open(
                f"{dir_path}/static/img/mediaImages/{serie_id}_Banner.png", "wb"
            ) as f:
                f.write(requests.get(banniere).content)
            img = Image.open(f"{dir_path}/static/img/mediaImages/{serie_id}_Banner.png")
            img = img.save(
                f"{dir_path}/static/img/mediaImages/{serie_id}_Banner.webp", "webp"
            )
            os.remove(f"{dir_path}/static/img/mediaImages/{serie_id}_Banner.png")

        banniere = f"/static/img/mediaImages/{serie_id}_Banner.webp"
        serie_cover_path = f"/static/img/mediaImages/{serie_id}_Cover.webp"
        description = res["overview"]
        note = res.vote_average
        date = res.first_air_date
        cast = details.credits.cast
        run_time = details.episode_run_time
        duration = ""
        for i in range(len(run_time)):
            if i != len(run_time) - 1:
                duration += f"{str(run_time[i])}:"
            else:
                duration += f"{str(run_time[i])}"
        serie_genre = details.genres
        bande_annonce = details.videos.results
        bande_annonce_url = ""
        if len(bande_annonce) > 0:
            for video in bande_annonce:
                bande_annonce_type = video.type
                bande_annonce_host = video.site
                bande_annonce_key = video.key
                if bande_annonce_type == "Trailer" or len(bande_annonce) == 1:
                    try:
                        bande_annonce_url = (
                            websites_trailers[bande_annonce_host] + bande_annonce_key
                        )
                        break
                    except KeyError as e:
                        bande_annonce_url = "Unknown"
                        print(e)
        genre_list = []
        for genre in serie_genre:
            genre_list.append(str(genre.name))
        new_cast = []
        cast = list(cast)[:5]
        for actor in cast:
            actor_name = actor.name.replace("/", "")
            actor_id = actor.id
            actor_image = f"https://image.tmdb.org/t/p/original{actor.profile_path}"
            if not os.path.exists(
                f"{dir_path}/static/img/mediaImages/Actor_{actor_id}.webp"
            ):
                with open(
                    f"{dir_path}/static/img/mediaImages/Actor_{actor_id}.png", "wb"
                ) as f:
                    f.write(requests.get(actor_image).content)
                img = Image.open(
                    f"{dir_path}/static/img/mediaImages/Actor_{actor_id}.png"
                )
                img = img.save(
                    f"{dir_path}/static/img/mediaImages/Actor_{actor_id}.webp", "webp"
                )
                os.remove(f"{dir_path}/static/img/mediaImages/Actor_{actor_id}.png")
            else:
                os.remove(f"{dir_path}/static/img/mediaImages/Actor_{actor_id}.webp")
                with open(
                    f"{dir_path}/static/img/mediaImages/Actor_{actor_id}.png", "wb"
                ) as f:
                    f.write(requests.get(actor_image).content)
                img = Image.open(
                    f"{dir_path}/static/img/mediaImages/Actor_{actor_id}.png"
                )
                img = img.save(
                    f"{dir_path}/static/img/mediaImages/Actor_{actor_id}.webp", "webp"
                )
                os.remove(f"{dir_path}/static/img/mediaImages/Actor_{actor_id}.png")

            actor_image = f"/static/img/mediaImages/Actor_{actor_id}.webp"
            actor_character = actor.character
            actor.profile_path = str(actor_image)
            this_actor = [
                str(actor_name),
                str(actor_character),
                str(actor_image),
                str(actor.id),
            ]
            new_cast.append(this_actor)

            person = Person()
            p = person.details(actor.id)
            exists = Actors.query.filter_by(actor_id=actor.id).first() is not None
            if not exists:
                actor = Actors(
                    name=actor.name,
                    actor_id=actor.id,
                    actor_image=actor_image,
                    actor_description=p.biography,
                    actor_birth_date=p.birthday,
                    actor_birth_place=p.place_of_birth,
                    actor_programs=f"{serie_id}",
                )
                DB.session.add(actor)
                DB.session.commit()
            else:
                actor = Actors.query.filter_by(actor_id=actor.id).first()
                actor.actor_programs = f"{actor.actor_programs} {serie_id}"
                DB.session.commit()
        all_series_path = Libraries.query.filter_by(lib_name=library).first().lib_folder
        serie_modified_time = os.path.getmtime(
            f"{all_series_path}/{the_serie.original_name}"
        )

        new_cast = jsonify(new_cast[:5])
        genre_list = jsonify(genre_list)
        is_adult = str(details["adult"])
        the_serie.id = serie_id
        the_serie.name = name
        the_serie.genre = genre_list
        the_serie.duration = duration
        the_serie.description = description
        the_serie.cast = new_cast
        the_serie.bande_annonce_url = bande_annonce_url
        the_serie.serie_cover_path = serie_cover_path
        the_serie.banniere = banniere
        the_serie.note = note
        the_serie.date = date
        the_serie.serie_modified_time = serie_modified_time
        the_serie.adult = is_adult
        the_serie.library_name = library

        DB.session.commit()
        scans.getSeries(library)

        return jsonify({"status": "success"})


@app.route("/get_season_data/<season_id>", methods=["GET"])
def get_season_data(season_id):
    season = Seasons.query.filter_by(season_id=season_id).first()
    if season is None:
        abort(404)
    episodes = Episodes.query.filter_by(season_id=season_id).all()
    episodes_dict = {}
    for episode in episodes:
        episodes_dict[episode.episode_number] = dict(episode.__dict__)
        del episodes_dict[episode.episode_number]["_sa_instance_state"]
    season = season.__dict__
    del season["_sa_instance_state"]
    season["episodes"] = episodes_dict
    return jsonify(season)


def sort_by_episode_number(episode):
    return episode["episode_number"]


@app.route("/get_episodes/<season_id>", methods=["GET"])
def get_episodes(season_id):
    token = request.headers.get("Authorization")
    if token not in all_auth_tokens:
        abort(401)

    username = all_auth_tokens[token]["user"]

    user = Users.query.filter_by(name=username).first()
    season = Seasons.query.filter_by(season_id=season_id).first()
    serie = Series.query.filter_by(id=season.serie).first()
    library = serie.library_name
    library = Libraries.query.filter_by(lib_name=library).first()

    if user is None:
        abort(404)

    if serie is None:
        abort(404)

    if season is None:
        abort(404)

    user_in_the_lib = user_in_lib(user.id, library)
    if not user_in_the_lib:
        abort(401)

    if serie is None or user is None:
        abort(404)

    episodes = Episodes.query.filter_by(season_id=season_id).all()
    episodes_list = []

    for episode in episodes:
        the_episode = dict(episode.__dict__)
        del the_episode["_sa_instance_state"]
        episodes_list.append(the_episode)

    episodes_list = sorted(episodes_list, key=sort_by_episode_number)

    data = {
        "episodes": episodes_list,
        "library": library.lib_name,
    }

    return jsonify(data)


@app.route("/get_episode_data/<episode_id>", methods=["GET"])
def get_episode_data(episode_id):
    episode = Episodes.query.filter_by(episode_id=episode_id).first()
    if episode is None:
        abort(404)

    episode = episode.__dict__

    season = episode["season_id"]
    episode_number = episode["episode_number"]
    all_episodes = Episodes.query.filter_by(season_id=season).all()
    all_episodes_list = []
    for episode_item in all_episodes:
        all_episodes_list.append(dict(episode_item.__dict__))
    all_episodes_list = sorted(all_episodes_list, key=lambda k: k["episode_number"])
    episode_index = all_episodes_list.index(
        [x for x in all_episodes_list if x["episode_number"] == episode_number][0]
    )
    previous_episode, next_episode = None, None

    if episode_index != 0:
        previous_episode = all_episodes_list[episode_index - 1]["episode_id"]
    if episode_index != len(all_episodes_list) - 1:
        next_episode = all_episodes_list[episode_index + 1]["episode_id"]

    new_episode_data = episode

    del new_episode_data["_sa_instance_state"]
    new_episode_data["previous_episode"] = previous_episode
    new_episode_data["next_episode"] = next_episode

    return jsonify(new_episode_data)


@app.route("/book_url/<id>")
def book_url(id):
    book = Books.query.filter_by(id=id).first()
    if book is None:
        abort(404)
    book = book.__dict__
    return send_file(book["slug"], as_attachment=True)


@app.route("/book_url/<id>/<page>")
def book_url_page(id, page):
    book = Books.query.filter_by(id=id).first()
    if book is None:
        abort(404)
    book = book.__dict__
    book_type = book["book_type"]
    book_slug = book["slug"]
    available = ["PDF", "CBZ", "CBR", "EPUB"]
    if book_type in available:
        if book_type == "PDF":
            import fitz

            pdf_doc = fitz.open(book_slug)
            page = pdf_doc[int(page)]
            pix = page.get_pixmap()
            # Créer un objet io.BytesIO pour stocker l'image en mémoire
            image_stream = io.BytesIO()
            pix.save(image_stream, format="JPEG")
            # Retourner le contenu de l'image
            image_stream.seek(0)
            return send_file(image_stream, mimetype="image/jpeg")

        elif book_type == "CBZ":
            with zipfile.ZipFile(book_slug, "r") as zip:
                image_file = zip.namelist()[int(page)]
                if image_file.endswith((".jpg", ".jpeg", ".png")):
                    with zip.open(image_file) as image:
                        # Créer un objet io.BytesIO pour stocker l'image en mémoire
                        image_stream = io.BytesIO(image.read())
                        # Retourner le contenu de l'image
                        image_stream.seek(0)
                        return send_file(image_stream, mimetype="image/jpeg")

        elif book_type == "CBR":
            with rarfile.RarFile(book_slug, "r") as rar:
                image_file = rar.infolist()[int(page)]
                if image_file.filename.endswith((".jpg", ".jpeg", ".png")):
                    with rar.open(image_file) as image:
                        # Créer un objet io.BytesIO pour stocker l'image en mémoire
                        image_stream = io.BytesIO(image.read())
                        # Retourner le contenu de l'image
                        image_stream.seek(0)
                        return send_file(image_stream, mimetype="image/jpeg")

        elif book_type == "EPUB":
            book = epub.read_epub(book_slug)
            item = book.get_items()[int(page)]
            for idx, item in enumerate(book.get_items()):
                print(idx, page)
                if idx == int(page):
                    content = item.get_content()
                    image_stream = io.BytesIO(content)
                    image_stream.seek(0)
                    return send_file(image_stream, mimetype="image/jpeg")

    abort(404, "Book type not supported")


@app.route("/book_data/<id>")
def book_data(id):
    book = Books.query.filter_by(id=id).first().__dict__
    del book["_sa_instance_state"]
    book_type = book["book_type"]
    book_slug = book["slug"]
    nb_pages = 0
    if book_type == "PDF":
        with open(book_slug, "rb") as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            nb_pages = len(pdf_reader.pages)
    elif book_type == "CBZ":
        with zipfile.ZipFile(book_slug, "r") as zip:
            nb_pages = len(zip.namelist())
    elif book_type == "CBR":
        with rarfile.RarFile(book_slug, "r") as rar:
            nb_pages = len(rar.infolist())
    elif book_type == "EPUB":
        nb_pages = len(epub.read_epub(book_slug).get_items())
    book["nb_pages"] = nb_pages
    return jsonify(book)


@app.route("/download_other/<video_hash>")
def download_other(video_hash):
    video = OthersVideos.query.filter_by(video_hash=video_hash).first()
    video = video.__dict__
    del video["_sa_instance_state"]
    return send_file(video["slug"], as_attachment=True)

@app.route("/get_all_others/<library>")
def get_all_others(library):
    token = request.headers.get("Authorization")
    if token not in all_auth_tokens:
        abort(401)

    username = all_auth_tokens[token]["user"]

    the_lib = Libraries.query.filter_by(lib_name=library).first()

    if not the_lib:
        abort(404)

    user = Users.query.filter_by(name=username).first()
    user_in_the_lib = user_in_lib(user.id, the_lib)
    if not user_in_the_lib:
        return jsonify([])

    other = OthersVideos.query.filter_by(library_name=the_lib.lib_name).all()
    other_list = [video.__dict__ for video in other]

    for video in other_list:
        del video["_sa_instance_state"]

    return jsonify(other_list)


@app.route("/get_tv/<tv_name>/<id>")
def get_tv(tv_name, id):
    if id != "undefined":
        tv = Libraries.query.filter_by(lib_name=tv_name).first()
        lib_folder = tv.lib_folder

        if is_valid_url(lib_folder):
            m3u = requests.get(lib_folder).text
            m3u = m3u.split("\n")
        else:
            with open(lib_folder, "r", encoding="utf-8") as f:
                m3u = f.readlines()
        m3u.pop(0)
        for ligne in m3u:
            if not ligne.startswith(("#EXTINF", "http")):
                m3u.remove(ligne)

        if int(id) >= len(m3u):
            return jsonify(
                {"channel_url": "", "channel_name": ""}
            )

        line = m3u[int(id)]
        next_line = m3u[int(id) + 1]
        the_line = line
        if the_line.startswith("#EXTINF"):
            the_line = next_line

        try:
            channel_name = line.split(",")[-1].replace("\n", "")
        except IndexError:
            channel_name = f"Channel {id}"

        if int(id) - 2 >= 0:
            previous_id = int(id) - 2
        else:
            previous_id = None

        if int(id) + 2 < len(m3u):
            next_id = int(id) + 2
        else:
            next_id = None

        return jsonify({
                "channel_url": the_line,
                "channel_name": channel_name,
                "previous_id": previous_id,
                "next_id": next_id,
            })
    return jsonify({"channel_url": "", "channel_name": "", "error": "Channel not found"})


@app.route("/get_channels/<channels>")
def get_channels(channels):
    token = request.headers.get("Authorization")
    check_authorization(request, token, channels)

    channels = Libraries.query.filter_by(lib_name=channels).first()
    if not channels:
        abort(404, "Library not found")
    lib_folder = channels.lib_folder

    # open the m3u file
    try:
        with open(lib_folder, "r", encoding="utf-8") as f:
            m3u = f.readlines()
    except OSError:
        lib_folder = lib_folder.replace("\\", "/")
        m3u = requests.get(lib_folder).text
        m3u = m3u.split("\n")
    # remove the first line
    m3u.pop(0)
    while m3u[0] == "\n":
        m3u.pop(0)

    # get the channels by getting 2 lines at a time
    channels = []
    for i in m3u:
        if not i.startswith(("#EXTINF", "http")):
            m3u.remove(i)
        elif i == "\n":
            m3u.remove(i)
    for i in range(0, len(m3u) - 1, 2):
        data = {}
        try:
            data["name"] = m3u[i].split(",")[-1].replace("\n", "")
            work = True
        except:
            work = False
        if work:
            data["url"] = m3u[i + 1].replace("\n", "")
            data["channelID"] = i
            tvg_id_regex = r'tvg-id="(.+?)"'
            tvg_id = None
            match = re.search(tvg_id_regex, m3u[i])
            if match:
                tvg_id = match.group(1)
                data["id"] = tvg_id

            tvg_logo_regex = r'tvg-logo="(.+?)"'
            match = re.search(tvg_logo_regex, m3u[i])
            if match and match.group(1) != '" group-title=':
                tvg_logo = match.group(1)
                data["logo"] = tvg_logo
            else:
                broken_path = ""
                data["logo"] = broken_path
                # print(data["logo"])
            channels.append(data)
    # order the channels by name
    channels = sorted(channels, key=lambda k: k["name"].lower())
    return jsonify(channels)


@app.route("/search_tv/<library>/<search>")
def search_tv(library, search):
    token = request.headers.get("Authorization")
    check_authorization(request, token, library)
    username = all_auth_tokens[token]["user"]

    library = Libraries.query.filter_by(lib_name=library).first()
    if not library:
        abort(404, "Library not found")
    lib_folder = library.lib_folder
    # open the m3u file
    try:
        with open(lib_folder, "r", encoding="utf-8") as f:
            m3u = f.readlines()
    except OSError:
        lib_folder = lib_folder.replace("\\", "/")
        m3u = requests.get(lib_folder).text
        m3u = m3u.split("\n")
    # remove the first line
    m3u.pop(0)
    while m3u[0] == "\n":
        m3u.pop(0)

    # get the channels by getting 2 lines at a time
    channels = []
    for i in m3u:
        if not i.startswith(("#EXTINF", "http")):
            m3u.remove(i)
        elif i == "\n":
            m3u.remove(i)
    for i in range(0, len(m3u) - 1, 2):
        data = {}
        try:
            data["name"] = m3u[i].split(",")[-1].replace("\n", "")
            work = True
        except:
            work = False
        if work:
            data["url"] = m3u[i + 1].replace("\n", "")
            data["channelID"] = i
            tvg_id_regex = r'tvg-id="(.+?)"'
            tvg_id = None
            match = re.search(tvg_id_regex, m3u[i])
            if match:
                tvg_id = match.group(1)
                data["id"] = tvg_id

            tvg_logo_regex = r'tvg-logo="(.+?)"'
            match = re.search(tvg_logo_regex, m3u[i])
            if match and match.group(1) != '" group-title=':
                tvg_logo = match.group(1)
                data["logo"] = tvg_logo
            else:
                broken_path = ""
                data["logo"] = broken_path
                # print(data["logo"])
            channels.append(data)
    # order the channels by name
    channels = sorted(channels, key=lambda k: k["name"].lower())

    # search the channels

    search = search.lower()
    search_terms = search.split(" ")
    search_results = []

    for channel in channels:
        count = 0
        name = channel["name"].lower()
        for term in search_terms:
            if term in name:
                count += 1
        if count > 0:
            data = channel
            data["count"] = count
            search_results.append(data)

    search_results = sorted(search_results, key=lambda k: k["count"], reverse=True)

    return jsonify(search_results)


@app.route("/search_tracks/<library>/<search>")
def search_tracks(library, search):
    tracks = Track.query.filter_by(library_name=library).all()

    search = search.lower()
    search_terms = search.split(" ")
    search_results = []

    for track in tracks:
        artist = Artist.query.filter_by(id=track.artist_id).first().name.lower()
        if track.album_id:
            album = Album.query.filter_by(id=track.album_id).first().name.lower()
        else:
            album = ""
        count = 0
        name = track.name.lower()
        for term in search_terms:
            if term in name:
                count += 1
            if term in artist:
                count += 1
            if term in album:
                count += 1
        if count > 0:
            data = track
            data.count = count
            data = data.__dict__
            del data["_sa_instance_state"]
            search_results.append(data)

    search_results = sorted(search_results, key=lambda k: k["count"], reverse=True)

    return jsonify(search_results)


@app.route("/search_albums/<library>/<search>")
def search_albums(library, search):
    albums = Album.query.filter_by(library_name=library).all()

    search = search.lower()
    search_terms = search.split(" ")
    search_results = []

    for album in albums:
        artist = Artist.query.filter_by(id=album.artist_id).first().name.lower()
        name = album.name.lower()
        count = 0
        for term in search_terms:
            if term in name:
                count += 1
            if term in artist:
                count += 1
        if count > 0:
            data = album
            data.count = count
            data = data.__dict__
            del data["_sa_instance_state"]
            search_results.append(data)

    search_results = sorted(search_results, key=lambda k: k["count"], reverse=True)

    return jsonify(search_results)


@app.route("/search_artists/<library>/<search>")
def search_artists(library, search):
    artists = Artist.query.filter_by(library_name=library).all()

    search = search.lower()
    search_terms = search.split(" ")
    search_results = []

    for artist in artists:
        name = artist.name.lower()
        count = 0
        for term in search_terms:
            if term in name:
                count += 1
        if count > 0:
            data = artist
            data.count = count
            data = data.__dict__
            del data["_sa_instance_state"]
            search_results.append(data)

    search_results = sorted(search_results, key=lambda k: k["count"], reverse=True)

    return jsonify(search_results)


@app.route("/search_playlists/<library>/<search>")
def search_playlists(library, search):
    playlists = Playlist.query.filter_by(library_name=library).all()

    search = search.lower()
    search_terms = search.split(" ")
    search_results = []

    for playlist in playlists:
        tracks = playlist.tracks.split(",")
        name = playlist.name.lower()
        count = 0
        for term in search_terms:
            if term in name:
                count += 1
            for track in tracks:
                track = Track.query.filter_by(id=track).first().name.lower()
                if term in track:
                    count += 1
        if count > 0:
            data = playlist
            data.count = count
            data = data.__dict__
            del data["_sa_instance_state"]
            search_results.append(data)

    search_results = sorted(search_results, key=lambda k: k["count"], reverse=True)

    return jsonify(search_results)

def is_valid_url(url):
    try:
        response = requests.get(url)
        return response.status_code == requests.codes.ok
    except requests.exceptions.RequestException:
        return False


@app.route("/get_all_consoles/<library>")
def get_all_consoles(library):

    token = request.headers.get("Authorization")
    check_authorization(request, token, library)
    generate_log(request, "SUCCESS")
    consoles_data = {
        "GB": {"name": "Gameboy", "image": "/static/img/Gameboy.png"},
        "GBA": {"name": "Gameboy Advance", "image": "/static/img/Gameboy Advance.png"},
        "GBC": {"name": "Gameboy Color", "image": "/static/img/Gameboy Color.png"},
        "N64": {"name": "Nintendo 64", "image": "/static/img/N64.png"},
        "NES": {
            "name": "Nintendo Entertainment System",
            "image": "/static/img/NES.png",
        },
        "NDS": {"name": "Nintendo DS", "image": "/static/img/Nintendo DS.png"},
        "SNES": {
            "name": "Super Nintendo Entertainment System",
            "image": "/static/img/SNES.png",
        },
        "Sega Mega Drive": {
            "name": "Sega Mega Drive",
            "image": "/static/img/Sega Mega Drive.png",
        },
        "Sega Master System": {
            "name": "Sega Master System",
            "image": "/static/img/Sega Master System.png",
        },
        "Sega Saturn": {"name": "Sega Saturn", "image": "/static/img/Sega Saturn.png"},
        "PS1": {"name": "PS1", "image": "/static/img/PS1.png"},
    }

    consoles = Games.query.filter_by(library_name=library).all()
    consoles_list = []

    for console in consoles:
        data = {
            "short_name": console.console,
            "image": consoles_data[console.console]["image"],
            "name": consoles_data[console.console]["name"],
        }
        if data not in consoles_list:
            consoles_list.append(data)

    return jsonify(consoles_list)


@app.route("/get_all_games/<lib>/<console_name>")
def get_all_games(lib, console_name):
    token = request.headers.get("Authorization")
    check_authorization(request, token, lib)
    generate_log(request, "SUCCESS")

    games = Games.query.filter_by(console=console_name, library_name=lib).all()

    if not games:
        return jsonify([])

    games_list = [game.__dict__ for game in games]
    for game in games_list:
        del game["_sa_instance_state"]
    return jsonify(games_list)


@app.route("/game_data/<lib>/<game_id>")
def game_data(lib, game_id):
    game_id = Games.query.filter_by(id=game_id, library_name=lib).first()
    if not game_id:
        abort(404)
    game_id = game_id.__dict__
    del game_id["_sa_instance_state"]

    return jsonify(game_id)


@app.route("/game_file/<lib>/<id>")
def game_file(lib, id):
    if id != None:
        game = Games.query.filter_by(id=id, library_name=lib).first()
        game = game.__dict__
        slug = game["slug"]
        return send_file(slug, as_attachment=True)


@app.route("/bios/<console>")
def bios(console):
    if console != None:
        if os.path.exists(f"{dir_path}/static/bios/{console}") == False:
            abort(404)
        bios = [
            i
            for i in os.listdir(f"{dir_path}/static/bios/{console}")
            if i.endswith(".bin")
        ]
        bios = f"{dir_path}/static/bios/{console}/{bios[0]}"

        if os.path.exists(bios) == False:
            abort(404)

        return send_file(bios, as_attachment=True)


@app.route("/search_movies/<library>/<search>")
def search_movies(library, search):
    token = request.headers.get("Authorization")
    check_authorization(request, token, library)

    username = all_auth_tokens[token]["user"]
    user_type = Users.query.filter_by(name=username).first()

    search = unidecode(search.replace("%20", " ").lower())
    search_terms = search.split()

    search = search.replace("%20", " ").lower()
    search_terms = search.split()

    movies = Movies.query.filter_by(library_name=library).all()
    results = {}
    for movie in movies:
        count = 0
        title = movie.title.lower()
        real_title = movie.real_title.lower()
        slug = movie.slug.lower()
        description = movie.description.lower().split(" ")
        cast = movie.cast.lower()
        date = str(movie.date).lower()
        genre = movie.genre.lower()
        alternatives_names = movie.alternatives_names.lower()
        value_used = [title, real_title, slug, cast, date, genre, alternatives_names]
        value_points = [2, 4, 3, 1, 0.5, 0.5, 1.5]
        for term in search_terms:
            for value in value_used:
                index = value_used.index(value)
                if term.lower() in value:
                    count += value_points[index]
            for word in description:
                if term == word.lower():
                    count += 0.1
        if count > 0:
            results[movie] = count

    results = sorted(results.items(), key=lambda x: x[1], reverse=True)

    movies = [i[0].__dict__ for i in results]
    for i in movies:
        del i["_sa_instance_state"]

    user_type = user_type.account_type

    if user_type in ["Kid", "Teen"]:
        for movie in movies:
            if movie["adult"] == "True":
                movies.remove(movie)
    return jsonify(movies)


@app.route("/search_series/<library>/<search>")
def search_series(library, search):
    token = request.headers.get("Authorization")
    check_authorization(request, token, library)

    username = all_auth_tokens[token]["user"]

    series = Series.query.filter_by(library_name=library).all()
    user = Users.query.filter_by(name=username).first()
    library = Libraries.query.filter_by(lib_name=library).first()

    search = unidecode(search.replace("%20", " ").lower())
    search_terms = search.split()

    results = []

    for serie_dict in series:
        count = 0
        name = unidecode(serie_dict.name.lower())
        original_name = unidecode(serie_dict.original_name.lower())
        description = unidecode(serie_dict.description.lower())
        cast = unidecode(serie_dict.cast.lower())
        date = unidecode(str(serie_dict.date).lower())
        genre = unidecode(serie_dict.genre.lower())

        value_used = [name, original_name, description, cast, date, genre]

        for term in search_terms:
            for value in value_used:
                if term in value:
                    count += 1
            for word in description:
                if term == word.lower():
                    count += 1
        if count > 0:
            serie_dict = serie_dict.__dict__
            serie_dict["count"] = count
            del serie_dict["_sa_instance_state"]
            results.append(serie_dict)

    results = sorted(results, key=lambda x: x["count"], reverse=True)

    user_type = user.account_type

    if user_type in ["Kid", "Teen"]:
        for serie_dict in results:
            if serie_dict["adult"] == "True":
                results.remove(serie_dict)

    return jsonify(results)


@app.route("/search_books/<library>/<search>")
def search_books(library, search):
    token = request.headers.get("Authorization")
    check_authorization(request, token, library)

    username = all_auth_tokens[token]["user"]

    books = Books.query.filter_by(library_name=library).all()
    user = Users.query.filter_by(name=username).first()
    library = Libraries.query.filter_by(lib_name=library).first()

    search = unidecode(search.replace("%20", " ").lower())
    search_terms = search.split()

    results = []

    for book in books:
        count = 0
        title = unidecode(book.title.lower())
        slug = unidecode(book.slug.lower())
        book_type = unidecode(book.book_type.lower())
        cover = unidecode(book.cover.lower())

        value_used = [title, slug, book_type, cover]

        for term in search_terms:
            for value in value_used:
                if term in value:
                    count += 1
        if count > 0:
            results.append(book)

    books = [i.__dict__ for i in results]
    for book in books:
        del book["_sa_instance_state"]

    user_type = user.account_type

    # reorder by title
    books = sorted(books, key=lambda k: k["title"].lower())
    return jsonify(books)


@app.route("/search_others/<library>/<search>")
def search_others(library, search):
    token = request.headers.get("Authorization")
    check_authorization(request, token, library)

    username = all_auth_tokens[token]["user"]

    search = search.replace("%20", " ").lower()
    search_terms = search.split()

    others = OthersVideos.query.filter_by(library_name=library).all()
    results = {}
    for other in others:
        count = 0
        video_hash = other.video_hash.lower()
        title = other.title.lower()
        slug = other.slug.lower()

        value_used = [title, slug, video_hash]
        for term in search_terms:
            for value in value_used:
                if term in value:
                    count += 1
        if count > 0:
            results[other] = count

    results = sorted(results.items(), key=lambda x: x[1], reverse=True)

    others = [i[0].__dict__ for i in results]
    for i in others:
        del i["_sa_instance_state"]

    user = Users.query.filter_by(name=username).first()
    user_type = user.account_type

    if user_type in ["Kid", "Teen"]:
        for other in others:
            if other["adult"] == "True":
                others.remove(other)
    return jsonify(others)


@app.route("/set_vues_time_code/", methods=["POST"])
def set_vues_time_code():
    time_code = request.get_json()
    movie_id = time_code["movie_id"]
    time_code = time_code["time_code"]
    username = time_code["username"]
    movie = Movies.query.filter_by(id=movie_id).first()
    if movie is None:
        abort(404)

    actual_vues = movie.vues
    p = re.compile("(?<!\\\\)'")
    actual_vues = p.sub('"', actual_vues)
    actual_vues = json.loads(actual_vues)
    actual_vues[username] = time_code
    actual_vues = str(actual_vues).replace("'", '"')
    movie.vues = actual_vues
    DB.session.commit()
    return "ok"


@app.route("/set_vues_other_time_code/", methods=["POST"])
def set_vues_other_time_code():
    data = request.get_json()
    video_hash = data["movieHASH"]
    time_code = data["time_code"]
    username = data["username"]
    video = OthersVideos.query.filter_by(video_hash=video_hash).first()
    if video is None:
        abort(404)

    actual_vues = video.vues
    p = re.compile("(?<!\\\\)'")
    actual_vues = p.sub('"', actual_vues)
    actual_vues = json.loads(actual_vues)
    actual_vues[username] = time_code
    actual_vues = str(actual_vues).replace("'", '"')
    video.vues = actual_vues
    DB.session.commit()
    return "ok"


@app.route("/whoami", methods=["POST"])
def whoami():
    data = request.get_json()
    user_id = data["user_id"]

    if user_id is None:
        return jsonify({"error": "not logged in"})

    user = Users.query.filter_by(id=user_id).first()

    return jsonify({"id": user_id, "user": user.name})


@app.route("/main_movie/<movie_id>")
def main_movie(movie_id):
    movie_id = movie_id.replace(".m3u8", "")
    movie = Movies.query.filter_by(id=movie_id).first()
    slug = movie.slug
    library = movie.library_name
    the_library = Libraries.query.filter_by(lib_name=library).first()
    path = the_library.lib_folder
    video_path = f"{path}/{slug}"
    video_properties = get_video_properties(video_path)
    height = int(video_properties["height"])
    width = int(video_properties["width"])
    m3u8_file = f"""#EXTM3U\n\n"""
    
    m3u8_file += generate_caption_movie(movie_id)
    qualities = [144, 240, 360, 480, 720, 1080]
    file = []
    for quality in qualities:
        if quality < height:
            new_width = int(quality)
            new_height = int(float(width) / float(height) * new_width)
            if (new_height % 2) != 0:
                new_height += 1
            m3u8_line = f"""#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH={new_width*new_height},CODECS=\"avc1.4d4033,mp4a.40.2",AUDIO="audio",RESOLUTION={new_height}x{new_width}\n/video_movie/{quality}/{movie_id}.m3u8\n"""
            file.append(m3u8_line)
    last_line = f"""#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH={width*height},CODECS=\"avc1.4d4033,mp4a.40.2",AUDIO="audio",RESOLUTION={width}x{height}\n/video_movie/{movie_id}.m3u8\n\n\n"""
    file.append(last_line)
    file = "".join(file)
    m3u8_file += file
    response = make_response(m3u8_file)

    response.headers.set("Content-Type", "application/x-mpegURL")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{movie_id}.m3u8"
    )
    return response


@app.route("/can_i_play_movie/<movie_id>")
def can_i_play_movie(movie_id):
    token = request.headers.get("Authorization")
    if token not in all_auth_tokens:
        return jsonify({"can_I_play": False})
    else:
        user = all_auth_tokens[token]["user"]
        movie = Movies.query.filter_by(id=movie_id).first()
        if movie is None:
            abort(404)

        lib = movie.library_name
        the_lib = Libraries.query.filter_by(lib_name=lib).first()

        if the_lib is None:
            abort(404)

        if the_lib.available_for is not None:
            if user not in the_lib.available_for:
                return jsonify({"can_I_play": False})
        return jsonify({"can_I_play": True})


@app.route("/can_i_play_episode/<episode_id>")
def can_i_play_episode(episode_id):
    token = request.headers.get("Authorization")
    if token not in all_auth_tokens:
        return jsonify({"can_I_play": False})
    else:
        user = all_auth_tokens[token]["user"]

        users = Users.query.filter_by(name=user).first()

        episode = Episodes.query.filter_by(episode_id=episode_id).first()
        season = Seasons.query.filter_by(season_id=episode.season_id).first()
        serie = Series.query.filter_by(id=season.serie).first()

        latest_episode_of_serie_exist = (
            LatestEpisodeWatched.query.filter_by(
                serie_id=serie.id, user_id=users.id
            ).first()
            is not None
        )

        if latest_episode_of_serie_exist:
            latest_episode_of_serie = LatestEpisodeWatched.query.filter_by(
                serie_id=serie.id, user_id=users.id
            ).first()
            latest_episode_of_serie.episode_id = episode_id
            DB.session.commit()
        else:
            latest_episode_of_serie = LatestEpisodeWatched(
                serie_id=serie.id, user_id=users.id, episode_id=episode_id
            )
            DB.session.add(latest_episode_of_serie)
            DB.session.commit()

        if episode is None:
            abort(404)

        lib = serie.library_name
        the_lib = Libraries.query.filter_by(lib_name=lib).first()

        if the_lib is None:
            abort(404)

        if the_lib.available_for is not None:
            if user not in the_lib.available_for:
                return jsonify({"can_I_play": False})
        return jsonify({"can_I_play": True})


@app.route("/can_i_play_other_video/<video_hash>")
def can_i_play_other_video(video_hash):
    token = request.headers.get("Authorization")
    if token not in all_auth_tokens:
        return jsonify({"can_I_play": False})
    else:
        user = all_auth_tokens[token]["user"]
        user_id = Users.query.filter_by(name=user).id
        video = OthersVideos.query.filter_by(video_hash=video_hash).first()
        if video is None:
            return jsonify({"can_I_play": False})

        lib = video.library_name
        the_lib = Libraries.query.filter_by(lib_name=lib).first()

        if the_lib is None:
            return jsonify({"can_I_play": False})

        if the_lib.available_for is not None:
            available_for = the_lib.available_for.split(",")
            if user not in available_for:
                return jsonify({"can_I_play": False})
        return jsonify({"can_I_play": True})


@app.route("/main_serie/<episode_id>")
def main_serie(episode_id):
    episode = Episodes.query.filter_by(episode_id=episode_id).first()
    season = Seasons.query.filter_by(season_id=episode.season_id).first()
    serie = Series.query.filter_by(id=season.serie).first()

    library = serie.library_name
    the_library = Libraries.query.filter_by(lib_name=library).first()
    path = the_library.lib_folder
    episode_path = episode.slug
    episode_path = episode_path.replace("\\", "/")
    episode_path = f"{path}{episode_path}"

    video_properties = get_video_properties(episode_path)
    height = int(video_properties["height"])
    width = int(video_properties["width"])
    m3u8_file = f"""#EXTM3U\n\n"""
    #m3u8_file += generate_caption_serie(episode_id)
    file = []
    qualities = [144, 240, 360, 480, 720, 1080]
    for quality in qualities:
        if quality < height:
            new_width = int(quality)
            new_height = int(float(width) / float(height) * new_width)
            if (new_height % 2) != 0:
                new_height += 1
            m3u8_line = f"""#EXT-X-STREAM-INF:BANDWIDTH={new_width*new_width},RESOLUTION={new_height}x{new_width}\n/video_serie/{quality}/{episode_id}\n"""
            file.append(m3u8_line)
    last_line = f"#EXT-X-STREAM-INF:BANDWIDTH={width*height},RESOLUTION={width}x{height}\n/video_serie/{episode_id}\n"
    file.append(last_line)
    file = file[::-1]
    file = "".join(file)
    m3u8_file += file

    response = make_response(m3u8_file)

    response.headers.set("Content-Type", "application/x-mpegURL")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{episode_id}.m3u8"
    )
    return response


@app.route("/main_other/<other_hash>")
def main_other(other_hash):
    movie = OthersVideos.query.filter_by(video_hash=other_hash).first()
    video_path = movie.slug
    video_properties = get_video_properties(video_path)
    height = int(video_properties["height"])
    width = int(video_properties["width"])
    m3u8_file = f"""#EXTM3U\n\n"""
    qualities = [144, 240, 360, 480, 720, 1080]
    file = []
    for quality in qualities:
        if quality < height:
            new_width = int(quality)
            new_height = int(float(width) / float(height) * new_width)
            if (new_height % 2) != 0:
                new_height += 1
            m3u8_line = f"""#EXT-X-STREAM-INF:BANDWIDTH={new_width*new_width},RESOLUTION={new_height}x{new_width}\n/video_other/{quality}/{other_hash}\n"""
            file.append(m3u8_line)
    last_line = f'#EXT-X-STREAM-INF:BANDWIDTH={width*height},RESOLUTION={width}x{height}"\n/video_other/{other_hash}\n'
    file.append(last_line)
    file = file[::-1]
    file = "".join(file)
    m3u8_file += file
    response = make_response(m3u8_file)

    response.headers.set("Content-Type", "application/x-mpegURL")
    response.headers.set("Range", "bytes=0-4095")
    response.headers.set("Accept-Encoding", "*")
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{other_hash}.m3u8"
    )
    return response


def generate_caption_serie(episode_id):
    episode = Episodes.query.filter_by(episode_id=episode_id).first()
    season = Seasons.query.filter_by(season_id=episode.season_id).first()
    serie = Series.query.filter_by(id=season.serie).first()
    library = serie.library_name
    the_library = Libraries.query.filter_by(lib_name=library).first()
    path = the_library.lib_folder
    episode_path = episode.slug
    episode_path = episode_path.replace("\\", "/")
    slug = f"{path}{episode_path}"
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
        slug,
    ]
    caption_pipe = subprocess.Popen(caption_command, stdout=subprocess.PIPE)
    try:
        slug = slug.split("\\")[-1]
        slug = slug.split("/")[-1]
    except:
        slug = slug.split("/")[-1]
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
            except:
                title_name = title_name
                subtitle_type = "Unknown"

        except:
            title_name = new_language
        subtitle_type = "Unknown"
        if subtitle_type.lower() != "pgs":
            all_captions.append(
                {
                    "index": index,
                    "languageCode": language,
                    "language": new_language,
                    "url": f"/chunk_caption_serie/{language}/{index}/{episode_id}.vtt",
                    "name": title_name,
                }
            )
    return all_captions


def generate_caption_movie(movie_id):
    movie_path = Movies.query.filter_by(id=movie_id).first()
    library = movie_path.library_name
    the_library = Libraries.query.filter_by(lib_name=library).first()
    path = the_library.lib_folder
    movie_path = movie_path.slug
    movie_path = movie_path.replace("\\", "/")
    slug = f"{path}\{movie_path}"

    caption_command = [
        "ffprobe",
        "-loglevel",
        "error",
        "-select_streams",
        "s",
        "-show_entries",
        "stream=index,codec_name:stream_tags=language,title,handler_name,codec_name",
        "-of",
        "csv=p=0",
        slug,
    ]

    caption_pipe = subprocess.Popen(caption_command, stdout=subprocess.PIPE)
    try:
        slug = slug.split("\\")[-1]
        slug = slug.split("/")[-1]
    except:
        slug = slug.split("/")[-1]
    caption_response = caption_pipe.stdout.read().decode("utf-8")
    caption_response = caption_response.split("\n")
    caption_response.pop()

    all_captions = []
    for line in caption_response:
        line = line.rstrip()
        index = line.split(",")[0]
        type = line.split(",")[1]
        language = line.split(",")[2]
        try:
            title_name = line.split(",")[3]
        except:
            title_name = language

        if type != "subrip":
            continue

        all_captions.append(
            {
                "index": index,
                "languageCode": language,
                "language": title_name,
                "url": f"/captionMovie/{movie_id}_{index}.m3u8",
                "name": title_name,
            }
        )
    string = ""

    for caption in all_captions:
        string += f'#EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subs",NAME="{caption["language"]}",DEFAULT=NO,FORCED=NO,URI="{caption["url"]}",LANGUAGE="{caption["languageCode"]}"\n'

    return string

@app.route("/get_actor_data/<actorId>", methods=["GET", "POST"])
def get_actor_data(actor_id):
    if actor_id == "undefined":
        abort(404)
    movies_data = []
    series_data = []
    actor = Actors.query.filter_by(actor_id=actor_id).first()
    movies = actor.actor_programs.split(" ")
    for movie in movies:
        in_movies = Movies.query.filter_by(id=movie).first() is not None
        in_series = Series.query.filter_by(id=movie).first() is not None
        if in_movies:
            this_movie = Movies.query.filter_by(id=movie).first().__dict__
            del this_movie["_sa_instance_state"]
            if this_movie not in movies_data:
                movies_data.append(this_movie)
        elif in_series:
            this_series = Series.query.filter_by(id=movie).first().__dict__
            del this_series["_sa_instance_state"]
            if this_series not in series_data:
                series_data.append(this_series)

    actor_data = {
        "actor_name": actor.name,
        "actorImage": actor.actorImage,
        "actorDescription": actor.actorDescription,
        "actorBirthday": actor.actorBirthDate,
        "actorBirthplace": actor.actorBirthPlace,
        "actorMovies": movies_data,
        "actorSeries": series_data,
    }
    return jsonify(actor_data, default=lambda o: o.__dict__)


@app.route("/get_this_episode_data/<episode_id>", methods=["GET", "POST"])
def get_this_episode_data(episode_id):
    episode = Episodes.query.filter_by(episode_id=episode_id).first()
    episode_data = {
        "episode_name": episode.episode_name,
        "intro_start": episode.intro_start,
        "intro_end": episode.intro_end,
    }
    return jsonify(episode_data, default=lambda o: o.__dict__)


@app.route("/is_chocolate", methods=["GET", "POST"])
def is_chocolate():
    return jsonify({"is_chocolate": True})


@app.route("/download_movie/<movie_id>")
def download_movie(movie_id):
    can_download = config["ChocolateSettings"]["allowDownload"].lower() == "true"
    if not can_download:
        return jsonify({"error": "download not allowed"})
    movie = Movies.query.filter_by(id=movie_id).first()
    movie_path = movie.slug
    movie_library = movie.library_name
    library = Libraries.query.filter_by(lib_name=movie_library).first()
    library_path = library.lib_folder
    movie_path = f"{library_path}/{movie_path}"
    return send_file(movie_path, as_attachment=True)


@app.route("/download_episode/<episode_id>")
def download_episode(episode_id):
    can_download = config["ChocolateSettings"]["allowDownload"].lower() == "true"
    if not can_download:
        return jsonify({"error": "download not allowed"})
    episode = Episodes.query.filter_by(episode_id=episode_id).first()
    season = Seasons.query.filter_by(season_id=episode.season_id).first()
    serie = Series.query.filter_by(id=season.serie).first()
    library = Libraries.query.filter_by(lib_name=serie.library_name).first()
    library_path = library.lib_folder
    episode_path = f"{library_path}/{episode.slug}"
    return send_file(episode_path, as_attachment=True)


if __name__ == "__main__":
    enabled_rpc = config["ChocolateSettings"]["discordrpc"]
    if enabled_rpc == "true":
        try:
            RPC.update(
                state="Loading Chocolate...",
                details=f"The Universal MediaManager | ({last_commit_hash})",
                large_image="loader",
                large_text="Chocolate",
                buttons=[
                    {
                        "label": "Github",
                        "url": "https://github.com/ChocolateApp/Chocolate",
                    }
                ],
                start=start_time,
            )
        except:
            pass

    with app.app_context():
        if not ARGUMENTS.no_scans:
            libraries = Libraries.query.all()
            libraries = [library.__dict__ for library in libraries]
            libraries = sorted(libraries, key=lambda k: k["lib_name"].lower())
            libraries = sorted(libraries, key=lambda k: k["lib_type"].lower())
            
            for library in libraries:
                if library["lib_type"] == "series":
                    scans.getSeries(library["lib_name"])
                elif library["lib_type"] == "movies":
                    scans.getMovies(library["lib_name"])
                elif library["lib_type"] == "consoles":
                    scans.getGames(library["lib_name"])
                elif library["lib_type"] == "others":
                    scans.getOthersVideos(library["lib_name"])
                elif library["lib_type"] == "books":
                    scans.getBooks(library["lib_name"])
                elif library["lib_type"] == "musics":
                    scans.getMusics(library["lib_name"])

            print()
    print("\033[?25h", end="")

    enabled_rpc = config["ChocolateSettings"]["discordrpc"]
    if enabled_rpc == "true":
        try:
            RPC.update(
                state="Idling",
                details=f"The Universal MediaManager | ({last_commit_hash})",
                large_image="largeimage",
                large_text="Chocolate",
                buttons=[
                    {
                        "label": "Github",
                        "url": "https://github.com/ChocolateApp/Chocolate",
                    }
                ],
                start=time(),
            )
        except:
            pass

    app.run(host="0.0.0.0", port="8888")