"""
Twin State - Twin 的状态记录
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime

from .base import TwinType


class StateStreamMode:
    """状态流模式"""
    VERSIONED = "versioned"  # 版本化状态流
    TIME_SERIES = "time_series"  # 时间序列状态流


@dataclass
class TwinState:
    """Twin 的状态记录"""
    
    twin_id: int
    twin_type: TwinType
    twin_name: str
    ts: str  # 时间戳
    data: Dict[str, Any]  # 状态数据（JSON）
    version: Optional[int] = None  # 版本化状态流使用
    time_key: Optional[str] = None  # 时间序列状态流使用（如 date, batch_period）
    
    def __post_init__(self):
        """确保 twin_type 是 TwinType 枚举"""
        if isinstance(self.twin_type, str):
            self.twin_type = TwinType(self.twin_type)
    
    @classmethod
    def from_row(cls, row, twin_name: str, twin_type: TwinType) -> "TwinState":
        """从数据库行创建 TwinState"""
        import json
        
        # 确保 row 是字典
        if not isinstance(row, dict):
            row = dict(row)
        
        data = row.get("data")
        if isinstance(data, str):
            data = json.loads(data)
        elif data is None:
            data = {}
        
        return cls(
            twin_id=row["twin_id"],
            twin_type=twin_type,
            twin_name=twin_name,
            version=row.get("version"),
            time_key=row.get("time_key"),
            ts=row["ts"],
            data=data,
        )
    
    def to_record(self) -> Dict[str, Any]:
        """转换为数据库记录"""
        import json
        
        record = {
            "twin_id": self.twin_id,
            "ts": self.ts,
            "data": json.dumps(self.data, ensure_ascii=False),
        }
        
        if self.version is not None:
            record["version"] = self.version
        
        if self.time_key is not None:
            record["time_key"] = self.time_key
        
        return record
