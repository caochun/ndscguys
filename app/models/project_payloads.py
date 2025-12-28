"""
Payload validators for project state streams.
"""
from __future__ import annotations

from typing import Dict, Optional, Any

from app.models.person_payloads import (
    PayloadValidationError,
    _normalize_string,
    _normalize_amount_non_negative,
)


def sanitize_project_payload(data: Optional[dict]) -> Dict[str, Any]:
    """项目基础信息 payload 清洗"""
    if not isinstance(data, dict):
        raise PayloadValidationError("project payload must be a dict")

    cleaned: Dict[str, Any] = {}

    # 合同名称（必填）
    contract_name = _normalize_string(data.get("contract_name"))
    if not contract_name:
        raise PayloadValidationError("project.contract_name is required")
    cleaned["contract_name"] = contract_name

    # 起止时间
    start_date = _normalize_string(data.get("start_date"))
    if start_date:
        cleaned["start_date"] = start_date

    end_date = _normalize_string(data.get("end_date"))
    if end_date:
        cleaned["end_date"] = end_date

    # 甲方单位
    client_company = _normalize_string(data.get("client_company"))
    if client_company:
        cleaned["client_company"] = client_company

    # 甲方部门
    client_department = _normalize_string(data.get("client_department"))
    if client_department:
        cleaned["client_department"] = client_department

    # 甲方项目经理
    client_project_manager = _normalize_string(data.get("client_project_manager"))
    if client_project_manager:
        cleaned["client_project_manager"] = client_project_manager

    # 注意：我方项目经理已移除，改为通过 person_project_history 中的 project_position 来记录

    return cleaned


def sanitize_person_project_payload(data: Optional[dict]) -> Optional[Dict[str, Any]]:
    """人员参与项目信息 payload 清洗"""
    if data is None:
        return None
    if not isinstance(data, dict):
        raise PayloadValidationError("person project payload must be a dict")

    cleaned: Dict[str, Any] = {}

    # 项目ID（必填）
    project_id_raw = data.get("project_id")
    if project_id_raw is None:
        raise PayloadValidationError("person_project.project_id is required")
    try:
        cleaned["project_id"] = int(project_id_raw)
    except (TypeError, ValueError) as exc:
        raise PayloadValidationError("person_project.project_id must be int") from exc

    # 人员材料提交时间
    material_submit_date = _normalize_string(data.get("material_submit_date"))
    if material_submit_date:
        cleaned["material_submit_date"] = material_submit_date

    # 入项岗位
    project_position = _normalize_string(data.get("project_position"))
    if project_position:
        cleaned["project_position"] = project_position

    # 评定等级
    assessment_level = _normalize_string(data.get("assessment_level"))
    if assessment_level:
        cleaned["assessment_level"] = assessment_level

    # 评定单价
    unit_price = _normalize_amount_non_negative(data.get("unit_price"))
    if unit_price is not None:
        cleaned["unit_price"] = unit_price

    # 当前管理流程状态
    process_status = _normalize_string(data.get("process_status"))
    if process_status:
        cleaned["process_status"] = process_status

    return cleaned or None

