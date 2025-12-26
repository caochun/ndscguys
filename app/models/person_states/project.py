"""
人员参与项目状态
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any

from .state import PersonState
from .base import ensure_dict, serialize_dict


@dataclass
class PersonProjectState:
    """人员参与项目状态（包含 project_id）"""

    person_id: int
    project_id: int
    version: int
    ts: str
    data: Dict[str, Any]

    @classmethod
    def from_row(cls, row) -> "PersonProjectState":
        # row 必须包含 project_id（从数据库查询）
        project_id = row.get("project_id")
        if project_id is None:
            raise ValueError("project_id is required in row")
        return cls(
            person_id=row["person_id"],
            project_id=project_id,
            version=row["version"],
            ts=row["ts"],
            data=ensure_dict(row.get("data")),
        )

    def to_dict(self) -> dict:
        return {
            "person_id": self.person_id,
            "project_id": self.project_id,
            "version": self.version,
            "ts": self.ts,
            "data": self.data,
        }

    def to_record(self) -> dict:
        return {
            "person_id": self.person_id,
            "project_id": self.project_id,
            "version": self.version,
            "ts": self.ts,
            "data": serialize_dict(self.data),
        }

