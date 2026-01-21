"""
配置模块
"""
from pathlib import Path


class Config:
    """应用配置"""
    BASE_DIR = Path(__file__).parent
    DATABASE_PATH = BASE_DIR / "data" / "twin.db"


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False


config = {
    "default": DevelopmentConfig,
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
