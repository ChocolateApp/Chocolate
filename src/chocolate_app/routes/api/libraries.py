from flask import Blueprint, request

from chocolate_app import DB, scans
from chocolate_app.tables import Libraries, Users
from chocolate_app.routes.api.auth import token_required
from chocolate_app.utils.utils import generate_response, Codes

lib_bp = Blueprint("libraries", __name__, url_prefix="/libraries")


@lib_bp.route("/refresh/<lib_id>", methods=["GET", "POST"])
@token_required
def refresh(current_user, lib_id):
    if not current_user.account_type == "Admin":
        return generate_response(Codes.NOT_LOGGED_IN, True)

    lib = Libraries.query.filter_by(id=lib_id).first()

    if not lib:
        return generate_response(Codes.LIBRARY_NOT_FOUND, True)

    library = lib.__dict__

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

    return generate_response(Codes.SUCCESS, False, {"message": "Library refreshed"})
