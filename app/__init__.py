"""Flask application factory."""

from flask import Flask

from config import Config
from app.models.database import init_database
from app.routes.api_routes import api_bp
from app.routes.view_routes import view_bp


def create_app(config_class=Config):
    """Create and configure the Flask application."""

    flask_app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    flask_app.config.from_object(config_class)

    init_database(flask_app.config["DATABASE_PATH"])

    flask_app.register_blueprint(view_bp)
    flask_app.register_blueprint(api_bp, url_prefix="/api")

    return flask_app
