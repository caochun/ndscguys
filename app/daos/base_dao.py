"""
Base DAO - 基础 DAO 类
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional


class BaseDAO:
    """基础 DAO 类"""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            from config import Config
            db_path = Config.DATABASE_PATH
        
        self.db_path = db_path
        # 确保数据库目录存在
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
