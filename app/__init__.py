"""
Flask application factory
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

from flask import Flask

# 从项目根目录加载 config.py（应用运行配置），避免与 app.config 包冲突
_root_config_path = Path(__file__).resolve().parent.parent / "config.py"
_spec = importlib.util.spec_from_file_location("_root_config", _root_config_path)
_root_config_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_root_config_module)
_config_dict = _root_config_module.config  # {"default": DevelopmentConfig, ...}

from app.db import init_db
from app.routes import web_bp
from app.twin_api import twin_api_bp
from app.payroll_api import payroll_api_bp


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
    
    return app
