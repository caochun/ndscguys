"""
请假记录模型
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class LeaveRecord:
    """请假记录"""

    id: Optional[int]
    person_id: int
    leave_date: str  # YYYY-MM-DD
    leave_type: str  # 事假、病假、年假、调休等
    hours: float
    status: str  # 待审批、已批准、已拒绝
    approver_person_id: Optional[int]
    reason: Optional[str]
    created_at: Optional[str] = None
    
    @classmethod
    def from_row(cls, row) -> "LeaveRecord":
        created_at = row["created_at"] if "created_at" in row.keys() else None
        return cls(
            id=row["id"],
            person_id=row["person_id"],
            leave_date=row["leave_date"],
            leave_type=row["leave_type"],
            hours=row["hours"],
            status=row["status"],
            approver_person_id=row["approver_person_id"],
            reason=row["reason"],
            created_at=created_at,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "person_id": self.person_id,
            "leave_date": self.leave_date,
            "leave_type": self.leave_type,
            "hours": self.hours,
            "status": self.status,
            "approver_person_id": self.approver_person_id,
            "reason": self.reason,
            "created_at": self.created_at,
        }

