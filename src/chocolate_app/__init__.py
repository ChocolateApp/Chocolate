# Copyright (C) 2024 Impre_visible
import os
import uuid
import json
import shutil
import hashlib
import pathlib
import logging
import argparse
import platform
import configparser

from flask import Flask
from tmdbv3api import TMDb  # type: ignore
from flask_cors import CORS
from typing import Dict, Any
from flask_migrate import Migrate
from flask_login import LoginManager  # type: ignore
from flask_sqlalchemy import SQLAlchemy

from chocolate_app.plugins_loader import loader

DB: SQLAlchemy = SQLAlchemy()
MIGRATE: Migrate = Migrate()
LOGIN_MANAGER: LoginManager = LoginManager()
all_auth_tokens: Dict[Any, Any] = {}


class ChocolateException(Exception):
    """Base class for exceptions in Chocolate"""


class UnsupportedSystemDefaultPath(ChocolateException):
    """Raised when the default path for the config file and the database file is not supported by Chocolate"""


class TemplateNotFound(ChocolateException):
    """Raised when a template was not found"""


parser: argparse.ArgumentParser = argparse.ArgumentParser("Chocolate")
parser.add_argument("-c", "--config", help="Path to the config file (a .ini file)")
parser.add_argument("--artefacts", help="Path to the artefacts folder (a folder)")
parser.add_argument(
    "-sqlite_file", "--sqlite_file", help="Path to the SQLLite file (a .db file)"
)
parser.add_argument(
    "-db", "--database-uri", help="Database URI to use (PostgreSQL, MySQL, etc.)"
)
parser.add_argument("-i", "--images", help="Path to the images folder (a folder)")
parser.add_argument("-pl", "--plugins", help="Path to the plugins folder (a folder)")
parser.add_argument("-l", "--logs", help="Path to the logs file (a .log file)")
parser.add_argument(
    "-ns", "--no-scans", help="Disable startup scans", action="store_true"
)
parser.add_argument("-p", "--port", help="Port to run the server on", type=int)
parser.add_argument(
    "-c:v", "--video-codec", help="Video codec to use", default="libx264"
)
parser.add_argument("-c:a", "--audio-codec", help="Audio codec to use", default="aac")
parser.add_argument("-f", "--ffmpeg-args", help="FFmpeg arguments to use", nargs="*")


ARGUMENTS = parser.parse_args()

paths = {
    "Windows": {
        "config": f"{os.getenv('APPDATA')}/Chocolate/config.ini",
        "sqlite_file": f"{os.getenv('APPDATA')}/Chocolate/database.db",
        "images": f"{os.getenv('APPDATA')}/Chocolate/images",
        "logs": f"{os.getenv('APPDATA')}/Chocolate/server.log",
        "plugins": f"{os.getenv('APPDATA')}/Chocolate/plugins",
        "artefacts": f"{os.getenv('APPDATA')}/Chocolate/artefacts",
        "replace_from": "",
        "replace_to": "",
    },
    "Linux": {
        "config": "/var/chocolate/config.ini",
        "sqlite_file": "/var/chocolate/database.db",
        "images": "/var/chocolate/images/",
        "plugins": "/var/chocolate/plugins/",
        "logs": "/var/chocolate/server.log",
        "artefacts": "/var/chocolate/artefacts/",
        "replace_from": "/var/chocolate",
        "replace_to": f"{os.getenv('HOME')}/.local/share/chocolate",
    },
    "Darwin": {
        "config": f"{os.getenv('HOME')}/Library/Application Support/Chocolate/config.ini",
        "sqlite_file": f"{os.getenv('HOME')}/Library/Application Support/Chocolate/database.db",
        "images": f"{os.getenv('HOME')}/Library/Application Support/Chocolate/images/",
        "plugins": f"{os.getenv('HOME')}/Library/Application Support/Chocolate/plugins/",
        "logs": f"{os.getenv('HOME')}/Library/Application Support/Chocolate/server.log",
        "artefacts": f"{os.getenv('HOME')}/Library/Application Support/Chocolate/artefacts/",
        "replace_from": "",
        "replace_to": "",
    },
}

OPERATING_SYSTEM: str = platform.system()

if OPERATING_SYSTEM not in paths.keys():
    raise UnsupportedSystemDefaultPath(
        f"No known default file path for the config / database on your operating system ({OPERATING_SYSTEM}). Please use --config and --database path or create a pull request to add your system to the one supported by Chocolate"
    )

CONFIG_PATH: str = ARGUMENTS.config or paths[OPERATING_SYSTEM]["config"]
CONFIG_PATH = CONFIG_PATH.replace("\\", "/")

