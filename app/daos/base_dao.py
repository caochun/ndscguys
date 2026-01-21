"""
Base DAO - 基础 DAO 类
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import contextmanager

from app.schema.loader import SchemaLoader
from app.schema.models import TwinSchema


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
        
        # Schema 相关（子类可以覆盖）
        self.schema_loader = SchemaLoader()
        self._twin_schemas: Dict[str, TwinSchema] = {}
    
    @contextmanager
    def get_connection(self):
        """
        获取数据库连接的上下文管理器
        
        使用示例:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(...)
                conn.commit()
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _get_twin_schema(self, twin_name: str) -> TwinSchema:
        """
        获取 Twin Schema（带缓存）
        
        子类可以覆盖此方法以提供自定义实现
        """
        if twin_name not in self._twin_schemas:
            from app.schema.models import TwinSchema
            twin_def = self.schema_loader.get_twin_schema(twin_name)
            if not twin_def:
                raise ValueError(f"Twin schema not found: {twin_name}")
            self._twin_schemas[twin_name] = TwinSchema.from_dict(twin_name, twin_def)
        return self._twin_schemas[twin_name]
