"""
API 公共工具：标准响应、Service/Loader 获取

供 twin_api、payroll_api 统一使用，避免重复定义。
"""
from __future__ import annotations

from flask import jsonify
from typing import Optional, Any

from app.root_config import Config
from app.services.twin_service import TwinService
from app.services.payroll_service import PayrollService


def standard_response(
    success: bool,
    data: Any = None,
    error: Optional[str] = None,
    status_code: int = 200,
):
    """标准 API 响应格式"""
    response: dict = {"success": success}
    if data is not None:
        response["data"] = data
    if error:
        response["error"] = error
    if isinstance(data, list):
        response["count"] = len(data)
    return jsonify(response), status_code


def get_twin_service(db_path: Optional[str] = None) -> TwinService:
    """获取 TwinService 实例"""
    if db_path is None:
        db_path = str(Config.DATABASE_PATH)
    return TwinService(db_path=db_path)


def get_payroll_service(db_path: Optional[str] = None) -> PayrollService:
    """获取 PayrollService 实例"""
    if db_path is None:
        db_path = str(Config.DATABASE_PATH)
    return PayrollService(db_path=db_path)
