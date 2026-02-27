"""
Twin API 路由 - 统一基于 Twin 的 REST API 接口
"""
from __future__ import annotations

from flask import Blueprint, request

from app.api_utils import standard_response, get_twin_service

twin_api_bp = Blueprint("twin_api", __name__)


# ==================== 统一的 Twin API 接口 ====================

@twin_api_bp.route("/twins/<twin_name>", methods=["GET"])
def list_twins(twin_name: str):
    """
    列出所有指定类型的 Twin（支持过滤和 enrich）
    
    GET /api/twins/<twin_name>?field1=value1&field2=value2&enrich=true
    GET /api/twins/<twin_name>?enrich=person,project
    
    参数：
    - field1, field2, ...: 过滤条件
    - enrich: enrich 参数，支持 "true"（enrich 所有 related_entities）或实体列表（如 "person,project"），仅对 Activity Twin 有效
    """
    try:
        # 从查询参数构建过滤条件
        filters = {}
        enrich = None
        
        for key, value in request.args.items():
            if key == "enrich":
                enrich = value.strip() if value else None
            elif value and value.strip():  # 只添加非空的过滤条件
                filters[key] = value.strip()
        
        service = get_twin_service()
        twins = service.list_twins(
            twin_name, 
            filters=filters if filters else None,
            enrich=enrich
        )
        return standard_response(True, twins)
    except ValueError as e:
        return standard_response(False, error=str(e), status_code=400)
    except Exception as e:
        return standard_response(False, error=str(e), status_code=500)


@twin_api_bp.route("/twins/<twin_name>/<int:twin_id>", methods=["GET"])
def get_twin(twin_name: str, twin_id: int):
    """
    获取指定 Twin 的详情（包含历史）
    
    GET /api/twins/<twin_name>/<twin_id>
    GET /api/twins/<twin_name>/<twin_id>?enrich=person,company  （Activity Twin 可携带 enrich 以返回关联实体名称等）
    """
    try:
        enrich = request.args.get("enrich", "").strip() or None
        service = get_twin_service()
        twin = service.get_twin(twin_name, twin_id, enrich=enrich)
        
        if not twin:
            return standard_response(False, error=f"{twin_name} not found", status_code=404)
        
        return standard_response(True, twin)
    except Exception as e:
        return standard_response(False, error=str(e), status_code=500)


@twin_api_bp.route("/twins/<twin_name>", methods=["POST"])
def create_twin(twin_name: str):
    """
    创建新的 Twin
    
    POST /api/twins/<twin_name>
    Body: JSON 对象，包含字段值
    """
    try:
        data = request.get_json()
        if not data:
            return standard_response(False, error="Request body is required", status_code=400)
        
        service = get_twin_service()
        twin = service.create_twin(twin_name, data)
        
        return standard_response(True, twin, status_code=201)
    except ValueError as e:
        return standard_response(False, error=str(e), status_code=400)
    except Exception as e:
        return standard_response(False, error=str(e), status_code=500)


@twin_api_bp.route("/twins/<twin_name>/<int:twin_id>", methods=["DELETE"])
def delete_twin(twin_name: str, twin_id: int):
    """
    删除 Twin 及其所有历史状态

    DELETE /api/twins/<twin_name>/<twin_id>
    """
    try:
        service = get_twin_service()
        deleted = service.delete_twin(twin_name, twin_id)

        if not deleted:
            return standard_response(False, error=f"{twin_name} not found", status_code=404)

        return standard_response(True, {"id": twin_id, "deleted": True})
    except ValueError as e:
        return standard_response(False, error=str(e), status_code=400)
    except Exception as e:
        return standard_response(False, error=str(e), status_code=500)

@twin_api_bp.route("/twins/<twin_name>/<int:twin_id>", methods=["PUT"])
def update_twin(twin_name: str, twin_id: int):
    """
    更新 Twin 状态（追加新状态）

    PUT /api/twins/<twin_name>/<twin_id>
    Body: JSON 对象，包含要更新的字段值
    """
    try:
        data = request.get_json()
        if not data:
            return standard_response(False, error="Request body is required", status_code=400)
        
        service = get_twin_service()
        twin = service.update_twin(twin_name, twin_id, data)
        
        return standard_response(True, twin)
    except ValueError as e:
        return standard_response(False, error=str(e), status_code=400)
    except Exception as e:
        return standard_response(False, error=str(e), status_code=500)
