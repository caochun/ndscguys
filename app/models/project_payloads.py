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

    # 项目类型（必填）
    project_type = _normalize_string(data.get("project_type"))
    if not project_type:
        raise PayloadValidationError("project.project_type is required")
    if project_type not in ["劳务型", "专项型"]:
        raise PayloadValidationError("project.project_type must be '劳务型' or '专项型'")
    cleaned["project_type"] = project_type

    # 内部项目信息（必填）
    internal_project_name = _normalize_string(data.get("internal_project_name"))
    if not internal_project_name:
        raise PayloadValidationError("project.internal_project_name is required")
    cleaned["internal_project_name"] = internal_project_name

    internal_department = _normalize_string(data.get("internal_department"))
    if not internal_department:
        raise PayloadValidationError("project.internal_department is required")
    cleaned["internal_department"] = internal_department

    internal_project_manager = _normalize_string(data.get("internal_project_manager"))
    if not internal_project_manager:
        raise PayloadValidationError("project.internal_project_manager is required")
    cleaned["internal_project_manager"] = internal_project_manager

    # 外部项目信息（必填）
    external_project_name = _normalize_string(data.get("external_project_name"))
    if not external_project_name:
        raise PayloadValidationError("project.external_project_name is required")
    cleaned["external_project_name"] = external_project_name

    external_company = _normalize_string(data.get("external_company"))
    if not external_company:
        raise PayloadValidationError("project.external_company is required")
    cleaned["external_company"] = external_company

    external_department = _normalize_string(data.get("external_department"))
    if external_department:
        cleaned["external_department"] = external_department

    external_manager = _normalize_string(data.get("external_manager"))
    if external_manager:
        cleaned["external_manager"] = external_manager

    external_order_number = _normalize_string(data.get("external_order_number"))
    if external_order_number:
        cleaned["external_order_number"] = external_order_number

    execution_start_date = _normalize_string(data.get("execution_start_date"))
    if execution_start_date:
        cleaned["execution_start_date"] = execution_start_date

    execution_end_date = _normalize_string(data.get("execution_end_date"))
    if execution_end_date:
        cleaned["execution_end_date"] = execution_end_date

    return cleaned


def sanitize_person_project_payload(data: Optional[dict], project_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """人员参与项目信息 payload 清洗
    
    Args:
        data: 人员参与项目数据
        project_type: 项目类型（"劳务型"或"专项型"），用于验证劳务型项目的必填字段
    """
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

    # 通用字段（所有项目类型）
    material_submit_date = _normalize_string(data.get("material_submit_date"))
    if material_submit_date:
        cleaned["material_submit_date"] = material_submit_date

    project_position = _normalize_string(data.get("project_position"))
    if project_position:
        cleaned["project_position"] = project_position

    assessment_level = _normalize_string(data.get("assessment_level"))
    if assessment_level:
        cleaned["assessment_level"] = assessment_level

    unit_price = _normalize_amount_non_negative(data.get("unit_price"))
    if unit_price is not None:
        cleaned["unit_price"] = unit_price

    process_status = _normalize_string(data.get("process_status"))
    if process_status:
        cleaned["process_status"] = process_status

    # 劳务型项目专用字段
    if project_type == "劳务型":
        client_requirement_number = _normalize_string(data.get("client_requirement_number"))
        if client_requirement_number:
            cleaned["client_requirement_number"] = client_requirement_number

        attendance_method = _normalize_string(data.get("attendance_method"))
        if attendance_method:
            if attendance_method not in ["现场打卡", "线上打卡"]:
                raise PayloadValidationError("attendance_method must be '现场打卡' or '线上打卡'")
            cleaned["attendance_method"] = attendance_method

            # 现场打卡专用字段
            if attendance_method == "现场打卡":
                attendance_location = _normalize_string(data.get("attendance_location"))
                if attendance_location:
                    cleaned["attendance_location"] = attendance_location
                work_time_range = _normalize_string(data.get("work_time_range"))
                if work_time_range:
                    cleaned["work_time_range"] = work_time_range

            # 线上打卡专用字段
            elif attendance_method == "线上打卡":
                online_location = _normalize_string(data.get("online_location"))
                if online_location:
                    cleaned["online_location"] = online_location
                online_work_time = _normalize_string(data.get("online_work_time"))
                if online_work_time:
                    cleaned["online_work_time"] = online_work_time
                face_recognition = data.get("face_recognition")
                if face_recognition is not None:
                    cleaned["face_recognition"] = bool(face_recognition)
                attendance_person = _normalize_string(data.get("attendance_person"))
                if attendance_person:
                    cleaned["attendance_person"] = attendance_person

        position_level = _normalize_string(data.get("position_level"))
        if position_level:
            cleaned["position_level"] = position_level

        labor_unit_price = _normalize_amount_non_negative(data.get("labor_unit_price"))
        if labor_unit_price is not None:
            cleaned["labor_unit_price"] = labor_unit_price

    return cleaned or None


def sanitize_person_project_status_payload(data: Optional[dict]) -> Dict[str, Any]:
    """人员项目状态 payload 清洗（在项/待入项/不可用）"""
    if not isinstance(data, dict):
        raise PayloadValidationError("person project status payload must be a dict")

    cleaned: Dict[str, Any] = {}

    # 状态（必填）
    status = _normalize_string(data.get("status"))
    if not status:
        raise PayloadValidationError("person_project_status.status is required")
    if status not in ["在项", "待入项", "不可用"]:
        raise PayloadValidationError("person_project_status.status must be '在项', '待入项', or '不可用'")
    cleaned["status"] = status

    # 项目ID（根据状态决定是否必填）
    project_id_raw = data.get("project_id")
    if status == "在项":
        if project_id_raw is None:
            raise PayloadValidationError("person_project_status.project_id is required when status is '在项'")
        try:
            cleaned["project_id"] = int(project_id_raw)
        except (TypeError, ValueError) as exc:
            raise PayloadValidationError("person_project_status.project_id must be int") from exc
    elif status == "待入项":
        # 待入项时，project_id可选（可以是占位符0）
        if project_id_raw is not None:
            try:
                cleaned["project_id"] = int(project_id_raw)
            except (TypeError, ValueError) as exc:
                raise PayloadValidationError("person_project_status.project_id must be int") from exc
        else:
            cleaned["project_id"] = 0  # 默认使用占位符
    else:  # 不可用
        cleaned["project_id"] = None

    # 备注（可选）
    note = _normalize_string(data.get("note"))
    if note:
        cleaned["note"] = note

    return cleaned

