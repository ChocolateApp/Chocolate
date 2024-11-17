import os

from iso639 import Lang

from chocolate_app import DB, get_config, get_dir_path, write_config
from chocolate_app.routes.api.auth import token_required
from flask import Blueprint, request, Response
from chocolate_app.tables import Libraries, Users
from chocolate_app.utils.utils import generate_response, Codes


settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


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


def handle_general_settings(method) -> Response:
    def get() -> Response:
        config = get_config()
        return generate_response(Codes.SUCCESS, data=config.__dict__["_sections"])

    def post() -> Response:
        if not request.json:
            return generate_response(Codes.INVALID_MEDIA_TYPE)

        data = request.json

        cleaned_data = clean_json_for_config(data)

        write_config(cleaned_data)

        return generate_response(Codes.SUCCESS)

    if method == "GET":
        return get()
    elif method == "POST":
        return post()
    else:
        return generate_response(Codes.INVALID_METHOD)


def handle_accounts_settings(method) -> Response:
    def get() -> Response:
        accounts = Users.query.all()
        accounts_list = []
        for account in accounts:
            accounts_list.append(
                {
                    "id": account.id,
                    "name": account.name,
                    "account_type": account.account_type,
                }
            )

        return generate_response(Codes.SUCCESS, data=accounts_list)

    def post() -> Response:
        if not request.json:
            return generate_response(Codes.INVALID_MEDIA_TYPE)

        data = request.json

        if "id" not in data:
            return generate_response(Codes.MISSING_DATA, True)

        account = Users.query.filter_by(id=data["id"]).first()

        if not account:
            return generate_response(Codes.USER_NOT_FOUND, True)

        if "name" in data:
            account.name = data["name"]

        if "account_type" in data:
            account.account_type = data["account_type"]

        DB.session.commit()

        return generate_response(Codes.SUCCESS)

    def delete() -> Response:
        if not request.json:
            return generate_response(Codes.INVALID_MEDIA_TYPE)

        data = request.json

        if "id" not in data:
            return generate_response(Codes.MISSING_DATA, True)

        account = Users.query.filter_by(id=data["id"]).first()

        if not account:
            return generate_response(Codes.USER_NOT_FOUND, True)

        DB.session.delete(account)
        DB.session.commit()

        return generate_response(Codes.SUCCESS)

    def put() -> Response:
        if not request.json:
            return generate_response(Codes.INVALID_MEDIA_TYPE)

        data = request.json

        if "name" not in data or "password" not in data or "account_type" not in data:
            return generate_response(Codes.MISSING_DATA, True)

        user = Users(
            name=data["name"],
            password=data["password"],
            account_type=data["account_type"],
            profile_picture="static/images/default_profile_picture.jpg",
        )
        DB.session.add(user)
        DB.session.commit()

        return generate_response(Codes.SUCCESS)

    if method == "GET":
        return get()
    elif method == "POST":
        return post()
    elif method == "DELETE":
        return delete()
    elif method == "PUT":
        return put()
    else:
        return generate_response(Codes.INVALID_METHOD)


def handle_libraries_settings(method) -> Response:
    def get() -> Response:
        libraries = Libraries.query.all()
        libraries_list = []
        for library in libraries:
            libraries_list.append(
                {
                    "id": library.id,
                    "name": library.name,
                    "path": library.folder,
                    "type": library.type,
                }
            )

        return generate_response(Codes.SUCCESS, data=libraries_list)

    def post() -> Response:
        if not request.json:
            return generate_response(Codes.INVALID_MEDIA_TYPE)

        data = request.json

        if "id" not in data:
            return generate_response(Codes.MISSING_DATA, True)

        library = DB.session.query(Libraries).filter_by(id=data["id"]).first()

        if "scan" in data and data["scan"]:
            # TODO: Implement the scan function
            return generate_response(Codes.SUCCESS)

        if not library:
            return generate_response(Codes.LIBRARY_NOT_FOUND, True)

        if "name" in data:
            library.name = data["name"]

        if "path" in data:
            library.folder = data["path"]

        DB.session.commit()

        return generate_response(Codes.SUCCESS)

    def delete() -> Response:
        if not request.json:
            return generate_response(Codes.INVALID_MEDIA_TYPE)

        data = request.json

        if "id" not in data:
            return generate_response(Codes.MISSING_DATA, True)

        library = DB.session.query(Libraries).filter_by(id=data["id"]).first()

        if not library:
            return generate_response(Codes.LIBRARY_NOT_FOUND, True)

        DB.session.delete(library)
        DB.session.commit()

        return generate_response(Codes.SUCCESS)

    def put() -> Response:
        if not request.json:
            return generate_response(Codes.INVALID_MEDIA_TYPE)

        data = request.json

        if "name" not in data or "path" not in data:
            return generate_response(Codes.MISSING_DATA, True)

        library = Libraries(
            name=data["name"],
            folder=data["path"],
            type=data["type"],
            image="",
            available_for=None,
        )

        DB.session.add(library)
        DB.session.commit()

        return generate_response(Codes.SUCCESS)

    if method == "GET":
        return get()
    elif method == "POST":
        return post()
    elif method == "DELETE":
        return delete()
    elif method == "PUT":
        return put()
    else:
        return generate_response(Codes.INVALID_METHOD)


@settings_bp.route("/<section>", methods=["GET", "POST", "PUT", "DELETE"])
@token_required
def settings(section) -> Response:
    if section == "general":
        return handle_general_settings(request.method)
    elif section == "accounts":
        return handle_accounts_settings(request.method)
    elif section == "libraries":
        return handle_libraries_settings(request.method)
    else:
        return generate_response(Codes.MISSING_DATA, True)


@settings_bp.route("/languages", methods=["GET"])
def languages() -> Response:
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
