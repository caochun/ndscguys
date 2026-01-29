"""
Twin Service - 通用 Twin 服务层
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional
from datetime import datetime

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
    
    def _apply_auto_fields(self, twin_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        应用自动字段（auto fields）
        
        根据 schema 定义，自动填充未提供的 auto 字段
        
        Args:
            twin_name: Twin 名称
            data: 状态数据字典
        
        Returns:
            填充了自动字段的数据字典
        """
        schema = self.schema_loader.get_twin_schema(twin_name)
        if not schema or not schema.get("fields"):
            return data
        
        result = data.copy()
        fields = schema.get("fields", {})
        
        for field_name, field_def in fields.items():
            # 跳过 reference 类型和已存在的字段
            if field_def.get("type") == "reference":
                continue
            if field_name in result and result[field_name] is not None:
                continue
            
            # 检查是否有 auto 属性
            auto_type = field_def.get("auto")
            if not auto_type:
                continue
            
            # 根据 auto 类型生成值
            if auto_type in ("timestamp", "now", "datetime"):
                # ISO 格式的时间戳：YYYY-MM-DDTHH:MM:SS
                result[field_name] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
            elif auto_type == "date":
                # 日期格式：YYYY-MM-DD
                result[field_name] = datetime.utcnow().strftime("%Y-%m-%d")
            # 未来可以扩展其他类型，如 uuid、increment 等
        
        return result
    
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
    
    def get_twin(self, twin_name: str, twin_id: int, enrich: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        获取 Twin 详情（包括历史）
        
        Args:
            twin_name: Twin 名称
            twin_id: Twin ID
            enrich: 可选，enrich 参数（如 "person,company"），仅对 Activity Twin 有效，用于填充关联实体名称等
        
        Returns:
            Twin 详情，包含 id、current（当前状态）、history（历史记录）
           注意：字段顺序由前端根据 schema.fields 的顺序控制
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
            "current": dict(latest_state.data),
            "history": [
                {
                    "version": h.version,
                    "time_key": h.time_key,
                    "ts": h.ts,
                    "data": h.data,
                }
                for h in history
            ]
        }
        
        # 如果是 Activity Twin，添加关联实体ID，并在需要时 enrich 关联实体名称
        if self._is_activity_twin(twin_name):
            activity = self.twin_dao.get_twin(twin_name, twin_id)
            if activity and isinstance(activity, ActivityTwin):
                for key, value in activity.related_entity_ids.items():
                    result[key] = value
                
                # 若请求了 enrich，则根据 related_entities 查询关联实体的最新状态并填充名称等
                if enrich:
                    schema = self.schema_loader.get_twin_schema(twin_name)
                    if schema and schema.get("related_entities"):
                        entities_to_enrich = [e.strip() for e in enrich.split(",") if e.strip()]
                        for rel_entity in schema.get("related_entities", []):
                            entity_name = rel_entity.get("entity")
                            if entity_name not in entities_to_enrich:
                                continue
                            key = rel_entity.get("key")  # e.g. person_id, company_id
                            entity_id = activity.related_entity_ids.get(key)
                            if entity_id is None:
                                continue
                            entity_state = self.state_dao.get_latest(entity_name, entity_id)
                            if entity_state and entity_state.data:
                                prefix = entity_name
                                for field_name, field_value in entity_state.data.items():
                                    if field_name in ("name", "label", "title"):
                                        enrich_key = f"{prefix}_{field_name}"
                                        result[enrich_key] = field_value
                                        result["current"][enrich_key] = field_value
                                        break
                                else:
                                    # 若没有 name/label/title，取第一个非 id 字段作为展示名
                                    for field_name, field_value in entity_state.data.items():
                                        if field_name != "id" and field_value is not None:
                                            result[f"{prefix}_{field_name}"] = field_value
                                            result["current"][f"{prefix}_{field_name}"] = field_value
                                            break
        
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
        
        # 应用自动字段
        data = self._apply_auto_fields(twin_name, data)
        
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
        
        # 检查是否为 time_series 模式，如果是，需要提取 time_key
        time_key = None
        if schema.get("mode") == "time_series":
            # 查找 unique_key 中包含 time_key 的字段，或者查找 storage: unique_key 的字段
            unique_key = schema.get("unique_key", [])
            fields = schema.get("fields", {})
            
            # 查找作为 time_key 的字段（通常是 unique_key 中除了 activity_id 或 twin_id 之外的字段）
            for field_name, field_def in fields.items():
                if field_def.get("storage") == "unique_key" or field_name in unique_key:
                    # 排除 reference 类型的字段（它们通常是外键）
                    if field_def.get("type") != "reference" and field_name in data:
                        time_key = data.get(field_name)
                        break
            
            # 如果没找到，尝试从 unique_key 中查找（排除 id 字段）
            if not time_key:
                for key in unique_key:
                    if key not in ["activity_id", "twin_id", "id"] and key in data:
                        time_key = data.get(key)
                        break
        
        # 添加初始状态
        self.state_dao.append(twin_name, twin_id, data, time_key=time_key)
        
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
        
        # 应用自动字段
        data = self._apply_auto_fields(twin_name, data)
        
        # 检查是否为 time_series 模式，如果是，需要提取 time_key
        schema = self.schema_loader.get_twin_schema(twin_name)
        time_key = None
        if schema and schema.get("mode") == "time_series":
            # 查找 unique_key 中包含 time_key 的字段，或者查找 storage: unique_key 的字段
            unique_key = schema.get("unique_key", [])
            fields = schema.get("fields", {})
            
            # 查找作为 time_key 的字段（通常是 unique_key 中除了 activity_id 或 twin_id 之外的字段）
            for field_name, field_def in fields.items():
                if field_def.get("storage") == "unique_key" or field_name in unique_key:
                    # 排除 reference 类型的字段（它们通常是外键）
                    if field_def.get("type") != "reference" and field_name in data:
                        time_key = data.get(field_name)
                        break
            
            # 如果没找到，尝试从 unique_key 中查找（排除 id 字段）
            if not time_key:
                for key in unique_key:
                    if key not in ["activity_id", "twin_id", "id"] and key in data:
                        time_key = data.get(key)
                        break
        
        # 追加新状态
        self.state_dao.append(twin_name, twin_id, data, time_key=time_key)
        
        # 返回更新后的 Twin 信息
        return self.get_twin(twin_name, twin_id)