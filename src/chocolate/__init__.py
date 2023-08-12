import os
import configparser
import platform
import argparse
import logging
import pathlib

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_login import LoginManager

from tmdbv3api import TMDb

DB = SQLAlchemy()
LOGIN_MANAGER = LoginManager()
all_auth_tokens = {}

parser = argparse.ArgumentParser("Chocolate")
parser.add_argument("--config", help="Path to the config file (a .ini file)")
parser.add_argument("--db", help="Path to the database file (a .db file)")

ARGUMENTS = parser.parse_args()

paths = {
    "Windows": {
        "config": f"{os.getenv('APPDATA')}/Chocolate/config.ini",
        "db": f"{os.getenv('APPDATA')}/Chocolate/database.db",
    },
    "Linux": {
        "config": "/var/chocolate/config.ini",
        "db": "/var/chocolate/database.db",
    },
    "Darwin": {
        "config": f"{os.getenv('HOME')}/Library/Application Support/Chocolate/config.ini",
        "db": f"{os.getenv('HOME')}/Library/Application Support/Chocolate/database.db",
    },
}

OPERATING_SYSTEM = platform.system()

if OPERATING_SYSTEM not in paths:
    raise UnsupportedSystemDefaultPath(f"No known default file path for the config / database on your operating system ({OPERATING_SYSTEM}). Please use --config and --database path or create a pull request to add your system to the one supported by Chocolate")


CONFIG_PATH = ARGUMENTS.config or paths[OPERATING_SYSTEM]["config"]
CONFIG_PATH = CONFIG_PATH.replace("\\", "/")
DB_PATH = ARGUMENTS.db or paths[OPERATING_SYSTEM]["db"]

class ChocolateException(Exception):
    """Base class for exceptions in Chocolate"""

class UnsupportedSystemDefaultPath(ChocolateException):
    """Raised when the default path for the config file and the database file is not supported by Chocolate"""

def create_app():
    is_in_docker = os.environ.get("AM_I_IN_A_DOCKER_CONTAINER", False)
    TEMPLATE_FOLDER = ""

    if is_in_docker:
        dir_path = "/chocolate"
        TEMPLATE_FOLDER = f"{dir_path}/templates"
    else:
        dir_path = pathlib.Path(__package__).parent
        TEMPLATE_FOLDER = f"{dir_path}/templates"
            
    app = Flask(__name__, static_folder=f"{dir_path}/static",
                template_folder=TEMPLATE_FOLDER)

    app.secret_key = "ChocolateDBPassword"

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
    LOGIN_MANAGER.init_app(app)
    LOGIN_MANAGER.login_view = "login"
    
    return app

def get_dir_path():
    is_in_docker = os.environ.get("AM_I_IN_A_DOCKER_CONTAINER", False)

    if is_in_docker:
        dir_path = "/chocolate"
    else:
        dir_path = os.path.dirname(__file__).replace("\\", "/")

    return dir_path

def create_tmdb():
    tmdb = TMDb()
    api_key_tmdb = config["APIKeys"]["TMDB"]
    if api_key_tmdb == "Empty":
        print(
            "Follow this tutorial to get your TMDB API Key : https://developers.themoviedb.org/3/getting-started/introduction"
        )
    tmdb.api_key = config["APIKeys"]["TMDB"]
    tmdb.language = config["ChocolateSettings"]["language"]

    return tmdb

def get_config():
    if not os.path.exists(CONFIG_PATH):
        logging.warning(f"Config file not found at {CONFIG_PATH}. Creating a new one...")
        
        if not os.path.isdir(os.path.dirname(CONFIG_PATH)):
            os.mkdir(os.path.dirname(CONFIG_PATH))

        with open(f"{get_dir_path()}/empty_config.ini", "r") as empty_config:
            with open(CONFIG_PATH, "w") as config:
                config.write(empty_config.read())

    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    if config["ChocolateSettings"]["language"] == "Empty":
        config["ChocolateSettings"]["language"] = "EN"
    return config

def write_config(config):
    with open(CONFIG_PATH, "w") as configfile:
        config.write(configfile)

config = get_config()
tmdb = create_tmdb()