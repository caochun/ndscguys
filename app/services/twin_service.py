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
    
    def list_twins(self, twin_name: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        列出所有 Twin 及其最新状态
        
        Args:
            twin_name: Twin 名称（如 "person", "person_company_employment"）
            filters: 可选的过滤条件
        
        Returns:
            Twin 列表，每个包含 id 和状态数据
        """
        # 查询所有最新状态
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
