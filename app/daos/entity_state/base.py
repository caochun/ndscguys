"""
实体状态流 DAO 基类
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Type

from app.daos.base_dao import BaseDAO


class EntityStateDAO(BaseDAO):
    """
    通用实体状态流 DAO（append-only）

    子类需定义：
        - table_name: str 目标表
        - state_cls: dataclass，必须包含 to_record()/from_row()
    """

    table_name: str = ""
    state_cls: Optional[Type] = None

    def __init__(self, db_path: Optional[str] = None):
        super().__init__(db_path=db_path)
        if not self.table_name or self.state_cls is None:
            raise ValueError("table_name 和 state_cls 必须在子类中定义")

    # ----- 写入 -----
    def _get_next_version(self, entity_id: int) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT COALESCE(MAX(version), 0) FROM {self.table_name} WHERE person_id = ?",
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

    def append(self, entity_id: int, data: dict, ts: Optional[str | datetime] = None) -> int:
        """追加一个新版本（不存在即第一个版本）"""
        ts = self._normalize_ts(ts)
        version = self._get_next_version(entity_id)
        state = self.state_cls(person_id=entity_id, version=version, ts=ts, data=data or {})
        record = state.to_record()

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"INSERT INTO {self.table_name} (person_id, version, ts, data) VALUES (?, ?, ?, ?)",
            (
                record["person_id"],
                record["version"],
                record["ts"],
                record["data"],
            ),
        )
        conn.commit()
        return version

    # ----- 读取 -----
    def get_latest(self, entity_id: int):
        """获取最新状态"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT person_id, version, ts, data
            FROM {self.table_name}
            WHERE person_id = ?
            ORDER BY version DESC
            LIMIT 1
            """,
            (entity_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return self.state_cls.from_row(row)

    def get_by_version(self, entity_id: int, version: int):
        """按版本获取状态"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT person_id, version, ts, data
            FROM {self.table_name}
            WHERE person_id = ? AND version = ?
            """,
            (entity_id, version),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return self.state_cls.from_row(row)

    def list_states(self, entity_id: int, limit: int = 50):
        """列出最近的状态"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT person_id, version, ts, data
            FROM {self.table_name}
            WHERE person_id = ?
            ORDER BY version DESC
            LIMIT ?
            """,
            (entity_id, limit),
        )
        rows = cursor.fetchall()
        return [self.state_cls.from_row(row) for row in rows]

    def get_at(self, entity_id: int, ts: str | datetime):
        """
        获取指定时间点的最新状态（<= ts）

        Args:
            entity_id: 实体ID
            ts: 指定时间（字符串或 datetime）
        """
        ts_str = self._normalize_ts(ts)
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT person_id, version, ts, data
            FROM {self.table_name}
            WHERE person_id = ? AND ts <= ?
            ORDER BY ts DESC, version DESC
            LIMIT 1
            """,
            (entity_id, ts_str),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return self.state_cls.from_row(row)

