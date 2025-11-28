"""
Person service for managing state streams
"""
from __future__ import annotations

import json
from typing import List, Dict, Any, Optional

import sqlite3

from app.daos.person_state_dao import (
    PersonBasicStateDAO,
    PersonPositionStateDAO,
    PersonSalaryStateDAO,
    PersonSocialSecurityStateDAO,
    PersonHousingFundStateDAO,
)
from app.models.person_payloads import (
    sanitize_basic_payload,
    sanitize_position_payload,
    sanitize_salary_payload,
    sanitize_social_security_payload,
    sanitize_housing_fund_payload,
)
from app.db import init_db


def generate_avatar(name: str) -> str:
    safe_name = (name or "user").strip() or "user"
    return (
        "https://api.dicebear.com/7.x/micah/svg"
        "?backgroundColor=bde0fe"
        "&mouth=smile"
        "&pose=thumbsUp"
        f"&seed={safe_name}"
    )


class PersonService:
    def __init__(self, db_path: str):
        self.db_path = db_path
        init_db(db_path)
        self.basic_dao = PersonBasicStateDAO(db_path=db_path)
        self.position_dao = PersonPositionStateDAO(db_path=db_path)
        self.salary_dao = PersonSalaryStateDAO(db_path=db_path)
        self.social_security_dao = PersonSocialSecurityStateDAO(db_path=db_path)
        self.housing_fund_dao = PersonHousingFundStateDAO(db_path=db_path)

    def _get_connection(self) -> sqlite3.Connection:
        return self.basic_dao.get_connection()

    def list_persons(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT pb.person_id, pb.ts, pb.data
            FROM person_basic_history pb
            JOIN (
                SELECT person_id, MAX(version) AS max_version
                FROM person_basic_history
                GROUP BY person_id
            ) latest
            ON pb.person_id = latest.person_id AND pb.version = latest.max_version
            ORDER BY pb.ts DESC
            """
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            data = json.loads(row["data"])
            result.append(
                {
                    "person_id": row["person_id"],
                    "ts": row["ts"],
                    "name": data.get("name"),
                    "id_card": data.get("id_card"),
                    "gender": data.get("gender"),
                    "phone": data.get("phone"),
                    "email": data.get("email"),
                    "avatar": data.get("avatar"),
                }
            )
        return result

    def create_person(
        self,
        basic_data: dict,
        position_data: Optional[dict] = None,
        salary_data: Optional[dict] = None,
        social_security_data: Optional[dict] = None,
        housing_fund_data: Optional[dict] = None,
    ) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO persons DEFAULT VALUES")
        conn.commit()
        person_id = cursor.lastrowid

        cleaned_basic = sanitize_basic_payload(basic_data)
        if not cleaned_basic.get("avatar"):
            cleaned_basic["avatar"] = generate_avatar(cleaned_basic.get("name"))
        self.basic_dao.append(entity_id=person_id, data=cleaned_basic)

        cleaned_position = sanitize_position_payload(position_data)
        if cleaned_position:
            self.position_dao.append(entity_id=person_id, data=cleaned_position)

        cleaned_salary = sanitize_salary_payload(salary_data)
        if cleaned_salary:
            self.salary_dao.append(entity_id=person_id, data=cleaned_salary)

        cleaned_social_security = sanitize_social_security_payload(social_security_data)
        if cleaned_social_security:
            self.social_security_dao.append(entity_id=person_id, data=cleaned_social_security)

        cleaned_housing_fund = sanitize_housing_fund_payload(housing_fund_data)
        if cleaned_housing_fund:
            self.housing_fund_dao.append(entity_id=person_id, data=cleaned_housing_fund)

        return person_id

    def get_person(self, person_id: int) -> Optional[Dict[str, Any]]:
        basic = self.basic_dao.get_latest(person_id)
        if not basic:
            return None

        position = self.position_dao.get_latest(person_id)
        salary = self.salary_dao.get_latest(person_id)
        social_security = self.social_security_dao.get_latest(person_id)
        housing_fund = self.housing_fund_dao.get_latest(person_id)

        details = {
            "person_id": person_id,
            "basic": basic.to_dict(),
            "position": position.to_dict() if position else None,
            "salary": salary.to_dict() if salary else None,
            "social_security": social_security.to_dict() if social_security else None,
            "housing_fund": housing_fund.to_dict() if housing_fund else None,
            "basic_history": [state.to_dict() for state in self.basic_dao.list_states(person_id, limit=10)],
            "position_history": [state.to_dict() for state in self.position_dao.list_states(person_id, limit=10)],
            "salary_history": [state.to_dict() for state in self.salary_dao.list_states(person_id, limit=10)],
            "social_security_history": [state.to_dict() for state in self.social_security_dao.list_states(person_id, limit=10)],
            "housing_fund_history": [state.to_dict() for state in self.housing_fund_dao.list_states(person_id, limit=10)],
        }
        return details

