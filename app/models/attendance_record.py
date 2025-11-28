"""
出勤记录模型
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class AttendanceRecord:
    """出勤记录"""

    id: Optional[int]
    person_id: int
    date: str  # YYYY-MM-DD
    check_in_time: Optional[str]  # HH:MM:SS
    check_out_time: Optional[str]  # HH:MM:SS
    work_hours: float
    overtime_hours: float
    status: str  # 正常、迟到、早退、缺勤等
    note: Optional[str]
    created_at: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "AttendanceRecord":
        created_at = row["created_at"] if "created_at" in row.keys() else None
        return cls(
            id=row["id"],
            person_id=row["person_id"],
            date=row["date"],
            check_in_time=row["check_in_time"],
            check_out_time=row["check_out_time"],
            work_hours=row["work_hours"] or 0.0,
            overtime_hours=row["overtime_hours"] or 0.0,
            status=row["status"],
            note=row["note"],
            created_at=created_at,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "person_id": self.person_id,
            "date": self.date,
            "check_in_time": self.check_in_time,
            "check_out_time": self.check_out_time,
            "work_hours": self.work_hours,
            "overtime_hours": self.overtime_hours,
            "status": self.status,
            "note": self.note,
            "created_at": self.created_at,
        }

