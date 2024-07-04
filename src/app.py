from flask import Flask

from src.database import init_db
from src.routes import api

def create_app() -> Flask:
    init_db()

    app = Flask(__name__)

    # Register blueprints
    app.register_blueprint(api)

    return app
