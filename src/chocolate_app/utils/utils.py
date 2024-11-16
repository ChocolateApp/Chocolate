import hashlib
import os
import time
import json
import base64
import requests
import datetime
import subprocess

from enum import Enum
from io import BytesIO
from typing import Any
from flask import Request, Response, abort, jsonify
from PIL import Image, UnidentifiedImageError

from chocolate_app.tables import Users, Libraries
from chocolate_app import all_auth_tokens, get_dir_path, LOG_PATH, get_language_file

dir_path = get_dir_path()
LANGUAGE_FILE = get_language_file()


class Codes(Enum):
    CONTINUE_REQUEST = 101
    PROCESSING = 102

    SUCCESS = 201
    MISSING_DATA = 202
    NO_RETURN_DATA = 203
    INVALID_MEDIA_TYPE = 204

    USER_CREATED = 211
    USER_DELETED = 212
    USER_UPDATED = 213
    USER_FOUND = 214
    USER_NOT_FOUND = 215
    USER_ALREADY_EXISTS = 216
    USER_NOT_CREATED = 217
    USER_NOT_DELETED = 218
    USER_NOT_UPDATED = 219

    LIBRARY_CREATED = 221
    LIBRARY_DELETED = 222
    LIBRARY_UPDATED = 223
    LIBRARY_FOUND = 224
    LIBRARY_NOT_FOUND = 225
    LIBRARY_ALREADY_EXISTS = 226
    LIBRARY_NOT_CREATED = 227
    LIBRARY_NOT_DELETED = 228
    LIBRARY_NOT_UPDATED = 229

    SETTINGS_UPDATED = 231
    SETTINGS_NOT_UPDATED = 232

    LOGIN_SUCCESS = 241
    LOGIN_FAILED = 242
    NOT_LOGGED_IN = 243
    LOGGED_IN = 244
    WRONG_PASSWORD = 245
    INVALID_TOKEN = 246

    MEDIA_NOT_FOUND = 251

    INVALID_METHOD = 261


def generate_log(request: Request, component: str) -> None:
    """
    Generate a log

    Args:
        request: The request
        component: The component of the log

    Returns:
        None
    """
    method = request.method

    token = request.headers.get("Authorization")
    ip_address = request.remote_addr
    path = request.path

    try:
        data = request.get_json()
    except Exception:
        data = None

    if token and token in all_auth_tokens:
        user = all_auth_tokens[token]["user"]
        if user:
            try:
                user = Users.query.filter_by(name=user).first()
                if user:
                    username = user.name
                else:
                    username = f"token {token}"
            except Exception:
                username = f"token {token}"
        else:
            username = f"token {token}"
    else:
        username = f"Token {token}"

    if username == "Token Bearer null":
        username = "Unknown"

    if not data:
        message = f"Request {method} at {path}. from {username}"
    else:
        if "password" in data:
            data["password"] = "********"
        if "image" in data:
            data["image"] = "Image as a base64 (to long)"
        message = (
            f"Request {method} at {path}. from {username} with data: {json.dumps(data)}"
        )

    log("INFO", component, message, ip_address)


def log(log_type: str, log_composant=None, log_message="", ip_address="") -> None:
    """
    Log a message

    Args:
        log_type (str): The type of the log
        log_composant (str, optional): The component of the log. Defaults to None.
        log_message (str, optional): The message of the log. Defaults to "".
        ip_address (str, optional): The IP address of the log. Defaults to "".

    Returns:
        None
    """

    the_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log = f"{the_time} - [{log_type}]"
    if log_composant:
        log += f" [{log_composant}] {log_message}\n"

    if ip_address and ip_address != "":
        log = f"[{ip_address}] {log}"

    # if file does not exist, create it
    if not os.path.exists(LOG_PATH):
        with open(LOG_PATH, "w") as logs:
            logs.write(log)
        return

    with open(LOG_PATH, "r") as logs:
        if log in logs.read():
            return

    with open(LOG_PATH, "a") as logs:
        logs.write(log)


def path_join(*args) -> str:
    """
    Join the path with the correct separator

    Args:
        *args: The path to join

    Returns:
        str: The joined path
    """
    return "/".join(args).replace("\\", "/")


def check_authorization(request, token=None, library=None):
    if not token:
        token = request.headers.get("Authorization")

    if token not in all_auth_tokens:
        generate_log(request, "UNAUTHORIZED")
        abort(401)

    username = all_auth_tokens[token]["user"]

    if library:
        the_lib = Libraries.query.filter_by(name=library).first()

        if not the_lib:
            generate_log(request, "ERROR")
            abort(404)

        user = Users.query.filter_by(name=username).first()
        user_in_the_lib = user_in_lib(user.id, the_lib)

        if not user_in_the_lib:
            generate_log(request, "UNAUTHORIZED")
            abort(401)

        if the_lib is None or user is None:
            generate_log(request, "ERROR")
            abort(404)


def check_admin(request, token):
    if token not in all_auth_tokens:
        generate_log(request, "UNAUTHORIZED")
        abort(401)

    username = all_auth_tokens[token]["user"]

    user = Users.query.filter_by(name=username).first()

    if user is None or not user.account_type == "Admin":
        generate_log(request, "UNAUTHORIZED")
        abort(401)


