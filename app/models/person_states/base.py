"""
人员状态流基础工具
"""
import json
from typing import Any, Dict


def ensure_dict(value: Any) -> Dict[str, Any]:
    """确保从数据库读取的 data 转为字典"""
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        return {"value": value}
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {}


def serialize_dict(data: Dict[str, Any]) -> str:
    """序列化 data 字段"""
    return json.dumps(data or {}, ensure_ascii=False)

