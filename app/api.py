"""
API 路由 - REST API 端点
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


@api_bp.route("/persons", methods=["GET"])
def list_persons():
    """获取人员列表"""
    try:
        service = get_twin_service()
        persons = service.list_twins("person")
        return jsonify({
            "success": True,
            "data": persons,
            "count": len(persons)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route("/persons/<int:person_id>", methods=["GET"])
def get_person(person_id: int):
    """获取人员详情"""
    try:
        service = get_twin_service()
        person = service.get_twin("person", person_id)
        
        if not person:
            return jsonify({
                "success": False,
                "error": "Person not found"
            }), 404
        
        return jsonify({
            "success": True,
            "data": person
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


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
            
            # 添加人员信息（只添加姓名，联系方式在详情中显示）
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
        
        return jsonify({
            "success": True,
            "data": enriched_employments,
            "count": len(enriched_employments)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route("/employments/<int:employment_id>", methods=["GET"])
def get_employment(employment_id: int):
    """获取雇佣关系详情"""
    try:
        service = get_twin_service()
        employment = service.get_twin("person_company_employment", employment_id)
        
        if not employment:
            return jsonify({
                "success": False,
                "error": "Employment not found"
            }), 404
        
        return jsonify({
            "success": True,
            "data": employment
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


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
            return jsonify({
                "success": False,
                "error": "Person not found"
            }), 404
        
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
        
        return jsonify({
            "success": True,
            "data": {
                "person": person["current"],
                "employments": enriched_employments
            },
            "count": len(enriched_employments)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500




@api_bp.route("/projects", methods=["GET"])
def list_projects():
    """获取项目列表"""
    try:
        service = get_twin_service()
        projects = service.list_twins("project")
        return jsonify({
            "success": True,
            "data": projects,
            "count": len(projects)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route("/projects/<int:project_id>", methods=["GET"])
def get_project(project_id: int):
    """获取项目详情（包含参与人员信息）"""
    try:
        service = get_twin_service()
        project = service.get_twin("project", project_id)
        
        if not project:
            return jsonify({
                "success": False,
                "error": "Project not found"
            }), 404
        
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
        
        return jsonify({
            "success": True,
            "data": project
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route("/projects/<int:project_id>/persons/<int:person_id>/participations", methods=["GET"])
def get_person_project_participations(project_id: int, person_id: int):
    """获取指定人员在指定项目中的所有参与记录"""
    try:
        service = get_twin_service()
        
        # 获取该人员在项目中的所有参与记录
        filters = {"project_id": project_id, "person_id": person_id}
        participations = service.list_twins("person_project_participation", filters=filters)
        
        # 获取人员信息
        person = service.get_twin("person", person_id)
        if not person:
            return jsonify({
                "success": False,
                "error": "Person not found"
            }), 404
        
        # 获取项目信息
        project = service.get_twin("project", project_id)
        if not project:
            return jsonify({
                "success": False,
                "error": "Project not found"
            }), 404
        
        # 获取每个参与活动的完整历史记录
        enriched_participations = []
        for part in participations:
            # 获取该参与活动的完整历史
            activity_id = part.get("id")
            if activity_id:
                activity_detail = service.get_twin("person_project_participation", activity_id)
                if activity_detail:
                    enriched_participations.append({
                        "activity_id": activity_id,
                        "history": activity_detail.get("history", []),
                        "current": activity_detail.get("current", {})
                    })
        
        # 获取相关 schema
        schema_loader = SchemaLoader()
        person_schema = schema_loader.get_twin_schema("person")
        project_schema = schema_loader.get_twin_schema("project")
        participation_schema = schema_loader.get_twin_schema("person_project_participation")
        
        return jsonify({
            "success": True,
            "data": {
                "person": person["current"],
                "project": project["current"],
                "participations": enriched_participations,
                "schemas": {
                    "person": {
                        "name": "person",
                        "label": person_schema.get("label", "人员") if person_schema else "人员",
                        "fields": person_schema.get("fields", {}) if person_schema else {}
                    },
                    "project": {
                        "name": "project",
                        "label": project_schema.get("label", "项目") if project_schema else "项目",
                        "fields": project_schema.get("fields", {}) if project_schema else {}
                    },
                    "participation": {
                        "name": "person_project_participation",
                        "label": participation_schema.get("label", "参与活动") if participation_schema else "参与活动",
                        "fields": participation_schema.get("fields", {}) if participation_schema else {}
                    }
                }
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


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
        
        return jsonify({
            "success": True,
            "data": result_list,
            "count": len(result_list)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
