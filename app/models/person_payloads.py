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
    "graduation_school",
    "major",
    "education_level",
    "graduation_date",
    "first_work_date",
}

STRING_FIELDS_POSITION = {
    "company_name",
    "employee_number",
    "department",
    "position",
}

ALLOWED_EMPLOYEE_TYPES = {"正式员工", "试用期员工", "实习生", "部分负责人", "其他"}
ALLOWED_POSITION_CHANGE_TYPES = {
    "入职",
    "转岗",
    "调部门",
    "转公司",
    "停薪留职",
    "返岗",
    "离职",
}
ALLOWED_SALARY_TYPES = {"年薪制", "月薪制", "日薪制度"}
ALLOWED_ASSESSMENT_GRADES = {"A", "B", "C", "D", "E"}

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

    # 员工类别
    employee_type = _normalize_string(data.get("employee_type"))
    if employee_type:
        if employee_type not in ALLOWED_EMPLOYEE_TYPES:
            raise PayloadValidationError("position.employee_type is invalid")
        cleaned["employee_type"] = employee_type

    # 上级员工 ID
    supervisor_raw = data.get("supervisor_employee_id")
    if supervisor_raw not in (None, ""):
        try:
            cleaned["supervisor_employee_id"] = int(supervisor_raw)
        except (TypeError, ValueError) as exc:
            raise PayloadValidationError("position.supervisor_employee_id must be int") from exc

    # 岗位变动事件类型（入职 / 转岗 / 调部门 / 转公司 / 停薪留职 / 返岗 / 离职）
    change_type = _normalize_string(data.get("change_type"))
    if change_type:
        if change_type not in ALLOWED_POSITION_CHANGE_TYPES:
            raise PayloadValidationError("position.change_type is invalid")
        cleaned["change_type"] = change_type

    # 变动日期（必然以 change_date 命名，不再兼容旧的 hire_date）
    change_date = _normalize_string(data.get("change_date"))
    if change_date:
        cleaned["change_date"] = change_date

    # 变动原因（可选）
    change_reason = _normalize_string(data.get("change_reason"))
    if change_reason:
        cleaned["change_reason"] = change_reason

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


def sanitize_assessment_payload(data: Optional[dict]) -> Optional[Dict[str, Any]]:
    """考核状态 payload 清洗：grade 在 A-E 之间，可选考核日期和备注。"""
    if data is None:
        return None
    if not isinstance(data, dict):
        raise PayloadValidationError("assessment payload must be a dict")

    cleaned: Dict[str, Any] = {}

    grade = _normalize_string(data.get("grade"))
    if grade:
        if grade not in ALLOWED_ASSESSMENT_GRADES:
            raise PayloadValidationError("assessment.grade is invalid")
        cleaned["grade"] = grade

    # 考核时间（业务含义上的“考核日期”，与状态流的 ts 字段互补）
    assessment_date = _normalize_string(data.get("assessment_date"))
    if assessment_date:
        cleaned["assessment_date"] = assessment_date

    note = _normalize_string(data.get("note"))
    if note:
        cleaned["note"] = note

    # 至少要有 grade 才算一条有效状态
    return cleaned or None


def sanitize_tax_deduction_payload(data: Optional[dict]) -> Optional[Dict[str, Any]]:
    """个税专项附加扣除 payload 清洗：6项扣除金额（元/月）。"""
    if data is None:
        return None
    if not isinstance(data, dict):
        raise PayloadValidationError("tax deduction payload must be a dict")

    cleaned: Dict[str, Any] = {}

    # 6项专项附加扣除
    tax_deduction_fields = [
        "continuing_education",
        "infant_care",
        "children_education",
        "housing_loan_interest",
        "housing_rent",
        "elderly_support",
    ]

    for field in tax_deduction_fields:
        amount = _normalize_amount_non_negative(data.get(field))
        if amount is not None:
            cleaned[field] = amount

    return cleaned or None



