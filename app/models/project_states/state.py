"""
项目状态流通用模型
"""
from dataclasses import dataclass
from typing import Dict, Any

from .base import ensure_dict, serialize_dict


@dataclass
class ProjectState:
    """通用 append-only 项目状态"""

    project_id: int
    version: int
    ts: str
    data: Dict[str, Any]

    @classmethod
    def from_row(cls, row) -> "ProjectState":
        # 支持 sqlite3.Row 和 dict（都支持 [] 访问）
        return cls(
            project_id=row["project_id"],
            version=row["version"],
            ts=row["ts"],
            data=ensure_dict(row["data"]),
        )

    def to_dict(self) -> dict:
        return {
            "project_id": self.project_id,
            "version": self.version,
            "ts": self.ts,
            "data": self.data,
        }

    def to_record(self) -> dict:
        return {
            "project_id": self.project_id,
            "version": self.version,
            "ts": self.ts,
            "data": serialize_dict(self.data),
        }

