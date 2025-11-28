"""
出勤服务
"""
from __future__ import annotations

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.daos.attendance_dao import AttendanceDAO
from app.models.attendance_record import AttendanceRecord


class AttendanceService:
    """出勤服务"""

    def __init__(self, db_path: str):
        self.attendance_dao = AttendanceDAO(db_path=db_path)

    def create_attendance(
        self,
        person_id: int,
        date: str,
        check_in_time: Optional[str] = None,
        check_out_time: Optional[str] = None,
        work_hours: float = 0.0,
        overtime_hours: float = 0.0,
        status: str = "正常",
        note: Optional[str] = None,
    ) -> int:
        """创建出勤记录"""
        record = AttendanceRecord(
            id=None,
            person_id=person_id,
            date=date,
            check_in_time=check_in_time,
            check_out_time=check_out_time,
            work_hours=work_hours,
            overtime_hours=overtime_hours,
            status=status,
            note=note,
        )
        return self.attendance_dao.create(record)

    def get_attendance(self, record_id: int) -> Optional[Dict[str, Any]]:
        """获取出勤记录"""
        record = self.attendance_dao.get_by_id(record_id)
        if not record:
            return None
        return record.to_dict()

    def get_attendance_by_date(self, person_id: int, date: str) -> Optional[Dict[str, Any]]:
        """根据日期获取出勤记录"""
        record = self.attendance_dao.get_by_person_and_date(person_id, date)
        if not record:
            return None
        return record.to_dict()

    def list_attendance(
        self,
        person_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """列出出勤记录"""
        records = self.attendance_dao.list_by_person(person_id, start_date, end_date)
        return [record.to_dict() for record in records]

    def update_attendance(
        self,
        record_id: int,
        check_in_time: Optional[str] = None,
        check_out_time: Optional[str] = None,
        work_hours: Optional[float] = None,
        overtime_hours: Optional[float] = None,
        status: Optional[str] = None,
        note: Optional[str] = None,
    ) -> bool:
        """更新出勤记录"""
        record = self.attendance_dao.get_by_id(record_id)
        if not record:
            return False

        if check_in_time is not None:
            record.check_in_time = check_in_time
        if check_out_time is not None:
            record.check_out_time = check_out_time
        if work_hours is not None:
            record.work_hours = work_hours
        if overtime_hours is not None:
            record.overtime_hours = overtime_hours
        if status is not None:
            record.status = status
        if note is not None:
            record.note = note

        return self.attendance_dao.update(record)

    def delete_attendance(self, record_id: int) -> bool:
        """删除出勤记录"""
        return self.attendance_dao.delete(record_id)

    def get_monthly_summary(self, person_id: int, year: int, month: int) -> Dict[str, Any]:
        """获取月度出勤汇总"""
        start_date = f"{year}-{month:02d}-01"
        # 计算月末日期
        if month == 12:
            end_date = f"{year}-12-31"
        else:
            next_month = datetime(year, month + 1, 1)
            last_day = (next_month - timedelta(days=1)).day
            end_date = f"{year}-{month:02d}-{last_day:02d}"

        records = self.attendance_dao.list_by_person(person_id, start_date, end_date)

        total_work_hours = sum(r.work_hours for r in records)
        total_overtime_hours = sum(r.overtime_hours for r in records)
        status_count = {}
        for r in records:
            status_count[r.status] = status_count.get(r.status, 0) + 1

        return {
            "person_id": person_id,
            "year": year,
            "month": month,
            "total_days": len(records),
            "total_work_hours": total_work_hours,
            "total_overtime_hours": total_overtime_hours,
            "status_count": status_count,
            "records": [r.to_dict() for r in records],
        }

