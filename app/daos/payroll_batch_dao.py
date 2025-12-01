from __future__ import annotations

from typing import Any, Dict, List, Optional

import sqlite3

from app.daos.base_dao import BaseDAO
from app.models.batches import PayrollBatch, PayrollBatchItem


class PayrollBatchDAO(BaseDAO):
    """薪酬批量发放批次与明细 DAO"""

    # ---- 批次相关 ----

    def create_batch(self, data: Dict[str, Any]) -> int:
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO payroll_batches (
                batch_period,
                effective_date,
                target_company,
                target_department,
                target_employee_type,
                note,
                status,
                affected_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["batch_period"],
                data.get("effective_date"),
                data.get("target_company"),
                data.get("target_department"),
                data.get("target_employee_type"),
                data.get("note"),
                data.get("status", "pending"),
                int(data.get("affected_count", 0)),
            ),
        )
        conn.commit()
        return cursor.lastrowid

    def get_batch(self, batch_id: int) -> Optional[Dict[str, Any]]:
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM payroll_batches WHERE id = ?", (batch_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return PayrollBatch.from_row(row).to_dict()

    def update_status(self, batch_id: int, status: str) -> None:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE payroll_batches SET status = ? WHERE id = ?", (status, batch_id)
        )
        conn.commit()

    def update_affected_count(self, batch_id: int, affected_count: int) -> None:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE payroll_batches SET affected_count = ? WHERE id = ?",
            (int(affected_count), batch_id),
        )
        conn.commit()

    def list_batches(self, limit: int = 50) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT *
            FROM payroll_batches
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [PayrollBatch.from_row(row).to_dict() for row in cursor.fetchall()]

    # ---- 明细相关 ----

    def create_item(self, data: Dict[str, Any]) -> int:
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO payroll_batch_items (
                batch_id,
                person_id,
                salary_base_amount,
                salary_performance_base,
                performance_factor,
                performance_amount,
                gross_amount_before_deductions,
                attendance_deduction,
                social_personal_amount,
                housing_personal_amount,
                other_deduction,
                net_amount_before_tax,
                applied
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["batch_id"],
                data["person_id"],
                data.get("salary_base_amount"),
                data.get("salary_performance_base"),
                data.get("performance_factor"),
                data.get("performance_amount"),
                data.get("gross_amount_before_deductions"),
                data.get("attendance_deduction"),
                data.get("social_personal_amount"),
                data.get("housing_personal_amount"),
                data.get("other_deduction"),
                data.get("net_amount_before_tax"),
                int(data.get("applied", 0)),
            ),
        )
        conn.commit()
        return cursor.lastrowid

    def list_items(self, batch_id: int) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM payroll_batch_items WHERE batch_id = ? ORDER BY id ASC",
            (batch_id,),
        )
        return [PayrollBatchItem.from_row(row).to_dict() for row in cursor.fetchall()]

    def get_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM payroll_batch_items WHERE id = ?",
            (item_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return PayrollBatchItem.from_row(row).to_dict()

    def update_item(self, item_id: int, new_data: Dict[str, Any]) -> None:
        """更新明细中的可编辑字段，例如 other_deduction。"""
        if not new_data:
            return
        fields = []
        params: List[Any] = []
        for key, value in new_data.items():
            fields.append(f"{key} = ?")
            params.append(value)
        params.append(item_id)
        sql = f"UPDATE payroll_batch_items SET {', '.join(fields)} WHERE id = ?"
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params))
        conn.commit()

    def mark_items_applied(self, batch_id: int) -> None:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE payroll_batch_items SET applied = 1 WHERE batch_id = ?", (batch_id,)
        )
        conn.commit()


