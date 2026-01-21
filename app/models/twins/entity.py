"""
Entity Twin - 实体孪生
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from .base import Twin, TwinType


@dataclass
class EntityTwin(Twin):
    """Entity Twin - 代表现实世界中的实体（Person, Company, Project 等）"""
    
    def __init__(
        self,
        twin_id: int,
        twin_name: str,
        created_at: Optional[datetime] = None,
    ):
        super().__init__(
            twin_id=twin_id,
            twin_type=TwinType.ENTITY,
            twin_name=twin_name,
            created_at=created_at,
        )