SQLITE_PATH: str = ARGUMENTS.sqlite_file or paths[OPERATING_SYSTEM]["sqlite_file"]
SQLITE_PATH = SQLITE_PATH.replace("\\", "/")

DB_URI: str = ARGUMENTS.database_uri

LOG_PATH: str = ARGUMENTS.logs or paths[OPERATING_SYSTEM]["logs"]
LOG_PATH = LOG_PATH.replace("\\", "/")

IMAGES_PATH: str = ARGUMENTS.images or paths[OPERATING_SYSTEM]["images"]
IMAGES_PATH = IMAGES_PATH.replace("\\", "/")
if IMAGES_PATH.endswith("/"):
    IMAGES_PATH = IMAGES_PATH[:-1]

PLUGINS_PATH: str = ARGUMENTS.plugins or paths[OPERATING_SYSTEM]["plugins"]
PLUGINS_PATH = PLUGINS_PATH.replace("\\", "/")
if PLUGINS_PATH.endswith("/"):
    PLUGINS_PATH = PLUGINS_PATH[:-1]

ARTEFACTS_PATH: str = ARGUMENTS.artefacts or paths[OPERATING_SYSTEM]["artefacts"]
ARTEFACTS_PATH = ARTEFACTS_PATH.replace("\\", "/")
if ARTEFACTS_PATH.endswith("/"):
    ARTEFACTS_PATH = ARTEFACTS_PATH[:-1]

SERVER_PORT: int = ARGUMENTS.port or 8888


VIDEO_CODEC: str = ARGUMENTS.video_codec

AUDIO_CODEC: str = ARGUMENTS.audio_codec

FFMPEG_ARGS: list = ARGUMENTS.ffmpeg_args or []
if len(FFMPEG_ARGS) == 1:
    FFMPEG_ARGS = FFMPEG_ARGS[0].split(" ")


def replace_path(path: str) -> str:
    return path.replace(
        paths[OPERATING_SYSTEM]["replace_from"], paths[OPERATING_SYSTEM]["replace_to"]
    )


def generate_secret_key():
    mac_addr = hex(uuid.getnode()).encode("utf-8")
    salt = b"chocolate is the best media manager ever"
    secret_key = hashlib.sha256(mac_addr + salt).hexdigest()

    return secret_key


try:
    if not os.path.isdir(os.path.dirname(CONFIG_PATH)):
        os.mkdir(os.path.dirname(CONFIG_PATH))
except PermissionError:
    CONFIG_PATH = replace_path(CONFIG_PATH)
    SQLITE_PATH = replace_path(SQLITE_PATH)
    LOG_PATH = replace_path(LOG_PATH)
    IMAGES_PATH = replace_path(IMAGES_PATH)

VIDEO_CHUNK_LENGTH = 45
AUDIO_CHUNK_LENGTH = 45

if os.getenv("NO_SCANS") == "true":
    ARGUMENTS.no_scans = True


def create_app() -> Flask:
    """
    Create the Flask app

    Returns:
        Flask: The Flask app
    """
    dir_path = pathlib.Path(__package__).parent  # type: ignore
    TEMPLATE_FOLDER = f"{dir_path}/templates"

    if not os.path.isdir(IMAGES_PATH):
        os.mkdir(IMAGES_PATH)
    if not os.path.isdir(f"{IMAGES_PATH}/avatars"):
        os.mkdir(f"{IMAGES_PATH}/avatars")

    app = Flask(
        __name__, static_folder=f"{dir_path}/static", template_folder=TEMPLATE_FOLDER
    )

    app.secret_key = generate_secret_key()

    CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})
    if DB_URI:
        app.config["SQLALCHEMY_DATABASE_URI"] = DB_URI
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{SQLITE_PATH}"
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_size": 30, "max_overflow": 0}
    app.config["MAX_CONTENT_LENGTH"] = 4096 * 4096
    app.config["UPLOAD_FOLDER"] = f"{dir_path}/static/img/"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["DIR_PATH"] = dir_path
    app.config["JSON_AS_ASCII"] = False

    from .routes.api.index import api_bp

    app.register_blueprint(api_bp)

    DB.init_app(app)
    MIGRATE.init_app(app, DB)
    LOGIN_MANAGER.init_app(app)
    LOGIN_MANAGER.login_view = "login"

    return app


def check_dependencies() -> None:
    """
    Check if the dependencies are installed
    """
    if not shutil.which("ffmpeg"):
        logging.warning(
            "ffmpeg is not installed. Chocolate will not be able to play videos."
        )

    if not shutil.which("git"):
        logging.warning(
            "git is not installed. Chocolate will not be able to install plugins."
        )


