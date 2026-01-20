"""
Twin State DAO - 管理 Twin 的状态流
"""
from __future__ import annotations

import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.daos.base_dao import BaseDAO
from app.models.twins import TwinState, TwinType
from app.models.twins.state import StateStreamMode
from app.schema.loader import SchemaLoader
from app.schema.models import TwinSchema, FieldDefinition


class TwinStateDAO(BaseDAO):
    """Twin 状态流 DAO"""
    
    def __init__(self, db_path: Optional[str] = None):
        super().__init__(db_path)
        self.schema_loader = SchemaLoader()
        self._twin_schemas: Dict[str, TwinSchema] = {}
    
    def _get_twin_schema(self, twin_name: str) -> TwinSchema:
        """获取 Twin Schema（带缓存）"""
        if twin_name not in self._twin_schemas:
            from app.schema.models import TwinSchema
            twin_def = self.schema_loader.get_twin_schema(twin_name)
            if not twin_def:
                raise ValueError(f"Twin schema not found: {twin_name}")
            self._twin_schemas[twin_name] = TwinSchema.from_dict(twin_name, twin_def)
        return self._twin_schemas[twin_name]
    
    def _get_next_version(self, twin_name: str, twin_id: int) -> int:
        """获取下一个版本号（版本化状态流）"""
        schema = self._get_twin_schema(twin_name)
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT COALESCE(MAX(version), 0) FROM {schema.state_table} WHERE twin_id = ?",
            (twin_id,)
        )
        max_version = cursor.fetchone()[0] or 0
        conn.close()
        return max_version + 1
    
    def _normalize_ts(self, ts: Optional[str | datetime]) -> str:
        """标准化时间戳"""
        if ts is None:
            return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
        if isinstance(ts, datetime):
            return ts.strftime("%Y-%m-%dT%H:%M:%S")
        return ts
    
    def append(
        self,
        twin_name: str,
        twin_id: int,
        data: Dict[str, Any],
        time_key: Optional[str] = None,
        ts: Optional[str | datetime] = None
    ) -> int:
        """追加状态记录"""
        schema = self._get_twin_schema(twin_name)
        ts_str = self._normalize_ts(ts)
        
        if schema.mode == StateStreamMode.VERSIONED:
            # 版本化状态流
            version = self._get_next_version(twin_name, twin_id)
            twin_type = TwinType.ENTITY if schema.type == "entity" else TwinType.ACTIVITY
            state = TwinState(
                twin_id=twin_id,
                twin_type=twin_type,
                twin_name=twin_name,
                version=version,
                ts=ts_str,
                data=data,
            )
            record = state.to_record()
            
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {schema.state_table} (twin_id, version, ts, data)
                VALUES (?, ?, ?, ?)
                """,
                (record["twin_id"], record["version"], record["ts"], record["data"])
            )
            conn.commit()
            conn.close()
            return version
        
        else:  # time_series
            # 时间序列状态流
            if not time_key:
                raise ValueError(f"time_key is required for time_series mode")
            
            twin_type = TwinType.ENTITY if schema.type == "entity" else TwinType.ACTIVITY
            state = TwinState(
                twin_id=twin_id,
                twin_type=twin_type,
                twin_name=twin_name,
                time_key=time_key,
                ts=ts_str,
                data=data,
            )
            record = state.to_record()
            
            conn = self.get_connection()
            cursor = conn.cursor()
            # 检查是否已存在（根据 unique_key）
            unique_key_fields = schema.unique_key or []
            if "time_key" in unique_key_fields:
                # 使用 INSERT OR REPLACE
                cursor.execute(
                    f"""
                    INSERT OR REPLACE INTO {schema.state_table} (twin_id, time_key, ts, data)
                    VALUES (?, ?, ?, ?)
                    """,
                    (record["twin_id"], record["time_key"], record["ts"], record["data"])
                )
            else:
                cursor.execute(
                    f"""
                    INSERT INTO {schema.state_table} (twin_id, time_key, ts, data)
                    VALUES (?, ?, ?, ?)
                    """,
                    (record["twin_id"], record["time_key"], record["ts"], record["data"])
                )
            conn.commit()
            conn.close()
            return 0  # 时间序列模式不返回版本号
    
    def get_latest(self, twin_name: str, twin_id: int) -> Optional[TwinState]:
        """获取最新状态"""
        schema = self._get_twin_schema(twin_name)
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if schema.mode == StateStreamMode.VERSIONED:
            cursor.execute(
                f"""
                SELECT * FROM {schema.state_table}
                WHERE twin_id = ?
                ORDER BY version DESC
                LIMIT 1
                """,
                (twin_id,)
            )
        else:  # time_series
            cursor.execute(
                f"""
                SELECT * FROM {schema.state_table}
                WHERE twin_id = ?
                ORDER BY time_key DESC
                LIMIT 1
                """,
                (twin_id,)
            )
        
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        
        twin_type = TwinType.ENTITY if schema.type == "entity" else TwinType.ACTIVITY
        return TwinState.from_row(dict(row), twin_name, twin_type)
    
    def list_states(
        self,
        twin_name: str,
        twin_id: int,
        limit: int = 50
    ) -> List[TwinState]:
        """列出状态记录"""
        schema = self._get_twin_schema(twin_name)
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if schema.mode == StateStreamMode.VERSIONED:
            cursor.execute(
                f"""
                SELECT * FROM {schema.state_table}
                WHERE twin_id = ?
                ORDER BY version DESC
                LIMIT ?
                """,
                (twin_id, limit)
            )
        else:  # time_series
            cursor.execute(
                f"""
                SELECT * FROM {schema.state_table}
                WHERE twin_id = ?
                ORDER BY time_key DESC
                LIMIT ?
                """,
                (twin_id, limit)
            )
        
        rows = cursor.fetchall()
        conn.close()
        twin_type = TwinType.ENTITY if schema.type == "entity" else TwinType.ACTIVITY
        return [
            TwinState.from_row(dict(row), twin_name, twin_type)
            for row in rows
        ]
    
    def _build_where_clause(
        self,
        schema: TwinSchema,
        filters: Dict[str, Any]
    ) -> tuple[str, List[Any]]:
        """
        构建 WHERE 子句
        
        Returns:
            (where_clause, params): WHERE 子句和参数列表
        """
        conditions = []
        params = []
        
        for field_name, field_value in filters.items():
            # 获取字段定义
            field_def = schema.fields.get(field_name) if schema.fields else None
            if not field_def:
                # 字段不存在，跳过或抛出异常
                continue
            
            # 根据字段的存储方式构建查询条件
            if field_def.storage == "foreign_key":
                # 作为外键存储，直接查询列
                conditions.append(f"{field_name} = ?")
                params.append(field_value)
            elif field_def.storage == "unique_key":
                # 作为唯一键的一部分存储，直接查询列
                conditions.append(f"{field_name} = ?")
                params.append(field_value)
            else:
                # 存储在 data JSON 中，使用 JSON 函数查询
                json_path = f"$.{field_name}"
                # 对于字符串类型，使用 LIKE 进行模糊搜索；其他类型使用精确匹配
                if field_def.type == "string":
                    conditions.append(f"json_extract(data, '{json_path}') LIKE ?")
                    params.append(f"%{field_value}%")
                else:
                    conditions.append(f"json_extract(data, '{json_path}') = ?")
                    params.append(field_value)
        
        if conditions:
            where_clause = " AND ".join(conditions)
            return f"WHERE {where_clause}", params
        return "", []
    
    def query_states(
        self,
        twin_name: str,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[TwinState]:
        """
        查询状态记录（支持基于属性的过滤）
        
        Args:
            twin_name: Twin 名称
            filters: 过滤条件字典，key 为字段名，value 为过滤值
            order_by: 排序字段（如 "version DESC" 或 "time_key DESC"）
            limit: 限制返回数量
        
        Returns:
            状态记录列表
        """
        schema = self._get_twin_schema(twin_name)
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 构建 WHERE 子句
        where_clause = ""
        params = []
        if filters:
            where_clause, params = self._build_where_clause(schema, filters)
        
        # 构建 ORDER BY 子句
        order_clause = ""
        if order_by:
            order_clause = f"ORDER BY {order_by}"
        elif schema.mode == "versioned":
            order_clause = "ORDER BY version DESC"
        else:  # time_series
            order_clause = "ORDER BY time_key DESC"
        
        # 构建 LIMIT 子句
        limit_clause = ""
        if limit:
            limit_clause = f"LIMIT {limit}"
        
        # 执行查询
        query = f"""
            SELECT * FROM {schema.state_table}
            {where_clause}
            {order_clause}
            {limit_clause}
        """
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        twin_type = TwinType.ENTITY if schema.type == "entity" else TwinType.ACTIVITY
        return [
            TwinState.from_row(dict(row) if not isinstance(row, dict) else row, twin_name, twin_type)
            for row in rows
        ]
    
    def query_latest_states(
        self,
        twin_name: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[TwinState]:
        """
        查询每个 Twin 的最新状态（支持过滤）
        
        对于版本化状态流：返回每个 twin_id 的最新版本
        对于时间序列状态流：返回每个 twin_id 的最新时间键记录
        
        对于 Activity Twin，如果过滤条件包含 related_entities 的 key（如 person_id），
        会先通过注册表过滤，再查询状态表。
        """
        schema = self._get_twin_schema(twin_name)
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 对于 Activity Twin，检查过滤条件中是否有 related_entities 的 key
        related_entity_filters = {}
        state_filters = {}
        
        if filters:
            if schema.type == "activity" and schema.related_entities:
                # 检查哪些过滤条件是 related_entities 的 key
                related_keys = {rel.key for rel in schema.related_entities}
                for key, value in filters.items():
                    if key in related_keys:
                        related_entity_filters[key] = value
                    else:
                        state_filters[key] = value
            else:
                state_filters = filters
        
        # 如果有 related_entity 过滤条件，先查询注册表获取 twin_id 列表
        twin_ids = None
        if related_entity_filters:
            # 构建注册表的 WHERE 子句
            conditions = []
            params = []
            for key, value in related_entity_filters.items():
                conditions.append(f"{key} = ?")
                params.append(value)
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            query = f"SELECT id FROM {schema.table} {where_clause}"
            cursor.execute(query, params)
            twin_ids = [row[0] for row in cursor.fetchall()]
            
            # 如果没有找到匹配的 twin_id，直接返回空列表
            if not twin_ids:
                conn.close()
                return []
        
        # 构建状态表的 WHERE 子句
        where_clause = ""
        params = []
        if state_filters:
            where_clause, params = self._build_where_clause(schema, state_filters)
        
        # 如果有 twin_ids 限制，添加到 WHERE 子句
        if twin_ids is not None:
            if where_clause:
                where_clause += f" AND s1.twin_id IN ({','.join(['?'] * len(twin_ids))})"
            else:
                where_clause = f"WHERE s1.twin_id IN ({','.join(['?'] * len(twin_ids))})"
            params.extend(twin_ids)
        
        if schema.mode == "versioned":
            # 版本化：获取每个 twin_id 的最新版本
            query = f"""
                SELECT s1.* FROM {schema.state_table} s1
                INNER JOIN (
                    SELECT twin_id, MAX(version) AS max_version
                    FROM {schema.state_table}
                    GROUP BY twin_id
                ) s2 ON s1.twin_id = s2.twin_id AND s1.version = s2.max_version
                {where_clause}
                ORDER BY s1.version DESC
            """
        else:
            # 时间序列：获取每个 twin_id 的最新时间键记录
            query = f"""
                SELECT s1.* FROM {schema.state_table} s1
                INNER JOIN (
                    SELECT twin_id, MAX(time_key) AS max_time_key
                    FROM {schema.state_table}
                    GROUP BY twin_id
                ) s2 ON s1.twin_id = s2.twin_id AND s1.time_key = s2.max_time_key
                {where_clause}
                ORDER BY s1.time_key DESC
            """
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        twin_type = TwinType.ENTITY if schema.type == "entity" else TwinType.ACTIVITY
        return [
            TwinState.from_row({key: row[key] for key in row.keys()}, twin_name, twin_type)
            for row in rows
        ]
    
    def query_by_json_field(
        self,
        twin_name: str,
        field_name: str,
        field_value: Any,
        operator: str = "="
    ) -> List[TwinState]:
        """
        直接通过 JSON 字段查询（简化方法）
        
        Args:
            twin_name: Twin 名称
            field_name: 字段名（存储在 data JSON 中）
            field_value: 字段值
            operator: 操作符（=, !=, >, <, LIKE, IN 等）
        """
        schema = self._get_twin_schema(twin_name)
        conn = self.get_connection()
        cursor = conn.cursor()
        
        json_path = f"$.{field_name}"
        
        # 根据操作符构建查询
        if operator == "=":
            condition = f"json_extract(data, '{json_path}') = ?"
            params = [field_value]
        elif operator == "!=":
            condition = f"json_extract(data, '{json_path}') != ?"
            params = [field_value]
        elif operator == ">":
            condition = f"json_extract(data, '{json_path}') > ?"
            params = [field_value]
        elif operator == "<":
            condition = f"json_extract(data, '{json_path}') < ?"
            params = [field_value]
        elif operator == "LIKE":
            condition = f"json_extract(data, '{json_path}') LIKE ?"
            params = [field_value]
        elif operator == "IN":
            # IN 操作需要特殊处理
            placeholders = ", ".join(["?" for _ in field_value])
            condition = f"json_extract(data, '{json_path}') IN ({placeholders})"
            params = list(field_value) if isinstance(field_value, (list, tuple)) else [field_value]
        else:
            condition = f"json_extract(data, '{json_path}') = ?"
            params = [field_value]
        
        # 构建排序
        if schema.mode == "versioned":
            order_clause = "ORDER BY version DESC"
        else:
            order_clause = "ORDER BY time_key DESC"
        
        query = f"""
            SELECT * FROM {schema.state_table}
            WHERE {condition}
            {order_clause}
        """
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        twin_type = TwinType.ENTITY if schema.type == "entity" else TwinType.ACTIVITY
        return [
            TwinState.from_row(dict(row) if not isinstance(row, dict) else row, twin_name, twin_type)
            for row in rows
        ]
    
    def query_latest_states_with_enrich(
        self,
        twin_name: str,
        filters: Optional[Dict[str, Any]] = None,
        enrich_entities: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        查询每个 Twin 的最新状态，并 enrich 关联的 Entity Twin 信息（通过 JOIN）
        
        Args:
            twin_name: Twin 名称（必须是 Activity Twin）
            filters: 过滤条件
            enrich_entities: 要 enrich 的实体列表（如 ["person", "project"]），None 表示 enrich 所有 related_entities
        
        Returns:
            包含 enrich 数据的字典列表，每个字典包含 Activity Twin 的状态数据和关联 Entity 的字段
        """
        schema = self._get_twin_schema(twin_name)
        
        # 只支持 Activity Twin 的 enrich
        if schema.type != "activity":
            raise ValueError(f"Enrichment is only supported for Activity Twins, got: {twin_name}")
        
        if not schema.related_entities:
            raise ValueError(f"Activity Twin {twin_name} has no related_entities to enrich")
        
        # 确定要 enrich 的实体
        if enrich_entities is None:
            # enrich 所有 related_entities
            entities_to_enrich = [rel.entity for rel in schema.related_entities]
        else:
            # 只 enrich 指定的实体
            entities_to_enrich = enrich_entities
        
        # 验证要 enrich 的实体是否存在于 related_entities 中
        valid_entities = {rel.entity for rel in schema.related_entities}
        for entity in entities_to_enrich:
            if entity not in valid_entities:
                raise ValueError(f"Entity {entity} is not a related_entity of {twin_name}")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 分离 related_entity 过滤条件和状态过滤条件
        related_entity_filters = {}
        state_filters = {}
        
        if filters:
            related_keys = {rel.key for rel in schema.related_entities}
            for key, value in filters.items():
                if key in related_keys:
                    related_entity_filters[key] = value
                else:
                    state_filters[key] = value
        
        # 构建基础查询：获取 Activity Twin 的最新状态
        activity_alias = "act"
        state_alias = "s1"
        state_table = schema.state_table
        activity_table = schema.table
        
        # 构建 JOIN 子句和 SELECT 字段
        joins = []
        select_fields = [
            f"{state_alias}.id",
            f"{state_alias}.twin_id",
            f"{state_alias}.version",
            f"{state_alias}.ts",
            f"{state_alias}.data",
        ]
        
        # 添加 Activity 注册表的字段（用于获取关联实体 ID）
        for rel_entity in schema.related_entities:
            select_fields.append(f"{activity_alias}.{rel_entity.key}")
        
        # 为每个要 enrich 的实体添加 JOIN
        entity_schemas = {}
        for rel_entity in schema.related_entities:
            if rel_entity.entity in entities_to_enrich:
                entity_schema = self._get_twin_schema(rel_entity.entity)
                entity_schemas[rel_entity.entity] = entity_schema
                
                entity_alias = f"e_{rel_entity.entity}"
                entity_state_alias = f"es_{rel_entity.entity}"
                
                # JOIN Activity 注册表获取关联实体 ID
                joins.append(f"""
                    LEFT JOIN {entity_schema.table} {entity_alias}
                        ON {activity_alias}.{rel_entity.key} = {entity_alias}.id
                """)
                
                # JOIN Entity 状态表获取最新状态
                if entity_schema.mode == "versioned":
                    joins.append(f"""
                        LEFT JOIN (
                            SELECT es1.* FROM {entity_schema.state_table} es1
                            INNER JOIN (
                                SELECT twin_id, MAX(version) AS max_version
                                FROM {entity_schema.state_table}
                                GROUP BY twin_id
                            ) es2 ON es1.twin_id = es2.twin_id AND es1.version = es2.max_version
                        ) {entity_state_alias}
                        ON {entity_alias}.id = {entity_state_alias}.twin_id
                    """)
                else:  # time_series
                    joins.append(f"""
                        LEFT JOIN (
                            SELECT es1.* FROM {entity_schema.state_table} es1
                            INNER JOIN (
                                SELECT twin_id, MAX(time_key) AS max_time_key
                                FROM {entity_schema.state_table}
                                GROUP BY twin_id
                            ) es2 ON es1.twin_id = es2.twin_id AND es1.time_key = es2.max_time_key
                        ) {entity_state_alias}
                        ON {entity_alias}.id = {entity_state_alias}.twin_id
                    """)
                
                # 添加 Entity 状态数据的字段（从 JSON 中提取所有字段）
                if entity_schema.fields:
                    for field_name in entity_schema.fields.keys():
                        select_fields.append(f"json_extract({entity_state_alias}.data, '$.{field_name}') AS {rel_entity.entity}_{field_name}")
        
        # 构建 WHERE 子句
        where_conditions = []
        params = []
        
        # Activity 注册表的过滤条件
        if related_entity_filters:
            for key, value in related_entity_filters.items():
                where_conditions.append(f"{activity_alias}.{key} = ?")
                params.append(value)
        
        # 状态表的过滤条件
        if state_filters:
            state_where, state_params = self._build_where_clause(schema, state_filters)
            if state_where:
                # 移除 "WHERE " 前缀，只保留条件
                conditions = state_where.replace("WHERE ", "")
                where_conditions.append(f"({conditions})")
                params.extend(state_params)
        
        # 构建获取最新状态的子查询
        if schema.mode == "versioned":
            latest_state_subquery = f"""
                SELECT s1.* FROM {state_table} s1
                INNER JOIN (
                    SELECT twin_id, MAX(version) AS max_version
                    FROM {state_table}
                    GROUP BY twin_id
                ) s2 ON s1.twin_id = s2.twin_id AND s1.version = s2.max_version
            """
        else:  # time_series
            latest_state_subquery = f"""
                SELECT s1.* FROM {state_table} s1
                INNER JOIN (
                    SELECT twin_id, MAX(time_key) AS max_time_key
                    FROM {state_table}
                    GROUP BY twin_id
                ) s2 ON s1.twin_id = s2.twin_id AND s1.time_key = s2.max_time_key
            """
        
        # 构建完整查询
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        query = f"""
            SELECT {', '.join(select_fields)}
            FROM ({latest_state_subquery}) {state_alias}
            INNER JOIN {activity_table} {activity_alias} ON {state_alias}.twin_id = {activity_alias}.id
            {''.join(joins)}
            {where_clause}
        """
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        # 转换结果为字典列表
        import json
        results = []
        for row in rows:
            row_dict = dict(row)
            
            # 解析 Activity Twin 的状态数据（JSON）
            activity_data = json.loads(row_dict["data"])
            
            # 构建结果字典
            result = {
                "id": row_dict["twin_id"],
                "twin_id": row_dict["twin_id"],
                "version": row_dict.get("version"),
                "ts": row_dict["ts"],
                **activity_data  # 展开 Activity 状态数据
            }
            
            # 添加关联实体 ID（从 Activity 注册表）
            for rel_entity in schema.related_entities:
                result[rel_entity.key] = row_dict.get(rel_entity.key)
            
            # 添加 enrich 的字段
            for rel_entity in schema.related_entities:
                if rel_entity.entity in entities_to_enrich:
                    entity_prefix = rel_entity.entity
                    # 添加所有以 entity_prefix 开头的字段
                    for key, value in row_dict.items():
                        if key.startswith(f"{entity_prefix}_") and value is not None:
                            result[key] = value
            
            results.append(result)
        
        return results