"""
工资计算步骤 API（基于 config JSON）
"""
from __future__ import annotations

from flask import Blueprint, request

from app.api_utils import standard_response, get_payroll_service

payroll_api_bp = Blueprint("payroll_api", __name__)


# ==================== 工资计算步骤（基于 config JSON） ====================

@payroll_api_bp.route("/payroll/calculation-config", methods=["GET"])
def payroll_calculation_config():
    """返回工资计算步骤配置 JSON（应发/社保公积金/个税三块步骤定义），供前端解析展示。"""
    try:
        config = get_payroll_service().load_calculation_config()
        return standard_response(True, config)
    except Exception as e:
        return standard_response(False, error=str(e), status_code=500)


@payroll_api_bp.route("/payroll/calculation-steps", methods=["GET"])
def payroll_calculation_steps():
    """
    完整工资计算步骤（应发+社保公积金+个税）。公式仅定义在 config JSON 中。
    GET: 从 config JSON 构建，返回三块步骤定义 { gross: [...], social: [...], tax: [...] }
    """
    try:
        data = get_payroll_service().get_calculation_steps_for_display()
        return standard_response(True, data)
    except Exception as e:
        return standard_response(False, error=str(e), status_code=500)


@payroll_api_bp.route("/payroll/calculation-steps/preview", methods=["POST"])
def payroll_calculation_steps_preview():
    """
    按当前周期、人员、公司预览完整工资计算步骤结果（应发+社保公积金+个税；上月带入暂为 0）。
    完全基于 config JSON，由 PayrollService.evaluate_calculation_steps 计算。公式仅来自 config。
    Body: { "person_id": 1, "company_id": 2, "period": "2024-01" }
    """
    try:
        payload = request.get_json() or {}
        person_id = payload.get("person_id")
        company_id = payload.get("company_id")
        period = payload.get("period")
        if not all([person_id, company_id, period]):
            return standard_response(False, error="person_id, company_id, period 为必填", status_code=400)

        service = get_payroll_service()
        result = service.evaluate_calculation_steps(
            int(person_id), int(company_id), str(period)
        )
        return standard_response(True, result)
    except Exception as e:
        return standard_response(False, error=str(e), status_code=500)


# ==================== 已创建工资单列表 ====================

@payroll_api_bp.route("/payroll/records", methods=["GET"])
def payroll_records():
    """
    列出指定周期、公司下已创建的工资单。
    Query: period, company_id
    """
    try:
        period = request.args.get("period")
        company_id = request.args.get("company_id")
        if not period or not company_id:
            return standard_response(False, error="period, company_id 为必填", status_code=400)
        service = get_payroll_service()
        records = service.list_payroll_records(period=str(period), company_id=int(company_id))
        return standard_response(True, records)
    except Exception as e:
        return standard_response(False, error=str(e), status_code=500)


@payroll_api_bp.route("/payroll/record/<int:activity_id>", methods=["GET"])
def payroll_record_detail(activity_id):
    """
    获取单条工资单详情。Query: period
    """
    try:
        period = request.args.get("period")
        if not period:
            return standard_response(False, error="period 为必填", status_code=400)
        service = get_payroll_service()
        record = service.get_payroll_record_detail(activity_id=int(activity_id), period=str(period))
        if record is None:
            return standard_response(False, error="工资单不存在", status_code=404)
        return standard_response(True, record)
    except Exception as e:
        return standard_response(False, error=str(e), status_code=500)


# ==================== 工资单生成（写入 person_company_payroll Twin） ====================

@payroll_api_bp.route("/payroll/generate/preview", methods=["GET"])
def payroll_generate_preview():
    """
    预览将生成工资单的人数（不实际写入）。
    Query: period, company_id, scope=person|department|company[, person_id][, department]
    """
    try:
        period = request.args.get("period")
        company_id = request.args.get("company_id")
        scope = request.args.get("scope", "person")
        person_id = request.args.get("person_id", type=int)
        department = request.args.get("department") or None
        if not period or not company_id:
            return standard_response(False, error="period, company_id 为必填", status_code=400)
        if scope == "person" and not person_id:
            return standard_response(False, error="scope=person 时 person_id 为必填", status_code=400)
        if scope == "department" and not department:
            return standard_response(False, error="scope=department 时 department 为必填", status_code=400)
        service = get_payroll_service()
        count = service.get_generate_preview_count(
            scope=scope,
            company_id=int(company_id),
            person_id=person_id,
            department=department,
        )
        return standard_response(True, {"count": count})
    except Exception as e:
        return standard_response(False, error=str(e), status_code=500)


@payroll_api_bp.route("/payroll/generate", methods=["POST"])
def payroll_generate():
    """
    按范围生成工资单并写入 person_company_payroll Twin。
    Body: { "period": "2025-01", "company_id": 1, "scope": "person"|"department"|"company", "person_id"?: 1, "department"?: "研发部" }
    """
    try:
        payload = request.get_json() or {}
        period = payload.get("period")
        company_id = payload.get("company_id")
        scope = payload.get("scope", "person")
        person_id = payload.get("person_id")
        department = payload.get("department")
        if not period or not company_id:
            return standard_response(False, error="period, company_id 为必填", status_code=400)
        if scope == "person" and not person_id:
            return standard_response(False, error="scope=person 时 person_id 为必填", status_code=400)
        if scope == "department" and not department:
            return standard_response(False, error="scope=department 时 department 为必填", status_code=400)
        service = get_payroll_service()
        result = service.generate_payroll(
            scope=scope,
            company_id=int(company_id),
            period=str(period),
            person_id=int(person_id) if person_id is not None else None,
            department=department,
        )
        return standard_response(True, result)
    except Exception as e:
        return standard_response(False, error=str(e), status_code=500)
