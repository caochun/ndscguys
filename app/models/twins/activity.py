"""
Activity Twin - 活动孪生
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional
from datetime import datetime

from .base import Twin, TwinType


@dataclass
class ActivityTwin(Twin):
    """Activity Twin - 代表现实世界中的活动（打卡、发薪、聘用等）"""
    
    # 关联的 Entity Twin ID（存储在 related_entity_ids 中）
    related_entity_ids: Dict[str, int] = field(default_factory=dict)  # {"person_id": 1, "company_id": 2}
    
    def __post_init__(self):
        """确保 twin_type 是 ACTIVITY"""
        super().__post_init__()
        if self.twin_type != TwinType.ACTIVITY:
            self.twin_type = TwinType.ACTIVITY
    
    def get_entity_id(self, role: str) -> Optional[int]:
        """根据 role 获取关联的 Entity ID"""
        key = f"{role}_id"
        return self.related_entity_ids.get(key)
