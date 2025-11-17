"""
薪资记录 DAO
"""
from typing import List, Optional
from app.daos.base_dao import BaseDAO
from app.models import SalaryRecord


class SalaryDAO(BaseDAO):
    """薪资记录数据访问对象"""

    def create(self, salary_record: SalaryRecord) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO salary_records (
                employee_id,
                base_amount,
                basic_salary,
                performance_salary,
                effective_date,
                end_date,
                change_reason,
                version,
                status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                salary_record.employee_id,
                salary_record.base_amount,
                salary_record.basic_salary,
                salary_record.performance_salary,
                salary_record.effective_date,
                salary_record.end_date,
                salary_record.change_reason,
                salary_record.version,
                salary_record.status,
            ),
        )

        salary_id = cursor.lastrowid
        conn.commit()
        return salary_id

    def get_by_id(self, salary_id: int) -> Optional[SalaryRecord]:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM salary_records WHERE id = ?", (salary_id,))
        row = cursor.fetchone()
        if row:
            return SalaryRecord.from_row(row)
        return None

    def get_current_by_employee(self, employee_id: int) -> Optional[SalaryRecord]:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM salary_records
            WHERE employee_id = ? AND status = 'active'
            ORDER BY effective_date DESC, version DESC
            LIMIT 1
            """,
            (employee_id,),
        )
        row = cursor.fetchone()
        if row:
            return SalaryRecord.from_row(row)
        return None

    def get_history_by_employee(self, employee_id: int) -> List[SalaryRecord]:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM salary_records
            WHERE employee_id = ?
            ORDER BY effective_date DESC, version DESC
            """,
            (employee_id,),
        )
        rows = cursor.fetchall()
        return [SalaryRecord.from_row(row) for row in rows]

    def deactivate_current(self, employee_id: int, end_date: Optional[str] = None) -> None:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE salary_records
            SET status = 'inactive',
                end_date = COALESCE(?, end_date),
                updated_at = CURRENT_TIMESTAMP
            WHERE employee_id = ? AND status = 'active'
            """,
            (end_date, employee_id),
        )
        conn.commit()

    def get_next_version(self, employee_id: int) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT MAX(version) AS max_version FROM salary_records WHERE employee_id = ?",
            (employee_id,),
        )
        row = cursor.fetchone()
        max_version = row['max_version'] if row and row['max_version'] is not None else 0
        return max_version + 1

    def clear_all(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM salary_records")
        conn.commit()

