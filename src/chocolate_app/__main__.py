# Copyright (C) 2024 Impre_visible
import warnings
import requests
import threading
import sqlalchemy

from sqlalchemy import inspect
from sqlalchemy.sql import text
from watchdog.observers import Observer
from time import sleep
from watchdog.events import FileSystemEventHandler

from flask import (
    jsonify,
    Response,
    request,
    send_file,
    render_template,
)

from chocolate_app import (
    app,
    SERVER_PORT,
    get_dir_path,
    DB,
    LOGIN_MANAGER,
    tmdb,
    config,
    ARGUMENTS,
    scans,
    get_language_file,
)
from chocolate_app.tables import (
    Movies,
    Episodes,
    OthersVideos,
    Users,
    Libraries,
)
from chocolate_app.utils.utils import generate_log
from chocolate_app.plugins_loader import events, routes

dir_path: str = get_dir_path()

with app.app_context():
    DB.create_all()


with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=sqlalchemy.exc.SAWarning)


@LOGIN_MANAGER.user_loader
def load_user(id: int) -> Users | None:
    """
    Load the user from the database

    Args:
        id (int): The user id

    Returns:
        Users | None: The user or None
    """
    return Users.query.get(int(id))


tmdb.language = config["ChocolateSettings"]["language"].lower()
tmdb.debug = True


@app.after_request
def after_request(response: Response) -> Response:
    """
    The after request function

    Args:
        response (Response): The response

    Returns:
        Response: The response
    """

    ip_address = request.remote_addr

    if "CF-Connecting-IP" in request.headers:
        ip_address = request.headers["CF-Connecting-IP"]
    elif "X-Real-IP" in request.headers:
        ip_address = request.headers["X-Real-IP"]
    elif "X-Forwarded-For" in request.headers:
        ip_address = request.headers["X-Forwarded-For"]

    request.remote_addr = ip_address

    generate_log(
        request,
        f"{response.status_code} - {request.method} - {request.path} - {ip_address}",
    )

    return response


@app.route(
    "/",
    methods=[
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "PATCH",
        "HEAD",
        "CONNECT",
        "OPTIONS",
        "TRACE",
    ],
)
@app.route(
    "/<path:path>",
    methods=[
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "PATCH",
        "HEAD",
        "CONNECT",
        "OPTIONS",
        "TRACE",
    ],
)
def index(path=None) -> str | Response:
    """
    The index route

    Args:
        path (str, optional): The path. Defaults to None.

    Returns:
        str: The rendered template
    """

    if path and routes.have_static_file(path):
        return routes.get_static_file(path)

    if path and routes.have_route(path):
        return routes.execute_route(path, request)

    return render_template("index.html")


@app.route("/language_file")
def route_language_file() -> Response:
    return jsonify(get_language_file())


@app.route("/download_other/<video_hash>")
def download_other(video_hash: str) -> Response:
    video = OthersVideos.query.filter_by(video_hash=video_hash).first()
    video = video.__dict__
    del video["_sa_instance_state"]
    return send_file(video["slug"], as_attachment=True)


def is_valid_url(url: str) -> bool:
    try:
        response = requests.get(url)
        return response.status_code == requests.codes.ok
    except requests.exceptions.RequestException:
        return False


@app.route("/is_chocolate", methods=["GET", "POST"])
def is_chocolate() -> Response:
    return jsonify({"is_chocolate": True})


@app.route("/download_movie/<movie_id>")
def download_movie(movie_id: int) -> Response:
    can_download = config["ChocolateSettings"]["allowDownload"].lower() == "true"
    if not can_download:
        return jsonify({"error": "download not allowed"})
    movie = Movies.query.filter_by(id=movie_id).first()
    return send_file(movie.slug, as_attachment=True)


@app.route("/download_episode/<episode_id>")
def download_episode(episode_id: int) -> Response:
    can_download = config["ChocolateSettings"]["allowDownload"].lower() == "true"
    if not can_download:
        return jsonify({"error": "download not allowed"})
    episode = Episodes.query.filter_by(episode_id=episode_id).first()
    episode_path = episode.slug
    return send_file(episode_path, as_attachment=True)


