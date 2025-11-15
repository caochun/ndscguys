"""
应用配置文件
"""
import os
from pathlib import Path
import platform


class Config:
    """基础配置类"""
    # Flask 配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hr-system-secret-key-change-in-production'
    JSON_AS_ASCII = False  # 支持中文 JSON
    
    # 数据库配置
    @staticmethod
    def get_db_path():
        """获取数据库路径（跨平台）"""
        system = platform.system()
        if system == "Darwin":  # macOS
            app_data_dir = Path.home() / "Library" / "Application Support" / "HRSystem"
        elif system == "Windows":  # Windows
            app_data_dir = Path(os.getenv('APPDATA', Path.home())) / "HRSystem"
        else:  # Linux 和其他系统
            app_data_dir = Path.home() / ".hrsystem"
        app_data_dir.mkdir(parents=True, exist_ok=True)
        return app_data_dir / "hr_system.db"


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'change-this-in-production'


# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

