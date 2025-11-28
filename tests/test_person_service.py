from __future__ import annotations

from pathlib import Path

import pytest

from app.services.person_service import PersonService
from app.models.person_payloads import PayloadValidationError


@pytest.fixture()
def tmp_service(tmp_path: Path) -> PersonService:
    db_path = tmp_path / "service.db"
    return PersonService(str(db_path))


def test_create_person_basic_only(tmp_service: PersonService):
    person_id = tmp_service.create_person(
        basic_data={"name": "Alice", "id_card": "ID001"},
    )
    assert person_id == 1
    person = tmp_service.get_person(person_id)
    assert person is not None
    assert person["basic"]["data"]["name"] == "Alice"
    assert person["position"] is None
    assert person["salary"] is None


def test_create_person_with_position_and_salary(tmp_service: PersonService):
    person_id = tmp_service.create_person(
        basic_data={"name": "Bob", "id_card": "ID002", "avatar": "custom"},
        position_data={
            "company_name": "ACME",
            "employee_number": "AC001",
            "department": "研发部",
            "position": "工程师",
            "employee_type": "正式员工",
        },
        salary_data={"salary_type": "月薪制", "amount": 12000, "effective_date": "2025-01-01"},
        social_security_data={
            "base_amount": 8000,
            "pension_company_rate": 0.16,
            "medical_personal_rate": 0.02,
        },
        housing_fund_data={
            "base_amount": 7000,
            "company_rate": 0.07,
            "personal_rate": 0.07,
        },
    )
    person = tmp_service.get_person(person_id)
    assert person["position"]["data"]["company_name"] == "ACME"
    assert person["salary"]["data"]["amount"] == 12000
    assert person["social_security"]["data"]["base_amount"] == 8000
    assert person["housing_fund"]["data"]["company_rate"] == 0.07


def test_create_person_invalid_payload_raises(tmp_service: PersonService):
    with pytest.raises(PayloadValidationError):
        tmp_service.create_person(
            basic_data={"name": "Invalid"},
            position_data={"employee_type": "未知类型"},
        )

    with pytest.raises(PayloadValidationError):
        tmp_service.create_person(
            basic_data={"name": "Invalid2"},
            salary_data={"salary_type": "月薪制", "amount": -10},
        )

    with pytest.raises(PayloadValidationError):
        tmp_service.create_person(
            basic_data={"name": "Invalid3"},
            social_security_data={"pension_company_rate": 2},
        )

    with pytest.raises(PayloadValidationError):
        tmp_service.create_person(
            basic_data={"name": "Invalid4"},
            housing_fund_data={"company_rate": -0.1},
        )

