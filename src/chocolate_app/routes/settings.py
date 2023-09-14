from flask import Blueprint, jsonify, request

from chocolate_app import config, write_config, tmdb
from chocolate_app.tables import Users, Libraries

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/get_settings", methods=["GET"])
def get_settings():
    all_users = Users.query.all()
    all_libraries = Libraries.query.all()
    users = []
    for user in all_users:
        user = user.__dict__
        del user["_sa_instance_state"]
        user["password"] = "Ratio"
        users.append(user)

    libs = []
    for library in all_libraries:
        library = library.__dict__
        del library["_sa_instance_state"]
        libs.append(library)

    data = {
        "users": users,
        "libraries": libs,
    }

    all_sections = config.sections()
    for section in all_sections:
        section_data = config[section]
        the_data = {}
        for key in section_data:
            the_data[key] = section_data[key]
        data[section] = the_data

    return jsonify(data)


@settings_bp.route("/save_settings", methods=["GET", "POST"])
def save_settings():
    global client_id, client_secret
    body = request.get_json()
    tmdb_api_key = body["tmdbKey"]
    language = body["language"]
    igdb_secret_key = body["igdbSecret"]
    igdb_client_id = body["igdbID"]

    radarr_adress = body["radarrAdress"]
    radarrfolder = body["radarrFolder"]
    radarr_api_key = body["radarrAPI"]
    sonarr_adress = body["sonarrAdress"]
    sonarrfolder = body["sonarrFolder"]
    sonarr_api_key = body["sonarrAPI"]
    readarr_adress = body["readarrAdress"]
    readarrfolder = body["readarrFolder"]
    readarr_api_key = body["readarrAPI"]
    lidarr_adress = body["lidarrAdress"]
    lidarrfolder = body["lidarrFolder"]
    lidarr_api_key = body["lidarrAPI"]

    if radarr_adress != "":
        if radarr_adress.startswith("https://"):
            radarr_adress = radarr_adress.replace("https://", "http://")
        if not radarr_adress.startswith("http://"):
            radarr_adress = f"http://{radarr_adress}"
        config.set("ARRSettings", "radarrurl", radarr_adress)
    if radarrfolder != "":
        radarrfolder = radarrfolder.replace("\\", "/")
        if not radarrfolder.endswith("/"):
            radarrfolder = f"{radarrfolder}/"
        config.set("ARRSettings", "radarrfolder", radarrfolder)
    if radarr_api_key != "":
        config.set("APIKeys", "radarr", radarr_api_key)

    if sonarr_adress != "":
        if sonarr_adress.startswith("https://"):
            sonarr_adress = sonarr_adress.replace("https://", "http://")
        if not sonarr_adress.startswith("http://"):
            sonarr_adress = f"http://{sonarr_adress}"
        config.set("ARRSettings", "sonarrurl", sonarr_adress)
    if sonarrfolder != "":
        sonarrfolder = sonarrfolder.replace("\\", "/")
        if not sonarrfolder.endswith("/"):
            sonarrfolder = f"{sonarrfolder}/"
        config.set("ARRSettings", "sonarrfolder", sonarrfolder)
    if sonarr_api_key != "":
        config.set("APIKeys", "sonarr", sonarr_api_key)

    if readarr_adress != "":
        if readarr_adress.startswith("https://"):
            readarr_adress = readarr_adress.replace("https://", "http://")
        if not readarr_adress.startswith("http://"):
            readarr_adress = f"http://{readarr_adress}"
        config.set("ARRSettings", "readarrurl", readarr_adress)
    if readarrfolder != "":
        readarrfolder = readarrfolder.replace("\\", "/")
        if not readarrfolder.endswith("/"):
            readarrfolder = f"{readarrfolder}/"
        config.set("ARRSettings", "readarrfolder", readarrfolder)
    if readarr_api_key != "":
        config.set("ARRSettings", "readarrurl", readarr_adress)

    if lidarr_adress != "":
        if lidarr_adress.startswith("https://"):
            lidarr_adress = lidarr_adress.replace("https://", "http://")
        if not lidarr_adress.startswith("http://"):
            lidarr_adress = f"http://{lidarr_adress}"
        config.set("ARRSettings", "lidarrurl", lidarr_adress)
    if lidarrfolder != "":
        lidarrfolder = lidarrfolder.replace("\\", "/")
        if not lidarrfolder.endswith("/"):
            lidarrfolder = f"{lidarrfolder}/"
        config.set("ARRSettings", "lidarrfolder", lidarrfolder)
    if lidarr_api_key != "":
        config.set("ARRSettings", "lidarrurl", lidarr_adress)
    if tmdb_api_key != "":
        config.set("APIKeys", "TMDB", tmdb_api_key)
        tmdb.api_key = tmdb_api_key
    if igdb_client_id != "" and igdb_secret_key != "":
        config.set("APIKeys", "igdbid", igdb_client_id)
        config.set("APIKeys", "igdbsecret", igdb_secret_key)
        client_id = igdb_client_id
        client_secret = igdb_secret_key

    if language != "undefined":
        config.set("ChocolateSettings", "language", language)

    try:
        allow_download = body["allowDownloadsCheckbox"]
        if allow_download == "on":
            config.set("ChocolateSettings", "allowdownload", "true")
        else:
            config.set("ChocolateSettings", "allowdownload", "false")
    except Exception:
        config.set("ChocolateSettings", "allowdownload", "false")

    write_config(config)

    return jsonify({"error": "success"})
