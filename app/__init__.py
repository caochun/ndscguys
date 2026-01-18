"""
Flask application factory
"""
from __future__ import annotations

from flask import Flask

from config import config
from app.db import init_db
from app.routes import web_bp
from app.api import api_bp


def create_app(config_name: str = "default") -> Flask:
    """创建 Flask 应用"""
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(config[config_name])
    
    # 初始化数据库
    db_path = str(app.config["DATABASE_PATH"])
    init_db(db_path)
    
    # 注册蓝图
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    
    return app
