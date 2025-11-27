"\"\"\"Flask application factory\"\"\""
from __future__ import annotations

import os

from flask import Flask

from config import config
from app.db import init_db
from app.seed import seed_initial_data


def create_app(config_name: str = "default") -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(config[config_name])

    db_path = app.config["DATABASE_PATH"]
    init_db(db_path)
    seed_initial_data(db_path)

    from app.routes import web_bp
    from app.api import api_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    return app