def user_in_lib(user_id, lib):
    user = Users.query.filter_by(id=user_id).first()

    if not user or not lib:
        return False

    user_id = str(user.id)

    if not isinstance(lib, dict):
        lib = lib.__dict__

    available_for = str(lib["available_for"]).split(",")

    if not lib["available_for"] or user_id in available_for:
        return True
    return False


def save_image(url, path) -> str | None:
    image_requests = requests.Session()
    if not os.path.exists(f"{path}.webp"):
        with open(f"{path}.png", "wb") as f:
            try:
                f.write(image_requests.get(url).content)
            except Exception:
                time.sleep(0.5)
                return save_image(url, path)

        try:
            image = Image.open(f"{path}.png")
        except UnidentifiedImageError:
            return None

        image.save(f"{path}.webp", "webp", optimize=True)
        if os.path.exists(f"{path}.png"):
            os.remove(f"{path}.png")

    return f"{path}.webp"


def check_extension(file, extensions: list) -> bool:
    """
    Check if the file is of a certain type

    Args:
        file (str): The file to check
        extensions (list): The list of extensions to check

    Returns:
        bool: True if the file is of a certain type, False otherwise
    """

    if file.split(".")[-1] in extensions:
        return True
    return False


def is_video_file(file: str) -> bool:
    """
    Check if the file is a video file

    Args:
        file (str): The file to check

    Returns:
        bool: True if the file is a video file, False otherwise
    """
    extensions = ["mkv", "avi", "mp4", "webm", "ogg", "m4v", "mov", "wmv", "flv", "3gp"]
    return check_extension(file, extensions)


def is_music_file(file: str) -> bool:
    """
    Check if the file is a music file

    Args:
        file (str): The file to check

    Returns:
        bool: True if the file is a music file, False otherwise
    """
    extensions = ["mp3", "wav", "ogg", "flac", "m4a", "wma"]
    return check_extension(file, extensions)


def is_book_file(file: str) -> bool:
    """
    Check if the file is a book file

    Args:
        file (str): The file to check

    Returns:
        bool: True if the file is a book file, False otherwise
    """
    extensions = ["pdf", "epub", "cbz", "cbr"]
    return check_extension(file, extensions)


def is_image_file(file: str) -> bool:
    """
    Check if the file is an image file

    Args:
        file (str): The file to check

    Returns:
        bool: True if the file is an image file, False otherwise
    """
    extensions = ["png", "jpg", "jpeg", "gif", "webp"]
    return check_extension(file, extensions)


def is_compressed_file(file: str) -> bool:
    """
    Check if the file is a compressed file

    Args:
        file (str): The file to check

    Returns:
        bool: True if the file is a compressed file, False otherwise
    """
    extensions = ["zip", "rar", "7z", "tar", "gz", "bz2", "xz"]
    return check_extension(file, extensions)


def is_directory(path: str) -> bool:
    """
    Check if the path is a directory

    Args:
        path (str): The path to check

    Returns:
        bool: True if the path is a directory, False otherwise
    """
    return os.path.isdir(path)


def get_chunk_user_token(request: Request) -> int | None:
    """
    Get the user token from the request

    Args:
        request: The request

    Returns:
        str: The user token
    """
    token = request.headers.get("Authorization")
    if token not in all_auth_tokens:
        return None
    user = all_auth_tokens[token]["user"]
    return Users.query.filter_by(name=user).first().id


def generate_response(code: Codes, error=False, data: Any = None) -> Response:
    """
    Function to generate a response, based on a model
    """

    output_json = {
        "code": code.value,
        "error": error,
        "message": Codes(code).name,
        "data": data,
    }

    return jsonify(output_json)


def generate_b64_image(
    image_path: str | None, width: int | None = None, height: int | None = None
) -> str | None:
    """
    Generate a base64 image

    Args:
        image_path (str | None): The path of the image

    Returns:
        str: The base64 image
    """
    if not image_path:
        return None

    if not os.path.exists(image_path):
        return None

    with open(image_path, "rb") as image_file:
        image_b64 = base64.b64encode(image_file.read()).decode("utf-8")

    image = Image.open(BytesIO(base64.b64decode(image_b64)))
    if width:
        wpercent = width / float(image.size[0])
        hsize = int((float(image.size[1]) * float(wpercent)))
        image = image.resize((width, hsize), Image.ANTIALIAS)
    if height:
        hpercent = height / float(image.size[1])
        wsize = int((float(image.size[0]) * float(hpercent)))
        image = image.resize((wsize, height), Image.ANTIALIAS)

    img_io = BytesIO()
    image.save(img_io, "WEBP")
    img_io.seek(0)
    img_str = base64.b64encode(img_io.getvalue()).decode("utf-8")

    return f"data:image/png;base64,{img_str}"


def translate(query: str | int) -> str:
    """
    Translate a query

    Args:
        query (str | number): The query to get the translation

    Returns:
        str: The translated query
    """
    if not query:
        return ""

    if isinstance(query, int):
        query = str(query)

    return LANGUAGE_FILE[query]


def hash_string(string: str) -> str:
    return hashlib.md5(string.encode()).hexdigest()


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
    except ValueError:
        return 0.0
