from __future__ import annotations

import pytest

from app.models.person_payloads import (
    sanitize_basic_payload,
    sanitize_position_payload,
    sanitize_salary_payload,
    sanitize_social_security_payload,
    sanitize_housing_fund_payload,
    sanitize_assessment_payload,
    PayloadValidationError,
)


def test_sanitize_basic_payload_requires_name():
    with pytest.raises(PayloadValidationError):
        sanitize_basic_payload({})

    payload = sanitize_basic_payload({"name": " Alice ", "phone": " 123 "})
    assert payload["name"] == "Alice"
    assert payload["phone"] == "123"


def test_sanitize_position_payload_handles_employee_type_and_supervisor():
    payload = sanitize_position_payload(
        {
            "company_name": " ACME ",
            "employee_type": "正式员工",
            "supervisor_employee_id": "10",
            "change_type": "入职",
            "change_date": "2025-01-01",
            "change_reason": "新入职",
        }
    )
    assert payload["company_name"] == "ACME"
    assert payload["employee_type"] == "正式员工"
    assert payload["supervisor_employee_id"] == 10
    assert payload["change_type"] == "入职"
    assert payload["change_date"] == "2025-01-01"
    assert payload["change_reason"] == "新入职"

    with pytest.raises(PayloadValidationError):
        sanitize_position_payload({"employee_type": "invalid"})

    with pytest.raises(PayloadValidationError):
        sanitize_position_payload({"supervisor_employee_id": "abc"})

    with pytest.raises(PayloadValidationError):
        sanitize_position_payload({"change_type": "未知事件"})


def test_sanitize_salary_payload_validates_amount_and_type():
    payload = sanitize_salary_payload(
        {"salary_type": "月薪制", "amount": "12345.678", "effective_date": "2025-01-01"}
    )
    assert payload["salary_type"] == "月薪制"
    assert payload["amount"] == 12345.68

    with pytest.raises(PayloadValidationError):
        sanitize_salary_payload({"salary_type": "unknown"})

    with pytest.raises(PayloadValidationError):
        sanitize_salary_payload({"amount": -1})


def test_sanitize_social_security_payload_accepts_rates():
    payload = sanitize_social_security_payload(
        {
            "base_amount": "8000",
            "pension_company_rate": 0.16,
            "medical_personal_rate": 0.02,
            "critical_illness_company_amount": 50,
        }
    )
    assert payload["base_amount"] == 8000
    assert payload["pension_company_rate"] == 0.16
    assert payload["medical_personal_rate"] == 0.02
    assert payload["critical_illness_company_amount"] == 50

    with pytest.raises(PayloadValidationError):
        sanitize_social_security_payload({"pension_company_rate": 2})


def test_sanitize_housing_fund_payload_requires_valid_rates():
    payload = sanitize_housing_fund_payload(
        {"base_amount": 9000, "company_rate": 0.07, "personal_rate": 0.07}
    )
    assert payload["company_rate"] == 0.07

    with pytest.raises(PayloadValidationError):
        sanitize_housing_fund_payload({"company_rate": -0.1})


def test_sanitize_assessment_payload_grade_required_and_limited():
    # empty or None -> None
    assert sanitize_assessment_payload(None) is None
    assert sanitize_assessment_payload({}) is None

    payload = sanitize_assessment_payload(
        {"grade": "A", "assessment_date": "2025-01-01", "note": "优秀"}
    )
    assert payload["grade"] == "A"
    assert payload["assessment_date"] == "2025-01-01"
    assert payload["note"] == "优秀"

    with pytest.raises(PayloadValidationError):
        sanitize_assessment_payload({"grade": "X"})

