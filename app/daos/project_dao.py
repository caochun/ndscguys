"""
项目注册表 DAO（用于生成 project_id）
"""
from __future__ import annotations

from app.daos.base_dao import BaseDAO


class ProjectDAO(BaseDAO):
    """项目注册表 DAO，仅用于生成 project_id"""

    def create_project(self) -> int:
        """创建新项目记录，返回 project_id"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO projects DEFAULT VALUES")
        conn.commit()
        return cursor.lastrowid

    def project_exists(self, project_id: int) -> bool:
        """检查 project_id 是否存在"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM projects WHERE id = ?", (project_id,))
        return cursor.fetchone() is not None
