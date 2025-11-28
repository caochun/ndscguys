"""
请假记录 DAO
"""
from __future__ import annotations

from typing import List, Optional

from app.daos.base_dao import BaseDAO
from app.models.leave_record import LeaveRecord


class LeaveDAO(BaseDAO):
    """请假记录 DAO"""

    def create(self, record: LeaveRecord) -> int:
        """创建请假记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO leave_records 
            (person_id, leave_date, leave_type, hours, status, approver_person_id, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.person_id,
                record.leave_date,
                record.leave_type,
                record.hours,
                record.status,
                record.approver_person_id,
                record.reason,
            ),
        )
        conn.commit()
        return cursor.lastrowid

    def get_by_id(self, record_id: int) -> Optional[LeaveRecord]:
        """根据ID获取请假记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM leave_records WHERE id = ?", (record_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return LeaveRecord.from_row(row)

    def list_by_person(
        self, person_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> List[LeaveRecord]:
        """列出人员的请假记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if start_date and end_date:
            cursor.execute(
                """
                SELECT * FROM leave_records 
                WHERE person_id = ? AND leave_date >= ? AND leave_date <= ?
                ORDER BY leave_date DESC
                """,
                (person_id, start_date, end_date),
            )
        elif start_date:
            cursor.execute(
                """
                SELECT * FROM leave_records 
                WHERE person_id = ? AND leave_date >= ?
                ORDER BY leave_date DESC
                """,
                (person_id, start_date),
            )
        else:
            cursor.execute(
                """
                SELECT * FROM leave_records 
                WHERE person_id = ?
                ORDER BY leave_date DESC
                """,
                (person_id,),
            )
        rows = cursor.fetchall()
        return [LeaveRecord.from_row(row) for row in rows]

    def update(self, record: LeaveRecord) -> bool:
        """更新请假记录"""
        if record.id is None:
            return False
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE leave_records 
            SET leave_type = ?, hours = ?, status = ?, approver_person_id = ?, reason = ?
            WHERE id = ?
            """,
            (
                record.leave_type,
                record.hours,
                record.status,
                record.approver_person_id,
                record.reason,
                record.id,
            ),
        )
        conn.commit()
        return cursor.rowcount > 0

    def delete(self, record_id: int) -> bool:
        """删除请假记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM leave_records WHERE id = ?", (record_id,))
        conn.commit()
        return cursor.rowcount > 0

