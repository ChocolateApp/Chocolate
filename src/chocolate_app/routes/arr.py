from flask import Blueprint, jsonify, request
from pyarr import LidarrAPI, RadarrAPI, ReadarrAPI, SonarrAPI
from tmdbv3api import Find

from chocolate_app import config

arr_bp = Blueprint("arr", __name__)

@arr_bp.route("/lookup", methods=["POST"])
def lookup():
    json_file = request.get_json()
    media_type = json_file["mediaType"]
    query = json_file["query"]

    if media_type == "movie":
        radarr_api_key = config["APIKeys"]["radarr"]
        radarr_url = config["ARRSettings"]["radarrurl"]
        radarr = RadarrAPI(radarr_url, radarr_api_key)
        search_results = radarr.lookup_movie(query)
        return jsonify(search_results)
    elif media_type == "serie":
        sonarr_api_key = config["APIKeys"]["sonarr"]
        sonarr_url = config["ARRSettings"]["sonarrurl"]
        sonarr = SonarrAPI(sonarr_url, sonarr_api_key)
        search_results = sonarr.lookup_series(query)
        return jsonify(search_results)
    elif media_type == "music":
        lidarr_api_key = config["APIKeys"]["lidarr"]
        lidarr_url = config["ARRSettings"]["lidarrurl"]
        lidarr = LidarrAPI(lidarr_url, lidarr_api_key)
        search_results = lidarr.lookup(query)
        return jsonify(search_results)
    elif media_type == "book":
        readarr_api_key = config["APIKeys"]["readarr"]
        readarr_url = config["ARRSettings"]["readarrurl"]
        readarr = ReadarrAPI(readarr_url, readarr_api_key)
        search_results = readarr.lookup_book(term=query)
        return jsonify(search_results)


@arr_bp.route("/list_qualities/<mediaType>", methods=["GET"])
def list_qualities(media_type):
    if media_type == "movie":
        radarr_api_key = config["APIKeys"]["radarr"]
        radarr_url = config["ARRSettings"]["radarrurl"]
        radarr = RadarrAPI(radarr_url, radarr_api_key)
        quality_list = radarr.get_quality_profile()

        real_quality_list = []

        for quality in quality_list:
            real_quality_list.append({"id": quality["id"], "name": quality["name"]})

        # order the list by name
        real_quality_list = sorted(real_quality_list, key=lambda k: k["name"].lower())

        return jsonify(real_quality_list)
    elif media_type == "serie":
        sonarr_api_key = config["APIKeys"]["sonarr"]
        sonarr_url = config["ARRSettings"]["sonarrurl"]
        sonarr = SonarrAPI(sonarr_url, sonarr_api_key)
        quality_list = sonarr.get_quality_profile()

        real_quality_list = []

        for quality in quality_list:
            real_quality_list.append({"id": quality["id"], "name": quality["name"]})

        # order the list by name
        real_quality_list = sorted(real_quality_list, key=lambda k: k["name"].lower())

        return jsonify(real_quality_list)

    elif media_type == "music":
        lidarr_api_key = config["APIKeys"]["lidarr"]
        lidarr_url = config["ARRSettings"]["lidarrurl"]
        lidarr = LidarrAPI(lidarr_url, lidarr_api_key)
        quality_list = lidarr.get_quality_profile()

        real_quality_list = []

        for quality in quality_list:
            real_quality_list.append({"id": quality["id"], "name": quality["name"]})

        # order the list by name
        real_quality_list = sorted(real_quality_list, key=lambda k: k["name"].lower())

        return jsonify(real_quality_list)

    elif media_type == "book":
        readarr_api_key = config["APIKeys"]["readarr"]
        readarr_url = config["ARRSettings"]["readarrurl"]
        readarr = ReadarrAPI(readarr_url, readarr_api_key)
        quality_list = readarr.get_quality_profile()

        real_quality_list = []

        for quality in quality_list:
            real_quality_list.append({"id": quality["id"], "name": quality["name"]})

        # order the list by name
        real_quality_list = sorted(real_quality_list, key=lambda k: k["name"].lower())

        return jsonify(real_quality_list)

    return jsonify(
        [
            {
                "id": 1,
                "name": "There's not quality profile, you must create one in the app",
            }
        ]
    )


