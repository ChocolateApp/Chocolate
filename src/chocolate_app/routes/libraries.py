import json
import natsort

from flask import Blueprint, jsonify, request, abort
from operator import itemgetter

from chocolate_app import DB, all_auth_tokens
from chocolate_app.tables import (
    Libraries,
    LibrariesMerge,
    Users,
    Movies,
    Series,
    Seasons,
    Episodes,
    Games,
    OthersVideos,
)
import chocolate_app.scans as scans
from ..utils.utils import generate_log

libraries_bp = Blueprint("libraries", __name__)


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
            if library["available_for"] is not None:
                available_for = str(library["available_for"]).split(",")
                if str(user.id) not in available_for:
                    libraries_list.remove(library)

    libraries = sorted(libraries_list, key=lambda k: k["lib_name"].lower())
    libraries = sorted(libraries_list, key=lambda k: k["lib_type"].lower())

    for library in libraries:
        child_libs = LibrariesMerge.query.filter_by(
            parent_lib=library["lib_name"]
        ).all()
        child_libs = [child.child_lib for child in child_libs]
        for child in child_libs:
            for lib in libraries:
                if lib["lib_name"] == child:
                    libraries.remove(lib)

    generate_log(request, "SERVER")

    return jsonify(libraries)


@libraries_bp.route("/get_all_libraries_created")
def get_all_libraries_created():
    token = request.headers.get("Authorization")
    if token not in all_auth_tokens:
        abort(401)

    user = all_auth_tokens[token]["user"]
    user = Users.query.filter_by(name=user).first()

    libraries = Libraries.query.filter_by().all()
    libraries_list = [library.__dict__ for library in libraries]
    for library in libraries_list:
        del library["_sa_instance_state"]
        # check if lib already have a parent
        parent = LibrariesMerge.query.filter_by(child_lib=library["lib_name"]).first()
        if parent is not None:
            library["merge_parent"] = parent.parent_lib
        # if lib is a parent, can't be a child
        child = LibrariesMerge.query.filter_by(parent_lib=library["lib_name"]).first()
        if child is None:
            library_type = library["lib_type"]
            # for all lib of the same type, remove the actual lib, and add all the lib to "possible_merge_parent"
            for lib in libraries_list:
                is_child = LibrariesMerge.query.filter_by(
                    child_lib=lib["lib_name"]
                ).first()
                if (
                    lib["lib_type"] == library_type
                    and lib["lib_name"] != library["lib_name"]
                    and is_child is None
                ):
                    if "possible_merge_parent" not in library:
                        library["possible_merge_parent"] = []
                    data = {"value": lib["lib_name"], "text": lib["lib_name"]}
                    library["possible_merge_parent"].append(data)

    if user.account_type != "Admin":
        for library in libraries_list:
            if library["available_for"] is not None:
                available_for = str(library["available_for"]).split(",")
                if str(user.id) not in available_for:
                    libraries_list.remove(library)



    generate_log(request, "SERVER")

    return jsonify(libraries_list)


@libraries_bp.route("/create_library", methods=["POST"])
def create_lib():
    the_request = request.get_json()
    the_request = json.loads(the_request)
    lib_name = the_request["lib_name"]
    lib_path = the_request["lib_path"]
    lib_type = the_request["lib_type"]
    lib_users = the_request["lib_users"]

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
        except Exception:
            pass

        return jsonify({"error": "worked"})
    else:
        abort(409)


@libraries_bp.route("/edit_library", methods=["POST"])
def edit_lib():
    token = request.headers.get("Authorization")
    if token not in all_auth_tokens:
        abort(401)

    the_request = request.get_json()
    default_path = the_request["default_path"]
    lib_name = the_request["name"]
    lib_path = the_request["path"]
    lib_type = the_request["type"]
    lib_users = the_request["users"]
    merge_parent = the_request["merge_parent"]

    merge_libraries(merge_parent, lib_name)

    lib_path = lib_path.replace("\\", "/")

    lib = Libraries.query.filter_by(lib_folder=default_path).first()
    if lib is None:
        abort(404)

    if lib_path is not None:
        lib.lib_folder = lib_path
    if lib_type is not None:
        lib.lib_type = lib_type
    if lib_users is not None:
        if len(lib_users.split(",")) == 1:
            lib_users = int(lib_users.replace('"', ""))
        lib.available_for = lib_users
    DB.session.commit()
    return jsonify({"error": "worked"})


@libraries_bp.route("/delete_library", methods=["POST"])
def delete_lib():
    the_request = request.get_json()

    lib_name = the_request["name"]
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
    libraries = [library.__dict__ for library in libraries]

    libraries = natsort.natsorted(libraries, key=itemgetter(*["lib_name"]))
    libraries = natsort.natsorted(libraries, key=itemgetter(*["lib_type"]))

    type_to_call = {
        "series": scans.getSeries,
        "movies": scans.getMovies,
        "consoles": scans.getGames,
        "others": scans.getOthersVideos,
        "books": scans.getBooks,
        "musics": scans.getMusics,
    }

    for library in libraries:
        if library["lib_type"] in type_to_call:
            type_to_call[library["lib_type"]](library["lib_name"])
    return jsonify(True)


@libraries_bp.route("/rescan/<library>", methods=["POST"])
def rescan(library):
    exists = Libraries.query.filter_by(lib_name=library).first() is not None

    type_to_call = {
        "series": scans.getSeries,
        "movies": scans.getMovies,
        "consoles": scans.getGames,
        "others": scans.getOthersVideos,
        "books": scans.getBooks,
        "musics": scans.getMusics,
    }

    if exists:
        library = Libraries.query.filter_by(lib_name=library).first().__dict__
        merges = LibrariesMerge.query.filter_by(parent_lib=library["lib_name"]).all()
        for merge in merges:
            child = Libraries.query.filter_by(lib_name=merge.child_lib).first()
            type_to_call[child.lib_type](child.lib_name)
        type_to_call[library["lib_type"]](library["lib_name"])
        return jsonify(True)
    return jsonify(False)


def merge_libraries(parent, child):
    if not child:
        return

    if not parent:
        merge = LibrariesMerge.query.filter_by(child_lib=child).first()
        if merge is not None:
            DB.session.delete(merge)
            DB.session.commit()
        return

    parent = Libraries.query.filter_by(lib_name=parent).first()
    if parent is None:
        return

    child = Libraries.query.filter_by(lib_name=child).first()
    if child is None:
        return

    if parent.lib_type != child.lib_type:
        return

    exist = LibrariesMerge.query.filter_by(
        parent_lib=parent.lib_name, child_lib=child.lib_name
    ).first()
    # child is already a parent
    is_parent = LibrariesMerge.query.filter_by(parent_lib=child.lib_name).first()

    if exist is None and is_parent is None:
        fusion = LibrariesMerge(parent_lib=parent.lib_name, child_lib=child.lib_name)
        DB.session.add(fusion)
        DB.session.commit()
    elif is_parent is None:
        fusion = LibrariesMerge.query.filter_by(
            parent_lib=parent.lib_name, child_lib=child.lib_name
        ).first()
        DB.session.delete(fusion)
        DB.session.commit()
    return
