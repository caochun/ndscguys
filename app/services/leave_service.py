"""
请假服务
"""
from __future__ import annotations

from typing import List, Optional, Dict, Any

from app.daos.leave_dao import LeaveDAO
from app.models.leave_record import LeaveRecord


class LeaveService:
    """请假服务"""

    def __init__(self, db_path: str):
        self.leave_dao = LeaveDAO(db_path=db_path)

    def create_leave(
        self,
        person_id: int,
        leave_date: str,
        leave_type: str,
        hours: float,
        status: str = "待审批",
        approver_person_id: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> int:
        """创建请假记录"""
        record = LeaveRecord(
            id=None,
            person_id=person_id,
            leave_date=leave_date,
            leave_type=leave_type,
            hours=hours,
            status=status,
            approver_person_id=approver_person_id,
            reason=reason,
        )
        return self.leave_dao.create(record)

    def get_leave(self, record_id: int) -> Optional[Dict[str, Any]]:
        """获取请假记录"""
        record = self.leave_dao.get_by_id(record_id)
        if not record:
            return None
        return record.to_dict()

    def list_leave(
        self,
        person_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """列出请假记录"""
        records = self.leave_dao.list_by_person(person_id, start_date, end_date)
        return [record.to_dict() for record in records]

    def update_leave(
        self,
        record_id: int,
        leave_type: Optional[str] = None,
        hours: Optional[float] = None,
        status: Optional[str] = None,
        approver_person_id: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> bool:
        """更新请假记录"""
        record = self.leave_dao.get_by_id(record_id)
        if not record:
            return False

        if leave_type is not None:
            record.leave_type = leave_type
        if hours is not None:
            record.hours = hours
        if status is not None:
            record.status = status
        if approver_person_id is not None:
            record.approver_person_id = approver_person_id
        if reason is not None:
            record.reason = reason

        return self.leave_dao.update(record)

    def delete_leave(self, record_id: int) -> bool:
        """删除请假记录"""
        return self.leave_dao.delete(record_id)

    def approve_leave(self, record_id: int, approver_person_id: int) -> bool:
        """审批通过请假"""
        return self.update_leave(record_id, status="已批准", approver_person_id=approver_person_id)

    def reject_leave(self, record_id: int, approver_person_id: int) -> bool:
        """拒绝请假"""
        return self.update_leave(record_id, status="已拒绝", approver_person_id=approver_person_id)

