import os
import time
import base64
import io

from PIL import Image
from flask import Blueprint, Response, jsonify, request, abort, send_file
from werkzeug.security import generate_password_hash

from chocolate_app import DB, get_dir_path, all_auth_tokens, IMAGES_PATH
from chocolate_app.tables import Users, InviteCodes
from chocolate_app.utils.utils import check_authorization, generate_log
from chocolate_app.plugins_loader.events import Events, execute_event

dir_path = get_dir_path()
users_bp = Blueprint("users", __name__)

@users_bp.route("/get_all_users", methods=["GET"])
def get_all_users():
    all_users = Users.query.filter().all()
    all_users_list = []
    for user in all_users:
        profile_picture = user.profile_picture
        if not os.path.exists(dir_path + profile_picture):
            profile_picture = "/static/img/avatars/defaultUserProfilePic.png"
        user_dict = {
            "name": user.name,
            "profile_picture": profile_picture,
            "account_type": user.account_type,
            "password_empty": True if not user.password else False,
            "id": user.id,
        }
        all_users_list.append(user_dict)
    return jsonify(all_users_list)

@users_bp.route("/profile_picture/<id>", methods=["GET"])
def get_profile_picture(id):
    user = Users.query.filter_by(id=id).first()
    if not user:
        return send_file("static/img/avatars/defaultUserProfilePic.png")
    
    profile_picture = user.profile_picture
    if not os.path.exists(profile_picture):
        profile_picture = "static/img/avatars/defaultUserProfilePic.png"
    return send_file(profile_picture)

@users_bp.route("/login", methods=["POST"])
def login():
    from uuid import uuid4

    auth_token = str(uuid4())
    account_name = ""
    if "name" not in request.get_json() and not "username" in request.get_json():
        abort(400, "Missing name or username")
    elif "name" not in request.get_json():
        account_name = request.get_json()["username"]
    else:
        account_name = request.get_json()["name"]

    account_password = request.get_json()["password"]
    user = Users.query.filter_by(name=account_name).first()
    token = f"Bearer {auth_token}"
    actual_time_in_seconds = int(time.time())
    all_auth_tokens[token] = {"user": account_name, "time": actual_time_in_seconds}
    if user:
        user_object = user.__dict__
        del user_object["_sa_instance_state"]

        if user.account_type == "Kid":
            generate_log(request, "LOGIN")
            execute_event(Events.LOGIN, user)
            return jsonify(
                {"id": user.id, "name": user.name, "error": "None", "token": auth_token, "user": user_object}
            )
        elif user.verify_password(account_password):
            generate_log(request, "LOGIN")
            execute_event(Events.LOGIN, user)
            return jsonify(
                {"id": user.id, "name": user.name, "error": "None", "token": auth_token, "user": user_object}
            )
        else:
            generate_log(request, "ERROR")
            user = user.__dict__
            user["error"] = "Unauthorized"
            execute_event(Events.LOGIN, user)
            return jsonify({"error": "Unauthorized"})
    else:
        generate_log(request, "ERROR")
        user = user.__dict__
        user["error"] = "Unauthorized"
        execute_event(Events.LOGIN, user)
        return jsonify({"error": "Unauthorized"})


@users_bp.route("/create_account", methods=["POST"])
def create_account():
    body = request.get_json()
    account_name = body["username"]
    account_password = body["password"]
    account_type_input = body["type"]

    profile_picture = f"{IMAGES_PATH}/avatars/{account_name}.webp"
    if "profile_picture" not in body:
        profile_picture = "/static/img/avatars/defaultUserProfilePic.png"
    else:
        file_base64 = body["profile_picture"]
        if file_base64.startswith("data:image"):
            file_base64 = file_base64.split(",", 1)[1]

        full_path = profile_picture

        image_data = base64.b64decode(file_base64)

        # Lire l'image à partir des bytes
        image = Image.open(io.BytesIO(image_data))

        # Déterminer le format de l'image
        image_format = image.format.lower()

        # Convertir l'image en format WebP si nécessaire
        if image_format != "webp":
            output_buffer = io.BytesIO()
            image.save(output_buffer, "WEBP")
            output_buffer.seek(0)
            image = Image.open(output_buffer)

        # Enregistrer l'image au format WebP
        image.save(full_path, "WEBP")
        image.close()

    user_exists = Users.query.filter_by(name=account_name).first()
    nb_users = len(Users.query.filter().all())
    if user_exists:
        abort(409)
    account_type_input = account_type_input.lower()
    account_type_input = account_type_input.capitalize()

    if nb_users == 0:
        account_type_input = "Admin"

    new_user = Users(
        name=account_name,
        password=account_password,
        profile_picture=profile_picture,
        account_type=account_type_input,
    )
    DB.session.add(new_user)
    DB.session.commit()
    return jsonify(
        {
            "id": new_user.id,
            "name": new_user.name,
        }
    )


