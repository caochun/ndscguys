"""
人员注册表 DAO（用于生成 person_id）
"""
from __future__ import annotations

from typing import List

from app.daos.base_dao import BaseDAO


class PersonDAO(BaseDAO):
    """人员注册表 DAO，仅用于生成 person_id"""

    def create_person(self) -> int:
        """创建新人员记录，返回 person_id"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO persons DEFAULT VALUES")
        conn.commit()
        return cursor.lastrowid

    def person_exists(self, person_id: int) -> bool:
        """检查 person_id 是否存在"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM persons WHERE id = ?", (person_id,))
        return cursor.fetchone() is not None

    def list_all_person_ids(self) -> List[int]:
        """获取所有已注册的 person_id 列表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM persons")
        return [row[0] for row in cursor.fetchall()]
