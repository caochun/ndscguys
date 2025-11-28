"""
Payload validators for person state streams.
"""
from __future__ import annotations

from typing import Dict, Optional, Any


class PayloadValidationError(ValueError):
    """Raised when payload validation fails."""


STRING_FIELDS_BASIC = {
    "name",
    "id_card",
    "birth_date",
    "gender",
    "phone",
    "email",
    "address",
    "avatar",
}

STRING_FIELDS_POSITION = {
    "company_name",
    "employee_number",
    "department",
    "position",
    "hire_date",
}

ALLOWED_EMPLOYEE_TYPES = {"正式员工", "试用期员工", "实习生", "部分负责人", "其他"}
ALLOWED_SALARY_TYPES = {"年薪制", "月薪制", "日薪制度"}

SOCIAL_RATE_FIELDS = [
    "pension_company_rate",
    "pension_personal_rate",
    "unemployment_company_rate",
    "unemployment_personal_rate",
    "medical_company_rate",
    "medical_personal_rate",
    "maternity_company_rate",
    "maternity_personal_rate",
]

SOCIAL_AMOUNT_FIELDS = [
    "critical_illness_company_amount",
    "critical_illness_personal_amount",
]


def _normalize_float(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise PayloadValidationError("value must be a number") from exc


def _normalize_rate(value: Any) -> Optional[float]:
    normalized = _normalize_float(value)
    if normalized is None:
        return None
    if not 0 <= normalized <= 1:
        raise PayloadValidationError("rate must be between 0 and 1")
    return round(normalized, 4)


def _normalize_amount_non_negative(value: Any) -> Optional[float]:
    normalized = _normalize_float(value)
    if normalized is None:
        return None
    if normalized < 0:
        raise PayloadValidationError("amount must be >= 0")
    return round(normalized, 2)

def _normalize_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def sanitize_basic_payload(data: Optional[dict]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        raise PayloadValidationError("basic payload must be a dict")

    cleaned: Dict[str, Any] = {}
    for field in STRING_FIELDS_BASIC:
        value = _normalize_string(data.get(field))
        if value is not None:
            cleaned[field] = value

    if not cleaned.get("name"):
        raise PayloadValidationError("basic.name is required")

    return cleaned


def sanitize_position_payload(data: Optional[dict]) -> Optional[Dict[str, Any]]:
    if data is None:
        return None
    if not isinstance(data, dict):
        raise PayloadValidationError("position payload must be a dict")

    cleaned: Dict[str, Any] = {}
    for field in STRING_FIELDS_POSITION:
        value = _normalize_string(data.get(field))
        if value is not None:
            cleaned[field] = value

    employee_type = _normalize_string(data.get("employee_type"))
    if employee_type:
        if employee_type not in ALLOWED_EMPLOYEE_TYPES:
            raise PayloadValidationError("position.employee_type is invalid")
        cleaned["employee_type"] = employee_type

    supervisor_raw = data.get("supervisor_employee_id")
    if supervisor_raw not in (None, ""):
        try:
            cleaned["supervisor_employee_id"] = int(supervisor_raw)
        except (TypeError, ValueError) as exc:
            raise PayloadValidationError("position.supervisor_employee_id must be int") from exc

    return cleaned or None


def sanitize_salary_payload(data: Optional[dict]) -> Optional[Dict[str, Any]]:
    if data is None:
        return None
    if not isinstance(data, dict):
        raise PayloadValidationError("salary payload must be a dict")

    cleaned: Dict[str, Any] = {}

    salary_type = _normalize_string(data.get("salary_type"))
    if salary_type:
        if salary_type not in ALLOWED_SALARY_TYPES:
            raise PayloadValidationError("salary.salary_type is invalid")
        cleaned["salary_type"] = salary_type

    amount_value = _normalize_amount_non_negative(data.get("amount"))
    if amount_value is not None:
        cleaned["amount"] = amount_value

    effective_date = _normalize_string(data.get("effective_date"))
    if effective_date:
        cleaned["effective_date"] = effective_date

    return cleaned or None


def sanitize_social_security_payload(data: Optional[dict]) -> Optional[Dict[str, Any]]:
    if data is None:
        return None
    if not isinstance(data, dict):
        raise PayloadValidationError("social security payload must be a dict")

    cleaned: Dict[str, Any] = {}

    base_amount = _normalize_amount_non_negative(data.get("base_amount"))
    if base_amount is not None:
        cleaned["base_amount"] = base_amount

    for field in SOCIAL_RATE_FIELDS:
        rate = _normalize_rate(data.get(field))
        if rate is not None:
            cleaned[field] = rate

    for field in SOCIAL_AMOUNT_FIELDS:
        amount = _normalize_amount_non_negative(data.get(field))
        if amount is not None:
            cleaned[field] = amount

    return cleaned or None


def sanitize_housing_fund_payload(data: Optional[dict]) -> Optional[Dict[str, Any]]:
    if data is None:
        return None
    if not isinstance(data, dict):
        raise PayloadValidationError("housing fund payload must be a dict")

    cleaned: Dict[str, Any] = {}

    base_amount = _normalize_amount_non_negative(data.get("base_amount"))
    if base_amount is not None:
        cleaned["base_amount"] = base_amount

    company_rate = _normalize_rate(data.get("company_rate"))
    if company_rate is not None:
        cleaned["company_rate"] = company_rate

    personal_rate = _normalize_rate(data.get("personal_rate"))
    if personal_rate is not None:
        cleaned["personal_rate"] = personal_rate

    return cleaned or None

