from flask import Blueprint, request

from chocolate_app import DB
from chocolate_app.tables import Users
from chocolate_app.routes.api.auth import token_required
from chocolate_app.utils.utils import generate_response, Codes

profil_bp = Blueprint("profil", __name__, url_prefix="/profil")


@profil_bp.route("", methods=["GET", "POST"])
@token_required
def profil(current_user):
    if request.method == "GET":
        data = current_user.__dict__
        data.pop("_sa_instance_state")
        data.pop("password")

        return generate_response(Codes.SUCCESS, data=data)
    elif request.method == "POST":
        if not request.json:
            return generate_response(Codes.INVALID_MEDIA_TYPE)

        data = request.json

        required_keys = ["id", "name", "password", "image"]

        for key in required_keys:
            if key not in data:
                return generate_response(Codes.MISSING_DATA)

        user = Users.query.filter_by(id=data["id"]).first()

        if not user:
            return generate_response(Codes.USER_NOT_FOUND)

        user.name = data["name"]
        if len(data["password"]) > 0:
            user.password = data["password"]
        user.profile_picture = data["image"]

        DB.session.commit()

        return generate_response(Codes.SUCCESS)
    else:
        return generate_response(Codes.INVALID_METHOD)
