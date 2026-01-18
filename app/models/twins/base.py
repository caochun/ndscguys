"""
Twin 基类 - 所有 Entity 和 Activity 都是 Twin
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime


class TwinType(str, Enum):
    """Twin 类型"""
    ENTITY = "entity"
    ACTIVITY = "activity"


@dataclass
class Twin:
    """Twin 基类 - 代表对现实世界的抽象"""
    
    twin_id: int
    twin_type: TwinType
    twin_name: str  # Schema 中定义的名称，如 "person", "person_company_employment"
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """确保 twin_type 是 TwinType 枚举"""
        if isinstance(self.twin_type, str):
            self.twin_type = TwinType(self.twin_type)
