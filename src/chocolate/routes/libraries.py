import json
import os

from flask import Blueprint, jsonify, request, abort, send_file

from chocolate import DB, all_auth_tokens
from chocolate.tables import *
import chocolate.scans as scans
from ..utils.utils import generate_log

libraries_bp = Blueprint('libraries', __name__)

@libraries_bp.route("/get_all_libraries", methods=["GET"])
def get_all_libraries():
    token = request.headers.get("Authorization")
    if token not in all_auth_tokens:
        abort(401)

    user = all_auth_tokens[token]["user"]
    user = Users.query.filter_by(name=user).first()

    libraries = Libraries.query.filter_by().all()
    libraries_list = [library.__dict__ for library in libraries]
    for library in libraries_list:
        del library["_sa_instance_state"]
    if user.account_type != "Admin":
        for library in libraries_list:
            if library["available_for"] != None:
                available_for = str(library["available_for"]).split(",")
                if str(user.id) not in available_for:
                    libraries_list.remove(library)

    libraries = sorted(libraries_list, key=lambda k: k["lib_name"].lower())
    libraries = sorted(libraries_list, key=lambda k: k["lib_type"].lower())

    generate_log(request, "SERVER")

    return jsonify(libraries)

@libraries_bp.route("/create_library", methods=["POST"])
def create_lib():
    the_request = request.get_json()
    the_request = json.loads(the_request)
    lib_name = the_request["lib_name"]
    lib_path = the_request["libPath"]
    lib_type = the_request["lib_type"]
    lib_users = the_request["libUsers"]

    if lib_users == "":
        lib_users = None

    icons = {
        "movies": "film",
        "series": "videocam",
        "consoles": "game-controller",
        "tv": "tv",
        "others": "desktop",
        "books": "book",
        "musics": "headset",
    }

    function_to_call = {
        "movies": scans.getMovies,
        "series": scans.getSeries,
        "consoles": scans.getGames,
        "others": scans.getOthersVideos,
        "books": scans.getBooks,
        "musics": scans.getMusics,
    }

    lib_path = lib_path.replace("\\", "/")

    exists = Libraries.query.filter_by(lib_name=lib_name).first() is not None
    if not exists:
        new_lib = Libraries(
            lib_name=lib_name,
            lib_folder=lib_path,
            lib_type=lib_type,
            lib_image=icons[lib_type],
            available_for=lib_users,
        )
        DB.session.add(new_lib)
        DB.session.commit()
        try:
            function_to_call[lib_type](lib_name)
        except:
            pass

        return jsonify({"error": "worked"})
    else:
        abort(409)

@libraries_bp.route("/edit_library", methods=["POST"])
def edit_lib():
    the_request = request.get_json()
    default_path = the_request["defaultPath"]
    lib_name = the_request["name"]
    lib_path = the_request["path"]
    lib_type = the_request["type"]

    lib_users = None

    lib_path = lib_path.replace("\\", "/")

    lib = Libraries.query.filter_by(lib_folder=default_path).first()
    if lib is None:
        abort(404)

    lib.lib_folder = lib_path
    lib.lib_type = lib_type
    lib.available_for = lib_users
    DB.session.commit()
    return jsonify({"error": "worked"})

@libraries_bp.route("/delete_library", methods=["POST"])
def delete_lib():
    the_request = request.get_json()
    print(the_request)
    lib_name = the_request["lib_name"]
    lib = Libraries.query.filter_by(lib_name=lib_name).first()

    if lib is None:
        abort(404)

    DB.session.delete(lib)

    lib_type = lib.lib_type

    if lib_type == "movies":
        all_movies = Movies.query.filter_by(library_name=lib_name).all()
        for movie in all_movies:
            DB.session.delete(movie)
    elif lib_type == "series":
        all_series = Series.query.filter_by(library_name=lib_name).all()
        for serie in all_series:
            seasons = Seasons.query.filter_by(serie=serie.id).all()
            for season in seasons:
                episodes = Episodes.query.filter_by(season_id=season.season_id).all()
                for episode in episodes:
                    DB.session.delete(episode)
                DB.session.delete(season)
            DB.session.delete(serie)
    elif lib_type == "consoles":
        all_games = Games.query.filter_by(library_name=lib_name).all()
        for game in all_games:
            DB.session.delete(game)
    elif lib_type == "others":
        all_other = OthersVideos.query.filter_by(library_name=lib_name).all()
        for other in all_other:
            DB.session.delete(other)

    DB.session.commit()
    return jsonify({"error": "worked"})

@libraries_bp.route("/rescan_all", methods=["POST"])
def rescan_all():
    libraries = Libraries.query.all()
    for lib in libraries:
        lib = lib.__dict__
        if "lib_type" not in lib.keys():
            continue
        if lib["lib_type"] == "series":
            scans.getSeries(lib["lib_name"])
        elif lib["lib_type"] == "movies":
            scans.getMovies(lib["lib_name"])
        elif lib["lib_type"] == "consoles":
            scans.getGames(lib["lib_name"])
        elif lib["lib_type"] == "others":
            scans.getOthersVideos(lib["lib_name"])
    return jsonify(True)

@libraries_bp.route("/rescan/<library>", methods=["POST"])
def rescan(library):
    exists = Libraries.query.filter_by(lib_name=library).first() is not None
    if exists:
        library = Libraries.query.filter_by(lib_name=library).first().__dict__
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
        return jsonify(True)
    return jsonify(False)