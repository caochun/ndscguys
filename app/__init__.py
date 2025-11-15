"""
Flask 应用工厂
"""
from flask import Flask
from config import config


def create_app(config_name='default'):
    """
    应用工厂函数
    
    Args:
        config_name: 配置名称（development, production, default）
    
    Returns:
        Flask 应用实例
    """
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # 注册蓝图
    from app.routes import main_bp, api_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app

