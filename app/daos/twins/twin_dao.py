"""
Twin DAO - 通用 Twin DAO
"""
from __future__ import annotations

import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.daos.base_dao import BaseDAO
from app.models.twins import Twin, EntityTwin, ActivityTwin, TwinType
from app.schema.loader import SchemaLoader
from app.schema.models import TwinSchema


class TwinDAO(BaseDAO):
    """通用 Twin DAO"""
    
    def __init__(self, db_path: Optional[str] = None):
        super().__init__(db_path)
        self.schema_loader = SchemaLoader()
        self._twin_schemas: Dict[str, TwinSchema] = {}
    
    def _get_twin_schema(self, twin_name: str) -> TwinSchema:
        """获取 Twin Schema（带缓存）"""
        if twin_name not in self._twin_schemas:
            from app.schema.models import TwinSchema
            twin_def = self.schema_loader.get_twin_schema(twin_name)
            if not twin_def:
                raise ValueError(f"Twin schema not found: {twin_name}")
            self._twin_schemas[twin_name] = TwinSchema.from_dict(twin_name, twin_def)
        return self._twin_schemas[twin_name]
    
    def create_entity_twin(self, twin_name: str) -> int:
        """创建 Entity Twin，返回 twin_id"""
        schema = self._get_twin_schema(twin_name)
        if schema.type != "entity":
            raise ValueError(f"Expected entity twin, got {schema.type}")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(f"INSERT INTO {schema.table} DEFAULT VALUES")
        conn.commit()
        twin_id = cursor.lastrowid
        conn.close()
        return twin_id
    
    def create_activity_twin(
        self,
        twin_name: str,
        related_entity_ids: Dict[str, int]
    ) -> int:
        """创建 Activity Twin，返回 twin_id"""
        schema = self._get_twin_schema(twin_name)
        if schema.type != "activity":
            raise ValueError(f"Expected activity twin, got {schema.type}")
        
        if not schema.related_entities:
            raise ValueError(f"Activity twin {twin_name} has no related entities")
        
        # 验证所有必需的关联实体
        for rel_entity in schema.related_entities:
            if rel_entity.required:
                key = rel_entity.key
                if key not in related_entity_ids:
                    raise ValueError(f"Missing required entity: {key}")
        
        # 构建插入语句
        columns = [rel.key for rel in schema.related_entities]
        placeholders = ", ".join(["?" for _ in columns])
        values = [related_entity_ids[rel.key] for rel in schema.related_entities]
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"INSERT INTO {schema.table} ({', '.join(columns)}) VALUES ({placeholders})",
            values
        )
        conn.commit()
        twin_id = cursor.lastrowid
        conn.close()
        return twin_id
    
    def get_twin(self, twin_name: str, twin_id: int) -> Optional[Twin]:
        """获取 Twin"""
        schema = self._get_twin_schema(twin_name)
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if schema.type == "entity":
            cursor.execute(f"SELECT * FROM {schema.table} WHERE id = ?", (twin_id,))
            row = cursor.fetchone()
            conn.close()
            if not row:
                return None
            row_dict = dict(row) if not isinstance(row, dict) else row
            return EntityTwin(
                twin_id=twin_id,
                twin_name=twin_name,
                created_at=datetime.fromisoformat(row_dict["created_at"]) if row_dict.get("created_at") else None,
            )
        else:  # activity
            # 需要查询关联的实体 ID
            related_keys = [rel.key for rel in schema.related_entities]
            columns = ["id"] + related_keys + ["created_at"]
            cursor.execute(
                f"SELECT {', '.join(columns)} FROM {schema.table} WHERE id = ?",
                (twin_id,)
            )
            row = cursor.fetchone()
            conn.close()
            if not row:
                return None
            
            row_dict = dict(row) if not isinstance(row, dict) else row
            related_entity_ids = {key: row_dict[key] for key in related_keys}
            activity = ActivityTwin(
                twin_id=twin_id,
                twin_type=TwinType.ACTIVITY,
                twin_name=twin_name,
                related_entity_ids=related_entity_ids,
                created_at=datetime.fromisoformat(row_dict["created_at"]) if row_dict.get("created_at") else None,
            )
            return activity
    
    def twin_exists(self, twin_name: str, twin_id: int) -> bool:
        """检查 Twin 是否存在"""
        schema = self._get_twin_schema(twin_name)
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT 1 FROM {schema.table} WHERE id = ?", (twin_id,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists
