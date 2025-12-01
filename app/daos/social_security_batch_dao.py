from __future__ import annotations

import sqlite3
from typing import Any, Dict, List

from app.daos.base_dao import BaseDAO
from app.models.batches import SocialSecurityBatch, SocialSecurityBatchItem


class SocialSecurityBatchDAO(BaseDAO):
    """DAO for social_security_adjustment_batches and social_security_batch_items."""

    def __init__(self, db_path: str):
        super().__init__(db_path=db_path)

    # ---- batch 操作 ----

    def create_batch(self, data: Dict[str, Any]) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO social_security_adjustment_batches (
                effective_date,
                min_base_amount,
                max_base_amount,
                default_pension_company_rate,
                default_pension_personal_rate,
                default_unemployment_company_rate,
                default_unemployment_personal_rate,
                default_medical_company_rate,
                default_medical_personal_rate,
                default_maternity_company_rate,
                default_maternity_personal_rate,
                default_critical_illness_company_amount,
                default_critical_illness_personal_amount,
                target_company,
                target_department,
                target_employee_type,
                note,
                status,
                affected_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["effective_date"],
                data["min_base_amount"],
                data["max_base_amount"],
                data.get("default_pension_company_rate"),
                data.get("default_pension_personal_rate"),
                data.get("default_unemployment_company_rate"),
                data.get("default_unemployment_personal_rate"),
                data.get("default_medical_company_rate"),
                data.get("default_medical_personal_rate"),
                data.get("default_maternity_company_rate"),
                data.get("default_maternity_personal_rate"),
                data.get("default_critical_illness_company_amount"),
                data.get("default_critical_illness_personal_amount"),
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
            "UPDATE social_security_adjustment_batches SET affected_count = ? WHERE id = ?",
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
                   default_pension_company_rate, default_pension_personal_rate,
                   default_unemployment_company_rate, default_unemployment_personal_rate,
                   default_medical_company_rate, default_medical_personal_rate,
                   default_maternity_company_rate, default_maternity_personal_rate,
                   default_critical_illness_company_amount, default_critical_illness_personal_amount,
                   target_company, target_department, target_employee_type,
                   note, status, affected_count
            FROM social_security_adjustment_batches
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        return [SocialSecurityBatch.from_row(row).to_dict() for row in rows]

    def update_status(self, batch_id: int, status: str) -> None:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE social_security_adjustment_batches SET status = ? WHERE id = ?",
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
                   default_pension_company_rate, default_pension_personal_rate,
                   default_unemployment_company_rate, default_unemployment_personal_rate,
                   default_medical_company_rate, default_medical_personal_rate,
                   default_maternity_company_rate, default_maternity_personal_rate,
                   default_critical_illness_company_amount, default_critical_illness_personal_amount,
                   target_company, target_department, target_employee_type,
                   note, status, affected_count
            FROM social_security_adjustment_batches
            WHERE id = ?
            """,
            (batch_id,),
        )
        row = cursor.fetchone()
        return SocialSecurityBatch.from_row(row).to_dict() if row else None

    # ---- 批次明细操作 ----

    def create_item(self, data: Dict[str, Any]) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO social_security_batch_items (
                batch_id,
                person_id,
                current_base_amount,
                current_pension_company_rate,
                current_pension_personal_rate,
                current_unemployment_company_rate,
                current_unemployment_personal_rate,
                current_medical_company_rate,
                current_medical_personal_rate,
                current_maternity_company_rate,
                current_maternity_personal_rate,
                current_critical_illness_company_amount,
                current_critical_illness_personal_amount,
                new_base_amount,
                new_pension_company_rate,
                new_pension_personal_rate,
                new_unemployment_company_rate,
                new_unemployment_personal_rate,
                new_medical_company_rate,
                new_medical_personal_rate,
                new_maternity_company_rate,
                new_maternity_personal_rate,
                new_critical_illness_company_amount,
                new_critical_illness_personal_amount,
                applied
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["batch_id"],
                data["person_id"],
                data.get("current_base_amount"),
                data.get("current_pension_company_rate"),
                data.get("current_pension_personal_rate"),
                data.get("current_unemployment_company_rate"),
                data.get("current_unemployment_personal_rate"),
                data.get("current_medical_company_rate"),
                data.get("current_medical_personal_rate"),
                data.get("current_maternity_company_rate"),
                data.get("current_maternity_personal_rate"),
                data.get("current_critical_illness_company_amount"),
                data.get("current_critical_illness_personal_amount"),
                data["new_base_amount"],
                data.get("new_pension_company_rate"),
                data.get("new_pension_personal_rate"),
                data.get("new_unemployment_company_rate"),
                data.get("new_unemployment_personal_rate"),
                data.get("new_medical_company_rate"),
                data.get("new_medical_personal_rate"),
                data.get("new_maternity_company_rate"),
                data.get("new_maternity_personal_rate"),
                data.get("new_critical_illness_company_amount"),
                data.get("new_critical_illness_personal_amount"),
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
                   current_base_amount,
                   current_pension_company_rate,
                   current_pension_personal_rate,
                   current_unemployment_company_rate,
                   current_unemployment_personal_rate,
                   current_medical_company_rate,
                   current_medical_personal_rate,
                   current_maternity_company_rate,
                   current_maternity_personal_rate,
                   current_critical_illness_company_amount,
                   current_critical_illness_personal_amount,
                   new_base_amount,
                   new_pension_company_rate,
                   new_pension_personal_rate,
                   new_unemployment_company_rate,
                   new_unemployment_personal_rate,
                   new_medical_company_rate,
                   new_medical_personal_rate,
                   new_maternity_company_rate,
                   new_maternity_personal_rate,
                   new_critical_illness_company_amount,
                   new_critical_illness_personal_amount,
                   applied
            FROM social_security_batch_items
            WHERE batch_id = ?
            ORDER BY id ASC
            """,
            (batch_id,),
        )
        rows = cursor.fetchall()
        return [SocialSecurityBatchItem.from_row(row).to_dict() for row in rows]

    def update_item(self, item_id: int, new_data: Dict[str, Any]) -> None:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE social_security_batch_items
            SET new_base_amount = ?,
                new_pension_company_rate = ?,
                new_pension_personal_rate = ?,
                new_unemployment_company_rate = ?,
                new_unemployment_personal_rate = ?,
                new_medical_company_rate = ?,
                new_medical_personal_rate = ?,
                new_maternity_company_rate = ?,
                new_maternity_personal_rate = ?,
                new_critical_illness_company_amount = ?,
                new_critical_illness_personal_amount = ?
            WHERE id = ?
            """,
            (
                new_data["new_base_amount"],
                new_data.get("new_pension_company_rate"),
                new_data.get("new_pension_personal_rate"),
                new_data.get("new_unemployment_company_rate"),
                new_data.get("new_unemployment_personal_rate"),
                new_data.get("new_medical_company_rate"),
                new_data.get("new_medical_personal_rate"),
                new_data.get("new_maternity_company_rate"),
                new_data.get("new_maternity_personal_rate"),
                new_data.get("new_critical_illness_company_amount"),
                new_data.get("new_critical_illness_personal_amount"),
                item_id,
            ),
        )
        conn.commit()

    def mark_items_applied(self, batch_id: int) -> None:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE social_security_batch_items SET applied = 1 WHERE batch_id = ?",
            (batch_id,),
        )
        conn.commit()