def get_dir_path() -> str:
    """
    Get the directory path of the package

    Returns:
        str: The directory path of the package
    """
    dir_path = os.path.dirname(__file__).replace("\\", "/")

    return dir_path


def create_tmdb() -> TMDb:
    """
    Create the TMDb object

    Returns:
        TMDb: The TMDb object
    """
    tmdb = TMDb()
    api_key_tmdb = config["APIKeys"]["TMDB"]
    if api_key_tmdb == "Empty":
        print(
            "Follow this tutorial to get your TMDB API Key : https://developers.themoviedb.org/3/getting-started/introduction"
        )
    tmdb.api_key = config["APIKeys"]["TMDB"]
    tmdb.language = config["ChocolateSettings"]["language"]

    return tmdb


def get_config() -> configparser.ConfigParser:
    """
    Get the config file

    Returns:
        configparser.ConfigParser: The config file
    """
    if not os.path.exists(CONFIG_PATH) or os.path.getsize(CONFIG_PATH) == 0:
        logging.warning(
            f"Config file not found at {CONFIG_PATH}. Creating a new one..."
        )

        if not os.path.isdir(os.path.dirname(CONFIG_PATH)):
            os.mkdir(os.path.dirname(CONFIG_PATH))

        with open(f"{get_dir_path()}/empty_config.ini", "r") as empty_config:
            with open(CONFIG_PATH, "w") as config:
                config.write(empty_config.read())

    configParser = configparser.ConfigParser()
    configParser.read(CONFIG_PATH)
    try:
        if configParser["ChocolateSettings"]["language"] == "Empty":
            configParser["ChocolateSettings"]["language"] = "en"
    except KeyError:
        configParser["ChocolateSettings"] = {
            "language": "en",
            "allowdownload": "false",
        }

        configParser["APIKeys"] = {
            "tmdb": "Empty",
            "igdbid": "Empty",
            "igdbsecret": "Empty",
        }

        write_config(configParser)

    return configParser


def write_config(config) -> None:
    """
    Write the config file

    Args:
        config (configparser.ConfigParser): The config file
    """
    with open(CONFIG_PATH, "w") as configfile:
        config.write(configfile)


def register_plugins() -> None:
    """
    Register the plugins
    """
    loader.load_plugins(PLUGINS_PATH)


def get_language_file() -> Dict:
    dir_path = get_dir_path()

    language = config["ChocolateSettings"]["language"]

    if (
        not os.path.isfile(f"{dir_path}/static/lang/{language.lower()}.json")
        or "{}"
        in open(
            f"{dir_path}/static/lang/{language.lower()}.json", "r", encoding="utf-8"
        ).read()
    ):
        language = "EN"

    with open(
        f"{dir_path}/static/lang/{language.lower()}.json", "r", encoding="utf-8"
    ) as f:
        language = json.load(f)

    with open(f"{dir_path}/static/lang/en.json", "r", encoding="utf-8") as f:
        en = json.load(f)

    language_dict = language

    for key in en:
        if key not in language_dict:
            language_dict[key] = en[key]

    return language_dict


def create_directories() -> None:
    """
    Create the directories
    """
    parent = os.path.dirname(PLUGINS_PATH)
    
    if not os.path.exists(parent):
        try:
            os.mkdir(parent)
        except PermissionError:
            print(
                "Permission denied to create parent folder. Please run Chocolate as an administrator or use the arguments to specify the folders you have access to."
            )
        
    if not os.path.exists(PLUGINS_PATH):
        try:
            os.mkdir(PLUGINS_PATH)
        except PermissionError:
            print(
                "Permission denied to create plugins folder. Please run Chocolate as an administrator or use the --plugins argument to specify a folder you have access to."
            )

    if not os.path.exists(IMAGES_PATH):
        try:
            os.mkdir(IMAGES_PATH)
        except PermissionError:
            print(
                "Permission denied to create images folder. Please run Chocolate as an administrator or use the --images argument to specify a folder you have access to."
            )

    if not os.path.exists(ARTEFACTS_PATH):
        try:
            os.mkdir(ARTEFACTS_PATH)
        except PermissionError:
            print(
                "Permission denied to create artefacts folder. Please run Chocolate as an administrator or use the --artefacts argument to specify a folder you have access to."
            )

check_dependencies()
create_directories()

config = get_config()
tmdb: TMDb = create_tmdb()
app = create_app()
language_file = get_language_file()

register_plugins()
