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


def build_schema_dict(
    twin_name: str, default_label: Optional[str] = None
) -> Dict[str, Any]:
    """构建 schema 字典，用于传递给前端模板"""
    twin_schema = _schema_loader.get_twin_schema(twin_name)
    if not twin_schema:
        twin_schema = {}
    return {
        "name": twin_name,
        "label": twin_schema.get("label", default_label or twin_name),
        "fields": twin_schema.get("fields", {})
    }


def _project_payment_schema() -> dict:
    """返回带 related_entities 的 project_payment_schema"""
    schema = build_schema_dict("internal_project_payment", "内部项目-款项关联")
    twin = _schema_loader.get_twin_schema("internal_project_payment")
    if twin:
        schema["related_entities"] = twin.get("related_entities", [])
    return schema


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


@web_bp.route("/assessments")
def assessments():
    """考核列表页"""
    schema_dict = build_schema_dict("person_assessment", "考核")
    return render_template("assessments.html", schema=schema_dict)


@web_bp.route("/attendance-records")
def attendance_records():
    """考勤记录列表页"""
    schema_dict = build_schema_dict("person_company_attendance", "考勤记录")
    return render_template("attendance_records.html", schema=schema_dict)


@web_bp.route("/contributions")
def contributions():
    """缴费与专项附加扣除汇总页（Tab 视图）"""
    social_schema = build_schema_dict(
        "person_company_social_security_base", "社保基数"
    )
    housing_schema = build_schema_dict(
        "person_company_housing_fund_base", "公积金基数"
    )
    tax_schema = build_schema_dict(
        "person_tax_deduction", "专项附加扣除年度累计"
    )
    return render_template(
        "contributions.html",
        social_schema=social_schema,
        housing_schema=housing_schema,
        tax_schema=tax_schema,
    )


@web_bp.route("/payroll")
def payroll_calculation_page():
    """工资管理页 - 应发、社保公积金、个税三步块与步骤预览"""
    return render_template("payroll.html")


@web_bp.route("/internal-projects")
def internal_projects():
    """内部项目管理页"""
    schema_dict = build_schema_dict("internal_project", "内部项目")
    return render_template("internal_projects.html", schema=schema_dict)


@web_bp.route("/client-contracts")
def client_contracts():
    """客户合同管理页"""
    schema_dict = build_schema_dict("client_contract", "客户合同")
    return render_template("client_contracts.html", schema=schema_dict)


@web_bp.route("/payment-items")
def payment_items():
    """款项管理页"""
    payment_item_schema = build_schema_dict("payment_item", "款项")
    project_payment_schema = _project_payment_schema()
    person_payment_schema = build_schema_dict(
        "person_payment_participation", "人员-款项参与"
    )
    return render_template(
        "payment_items.html",
        payment_item_schema=payment_item_schema,
        project_payment_schema=project_payment_schema,
        person_payment_schema=person_payment_schema,
    )


@web_bp.route("/config")
def config_page():
    """配置页（只读，展示 app/config 下所有配置项）"""
    from datetime import datetime
    from app.config.payroll_config import get_brackets_for_display
    from app.config.payroll_config import (
        get_all_position_salary_ratio,
        get_all_employee_type_discount,
        get_all_assessment_grade_coefficient,
        get_all_social_security_config,
        get_social_security_config,
    )
    period = datetime.now().strftime("%Y-%m")
    return render_template(
        "config.html",
        tax_brackets=get_brackets_for_display(),
        position_salary_ratio=get_all_position_salary_ratio(),
        employee_type_discount=get_all_employee_type_discount(),
        assessment_grade_coefficient=get_all_assessment_grade_coefficient(),
        social_security_list=get_all_social_security_config(),
        social_security_current=get_social_security_config(period),
        period=period,
    )


@web_bp.route("/analytics")
def analytics():
    """经营分析页"""
    return render_template("analytics.html")


@web_bp.route("/project")
def project():
    """项目管理 - 统一管理合同、项目、款项"""
    payment_item_schema = build_schema_dict("payment_item", "款项")
    contract_schema = build_schema_dict("client_contract", "客户合同")
    project_schema = build_schema_dict("internal_project", "内部项目")
    project_payment_schema = _project_payment_schema()
    person_payment_schema = build_schema_dict(
        "person_payment_participation", "人员-款项参与"
    )
    return render_template(
        "project.html",
        payment_item_schema=payment_item_schema,
        contract_schema=contract_schema,
        project_schema=project_schema,
        project_payment_schema=project_payment_schema,
        person_payment_schema=person_payment_schema,
    )
