from .users import users_blueprint
from .faces import faces_blueprint

def register_blueprints(app):
    app.register_blueprint(users_blueprint, url_prefix="/users")
    app.register_blueprint(faces_blueprint, url_prefix="/faces")
