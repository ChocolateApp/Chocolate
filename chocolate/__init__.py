import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_login import LoginManager

db = SQLAlchemy()
loginManager = LoginManager()


def create_app():
    dirPath = os.getcwd()
    dirPath = os.path.dirname(__file__).replace("\\", "/")
    dirPath = dirPath.replace("/chocolate", "")

    app = Flask(__name__, static_folder=f"{dirPath}/static")
    app.secret_key = "ChocolateDBPassword"

    CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})
    app.config["SQLALCHEMY_DATABASE_URI"] = f'sqlite:///{dirPath}/database.db'
    app.config['MAX_CONTENT_LENGTH'] = 4096 * 4096
    app.config['UPLOAD_FOLDER'] = f"{dirPath}/static/img/"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    loginManager.init_app(app)
    loginManager.login_view = 'login'

    return app