@users_bp.route("/edit_profil", methods=["POST"])
def edit_profil() -> Response:
    authorization = request.headers.get("Authorization")

    if authorization not in all_auth_tokens:
        abort(401, "Unauthorized")

    user = Users.query.filter_by(name=all_auth_tokens[authorization]["user"]).first()

    body = request.get_json()

    user_name = body["name"]
    password = body["password"]

    db_user = Users.query.filter_by(name=user_name).first()

    if not db_user or str(db_user.id) != str(user.id):
        abort(500, "You are not allowed to change the username of this user")

    type = None
    if "type" in body:
        type = body["type"]
    id = body["id"]

    if str(id) != str(user.id) and user.account_type != "Admin":
        abort(401, "Unauthorized")

    username_in_tokens = all_auth_tokens[authorization]["user"]
    user = Users.query.filter_by(name=username_in_tokens).first()
    try:
        f = request.files["image"]
        name, extension = os.path.splitext(f.filename or "")
        profile_picture = f"/static/img/{user_name}{extension}"
        if extension == "":
            profile_picture = "/static/img/avatars/defaultUserProfilePic.png"
    except Exception:
        profile_picture = "/static/img/avatars/defaultUserProfilePic.png"

    user_to_edit = Users.query.filter_by(id=id).first()

    if user_to_edit.name != user_name:
        user_to_edit.name = user_name

    if type and user_to_edit.account_type != type:
        user_to_edit.account_type = type

    if user_to_edit.password != generate_password_hash(password) and len(password) > 0:
        user_to_edit.password = generate_password_hash(password)

    if password == "":
        user_to_edit.password = None
    if (
        user_to_edit.profile_picture != profile_picture
        and "/static/img/avatars/defaultUserProfilePic.png" not in profile_picture
    ):
        f = request.files["profile_picture"]
        f.save(f"{dir_path}{profile_picture}")
        user_to_edit.profile_picture = profile_picture

    DB.session.commit()

    return jsonify(
        {
            "id": user_to_edit.id,
            "name": user_to_edit.name,
        }
    )


@users_bp.route("/delete_account", methods=["POST"])
def delete_account() -> Response:
    authorization = request.headers.get("Authorization")
    check_authorization(request, authorization)
    body = request.get_json()
    if not body:
        abort(400, "Missing body")
    if "id" not in body:
        abort(400, "Missing id")
    id = body["id"]

    user = Users.query.filter_by(id=id).first()
    DB.session.delete(user)
    DB.session.commit()

    execute_event(Events.USER_DELETE, user)

    return jsonify(
        {
            "id": user.id,
            "name": user.name,
        }
    )


@users_bp.route("/get_profil/<id>")
def get_profil(id: int) -> Response:
    user = Users.query.filter_by(id=id).first()
    profile_picture = user.profile_picture
    if not os.path.exists(profile_picture):
        profile_picture = "/static/img/avatars/defaultUserProfilePic.png"
    user_dict = {
        "name": user.name,
        "profile_picture": profile_picture,
        "account_type": user.account_type,
    }
    return jsonify(user_dict)


@users_bp.route("/is_admin", methods=["GET"])
def is_admin() -> Response:
    authorization = request.headers.get("Authorization")
    check_authorization(request, authorization)
    user = Users.query.filter_by(name=all_auth_tokens[authorization]["user"]).first()
    if user.account_type == "Admin":
        return jsonify(True)
    else:
        return jsonify(False)


@users_bp.route("/invite_exist/<hash>", methods=["GET"])
def invite_exist(hash: str) -> Response:
    can = InviteCodes.query.filter_by(code=hash).first() is not None
    return jsonify(can)


@users_bp.route("/create_invite", methods=["POST"])
def create_invite() -> Response:
    authorization = request.headers.get("Authorization")
    check_authorization(request, authorization)
    user = Users.query.filter_by(name=all_auth_tokens[authorization]["user"]).first()

    if user.account_type != "Admin":
        abort(401, "Unauthorized")

    body = request.get_json()
    code = body["code"]
    new_invite = InviteCodes(code=code)
    DB.session.add(new_invite)
    DB.session.commit()
    return jsonify({"code": code})
