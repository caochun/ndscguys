"""
API 路由 - REST API 端点
统一基于 Twin 的 API 接口
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request
from typing import Optional

from app.services.twin_service import TwinService
from app.schema.loader import SchemaLoader
from config import Config

api_bp = Blueprint("api", __name__)


def get_twin_service() -> TwinService:
    """获取 TwinService 实例"""
    return TwinService(db_path=str(Config.DATABASE_PATH))


def get_schema_loader() -> SchemaLoader:
    """获取 SchemaLoader 实例"""
    return SchemaLoader()


def standard_response(success: bool, data=None, error: str = None, status_code: int = 200):
    """标准响应格式"""
    response = {"success": success}
    if data is not None:
        response["data"] = data
    if error:
        response["error"] = error
    if isinstance(data, list):
        response["count"] = len(data)
    return jsonify(response), status_code


# ==================== 统一的 Twin API 接口 ====================

@api_bp.route("/twins/<twin_name>", methods=["GET"])
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


@api_bp.route("/twins/<twin_name>/<int:twin_id>", methods=["GET"])
def get_twin(twin_name: str, twin_id: int):
    """
    获取指定 Twin 的详情（包含历史）
    
    GET /api/twins/<twin_name>/<twin_id>
    """
    try:
        service = get_twin_service()
        twin = service.get_twin(twin_name, twin_id)
        
        if not twin:
            return standard_response(False, error=f"{twin_name} not found", status_code=404)
        
        return standard_response(True, twin)
    except Exception as e:
        return standard_response(False, error=str(e), status_code=500)


@api_bp.route("/twins/<twin_name>", methods=["POST"])
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


@api_bp.route("/twins/<twin_name>/<int:twin_id>", methods=["PUT"])
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


# ==================== 特殊业务端点（数据增强和复杂查询）====================

@api_bp.route("/projects/<int:project_id>", methods=["GET"])
def get_project(project_id: int):
    """获取项目详情（包含参与人员信息）"""
    try:
        service = get_twin_service()
        project = service.get_twin("project", project_id)
        
        if not project:
            return standard_response(False, error="Project not found", status_code=404)
        
        # 获取该项目的所有参与人员
        filters = {"project_id": project_id}
        participations = service.list_twins("person_project_participation", filters=filters)
        
        # 获取所有人员信息用于关联
        persons = service.list_twins("person")
        person_map = {p["id"]: p for p in persons}
        
        # 合并参与人员信息
        enriched_participations = []
        for part in participations:
            enriched = {**part}
            
            # 添加人员信息
            person_id = part.get("person_id")
            if person_id and person_id in person_map:
                person = person_map[person_id]
                enriched["person_name"] = person.get("name", "")
                enriched["person_phone"] = person.get("phone", "")
            
            enriched_participations.append(enriched)
        
        # 将参与人员信息添加到项目数据中
        project["participations"] = enriched_participations
        
        return standard_response(True, project)
    except Exception as e:
        return standard_response(False, error=str(e), status_code=500)


@api_bp.route("/employments", methods=["GET"])
def list_employments():
    """获取雇佣关系列表（包含关联的人员和公司信息）"""
    try:
        service = get_twin_service()
        employments = service.list_twins("person_company_employment")
        
        # 获取所有人员和公司信息用于关联
        persons = service.list_twins("person")
        companies = service.list_twins("company")
        
        # 构建映射表
        person_map = {p["id"]: p for p in persons}
        company_map = {c["id"]: c for c in companies}
        
        # 合并关联数据
        enriched_employments = []
        for emp in employments:
            enriched = {**emp}
            
            # 添加人员信息
            person_id = emp.get("person_id")
            if person_id and person_id in person_map:
                person = person_map[person_id]
                enriched["person_name"] = person.get("name", "")
            
            # 添加公司信息
            company_id = emp.get("company_id")
            if company_id and company_id in company_map:
                company = company_map[company_id]
                enriched["company_name"] = company.get("name", "")
            
            enriched_employments.append(enriched)
        
        return standard_response(True, enriched_employments)
    except Exception as e:
        return standard_response(False, error=str(e), status_code=500)

@api_bp.route("/persons/<int:person_id>/employments", methods=["GET"])
def get_person_employments(person_id: int):
    """获取指定人员的所有雇佣关系（包含关联的公司信息）"""
    try:
        service = get_twin_service()
        filters = {"person_id": person_id}
        employments = service.list_twins("person_company_employment", filters=filters)
        
        # 获取人员信息
        person = service.get_twin("person", person_id)
        if not person:
            return standard_response(False, error="Person not found", status_code=404)
        
        # 获取所有公司信息用于关联
        companies = service.list_twins("company")
        company_map = {c["id"]: c for c in companies}
        
        # 合并关联数据
        enriched_employments = []
        for emp in employments:
            enriched = {**emp}
            
            # 添加人员信息
            enriched["person_name"] = person["current"].get("name", "")
            enriched["person_phone"] = person["current"].get("phone", "")
            enriched["person_email"] = person["current"].get("email", "")
            
            # 添加公司信息
            company_id = emp.get("company_id")
            if company_id and company_id in company_map:
                company = company_map[company_id]
                enriched["company_name"] = company.get("name", "")
            
            enriched_employments.append(enriched)
        
        return standard_response(True, {
            "person": person["current"],
            "employments": enriched_employments
        })
    except Exception as e:
        return standard_response(False, error=str(e), status_code=500)


@api_bp.route("/person-project-status", methods=["GET"])
def get_person_project_status():
    """获取所有人员在项目中的参与状态（每个人员的最新状态）"""
    try:
        service = get_twin_service()
        
        # 获取所有参与记录
        participations = service.list_twins("person_project_participation")
        
        # 获取所有人员和项目信息
        persons = service.list_twins("person")
        projects = service.list_twins("project")
        
        person_map = {p["id"]: p for p in persons}
        project_map = {p["id"]: p for p in projects}
        
        # 按 person_id 和 project_id 分组，获取每个人员-项目组合的最新状态
        person_project_map = {}
        for part in participations:
            person_id = part.get("person_id")
            project_id = part.get("project_id")
            change_date = part.get("change_date", "")
            
            key = (person_id, project_id)
            if key not in person_project_map:
                person_project_map[key] = part
            else:
                # 保留最新的记录
                existing_date = person_project_map[key].get("change_date", "")
                if change_date > existing_date:
                    person_project_map[key] = part
        
        # 转换为列表并添加关联信息
        result_list = []
        for (person_id, project_id), part in person_project_map.items():
            enriched = {**part}
            
            # 添加人员信息
            if person_id in person_map:
                person = person_map[person_id]
                enriched["person_name"] = person.get("name", "")
                enriched["person_phone"] = person.get("phone", "")
                enriched["person_email"] = person.get("email", "")
            
            # 添加项目信息
            if project_id in project_map:
                project = project_map[project_id]
                enriched["project_name"] = project.get("internal_project_name", "")
                enriched["project_code"] = project.get("project_code", "")
                enriched["project_type"] = project.get("project_type", "")
            
            result_list.append(enriched)
        
        return standard_response(True, result_list)
    except Exception as e:
        return standard_response(False, error=str(e), status_code=500)
