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
    
    # 注意：_get_twin_schema 方法已从 BaseDAO 继承，无需重复定义
    
    def create_entity_twin(self, twin_name: str) -> int:
        """创建 Entity Twin，返回 twin_id"""
        schema = self._get_twin_schema(twin_name)
        if schema.type != "entity":
            raise ValueError(f"Expected entity twin, got {schema.type}")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"INSERT INTO {schema.table} DEFAULT VALUES")
            conn.commit()
            twin_id = cursor.lastrowid
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
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"INSERT INTO {schema.table} ({', '.join(columns)}) VALUES ({placeholders})",
                values
            )
            conn.commit()
            twin_id = cursor.lastrowid
        return twin_id
    
    def get_twin(self, twin_name: str, twin_id: int) -> Optional[Twin]:
        """获取 Twin"""
        schema = self._get_twin_schema(twin_name)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if schema.type == "entity":
                cursor.execute(f"SELECT * FROM {schema.table} WHERE id = ?", (twin_id,))
                row = cursor.fetchone()
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
    
    def delete_twin(self, twin_name: str, twin_id: int) -> bool:
        """删除 Twin 及其所有历史状态，返回是否删除成功"""
        schema = self._get_twin_schema(twin_name)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # 先删除历史状态
            cursor.execute(f"DELETE FROM {schema.state_table} WHERE twin_id = ?", (twin_id,))
            # 再删除主记录
            cursor.execute(f"DELETE FROM {schema.table} WHERE id = ?", (twin_id,))
            conn.commit()
            return cursor.rowcount > 0

    def twin_exists(self, twin_name: str, twin_id: int) -> bool:
        """检查 Twin 是否存在"""
        schema = self._get_twin_schema(twin_name)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT 1 FROM {schema.table} WHERE id = ?", (twin_id,))
            exists = cursor.fetchone() is not None
        return exists
