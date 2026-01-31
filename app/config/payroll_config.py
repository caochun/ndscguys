"""
工资相关配置加载（从同目录 *.yaml，不保存历史版本）

含：岗位比例、员工折算、考核系数、社保公积金、个税税率表（income_tax_brackets.yaml）
及根据累计应纳税所得额计算累计个税（累计预扣法）。
"""
from __future__ import annotations

import logging
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

_CONFIG_DIR = Path(__file__).parent
_log = logging.getLogger(__name__)

# 配置文件路径（统一定义）
_POSITION_SALARY_RATIO_PATH = _CONFIG_DIR / "position_salary_ratio.yaml"
_EMPLOYEE_TYPE_DISCOUNT_PATH = _CONFIG_DIR / "employee_type_discount.yaml"
_ASSESSMENT_GRADE_COEFFICIENT_PATH = _CONFIG_DIR / "assessment_grade_coefficient.yaml"
_SOCIAL_SECURITY_CONFIG_PATH = _CONFIG_DIR / "social_security_config.yaml"
_BRACKETS_PATH = _CONFIG_DIR / "income_tax_brackets.yaml"

# 简单缓存，避免重复读文件
_position_ratio: Optional[Dict[str, Dict[str, Any]]] = None
_employee_discount: Optional[Dict[str, float]] = None
_grade_coefficient: Optional[Dict[str, float]] = None
_social_config_list: Optional[List[Dict[str, Any]]] = None
_cached_brackets: Optional[List[Tuple[float, float, float]]] = None


def _load_yaml(path: Path, *, raise_on_error: bool = False) -> dict:
    """加载 YAML 文件。默认失败时打日志并返回空 dict；raise_on_error=True 时抛出异常。"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            return data
    except FileNotFoundError:
        if raise_on_error:
            _log.error("配置文件不存在: %s", path)
            raise FileNotFoundError(f"配置文件不存在: {path}") from None
        _log.warning("配置文件不存在: %s", path)
        return {}
    except yaml.YAMLError as e:
        if raise_on_error:
            _log.error("配置 YAML 解析失败 %s: %s", path, e)
            raise ValueError(f"配置 YAML 格式错误: {e}") from e
        _log.warning("配置 YAML 解析失败 %s: %s", path, e)
        return {}


def get_position_salary_ratio(position_category: Optional[str]) -> Optional[Dict[str, Any]]:
    """按岗位类别查基础/绩效划分比例"""
    if not position_category:
        return None
    global _position_ratio
    if _position_ratio is None:
        data = _load_yaml(_POSITION_SALARY_RATIO_PATH)
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
        data = _load_yaml(_EMPLOYEE_TYPE_DISCOUNT_PATH)
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
        data = _load_yaml(_ASSESSMENT_GRADE_COEFFICIENT_PATH)
        _grade_coefficient = {
            str(item["grade"]): float(item.get("coefficient", 1.0))
            for item in data.get("items", [])
        }
    return _grade_coefficient.get(str(grade), 1.0)


def _period_end_str(period: str) -> str:
    """period 如 '2025-01' -> 周期末次日 '2025-02-01'（用于 effective_date 比较）"""
    try:
        period_date = datetime.strptime(period + "-01", "%Y-%m-%d").date()
        if period_date.month == 12:
            period_end = datetime(period_date.year + 1, 1, 1).date()
        else:
            period_end = datetime(period_date.year, period_date.month + 1, 1).date()
        return period_end.strftime("%Y-%m-%d")
    except ValueError:
        return "9999-12-31"


def get_social_security_config(period: str) -> Optional[Dict[str, Any]]:
    """获取发放周期适用的社保公积金配置（effective_date 不晚于周期末的最新一条）"""
    global _social_config_list
    if _social_config_list is None:
        _social_config_list = _load_items(_SOCIAL_SECURITY_CONFIG_PATH)
    if not _social_config_list:
        return None
    period_end_str = _period_end_str(period)
    valid = [
        c for c in _social_config_list
        if (c.get("effective_date") or "") <= period_end_str
    ]
    if not valid:
        return None
    return max(valid, key=lambda c: c.get("effective_date") or "")


def _load_items(path: Path) -> List[Dict[str, Any]]:
    """加载 YAML 中 items 列表，用于配置页展示。失败返回 []。"""
    return _load_yaml(path).get("items", [])


def get_all_position_salary_ratio() -> List[Dict[str, Any]]:
    """返回岗位薪资结构配置完整列表，用于配置页展示"""
    return _load_items(_POSITION_SALARY_RATIO_PATH)


def get_all_employee_type_discount() -> List[Dict[str, Any]]:
    """返回员工类别折算配置完整列表，用于配置页展示"""
    return _load_items(_EMPLOYEE_TYPE_DISCOUNT_PATH)


def get_all_assessment_grade_coefficient() -> List[Dict[str, Any]]:
    """返回考核等级绩效系数配置完整列表，用于配置页展示"""
    return _load_items(_ASSESSMENT_GRADE_COEFFICIENT_PATH)


def get_all_social_security_config() -> List[Dict[str, Any]]:
    """返回社保公积金配置完整列表，用于配置页展示"""
    return _load_items(_SOCIAL_SECURITY_CONFIG_PATH)


# -------- 个税税率表（income_tax_brackets.yaml）--------


def _load_brackets_raw() -> dict:
    """加载税率表 YAML 原始数据，失败时抛出异常（计算依赖有效数据）"""
    data = _load_yaml(_BRACKETS_PATH, raise_on_error=True)
    if not data:
        raise ValueError("税率表文件为空或无效")
    return data


def get_brackets() -> List[Tuple[float, float, float]]:
    """
    加载税率表，返回 [(应纳税所得额上限, 税率, 速算扣除数), ...]。
    最后一档上限为 float('inf')。
    """
    global _cached_brackets
    if _cached_brackets is not None:
        return _cached_brackets
    data = _load_brackets_raw()
    rows = data.get("brackets", [])
    result = []
    for row in rows:
        upper = row.get("income_upper")
        if upper is None:
            upper = float("inf")
        else:
            upper = float(upper)
        rate = float(row.get("rate", 0))
        quick = float(row.get("quick_deduction", 0))
        result.append((upper, rate, quick))
    _cached_brackets = result
    return result


def get_brackets_for_display() -> List[Dict[str, Any]]:
    """加载税率表原始列表，用于配置页展示（含 level、income_upper、rate、quick_deduction）"""
    try:
        data = _load_brackets_raw()
        return data.get("brackets", [])
    except (FileNotFoundError, ValueError, yaml.YAMLError):
        return []


def calculate_tax(taxable_income: float) -> float:
    """
    根据应纳税所得额（累计或全年）计算税额。
    公式：税额 = 应纳税所得额 × 税率 − 速算扣除数。
    适用于累计预扣法中的「累计个税」计算。
    """
    if taxable_income <= 0:
        return 0.0
    for upper, rate, quick in get_brackets():
        if taxable_income <= upper:
            return round(taxable_income * rate - quick, 2)
    return 0.0
