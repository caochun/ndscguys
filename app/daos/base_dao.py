"""
DAO 基类
"""
from app.database import get_db


class BaseDAO:
    """DAO 基类，提供数据库连接"""
    
    def __init__(self):
        self.db = get_db()
    
    def get_connection(self):
        """获取数据库连接"""
        return self.db.get_connection()