def start_scanning_threads(app) -> None:
    def scan(library: Libraries = None) -> None:
        if library is None:
            return
        with app.app_context():
            update_db_columns(DB.engine, DB)
            library = library.__dict__

            type_to_call = {
                "series": scans.getSeries,
                "consoles": scans.getGames,
                "others": scans.getOthersVideos,
                "books": scans.getBooks,
                "musics": scans.getMusics,
            }

            scanner = None
            if library["type"] == "movies":
                scanner = scans.MovieScanner()
                scanner.set_library_name(library["name"])
                scanner.scan()
            elif library["type"] == "tv":
                scanner = scans.LiveTVScanner()
                scanner.set_library_name(library["name"])
                scanner.scan()
            else:
                scanner = type_to_call[library["type"]]
                scanner(library["name"])

    class ScanEventHandler(FileSystemEventHandler):

        def __init__(self):
            self.timer = None

        def on_any_event(self, event):
            with app.app_context():
                library = (
                    Libraries.query.filter_by(folder=event.src_path).first()
                    or Libraries.query.filter_by(folder=event.src_path + "/").first()
                )
                if event.event_type not in ["created", "deleted"]:
                    return

                if library is None:
                    return

                print(f"Detected event {event.event_type} in {event.src_path}")

                if self.timer is not None:
                    self.timer.cancel()

                self.timer = threading.Timer(30, scan, args=(library,))
                self.timer.start()

    # Launch the scan thread every 24 hours

    with app.app_context():
        # Setup watchdog for directory monitoring
        def start_watchdog(path_to_watch):
            event_handler = ScanEventHandler()
            observer = Observer()
            observer.schedule(event_handler, path=path_to_watch, recursive=True)
            observer.start()
            try:
                while True:
                    sleep(1)
            except KeyboardInterrupt:
                observer.stop()
            observer.join()

        # Launch watchdog thread for the directory to monitor
        for library in Libraries.query.all():
            if library.type == "tv":
                continue
                scanner = scans.LiveTVScanner()
                scanner.set_library_name(library.name)
                scanner.scan()
                continue

            scan(library)

            watchdog_thread = threading.Thread(
                target=start_watchdog, args=(library.folder,)
            )
            watchdog_thread.daemon = True
            watchdog_thread.start()

    print("Scanning threads and watchdog initialized.")


def start_chocolate() -> None:
    events.execute_event(events.Events.BEFORE_START)
    if not ARGUMENTS.no_scans and config["APIKeys"]["TMDB"] != "Empty":
        start_scanning_threads(app)

    app.run(host="0.0.0.0", port=SERVER_PORT)
    events.execute_event(events.Events.AFTER_START)


def update_db_columns(engine, db):
    # Connecter à la base de données
    connection = engine.connect()
    inspector = inspect(engine)

    # Parcourir toutes les classes définies dans Base
    for cls in db.metadata.tables.values():
        # Si la classe est une sous-classe de db.Model
        # print the attributes of the class
        name = None

        if hasattr(cls, "name"):
            name = cls.name
        elif hasattr(cls, "full_name"):
            name = cls.full_name

        if name:
            table_name = name

            columns = inspector.get_columns(table_name)

            class_columns = cls.columns.keys()

            missing_columns = [
                column
                for column in class_columns
                if column not in [col["name"] for col in columns]
            ]

            extra_columns = [
                column
                for column in columns
                if (column["name"] or column["full_name"]) not in class_columns
            ]

            for column in missing_columns:
                column_type = cls.columns[column].type
                connection.execute(
                    text(f"ALTER TABLE {table_name} ADD COLUMN {column} {column_type};")
                )

            for column in extra_columns:
                name = None

                if hasattr(column, "name"):
                    name = column.name
                elif hasattr(column, "full_name"):
                    name = column.full_name
                else:
                    continue

                connection.execute(
                    text(f"ALTER TABLE {table_name} DROP COLUMN {column['name']};")
                )

    connection.close()


if __name__ == "__main__":
    start_chocolate()
