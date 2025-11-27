"""
Person service for managing state streams
"""
from __future__ import annotations

import json
from typing import List, Dict, Any, Optional

import sqlite3

from app.daos.person_state_dao import PersonBasicStateDAO, PersonPositionStateDAO
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

    def create_person(self, basic_data: dict, position_data: Optional[dict] = None) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO persons DEFAULT VALUES")
        conn.commit()
        person_id = cursor.lastrowid

        if not basic_data.get("avatar"):
            basic_data["avatar"] = generate_avatar(basic_data.get("name"))
        self.basic_dao.append(entity_id=person_id, data=basic_data)

        if position_data:
            self.position_dao.append(entity_id=person_id, data=position_data)

        return person_id

    def get_person(self, person_id: int) -> Optional[Dict[str, Any]]:
        basic = self.basic_dao.get_latest(person_id)
        if not basic:
            return None

        position = self.position_dao.get_latest(person_id)

        details = {
            "person_id": person_id,
            "basic": basic.to_dict(),
            "position": position.to_dict() if position else None,
            "basic_history": [state.to_dict() for state in self.basic_dao.list_states(person_id, limit=10)],
            "position_history": [state.to_dict() for state in self.position_dao.list_states(person_id, limit=10)],
        }
        return details

