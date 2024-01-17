from flask import Flask

from src.core.constants import OPERATION_AUTH_KEY
from src.routes import api

def create_app() -> Flask:
    app = Flask(__name__)

    app.config['SECRET_KEY'] = OPERATION_AUTH_KEY

    # Register blueprints
    app.register_blueprint(api)

    return app
