"""
人员参与项目状态流 DAO
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Optional, List

from app.daos.base_dao import BaseDAO
from app.models.person_states.project import PersonProjectState
from app.models.person_states.base import ensure_dict, serialize_dict


class PersonProjectStateDAO(BaseDAO):
    """
    人员参与项目状态流 DAO（复合键：person_id + project_id）
    """
    table_name = "person_project_history"

    def _get_next_version(self, person_id: int, project_id: int) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT COALESCE(MAX(version), 0) 
            FROM {self.table_name} 
            WHERE person_id = ? AND project_id = ?
            """,
            (person_id, project_id),
        )
        max_version = cursor.fetchone()[0] or 0
        return max_version + 1

    def _normalize_ts(self, ts: Optional[str | datetime]) -> str:
        if ts is None:
            return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
        if isinstance(ts, datetime):
            return ts.strftime("%Y-%m-%dT%H:%M:%S")
        return ts

    def append(
        self, 
        person_id: int, 
        project_id: int, 
        data: dict, 
        ts: Optional[str | datetime] = None
    ) -> int:
        """追加一个新版本"""
        ts = self._normalize_ts(ts)
        version = self._get_next_version(person_id, project_id)
        
        state = PersonProjectState(
            person_id=person_id,
            project_id=project_id,
            version=version,
            ts=ts,
            data=data or {}
        )
        record = state.to_record()

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"""
            INSERT INTO {self.table_name} (person_id, project_id, version, ts, data) 
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                person_id,
                project_id,
                record["version"],
                record["ts"],
                serialize_dict(data),
            ),
        )
        conn.commit()
        return version

    def get_latest(self, person_id: int, project_id: int):
        """获取最新状态"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT person_id, project_id, version, ts, data
            FROM {self.table_name}
            WHERE person_id = ? AND project_id = ?
            ORDER BY version DESC
            LIMIT 1
            """,
            (person_id, project_id),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return PersonProjectState.from_row(dict(row))

    def list_states(self, person_id: int, project_id: int, limit: int = 50) -> List[PersonProjectState]:
        """列出最近的状态"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT person_id, project_id, version, ts, data
            FROM {self.table_name}
            WHERE person_id = ? AND project_id = ?
            ORDER BY version DESC
            LIMIT ?
            """,
            (person_id, project_id, limit),
        )
        rows = cursor.fetchall()
        return [PersonProjectState.from_row(dict(row)) for row in rows]

    def list_by_person(self, person_id: int) -> List[PersonProjectState]:
        """列出某人员参与的所有项目（最新状态）"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT pp.person_id, pp.project_id, pp.version, pp.ts, pp.data
            FROM {self.table_name} pp
            JOIN (
                SELECT person_id, project_id, MAX(version) AS max_version
                FROM {self.table_name}
                WHERE person_id = ?
                GROUP BY person_id, project_id
            ) latest
            ON pp.person_id = latest.person_id 
            AND pp.project_id = latest.project_id 
            AND pp.version = latest.max_version
            ORDER BY pp.ts DESC
            """,
            (person_id,),
        )
        rows = cursor.fetchall()
        return [PersonProjectState.from_row(dict(row)) for row in rows]

    def list_by_project(self, project_id: int) -> List[PersonProjectState]:
        """列出某项目的所有参与人员（最新状态）"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT pp.person_id, pp.project_id, pp.version, pp.ts, pp.data
            FROM {self.table_name} pp
            JOIN (
                SELECT person_id, project_id, MAX(version) AS max_version
                FROM {self.table_name}
                WHERE project_id = ?
                GROUP BY person_id, project_id
            ) latest
            ON pp.person_id = latest.person_id 
            AND pp.project_id = latest.project_id 
            AND pp.version = latest.max_version
            ORDER BY pp.ts DESC
            """,
            (project_id,),
        )
        rows = cursor.fetchall()
        return [PersonProjectState.from_row(dict(row)) for row in rows]

    def get_at(self, person_id: int, project_id: int, ts: str | datetime):
        """获取指定时间点的最新状态（<= ts）"""
        ts_str = self._normalize_ts(ts)
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT person_id, project_id, version, ts, data
            FROM {self.table_name}
            WHERE person_id = ? AND project_id = ? AND ts <= ?
            ORDER BY ts DESC, version DESC
            LIMIT 1
            """,
            (person_id, project_id, ts_str),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return PersonProjectState.from_row(dict(row))

