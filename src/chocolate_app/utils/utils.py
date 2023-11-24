import os
import datetime
import json
import requests

from flask import abort

from PIL import Image, UnidentifiedImageError

from chocolate_app import all_auth_tokens, get_dir_path, LOG_PATH
from chocolate_app.tables import Users, Libraries

dir_path = get_dir_path()


def generate_log(request, component):
    method = request.method

    token = request.headers.get("Authorization")

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

    log("INFO", component, message)


def log(log_type, log_composant=None, log_message=""):
    the_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log = f"{the_time} - [{log_type}]"
    if log_composant:
        log += f" [{log_composant}] {log_message}\n"


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


def path_join(*args):
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

def check_extension(file, extensions):
    if file.split(".")[-1] in extensions:
        return True
    return False

def is_video_file(file):
    extensions = ["mkv", "avi", "mp4", "webm", "ogg", "m4v", "mov", "wmv", "flv", "3gp"]
    return check_extension(file, extensions)

def is_music_file(file):
    extensions = ["mp3", "wav", "ogg", "flac", "m4a", "wma"]
    return check_extension(file, extensions)

def is_book_file(file):
    extensions = ["pdf", "epub", "cbz", "cbr"]
    return check_extension(file, extensions)

def is_image_file(file):
    extensions = ["png", "jpg", "jpeg", "gif", "webp"]
    return check_extension(file, extensions)

def is_compressed_file(file):
    extensions = ["zip", "rar", "7z", "tar", "gz", "bz2", "xz"]
    return check_extension(file, extensions)

def is_directory(file):
    return os.path.isdir(file)