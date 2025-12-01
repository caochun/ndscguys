from __future__ import annotations

import sqlite3
from typing import Any, Dict, List

from app.daos.base_dao import BaseDAO
from app.models.batches import HousingFundBatch, HousingFundBatchItem


class HousingFundBatchDAO(BaseDAO):
    """DAO for housing_fund_adjustment_batches and housing_fund_batch_items."""

    def __init__(self, db_path: str):
        super().__init__(db_path=db_path)

    # ---- batch 操作 ----

    def create_batch(self, data: Dict[str, Any]) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO housing_fund_adjustment_batches (
                effective_date,
                min_base_amount,
                max_base_amount,
                default_company_rate,
                default_personal_rate,
                target_company,
                target_department,
                target_employee_type,
                note,
                status,
                affected_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["effective_date"],
                data["min_base_amount"],
                data["max_base_amount"],
                data["default_company_rate"],
                data["default_personal_rate"],
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
            "UPDATE housing_fund_adjustment_batches SET affected_count = ? WHERE id = ?",
            (affected_count, batch_id),
        )
        conn.commit()

    def list_batches(self, limit: int = 50) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, created_at, effective_date,
                   min_base_amount, max_base_amount,
                   default_company_rate, default_personal_rate,
                   target_company, target_department, target_employee_type,
                   note, status, affected_count
            FROM housing_fund_adjustment_batches
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        return [HousingFundBatch.from_row(row).to_dict() for row in rows]

    def update_status(self, batch_id: int, status: str) -> None:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE housing_fund_adjustment_batches SET status = ? WHERE id = ?",
            (status, batch_id),
        )
        conn.commit()

    def get_batch(self, batch_id: int) -> Dict[str, Any] | None:
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, created_at, effective_date,
                   min_base_amount, max_base_amount,
                   default_company_rate, default_personal_rate,
                   target_company, target_department, target_employee_type,
                   note, status, affected_count
            FROM housing_fund_adjustment_batches
            WHERE id = ?
            """,
            (batch_id,),
        )
        row = cursor.fetchone()
        return HousingFundBatch.from_row(row).to_dict() if row else None

    # ---- 批次明细操作 ----

    def create_item(self, data: Dict[str, Any]) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO housing_fund_batch_items (
                batch_id,
                person_id,
                current_base_amount,
                current_company_rate,
                current_personal_rate,
                new_base_amount,
                new_company_rate,
                new_personal_rate,
                applied
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["batch_id"],
                data["person_id"],
                data.get("current_base_amount"),
                data.get("current_company_rate"),
                data.get("current_personal_rate"),
                data["new_base_amount"],
                data["new_company_rate"],
                data["new_personal_rate"],
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
                   current_base_amount, current_company_rate, current_personal_rate,
                   new_base_amount, new_company_rate, new_personal_rate,
                   applied
            FROM housing_fund_batch_items
            WHERE batch_id = ?
            ORDER BY id ASC
            """,
            (batch_id,),
        )
        rows = cursor.fetchall()
        return [HousingFundBatchItem.from_row(row).to_dict() for row in rows]

    def update_item(self, item_id: int, new_data: Dict[str, Any]) -> None:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE housing_fund_batch_items
            SET new_base_amount = ?,
                new_company_rate = ?,
                new_personal_rate = ?
            WHERE id = ?
            """,
            (
                new_data["new_base_amount"],
                new_data["new_company_rate"],
                new_data["new_personal_rate"],
                item_id,
            ),
        )
        conn.commit()

    def mark_items_applied(self, batch_id: int) -> None:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE housing_fund_batch_items SET applied = 1 WHERE batch_id = ?",
            (batch_id,),
        )
        conn.commit()


