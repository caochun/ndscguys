"""
人员项目状态（在项/待入项/不可用）
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any

from .state import PersonState
from .base import ensure_dict, serialize_dict


@dataclass
class PersonProjectStatusState:
    """人员项目状态（在项/待入项/不可用）"""

    person_id: int
    version: int
    ts: str
    data: Dict[str, Any]

    @classmethod
    def from_row(cls, row) -> "PersonProjectStatusState":
        # 支持 sqlite3.Row 和 dict（都支持 [] 访问）
        return cls(
            person_id=row["person_id"],
            version=row["version"],
            ts=row["ts"],
            data=ensure_dict(row["data"]),
        )

    def to_dict(self) -> dict:
        return {
            "person_id": self.person_id,
            "version": self.version,
            "ts": self.ts,
            "data": self.data,
        }

    def to_record(self) -> dict:
        return {
            "person_id": self.person_id,
            "version": self.version,
            "ts": self.ts,
            "data": serialize_dict(self.data),
        }
