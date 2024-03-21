import os
import datetime
import json
import requests

from flask import Request, abort

from PIL import Image, UnidentifiedImageError

from chocolate_app import all_auth_tokens, get_dir_path, LOG_PATH
from chocolate_app.tables import Users, Libraries

dir_path = get_dir_path()


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


def check_authorization(request, token, library=None):
    if token not in all_auth_tokens:
        generate_log(request, "UNAUTHORIZED")
        abort(401)

    username = all_auth_tokens[token]["user"]

    if library:
        the_lib = Libraries.query.filter_by(lib_name=library).first()

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

def save_image(url, path, width=600, ratio=73/50):
    if "Banner" in path:
        width = 1920
        ratio = 9/16
    elif "Actor" in path:
        width = 300
        ratio = 1
    height = int(width * ratio)
    image_requests = requests.Session()
    if not os.path.exists(f"{path}.webp"):
        with open(f"{path}.png", "wb") as f:
            f.write(image_requests.get(url).content)

        try:
            image = Image.open(f"{path}.png")
        except UnidentifiedImageError:
            return "/static/images/broken" + "Banner" * ("Banner" in path) + ".png"
        #resize image but don't crop it
        image = image.resize((width, height), Image.ANTIALIAS)
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