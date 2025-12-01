"""
人员考核状态（A-E）
"""
from __future__ import annotations

from .state import PersonState

# 语义化别名：底层仍使用通用 PersonState
PersonAssessmentState = PersonState

__all__ = ["PersonAssessmentState"]


