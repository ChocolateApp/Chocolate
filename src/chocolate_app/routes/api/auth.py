import os
import jwt
import base64
import datetime

from PIL import Image
from io import BytesIO
from functools import wraps
from flask import Blueprint, request, current_app

from chocolate_app import DB, get_dir_path
from chocolate_app.tables import Users
from chocolate_app.utils.utils import generate_response, Codes

dir_path = get_dir_path()
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

ACCESS_TOKEN_EXPIRATION = 24 * 30  # 30 days
REFRESH_TOKEN_EXPIRATION = 24 * 30 * 6  # approximatively 6 months


def image_to_base64(
    image_path: str, width: int | None = None, height: int | None = None
) -> str:
    image_base64 = None
    with open(image_path, "rb") as image_file:
        image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

    if width and height:
        image = Image.open(BytesIO(base64.b64decode(image_base64)))
        image = image.resize((width, height))
        buffered = BytesIO()

        image.save(buffered, format="JPEG")

        image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return image_base64


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        access_token = None

        if "Authorization" in request.headers:
            access_token = request.headers["Authorization"]

        if not access_token:
            return generate_response(Codes.MISSING_DATA, True)

        splited_token = access_token.split(" ")

        if len(splited_token) != 2:
            return generate_response(Codes.INVALID_TOKEN, True)

        access_token = splited_token[1]
        try:
            data = jwt.decode(
                access_token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )
            current_user = Users.query.filter_by(id=data["id"]).first()
        except Exception:
            return generate_response(Codes.INVALID_TOKEN, True)

        if not current_user:
            return generate_response(Codes.USER_NOT_FOUND, True)

        if "current_user" in f.__code__.co_varnames:
            return f(current_user, *args, **kwargs)
        else:
            return f(*args, **kwargs)

    return decorated


@auth_bp.route("/check", methods=["GET", "POST"])
@token_required
def check_auth(current_user):
    profile_picture = current_user.profile_picture

    if not profile_picture.startswith("data:image"):
        profile_picture = os.path.join(dir_path, current_user.profile_picture)
        profile_picture = (
            f"data:image/jpeg;base64,{image_to_base64(profile_picture, 200, 200)}"
        )

    return generate_response(
        Codes.SUCCESS,
        False,
        {
            "username": current_user.name,
            "account_type": current_user.account_type,
            "account_id": current_user.id,
            "profile_picture": profile_picture,
        },
    )


@auth_bp.route("/login", methods=["POST"])
def login():
    account_name = ""
    if "name" not in request.get_json() and "username" not in request.get_json():
        return generate_response(Codes.MISSING_DATA, True)
    elif "name" not in request.get_json():
        account_name = request.get_json()["username"]
    else:
        account_name = request.get_json()["name"]

    account_password = request.get_json()["password"]
    user = Users.query.filter_by(name=account_name).first()

    if not user:
        return generate_response(Codes.USER_NOT_FOUND, True)

    if not Users.verify_password(user, account_password):
        return generate_response(Codes.WRONG_PASSWORD, True)

    access_token = jwt.encode(
        {
            "id": user.id,
            "exp": datetime.datetime.utcnow()
            + datetime.timedelta(hours=ACCESS_TOKEN_EXPIRATION),
        },
        current_app.config["SECRET_KEY"],
    )

    refresh_token = jwt.encode(
        {
            "id": user.id,
            "exp": datetime.datetime.utcnow()
            + datetime.timedelta(days=REFRESH_TOKEN_EXPIRATION),
        },
        current_app.config["SECRET_KEY"],
    )

    profile_picture = os.path.join(dir_path, user.profile_picture)

    profile_picture = user.profile_picture
    if not profile_picture.startswith("data:image"):
        if not os.path.exists(profile_picture):
            profile_picture = f"data:image/jpeg;base64,{image_to_base64(dir_path + '/static/img/avatars/defaultUserProfilePic.png', 200, 200)}"
        else:
            profile_picture = (
                f"data:image/jpeg;base64,{image_to_base64(profile_picture, 200, 200)}"
            )

    user_object = {
        "username": user.name,
        "account_type": user.account_type,
        "account_id": user.id,
        "profile_picture": profile_picture,
    }

    return generate_response(
        Codes.SUCCESS,
        False,
        {
            "user": user_object,
            "access_token": access_token,
            "refresh_token": refresh_token,
        },
    )


@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    token = request.get_json()["refresh_token"]
    try:
        data = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
        current_user = Users.query.filter_by(id=data["id"]).first()
    except Exception:
        return generate_response(Codes.INVALID_TOKEN, True)

    access_token = jwt.encode(
        {
            "id": current_user.id,
            "exp": datetime.datetime.utcnow()
            + datetime.timedelta(hours=ACCESS_TOKEN_EXPIRATION),
        },
        current_app.config["SECRET_KEY"],
    )

    img_path = os.path.join(dir_path, current_user.profile_picture)

    user_object = {
        "username": current_user.name,
        "account_type": current_user.account_type,
        "account_id": current_user.id,
        "profile_picture": f"data:image/jpeg;base64,{image_to_base64(img_path, 200, 200)}",
    }

    return generate_response(
        Codes.SUCCESS,
        False,
        {
            "id": current_user.id,
            "name": current_user.name,
            "account_type": current_user.account_type,
            "access_token": access_token,
            "user": user_object,
        },
    )


@auth_bp.route("/signup", methods=["POST"])
def signup():
    if "username" not in request.get_json() or "password" not in request.get_json():
        return generate_response(Codes.MISSING_DATA, True)

    account_name = request.get_json()["username"]
    account_password = request.get_json()["password"]
    account_type = request.get_json()["type"] if "type" in request.get_json() else "Kid"

    if Users.query.filter_by(name=account_name).first():
        return generate_response(Codes.USER_ALREADY_EXISTS, True)

    if "code" not in request.get_json():
        existing_users = Users.query.all()
        if len(existing_users) > 0:
            return generate_response(Codes.USER_ALREADY_EXISTS, True)
        account_type = "Admin"

    user = Users(
        name=account_name,
        password=account_password,
        account_type=account_type,
        profile_picture="static/images/default_profile_picture.jpg",
    )

    DB.session.add(user)
    DB.session.commit()

    return generate_response(Codes.SUCCESS)


@auth_bp.route("/accounts", methods=["GET"])
def get_accounts():
    all_users = Users.query.filter().all()
    all_users_list = []
    for user in all_users:
        profile_picture = user.profile_picture
        if not profile_picture.startswith("data:image"):
            if not os.path.exists(dir_path + profile_picture):
                profile_picture = f"data:image/jpeg;base64,{image_to_base64(dir_path+'/static/img/avatars/defaultUserProfilePic.png', 200, 200)}"
            else:
                profile_picture = f"data:image/jpeg;base64,{image_to_base64(dir_path + profile_picture, 200, 200)}"

        user_dict = {
            "name": user.name,
            "profile_picture": profile_picture,
            "account_type": user.account_type,
            "password_empty": True if not user.password else False,
            "id": user.id,
        }
        all_users_list.append(user_dict)
    return generate_response(Codes.SUCCESS, False, all_users_list)
