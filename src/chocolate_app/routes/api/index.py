from flask import Blueprint


from chocolate_app.routes.api.auth import auth_bp
from chocolate_app.routes.api.watch import watch_bp
from chocolate_app.routes.api.libraries import lib_bp
from chocolate_app.routes.api.profil import profil_bp
from chocolate_app.routes.api.medias import medias_bp
from chocolate_app.routes.api.settings import settings_bp

api_bp = Blueprint('api', __name__, url_prefix='/api')

api_bp.register_blueprint(auth_bp)
api_bp.register_blueprint(medias_bp)
api_bp.register_blueprint(watch_bp)
api_bp.register_blueprint(settings_bp)
api_bp.register_blueprint(profil_bp)
api_bp.register_blueprint(lib_bp)
