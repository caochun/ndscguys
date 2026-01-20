"""
Web 路由 - 页面路由
"""
from __future__ import annotations

from flask import Blueprint, render_template
from typing import Dict, Any, Optional

from app.schema.loader import SchemaLoader

web_bp = Blueprint("web", __name__)

# 共享的 SchemaLoader 实例（避免重复创建）
_schema_loader = SchemaLoader()


def build_schema_dict(twin_name: str, default_label: Optional[str] = None) -> Dict[str, Any]:
    """
    构建 schema 字典，用于传递给前端模板
    
    Args:
        twin_name: Twin 名称
        default_label: 默认标签（如果 schema 中没有定义）
    
    Returns:
        schema 字典，包含 name、label、fields
    """
    twin_schema = _schema_loader.get_twin_schema(twin_name)
    
    if not twin_schema:
        twin_schema = {}
    
    return {
        "name": twin_name,
        "label": twin_schema.get("label", default_label or twin_name),
        "fields": twin_schema.get("fields", {})
    }


@web_bp.route("/")
def index():
    """首页 - 重定向到人员列表"""
    schema_dict = build_schema_dict("person", "人员")
    return render_template("persons.html", schema=schema_dict)


@web_bp.route("/persons")
def persons():
    """人员列表页"""
    schema_dict = build_schema_dict("person", "人员")
    return render_template("persons.html", schema=schema_dict)


@web_bp.route("/employments")
def employments():
    """聘用管理列表页"""
    schema_dict = build_schema_dict("person_company_employment", "聘用管理")
    return render_template("employments.html", schema=schema_dict)


@web_bp.route("/projects")
def projects():
    """项目列表页"""
    schema_dict = build_schema_dict("project", "项目")
    participation_schema_dict = build_schema_dict("person_project_participation", "人员项目参与")
    
    # 添加 related_entities（仅对 participation schema）
    participation_schema = _schema_loader.get_twin_schema("person_project_participation")
    if participation_schema:
        participation_schema_dict["related_entities"] = participation_schema.get("related_entities", [])
    
    return render_template("projects.html", schema=schema_dict, participation_schema=participation_schema_dict)


@web_bp.route("/assessments")
def assessments():
    """考核列表页"""
    schema_dict = build_schema_dict("person_assessment", "考核")
    return render_template("assessments.html", schema=schema_dict)


@web_bp.route("/social-bases")
def social_bases():
    """社保基数列表页"""
    schema_dict = build_schema_dict("person_company_social_security_base", "社保基数")
    return render_template("social_bases.html", schema=schema_dict)


@web_bp.route("/housing-fund-bases")
def housing_fund_bases():
    """公积金基数列表页"""
    schema_dict = build_schema_dict("person_company_housing_fund_base", "公积金基数")
    return render_template("housing_fund_bases.html", schema=schema_dict)


@web_bp.route("/tax-deductions")
def tax_deductions():
    """专项附加扣除列表页"""
    schema_dict = build_schema_dict("person_tax_deduction", "专项附加扣除")
    return render_template("tax_deductions.html", schema=schema_dict)


@web_bp.route("/contributions")
def contributions():
    """缴费与专项附加扣除汇总页（Tab 视图）"""
    social_schema = build_schema_dict("person_company_social_security_base", "社保基数")
    housing_schema = build_schema_dict("person_company_housing_fund_base", "公积金基数")
    tax_schema = build_schema_dict("person_tax_deduction", "专项附加扣除")
    return render_template("contributions.html", 
                          social_schema=social_schema,
                          housing_schema=housing_schema,
                          tax_schema=tax_schema)


@web_bp.route("/payroll")
def payroll():
    """工资管理页"""
    schema_dict = build_schema_dict("person_company_payroll", "工资管理")
    return render_template("payroll.html", schema=schema_dict)
