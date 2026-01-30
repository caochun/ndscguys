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
