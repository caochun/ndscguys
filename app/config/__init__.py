"""
应用配置：工资/个税相关 YAML 配置及加载逻辑

- YAML：税率表、岗位比例、员工折算、考核系数、社保公积金等
- 加载器：payroll_config（含税率表 get_brackets / calculate_tax / get_brackets_for_display）
"""
from app.config.payroll_config import (
    get_brackets,
    calculate_tax,
    get_brackets_for_display,
    get_position_salary_ratio,
    get_employee_type_discount,
    get_assessment_grade_coefficient,
    get_social_security_config,
)

__all__ = [
    "get_brackets",
    "calculate_tax",
    "get_brackets_for_display",
    "get_position_salary_ratio",
    "get_employee_type_discount",
    "get_assessment_grade_coefficient",
    "get_social_security_config",
]
