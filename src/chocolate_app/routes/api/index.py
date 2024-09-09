from flask import Blueprint

from chocolate_app.routes.api.auth import auth_bp
from chocolate_app.routes.api.medias import medias_bp
from chocolate_app.routes.api.watch import watch_bp

api_bp = Blueprint('medias', __name__, url_prefix='/api')

api_bp.register_blueprint(auth_bp)
api_bp.register_blueprint(medias_bp)
api_bp.register_blueprint(watch_bp)