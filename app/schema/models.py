"""
Schema Models - Schema 定义的数据结构
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List, Optional


@dataclass
class FieldDefinition:
    """字段定义"""
    name: str
    type: str
    required: bool = False
    label: Optional[str] = None
    description: Optional[str] = None
    validation: Optional[Dict[str, Any]] = None
    ui: Optional[Dict[str, Any]] = None
    storage: Optional[str] = None  # "foreign_key", "unique_key", None (data)
    reference_entity: Optional[str] = None
    options: Optional[List[str]] = None  # enum 类型的选项
    
    @classmethod
    def from_dict(cls, name: str, field_def: Dict[str, Any]) -> "FieldDefinition":
        """从字典创建 FieldDefinition"""
        return cls(
            name=name,
            type=field_def.get("type", "string"),
            required=field_def.get("required", False),
            label=field_def.get("label"),
            description=field_def.get("description"),
            validation=field_def.get("validation"),
            ui=field_def.get("ui"),
            storage=field_def.get("storage"),
            reference_entity=field_def.get("reference_entity"),
            options=field_def.get("options"),
        )


@dataclass
class RelatedEntity:
    """Activity Twin 关联的 Entity"""
    entity: str
    role: str
    key: str
    required: bool = True


@dataclass
class TwinSchema:
    """Twin Schema 定义"""
    name: str
    type: str  # "entity" 或 "activity"
    label: str
    description: Optional[str] = None
    table: Optional[str] = None
    state_table: Optional[str] = None
    mode: str = "versioned"  # "versioned" 或 "time_series"
    unique_key: Optional[List[str]] = None
    fields: Optional[Dict[str, FieldDefinition]] = None
    related_entities: Optional[List[RelatedEntity]] = None
    
    @classmethod
    def from_dict(cls, name: str, twin_def: Dict[str, Any]) -> "TwinSchema":
        """从字典创建 TwinSchema"""
        fields = {}
        if "fields" in twin_def:
            fields = {
                field_name: FieldDefinition.from_dict(field_name, field_def)
                for field_name, field_def in twin_def["fields"].items()
            }
        
        related_entities = None
        if "related_entities" in twin_def:
            related_entities = [
                RelatedEntity(
                    entity=rel.get("entity"),
                    role=rel.get("role"),
                    key=rel.get("key"),
                    required=rel.get("required", True),
                )
                for rel in twin_def["related_entities"]
            ]
        
        return cls(
            name=name,
            type=twin_def.get("type", "entity"),
            label=twin_def.get("label", name),
            description=twin_def.get("description"),
            table=twin_def.get("table"),
            state_table=twin_def.get("state_table"),
            mode=twin_def.get("mode", "versioned"),
            unique_key=twin_def.get("unique_key"),
            fields=fields,
            related_entities=related_entities,
        )
