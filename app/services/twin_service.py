"""
Twin Service - 通用 Twin 服务层
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional

from app.daos.twins.twin_dao import TwinDAO
from app.daos.twins.state_dao import TwinStateDAO
from app.schema.loader import SchemaLoader
from app.models.twins import ActivityTwin


class TwinService:
    """通用 Twin 服务层"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.twin_dao = TwinDAO(db_path=db_path)
        self.state_dao = TwinStateDAO(db_path=db_path)
        self.schema_loader = SchemaLoader()
    
    def _is_activity_twin(self, twin_name: str) -> bool:
        """判断是否为 Activity Twin"""
        schema = self.schema_loader.get_twin_schema(twin_name)
        return schema and schema.get("type") == "activity"
    
    def list_twins(
        self, 
        twin_name: str, 
        filters: Optional[Dict[str, Any]] = None,
        enrich: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        列出所有 Twin 及其最新状态
        
        Args:
            twin_name: Twin 名称（如 "person", "person_company_employment"）
            filters: 可选的过滤条件
            enrich: enrich 参数，支持 "true" 或实体列表（如 "person,project"），仅对 Activity Twin 有效
        
        Returns:
            Twin 列表，每个包含 id 和状态数据
        """
        # 如果是 Activity Twin 且需要 enrich，使用 enrich 查询
        if self._is_activity_twin(twin_name) and enrich:
            enrich_entities = None
            if enrich.lower() == "true":
                # enrich 所有 related_entities
                enrich_entities = None
            else:
                # enrich 指定的实体
                enrich_entities = [e.strip() for e in enrich.split(",")]
            
            # 使用 enrich 查询
            return self.state_dao.query_latest_states_with_enrich(
                twin_name, 
                filters=filters,
                enrich_entities=enrich_entities
            )
        
        # 普通查询（不使用 enrich）
        latest_states = self.state_dao.query_latest_states(twin_name, filters=filters)
        
        twins = []
        for state in latest_states:
            twin_info = {
                "id": state.twin_id,
                **state.data  # 展开状态数据
            }
            
            # 如果是 Activity Twin，添加关联实体ID
            if self._is_activity_twin(twin_name):
                activity = self.twin_dao.get_twin(twin_name, state.twin_id)
                if activity and isinstance(activity, ActivityTwin):
                    # 添加关联实体ID到结果中
                    for key, value in activity.related_entity_ids.items():
                        twin_info[key] = value
            
            twins.append(twin_info)
        
        return twins
    
    def get_twin(self, twin_name: str, twin_id: int) -> Optional[Dict[str, Any]]:
        """
        获取 Twin 详情（包括历史）
        
        Args:
            twin_name: Twin 名称
            twin_id: Twin ID
        
        Returns:
            Twin 详情，包含 id、current（当前状态）、history（历史记录）
        """
        # 检查 Twin 是否存在
        if not self.twin_dao.twin_exists(twin_name, twin_id):
            return None
        
        # 获取最新状态
        latest_state = self.state_dao.get_latest(twin_name, twin_id)
        if not latest_state:
            return None
        
        # 获取所有历史状态
        history = self.state_dao.list_states(twin_name, twin_id, limit=100)
        
        result = {
            "id": twin_id,
            "current": latest_state.data,
            "history": [
                {
                    "version": h.version,
                    "ts": h.ts,
                    "data": h.data,
                }
                for h in history
            ]
        }
        
        # 如果是 Activity Twin，添加关联实体ID
        if self._is_activity_twin(twin_name):
            activity = self.twin_dao.get_twin(twin_name, twin_id)
            if activity and isinstance(activity, ActivityTwin):
                for key, value in activity.related_entity_ids.items():
                    result[key] = value
        
        return result
    
    def query_twins(
        self,
        twin_name: str,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        查询 Twin（支持过滤、排序、限制）
        
        Args:
            twin_name: Twin 名称
            filters: 过滤条件
            order_by: 排序字段
            limit: 限制数量
        
        Returns:
            Twin 列表
        """
        states = self.state_dao.query_states(twin_name, filters=filters, order_by=order_by, limit=limit)
        
        twins = []
        for state in states:
            twin_info = {
                "id": state.twin_id,
                **state.data
            }
            
            # 如果是 Activity Twin，添加关联实体ID
            if self._is_activity_twin(twin_name):
                activity = self.twin_dao.get_twin(twin_name, state.twin_id)
                if activity and isinstance(activity, ActivityTwin):
                    for key, value in activity.related_entity_ids.items():
                        twin_info[key] = value
            
            twins.append(twin_info)
        
        return twins
    
    def create_twin(self, twin_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建 Twin 并添加初始状态
        
        Args:
            twin_name: Twin 名称
            data: 状态数据（字段值字典）
        
        Returns:
            创建的 Twin 信息（包含 id 和状态数据）
        """
        schema = self.schema_loader.get_twin_schema(twin_name)
        if not schema:
            raise ValueError(f"Twin schema not found: {twin_name}")
        
        # 创建 Twin
        if schema.get("type") == "entity":
            twin_id = self.twin_dao.create_entity_twin(twin_name)
        else:  # activity
            # 对于 Activity Twin，需要从 data 中提取 related_entities 的 ID
            related_entity_ids = {}
            if schema.get("related_entities"):
                for rel_entity in schema.get("related_entities", []):
                    key = rel_entity.get("key")
                    if key not in data:
                        if rel_entity.get("required", True):
                            raise ValueError(f"Missing required entity: {key}")
                    else:
                        related_entity_ids[key] = data.pop(key)  # 从 data 中移除，不存储在状态中
            
            twin_id = self.twin_dao.create_activity_twin(twin_name, related_entity_ids)
        
        # 添加初始状态
        self.state_dao.append(twin_name, twin_id, data)
        
        # 返回创建的 Twin 信息
        return self.get_twin(twin_name, twin_id)
    
    def update_twin(self, twin_name: str, twin_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新 Twin 状态（追加新状态）
        
        Args:
            twin_name: Twin 名称
            twin_id: Twin ID
            data: 新的状态数据
        
        Returns:
            更新后的 Twin 信息
        """
        # 检查 Twin 是否存在
        if not self.twin_dao.twin_exists(twin_name, twin_id):
            raise ValueError(f"Twin not found: {twin_name}:{twin_id}")
        
        # 追加新状态
        self.state_dao.append(twin_name, twin_id, data)
        
        # 返回更新后的 Twin 信息
        return self.get_twin(twin_name, twin_id)