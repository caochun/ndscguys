"""
工资相关配置加载（从同目录 *.yaml，不保存历史版本）
"""
from __future__ import annotations

import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

_CONFIG_DIR = Path(__file__).parent

# 简单缓存，避免重复读文件
_position_ratio: Optional[Dict[str, Dict[str, Any]]] = None
_employee_discount: Optional[Dict[str, float]] = None
_grade_coefficient: Optional[Dict[str, float]] = None
_social_config_list: Optional[List[Dict[str, Any]]] = None


def get_position_salary_ratio(position_category: Optional[str]) -> Optional[Dict[str, Any]]:
    """按岗位类别查基础/绩效划分比例"""
    if not position_category:
        return None
    global _position_ratio
    if _position_ratio is None:
        path = _CONFIG_DIR / "position_salary_ratio.yaml"
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        _position_ratio = {
            item["position_category"]: {
                "base_ratio": float(item.get("base_ratio", 0.7)),
                "performance_ratio": float(item.get("performance_ratio", 0.3)),
            }
            for item in data.get("items", [])
        }
    return _position_ratio.get(position_category)


def get_employee_type_discount(employee_type: Optional[str]) -> float:
    """按员工类别查折算系数，默认 1.0"""
    if not employee_type:
        return 1.0
    global _employee_discount
    if _employee_discount is None:
        path = _CONFIG_DIR / "employee_type_discount.yaml"
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        _employee_discount = {
            item["employee_type"]: float(item.get("discount_ratio", 1.0))
            for item in data.get("items", [])
        }
    return _employee_discount.get(employee_type, 1.0)


def get_assessment_grade_coefficient(grade: Optional[str]) -> float:
    """按考核等级查绩效系数，默认 1.0"""
    if not grade:
        return 1.0
    global _grade_coefficient
    if _grade_coefficient is None:
        path = _CONFIG_DIR / "assessment_grade_coefficient.yaml"
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        _grade_coefficient = {
            str(item["grade"]): float(item.get("coefficient", 1.0))
            for item in data.get("items", [])
        }
    return _grade_coefficient.get(str(grade), 1.0)


def get_social_security_config(period: str) -> Optional[Dict[str, Any]]:
    """获取发放周期适用的社保公积金配置（effective_date 不晚于周期末的最新一条）"""
    global _social_config_list
    if _social_config_list is None:
        path = _CONFIG_DIR / "social_security_config.yaml"
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        _social_config_list = data.get("items", [])
    if not _social_config_list:
        return None
    # 周期末：period 如 "2025-01" -> 2025-01-31 的次日 00:00 即 2025-02-01
    try:
        period_date = datetime.strptime(period + "-01", "%Y-%m-%d").date()
        if period_date.month == 12:
            period_end = datetime(period_date.year + 1, 1, 1).date()
        else:
            period_end = datetime(period_date.year, period_date.month + 1, 1).date()
        period_end_str = period_end.strftime("%Y-%m-%d")
    except ValueError:
        period_end_str = "9999-12-31"
    valid = [
        c for c in _social_config_list
        if (c.get("effective_date") or "") <= period_end_str
    ]
    if not valid:
        return None
    return max(valid, key=lambda c: c.get("effective_date") or "")


def get_all_position_salary_ratio() -> List[Dict[str, Any]]:
    """返回岗位薪资结构配置完整列表，用于配置页展示"""
    path = _CONFIG_DIR / "position_salary_ratio.yaml"
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("items", [])


def get_all_employee_type_discount() -> List[Dict[str, Any]]:
    """返回员工类别折算配置完整列表，用于配置页展示"""
    path = _CONFIG_DIR / "employee_type_discount.yaml"
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("items", [])


def get_all_assessment_grade_coefficient() -> List[Dict[str, Any]]:
    """返回考核等级绩效系数配置完整列表，用于配置页展示"""
    path = _CONFIG_DIR / "assessment_grade_coefficient.yaml"
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("items", [])


def get_all_social_security_config() -> List[Dict[str, Any]]:
    """返回社保公积金配置完整列表，用于配置页展示"""
    path = _CONFIG_DIR / "social_security_config.yaml"
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("items", [])
