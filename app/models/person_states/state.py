"""
通用人员状态记录
"""
from dataclasses import dataclass
from typing import Dict, Any

from .base import ensure_dict, serialize_dict


@dataclass
class PersonState:
    """通用 append-only 人员状态"""

    person_id: int
    version: int
    ts: str
    data: Dict[str, Any]

    @classmethod
    def from_row(cls, row) -> "PersonState":
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

