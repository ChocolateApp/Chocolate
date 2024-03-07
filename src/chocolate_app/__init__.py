import os
import configparser
import platform
import argparse
import logging
import pathlib
import shutil

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_login import LoginManager # type: ignore
from flask_migrate import Migrate

from typing import Dict, Any

from tmdbv3api import TMDb # type: ignore

from chocolate_app.plugins_loader import loader

DB: SQLAlchemy = SQLAlchemy()
MIGRATE: Migrate = Migrate()
LOGIN_MANAGER: LoginManager = LoginManager()
all_auth_tokens: Dict[Any, Any] = {}


class ChocolateException(Exception):
    """Base class for exceptions in Chocolate"""


class UnsupportedSystemDefaultPath(ChocolateException):
    """Raised when the default path for the config file and the database file is not supported by Chocolate"""


parser: argparse.ArgumentParser = argparse.ArgumentParser("Chocolate")
parser.add_argument("--config", help="Path to the config file (a .ini file)")
parser.add_argument("--db", help="Path to the database file (a .db file)")
parser.add_argument("--images", help="Path to the images folder (a folder)")
parser.add_argument("--plugins", help="Path to the plugins folder (a folder)")
parser.add_argument("--logs", help="Path to the logs file (a .log file)")
parser.add_argument("--no-scans", help="Disable startup scans", action="store_true")

ARGUMENTS = parser.parse_args()

paths = {
    "Windows": {
        "config": f"{os.getenv('APPDATA')}/Chocolate/config.ini",
        "db": f"{os.getenv('APPDATA')}/Chocolate/database.db",
        "images": f"{os.getenv('APPDATA')}/Chocolate/images",
        "plugins": f"{os.getenv('APPDATA')}/Chocolate/plugins",
        "logs": f"{os.getenv('APPDATA')}/Chocolate/server.log",
    },
    "Linux": {
        "config": "/var/chocolate/config.ini",
        "db": "/var/chocolate/database.db",
        "images": "/var/chocolate/images/",
        "plugins": "/var/chocolate/plugins/",
        "logs": "/var/chocolate/server.log",
    },
    "Darwin": {
        "config": f"{os.getenv('HOME')}/Library/Application Support/Chocolate/config.ini",
        "db": f"{os.getenv('HOME')}/Library/Application Support/Chocolate/database.db",
        "images": f"{os.getenv('HOME')}/Library/Application Support/Chocolate/images/",
        "plugins": f"{os.getenv('HOME')}/Library/Application Support/Chocolate/plugins/",
        "logs": f"{os.getenv('HOME')}/Library/Application Support/Chocolate/server.log",
    },
}

OPERATING_SYSTEM: str = platform.system()

if OPERATING_SYSTEM not in paths.keys():
    raise UnsupportedSystemDefaultPath(
        f"No known default file path for the config / database on your operating system ({OPERATING_SYSTEM}). Please use --config and --database path or create a pull request to add your system to the one supported by Chocolate"
    )

CONFIG_PATH: str = ARGUMENTS.config or paths[OPERATING_SYSTEM]["config"]
CONFIG_PATH = CONFIG_PATH.replace("\\", "/")

DB_PATH: str = ARGUMENTS.db or paths[OPERATING_SYSTEM]["db"]
DB_PATH = DB_PATH.replace("\\", "/")

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


if os.getenv("NO_SCANS") == "true":
    ARGUMENTS.no_scans = True

def create_app() -> Flask:
    """
    Create the Flask app

    Returns:
        Flask: The Flask app
    """
    dir_path = pathlib.Path(__package__).parent
    TEMPLATE_FOLDER = f"{dir_path}/templates"

    if not os.path.isdir(IMAGES_PATH):
        os.mkdir(IMAGES_PATH)
    if not os.path.isdir(f"{IMAGES_PATH}/avatars"):
        os.mkdir(f"{IMAGES_PATH}/avatars")

    app = Flask(
        __name__, static_folder=f"{dir_path}/static", template_folder=TEMPLATE_FOLDER
    )

    app.secret_key = os.urandom(24)

    CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
    app.config["MAX_CONTENT_LENGTH"] = 4096 * 4096
    app.config["UPLOAD_FOLDER"] = f"{dir_path}/static/img/"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["DIR_PATH"] = dir_path
    app.config["JSON_AS_ASCII"] = False

    from .routes.users import users_bp
    from .routes.settings import settings_bp
    from .routes.libraries import libraries_bp
    from .routes.arr import arr_bp

    app.register_blueprint(users_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(libraries_bp)
    app.register_blueprint(arr_bp)

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
    if not os.path.exists(CONFIG_PATH):
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
    if configParser["ChocolateSettings"]["language"] == "Empty":
        configParser["ChocolateSettings"]["language"] = "EN"

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

check_dependencies()

config = get_config()
tmdb: TMDb = create_tmdb()
app = create_app()

register_plugins()
