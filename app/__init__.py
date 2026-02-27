"""
Flask application factory
"""
from __future__ import annotations

from flask import Flask

from app.root_config import config as _config_dict
from app.db import init_db
from app.routes import web_bp
from app.twin_api import twin_api_bp
from app.payroll_api import payroll_api_bp
from app.config_api import config_api_bp
from app.analytics_api import analytics_api_bp


def create_app(config_name: str = "default") -> Flask:
    """创建 Flask 应用"""
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(_config_dict[config_name])
    
    # 初始化数据库
    db_path = str(app.config["DATABASE_PATH"])
    init_db(db_path)
    
    # 注册蓝图
    app.register_blueprint(web_bp)
    app.register_blueprint(twin_api_bp, url_prefix="/api")
    app.register_blueprint(payroll_api_bp, url_prefix="/api")
    app.register_blueprint(config_api_bp, url_prefix="/api")
    app.register_blueprint(analytics_api_bp, url_prefix="/api")

    return app
