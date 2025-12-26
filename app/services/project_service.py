"""
项目服务层
"""
from __future__ import annotations

import json
import sqlite3
from typing import List, Dict, Any, Optional

from app.db import init_db, create_project
from app.daos.project_state_dao import ProjectBasicStateDAO
from app.models.person_payloads import sanitize_project_payload


class ProjectService:
    def __init__(self, db_path: str):
        self.db_path = db_path
        init_db(db_path)
        self.basic_dao = ProjectBasicStateDAO(db_path=db_path)

    def _get_connection(self) -> sqlite3.Connection:
        return self.basic_dao.get_connection()

    def create_project(self, project_data: dict) -> int:
        """创建新项目"""
        cleaned_data = sanitize_project_payload(project_data)
        conn = self._get_connection()
        project_id = create_project(conn)
        self.basic_dao.append(project_id, cleaned_data)
        return project_id

    def list_projects(self) -> List[Dict[str, Any]]:
        """列出所有项目（最新状态）"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT pb.project_id, pb.ts, pb.data
            FROM project_basic_history pb
            JOIN (
                SELECT project_id, MAX(version) AS max_version
                FROM project_basic_history
                GROUP BY project_id
            ) latest
            ON pb.project_id = latest.project_id AND pb.version = latest.max_version
            ORDER BY pb.ts DESC
            """
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            data = json.loads(row["data"])
            result.append({
                "project_id": row["project_id"],
                "ts": row["ts"],
                "data": data,
            })
        return result

    def get_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        """获取项目详情（包含历史）"""
        basic_state = self.basic_dao.get_latest(project_id)
        if not basic_state:
            return None

        basic_history = self.basic_dao.list_states(project_id, limit=100)

        return {
            "project_id": project_id,
            "basic": {
                "version": basic_state.version,
                "ts": basic_state.ts,
                "data": basic_state.data,
            },
            "basic_history": [
                {
                    "version": h.version,
                    "ts": h.ts,
                    "data": h.data,
                }
                for h in basic_history
            ],
        }

    def append_project_change(self, project_id: int, project_data: dict) -> int:
        """追加项目信息变更"""
        cleaned_data = sanitize_project_payload(project_data)
        return self.basic_dao.append(project_id, cleaned_data)

