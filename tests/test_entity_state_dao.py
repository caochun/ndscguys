from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from app.daos.person_state_dao import PersonBasicStateDAO, PersonPositionStateDAO
from app.db import init_db


def test_basic_state_append_and_fetch(tmp_path):
    db_path = tmp_path / "basic.db"
    init_db(str(db_path))
    dao = PersonBasicStateDAO(db_path=str(db_path))

    v1 = dao.append(
        entity_id=1,
        data={"name": "Alice", "id_card": "ID001"},
        ts="2025-01-01T08:00:00",
    )
    v2 = dao.append(
        entity_id=1,
        data={"name": "Alice Zhang", "id_card": "ID001"},
        ts="2025-02-01T09:00:00",
    )

    assert v1 == 1
    assert v2 == 2

    latest = dao.get_latest(1)
    assert latest.version == 2
    assert latest.data["name"] == "Alice Zhang"

    first = dao.get_by_version(1, 1)
    assert first.version == 1
    assert first.data["name"] == "Alice"


def test_list_states_respects_limit(tmp_path):
    db_path = tmp_path / "basic_limit.db"
    init_db(str(db_path))
    dao = PersonBasicStateDAO(db_path=str(db_path))

    for month in range(1, 5):
        dao.append(
            entity_id=2,
            data={"version": month},
            ts=f"2025-0{month}-01T00:00:00",
        )

    states = dao.list_states(2, limit=2)
    assert len(states) == 2
    assert [state.version for state in states] == [4, 3]


def test_get_at_returns_state_for_timestamp(tmp_path):
    db_path = tmp_path / "position.db"
    init_db(str(db_path))
    dao = PersonPositionStateDAO(db_path=str(db_path))

    dao.append(
        entity_id=3,
        data={"company_name": "A", "position": "Engineer"},
        ts="2025-01-01T08:00:00",
    )
    dao.append(
        entity_id=3,
        data={"company_name": "A", "position": "Senior Engineer"},
        ts="2025-02-01T08:00:00",
    )

    state_mid_jan = dao.get_at(3, "2025-01-15T00:00:00")
    assert state_mid_jan.version == 1
    assert state_mid_jan.data["position"] == "Engineer"

    state_feb = dao.get_at(3, datetime(2025, 2, 15, 0, 0, 0))
    assert state_feb.version == 2
    assert state_feb.data["position"] == "Senior Engineer"

    no_state = dao.get_at(3, "2024-12-31T23:59:59")
    assert no_state is None

