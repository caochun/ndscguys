"""
Schema Loader - 加载和解析 Twin Schema
"""
from __future__ import annotations

import yaml
from collections import OrderedDict
from pathlib import Path
from typing import Dict, Any, Optional

class SchemaLoader:
    """Schema 加载器"""
    
    def __init__(self, schema_path: Optional[str] = None):
        if schema_path is None:
            from pathlib import Path
            base_dir = Path(__file__).parent.parent.parent
            schema_path = base_dir / "app" / "schema" / "twin_schema.yaml"
        self.schema_path = Path(schema_path)
        self._schema: Optional[Dict[str, Any]] = None
    
    def load(self) -> Dict[str, Any]:
        """加载 Schema，使用 OrderedDict 保持字段顺序"""
        if self._schema is None:
            # 定义 OrderedLoader 类，用于保持 YAML 字段顺序
            class OrderedLoader(yaml.SafeLoader):
                pass
            
            def construct_mapping(loader, node):
                loader.flatten_mapping(node)
                return OrderedDict(loader.construct_pairs(node))
            
            OrderedLoader.add_constructor(
                yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                construct_mapping)
            
            with open(self.schema_path, "r", encoding="utf-8") as f:
                self._schema = yaml.load(f, OrderedLoader)
        return self._schema
    
    def get_twin_schema(self, twin_name: str) -> Optional[Dict[str, Any]]:
        """获取指定 Twin 的 Schema"""
        schema = self.load()
        twins = schema.get("twins", {})
        return twins.get(twin_name)
    
    def list_entity_twins(self) -> Dict[str, Dict[str, Any]]:
        """列出所有 Entity Twin"""
        schema = self.load()
        twins = schema.get("twins", {})
        return {
            name: twin_def
            for name, twin_def in twins.items()
            if twin_def.get("type") == "entity"
        }
    
    def list_activity_twins(self) -> Dict[str, Dict[str, Any]]:
        """列出所有 Activity Twin"""
        schema = self.load()
        twins = schema.get("twins", {})
        return {
            name: twin_def
            for name, twin_def in twins.items()
            if twin_def.get("type") == "activity"
        }
    
    def get_all_twins(self) -> Dict[str, Dict[str, Any]]:
        """获取所有 Twin 定义"""
        schema = self.load()
        return schema.get("twins", {})
