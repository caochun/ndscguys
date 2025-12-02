from __future__ import annotations

import sqlite3
from typing import Any, Dict, List

from app.daos.base_dao import BaseDAO
from app.models.batches import TaxDeductionBatch, TaxDeductionBatchItem


class TaxDeductionBatchDAO(BaseDAO):
    """DAO for tax_deduction_adjustment_batches and tax_deduction_batch_items."""

    def __init__(self, db_path: str):
        super().__init__(db_path=db_path)

    # ---- batch 操作 ----

    def create_batch(self, data: Dict[str, Any]) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO tax_deduction_adjustment_batches (
                effective_date,
                effective_month,
                target_company,
                target_department,
                target_employee_type,
                note,
                status,
                affected_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["effective_date"],
                data["effective_month"],
                data.get("target_company"),
                data.get("target_department"),
                data.get("target_employee_type"),
                data.get("note"),
                data.get("status", "pending"),
                data.get("affected_count", 0),
            ),
        )
        conn.commit()
        return cursor.lastrowid

    def update_affected_count(self, batch_id: int, affected_count: int) -> None:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE tax_deduction_adjustment_batches SET affected_count = ? WHERE id = ?",
            (affected_count, batch_id),
        )
        conn.commit()

    def list_batches(self, limit: int = 50) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, created_at, effective_date, effective_month,
                   target_company, target_department, target_employee_type,
                   note, status, affected_count
            FROM tax_deduction_adjustment_batches
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        return [TaxDeductionBatch.from_row(row).to_dict() for row in rows]

    def update_status(self, batch_id: int, status: str) -> None:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE tax_deduction_adjustment_batches SET status = ? WHERE id = ?",
            (status, batch_id),
        )
        conn.commit()

    def get_batch(self, batch_id: int) -> Dict[str, Any] | None:
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, created_at, effective_date, effective_month,
                   target_company, target_department, target_employee_type,
                   note, status, affected_count
            FROM tax_deduction_adjustment_batches
            WHERE id = ?
            """,
            (batch_id,),
        )
        row = cursor.fetchone()
        return TaxDeductionBatch.from_row(row).to_dict() if row else None

    # ---- 批次明细操作 ----

    def create_item(self, data: Dict[str, Any]) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO tax_deduction_batch_items (
                batch_id,
                person_id,
                current_continuing_education,
                current_infant_care,
                current_children_education,
                current_housing_loan_interest,
                current_housing_rent,
                current_elderly_support,
                new_continuing_education,
                new_infant_care,
                new_children_education,
                new_housing_loan_interest,
                new_housing_rent,
                new_elderly_support,
                applied
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["batch_id"],
                data["person_id"],
                data.get("current_continuing_education", 0.0),
                data.get("current_infant_care", 0.0),
                data.get("current_children_education", 0.0),
                data.get("current_housing_loan_interest", 0.0),
                data.get("current_housing_rent", 0.0),
                data.get("current_elderly_support", 0.0),
                data.get("new_continuing_education", 0.0),
                data.get("new_infant_care", 0.0),
                data.get("new_children_education", 0.0),
                data.get("new_housing_loan_interest", 0.0),
                data.get("new_housing_rent", 0.0),
                data.get("new_elderly_support", 0.0),
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
            """
            SELECT id, batch_id, person_id, created_at,
                   current_continuing_education,
                   current_infant_care,
                   current_children_education,
                   current_housing_loan_interest,
                   current_housing_rent,
                   current_elderly_support,
                   new_continuing_education,
                   new_infant_care,
                   new_children_education,
                   new_housing_loan_interest,
                   new_housing_rent,
                   new_elderly_support,
                   applied
            FROM tax_deduction_batch_items
            WHERE batch_id = ?
            ORDER BY id ASC
            """,
            (batch_id,),
        )
        rows = cursor.fetchall()
        return [TaxDeductionBatchItem.from_row(row).to_dict() for row in rows]

    def update_item(self, item_id: int, new_data: Dict[str, Any]) -> None:
        """更新明细中的可编辑字段"""
        if not new_data:
            return
        fields = []
        params: List[Any] = []
        for key, value in new_data.items():
            if key.startswith("new_"):
                fields.append(f"{key} = ?")
                params.append(value)
        if not fields:
            return
        params.append(item_id)
        sql = f"UPDATE tax_deduction_batch_items SET {', '.join(fields)} WHERE id = ?"
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params))
        conn.commit()

    def mark_items_applied(self, batch_id: int) -> None:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE tax_deduction_batch_items SET applied = 1 WHERE batch_id = ?",
            (batch_id,),
        )
        conn.commit()

