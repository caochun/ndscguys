"""
出勤记录 DAO
"""
from __future__ import annotations

from typing import List, Optional
from datetime import datetime

from app.daos.base_dao import BaseDAO
from app.models.attendance_record import AttendanceRecord


class AttendanceDAO(BaseDAO):
    """出勤记录 DAO"""

    def create(self, record: AttendanceRecord) -> int:
        """创建出勤记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO attendance_records 
            (person_id, date, check_in_time, check_out_time, work_hours, overtime_hours, status, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.person_id,
                record.date,
                record.check_in_time,
                record.check_out_time,
                record.work_hours,
                record.overtime_hours,
                record.status,
                record.note,
            ),
        )
        conn.commit()
        return cursor.lastrowid

    def get_by_id(self, record_id: int) -> Optional[AttendanceRecord]:
        """根据ID获取出勤记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM attendance_records WHERE id = ?", (record_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return AttendanceRecord.from_row(row)

    def get_by_person_and_date(self, person_id: int, date: str) -> Optional[AttendanceRecord]:
        """根据人员和日期获取出勤记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM attendance_records WHERE person_id = ? AND date = ?",
            (person_id, date),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return AttendanceRecord.from_row(row)

    def list_by_person(
        self, person_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> List[AttendanceRecord]:
        """列出人员的出勤记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if start_date and end_date:
            cursor.execute(
                """
                SELECT * FROM attendance_records 
                WHERE person_id = ? AND date >= ? AND date <= ?
                ORDER BY date DESC
                """,
                (person_id, start_date, end_date),
            )
        elif start_date:
            cursor.execute(
                """
                SELECT * FROM attendance_records 
                WHERE person_id = ? AND date >= ?
                ORDER BY date DESC
                """,
                (person_id, start_date),
            )
        else:
            cursor.execute(
                """
                SELECT * FROM attendance_records 
                WHERE person_id = ?
                ORDER BY date DESC
                """,
                (person_id,),
            )
        rows = cursor.fetchall()
        return [AttendanceRecord.from_row(row) for row in rows]

    def update(self, record: AttendanceRecord) -> bool:
        """更新出勤记录"""
        if record.id is None:
            return False
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE attendance_records 
            SET check_in_time = ?, check_out_time = ?, work_hours = ?, 
                overtime_hours = ?, status = ?, note = ?
            WHERE id = ?
            """,
            (
                record.check_in_time,
                record.check_out_time,
                record.work_hours,
                record.overtime_hours,
                record.status,
                record.note,
                record.id,
            ),
        )
        conn.commit()
        return cursor.rowcount > 0

    def delete(self, record_id: int) -> bool:
        """删除出勤记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM attendance_records WHERE id = ?", (record_id,))
        conn.commit()
        return cursor.rowcount > 0

