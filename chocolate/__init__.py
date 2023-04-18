import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_login import LoginManager


db = SQLAlchemy()
loginManager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.secret_key = "ChocolateDBPassword"

    CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

    dirPath = os.getcwd()
    dirPath = os.path.dirname(__file__).replace("\\", "/")
    app.config["SQLALCHEMY_DATABASE_URI"] = f'sqlite:///{dirPath}/database.db'
    app.config['MAX_CONTENT_LENGTH'] = 4096 * 4096
    app.config['UPLOAD_FOLDER'] = f"{dirPath}/static/img/"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    loginManager.init_app(app)
    loginManager.login_view = 'login'

    return app
