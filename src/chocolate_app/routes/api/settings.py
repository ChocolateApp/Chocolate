import os

from iso639 import Lang

from chocolate_app import CONFIG_PATH, get_config, get_dir_path, write_config
from chocolate_app.routes.api.auth import token_required
from flask import Blueprint, request, Response
from chocolate_app.utils.utils import generate_response, Codes


settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


def handle_get_settings() -> Response:
    config = get_config()
    print(config.__dict__)
    return generate_response(Codes.SUCCESS, data=config.__dict__["_sections"])


def clean_json_for_config(json: dict) -> dict:
    for key, value in json.items():
        if isinstance(value, dict):
            json[key] = clean_json_for_config(value)
        elif value is True:
            json[key] = "true"
        elif value is False:
            json[key] = "false"
        elif value.isdigit():
            json[key] = int(value)
        elif value.replace(".", "", 1).isdigit():
            json[key] = float(value)
    return json


def handle_update_settings() -> Response:
    if not request.json:
        return generate_response(Codes.INVALID_MEDIA_TYPE)

    data = request.json

    cleaned_data = clean_json_for_config(data)

    write_config(cleaned_data)

    return generate_response(Codes.SUCCESS)


@settings_bp.route("", methods=["GET", "POST"])
@token_required
def settings() -> Response:
    if request.method == "GET":
        return handle_get_settings()
    elif request.method == "POST":
        return handle_update_settings()
    else:
        return generate_response(Codes.INVALID_METHOD)


@settings_bp.route("/languages", methods=["GET"])
def languages() -> Response:
    # get all the jsons in the static/lang folder (the file.json is the iso code)
    languages = []
    dir_path = get_dir_path()
    for file in os.listdir(f"{dir_path}/static/lang"):
        if file.endswith(".json"):
            languages.append(file[:-5])

    languages_list = []
    for language in languages:
        languages_list.append(
            {
                "code": language,
                "name": Lang(language).name,
            }
        )

    languages_list = sorted(languages_list, key=lambda x: x["name"])

    return generate_response(Codes.SUCCESS, data=languages_list)
