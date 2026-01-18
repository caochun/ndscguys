"""
Web 路由 - 页面路由
"""
from __future__ import annotations

from flask import Blueprint, render_template

from app.schema.loader import SchemaLoader

web_bp = Blueprint("web", __name__)


@web_bp.route("/")
def index():
    """首页 - 重定向到人员列表"""
    schema_loader = SchemaLoader()
    person_schema = schema_loader.get_twin_schema("person")
    
    if not person_schema:
        person_schema = {}
    
    schema_dict = {
        "name": "person",
        "label": person_schema.get("label", "人员"),
        "fields": person_schema.get("fields", {})
    }
    
    return render_template("persons.html", schema=schema_dict)


@web_bp.route("/persons")
def persons():
    """人员列表页"""
    schema_loader = SchemaLoader()
    person_schema = schema_loader.get_twin_schema("person")
    
    if not person_schema:
        person_schema = {}
    
    # 确保字段存在
    schema_dict = {
        "name": "person",
        "label": person_schema.get("label", "人员"),
        "fields": person_schema.get("fields", {})
    }
    
    return render_template("persons.html", schema=schema_dict)


@web_bp.route("/employments")
def employments():
    """雇佣关系列表页"""
    schema_loader = SchemaLoader()
    employment_schema = schema_loader.get_twin_schema("person_company_employment")
    
    if not employment_schema:
        employment_schema = {}
    
    schema_dict = {
        "name": "person_company_employment",
        "label": employment_schema.get("label", "雇佣关系"),
        "fields": employment_schema.get("fields", {})
    }
    
    return render_template("employments.html", schema=schema_dict)


@web_bp.route("/projects")
def projects():
    """项目列表页"""
    schema_loader = SchemaLoader()
    project_schema = schema_loader.get_twin_schema("project")
    
    if not project_schema:
        project_schema = {}
    
    schema_dict = {
        "name": "project",
        "label": project_schema.get("label", "项目"),
        "fields": project_schema.get("fields", {})
    }
    
    return render_template("projects.html", schema=schema_dict)