@arr_bp.route("/list_language_profiles/<mediaType>", methods=["GET"])
def list_language_profiles(media_type):
    if media_type == "serie":
        sonarr_api_key = config["APIKeys"]["sonarr"]
        sonarr_url = config["ARRSettings"]["sonarrurl"]
        sonarr = SonarrAPI(sonarr_url, sonarr_api_key)
        languages = sonarr.get_language_profile()
        real_languages = []
        saved_ids = []
        for language in languages:
            the_languages = language["languages"]
            for the_language in the_languages:
                if the_language["allowed"]:
                    if the_language["language"]["id"] not in saved_ids:
                        saved_ids.append(the_language["language"]["id"])
                        real_languages.append(the_language["language"])
        return jsonify(real_languages)
    return jsonify(
        [
            {
                "id": 1,
                "name": "There's not language profile, you must create one in the app",
            }
        ]
    )


@arr_bp.route("/add_media", methods=["POST"])
def add_media():
    media_type = request.get_json()["mediaType"]
    media_id = request.get_json()["ID"]
    quality_profile = request.get_json()["qualityID"]
    term = request.get_json()["term"]

    if media_type == "movie":
        radarr_folder = config["ARRSettings"]["radarrFolder"]
        radarr_api_key = config["APIKeys"]["radarr"]
        radarr_url = config["ARRSettings"]["radarrurl"]
        radarr = RadarrAPI(radarr_url, radarr_api_key)
        # get all quality : print(radarr.get_quality_profile())
        movie = radarr.lookup_movie(term=term)[int(media_id)]
        radarr.add_movie(
            movie=movie, quality_profile_id=int(quality_profile), root_dir=radarr_folder
        )
    elif media_type == "serie":
        language_id = request.get_json()["languageId"]
        sonarr_folder = config["ARRSettings"]["sonarrFolder"]
        sonarr_api_key = config["APIKeys"]["sonarr"]
        sonarr_url = config["ARRSettings"]["sonarrurl"]
        language_id = request.get_json()["languageId"]
        sonarr = SonarrAPI(sonarr_url, sonarr_api_key)
        serie = sonarr.lookup_series(term=term)[int(media_id)]
        sonarr.add_series(
            series=serie,
            quality_profile_id=int(quality_profile),
            root_dir=sonarr_folder,
            language_profile_id=int(language_id),
        )
    elif media_type == "music":
        file_type = request.get_json()["type"]
        lidarr_folder = config["ARRSettings"]["lidarrFolder"]
        lidarr_api_key = config["APIKeys"]["lidarr"]
        lidarr_url = config["ARRSettings"]["lidarrurl"]
        lidarr = LidarrAPI(lidarr_url, lidarr_api_key)
        # print(f"mediaID: {mediaID} | quality_profile: {quality_profile} | lidarrFolder: {lidarrFolder}")
        if file_type == "album":
            album = lidarr.lookup(term=term)[int(media_id)]["album"]
            add_album = lidarr.add_album(
                album=album,
                quality_profile_id=int(quality_profile),
                root_dir=lidarr_folder,
            )
            print(add_album)
        elif file_type == "artist":
            artist = lidarr.lookup(term=term)[int(media_id)]
            lidarr.add_artist(
                artist=artist,
                quality_profile_id=int(quality_profile),
                root_dir=lidarr_folder,
            )
    elif media_type == "book":
        readarr_folder = config["ARRSettings"]["readarrFolder"]
        readarr_api_key = config["APIKeys"]["readarr"]
        readarr_url = config["ARRSettings"]["readarrurl"]
        readarr = ReadarrAPI(readarr_url, readarr_api_key)

        readarr.add_book(
            db_id=int(media_id),
            quality_profile_id=int(quality_profile),
            root_dir=readarr_folder,
            book_id_type="goodreads",
        )

    return jsonify({"status": "ok"})


@arr_bp.route("/get_tmdb_poster", methods=["POST"])
def get_imdb_poster():
    json_file = request.get_json()
    if "imdbId" in json_file:
        imdb_id = json_file["imdbId"]
        find = Find()
        media = find.find_by_imdb_id(imdb_id)
        url = ""
        if media:
            try:
                for movie in media["movie_results"]:
                    url = f"https://www.themoviedb.org/t/p/w600_and_h900_bestv2{movie['poster_path']}"
                    break
                for serie in media["tv_results"]:
                    url = f"https://www.themoviedb.org/t/p/w600_and_h900_bestv2{serie['poster_path']}"
                    break
            except Exception:
                url = "/static/img/broken.webp"
        return jsonify({"url": url})
    else:
        return jsonify({"url": "/static/img/broken.webp"})
