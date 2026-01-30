"""
个税税率表加载与计算

从同目录 income_tax_brackets.yaml 加载税率表，
提供根据累计应纳税所得额计算累计个税的函数（累计预扣法适用）。
"""
from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

_CONFIG_DIR = Path(__file__).parent
_BRACKETS_PATH = _CONFIG_DIR / "income_tax_brackets.yaml"
_cached_brackets: Optional[List[Tuple[float, float, float]]] = None


def get_brackets() -> List[Tuple[float, float, float]]:
    """
    加载税率表，返回 [(应纳税所得额上限, 税率, 速算扣除数), ...]。
    最后一档上限为 float('inf')。
    """
    global _cached_brackets
    if _cached_brackets is not None:
        return _cached_brackets
    with open(_BRACKETS_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
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
    with open(_BRACKETS_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("brackets", [])


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
