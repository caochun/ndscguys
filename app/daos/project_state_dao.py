"""
项目状态流 DAO（具体实现）
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import List, Optional, Type

from app.daos.base_dao import BaseDAO
from app.models.project_states import ProjectBasicState
from app.models.project_states.base import serialize_dict


class ProjectStateDAO(BaseDAO):
    """
    项目状态流 DAO（基于 EntityStateDAO，但使用 project_id）
    """
    table_name: str = ""
    state_cls: Optional[Type] = None

    def __init__(self, db_path: Optional[str] = None):
        super().__init__(db_path=db_path)
        if not self.table_name or self.state_cls is None:
            raise ValueError("table_name 和 state_cls 必须在子类中定义")

    def _get_next_version(self, entity_id: int) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT COALESCE(MAX(version), 0) FROM {self.table_name} WHERE project_id = ?",
            (entity_id,),
        )
        max_version = cursor.fetchone()[0] or 0
        return max_version + 1

    def _normalize_ts(self, ts: Optional[str | datetime]) -> str:
        if ts is None:
            return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
        if isinstance(ts, datetime):
            return ts.strftime("%Y-%m-%dT%H:%M:%S")
        return ts

    def append(self, project_id: int, data: dict, ts: Optional[str | datetime] = None) -> int:
        """追加一个新版本（不存在即第一个版本）"""
        ts = self._normalize_ts(ts)
        version = self._get_next_version(project_id)
        state = self.state_cls(project_id=project_id, version=version, ts=ts, data=data or {})
        record = state.to_record()

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"INSERT INTO {self.table_name} (project_id, version, ts, data) VALUES (?, ?, ?, ?)",
            (
                project_id,
                version,
                ts,
                serialize_dict(data),
            ),
        )
        conn.commit()
        return version

    def get_latest(self, project_id: int):
        """获取最新状态"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT project_id, version, ts, data
            FROM {self.table_name}
            WHERE project_id = ?
            ORDER BY version DESC
            LIMIT 1
            """,
            (project_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return self.state_cls.from_row(dict(row))

    def get_by_version(self, project_id: int, version: int):
        """按版本获取状态"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT project_id, version, ts, data
            FROM {self.table_name}
            WHERE project_id = ? AND version = ?
            """,
            (project_id, version),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return self.state_cls.from_row(row)

    def list_states(self, project_id: int, limit: int = 50):
        """列出最近的状态"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT project_id, version, ts, data
            FROM {self.table_name}
            WHERE project_id = ?
            ORDER BY version DESC
            LIMIT ?
            """,
            (project_id, limit),
        )
        rows = cursor.fetchall()
        return [self.state_cls.from_row(row) for row in rows]

    def get_at(self, project_id: int, ts: str | datetime):
        """获取指定时间点的最新状态（<= ts）"""
        ts_str = self._normalize_ts(ts)
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT project_id, version, ts, data
            FROM {self.table_name}
            WHERE project_id = ? AND ts <= ?
            ORDER BY ts DESC, version DESC
            LIMIT 1
            """,
            (project_id, ts_str),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return self.state_cls.from_row(row)


class ProjectBasicStateDAO(ProjectStateDAO):
    table_name = "project_basic_history"
    state_cls = ProjectBasicState

    def list_all_latest(self) -> List[ProjectBasicState]:
        """获取所有项目的最新基础信息状态"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT pb.project_id, pb.version, pb.ts, pb.data
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
        return [self.state_cls.from_row(row) for row in rows]
