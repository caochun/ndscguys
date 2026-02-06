"""
配置相关 API：可选公司等
"""
from __future__ import annotations

from flask import Blueprint

from app.api_utils import standard_response, get_twin_service
from app.config.companies_config import ensure_companies_in_db

config_api_bp = Blueprint("config_api", __name__)


@config_api_bp.route("/config/companies", methods=["GET"])
def get_selectable_companies():
    """
    返回可选公司列表（来自 config/companies.yaml，并确保已同步到数据库）。
    用于聘用、考勤、缴费等页面的公司下拉。
    """
    try:
        service = get_twin_service()
        ensure_companies_in_db(service)
        all_companies = service.list_twins("company")
        # 只返回当前最新状态为「有效」的公司
        companies = [c for c in all_companies if c.get("status") == "有效"]
        return standard_response(True, companies)
    except Exception as e:
        return standard_response(False, error=str(e), status_code=500)
