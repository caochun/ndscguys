"""
数据库初始化 - 根据 Schema 自动创建表结构
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from app.schema.loader import SchemaLoader
from app.schema.models import TwinSchema, FieldDefinition


class DatabaseInitializer:
    """数据库初始化器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.schema_loader = SchemaLoader()
        # 确保数据库目录存在
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        return conn
    
    def _create_entity_table(self, schema: TwinSchema):
        """创建 Entity Twin 注册表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Entity 表只需要 id 和 created_at
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {schema.table} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _create_activity_table(self, schema: TwinSchema):
        """创建 Activity Twin 注册表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Activity 表需要关联实体的外键列
        columns = ["id INTEGER PRIMARY KEY AUTOINCREMENT"]
        
        if schema.related_entities:
            for rel_entity in schema.related_entities:
                columns.append(f"{rel_entity.key} INTEGER NOT NULL")
        
        columns.append("created_at TEXT DEFAULT CURRENT_TIMESTAMP")
        
        create_sql = f"""
            CREATE TABLE IF NOT EXISTS {schema.table} (
                {', '.join(columns)}
            )
        """
        
        cursor.execute(create_sql)
        
        # 创建外键索引（如果有关联实体）
        if schema.related_entities:
            for rel_entity in schema.related_entities:
                cursor.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{schema.table}_{rel_entity.key}
                    ON {schema.table}({rel_entity.key})
                """)
        
        conn.commit()
        conn.close()
    
    def _create_state_table(self, schema: TwinSchema):
        """创建状态流表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        columns = [
            "id INTEGER PRIMARY KEY AUTOINCREMENT",
            "twin_id INTEGER NOT NULL",
        ]
        
        # 根据状态流模式添加列
        if schema.mode == "versioned":
            columns.append("version INTEGER NOT NULL")
        elif schema.mode == "time_series":
            columns.append("time_key TEXT NOT NULL")
        
        columns.append("ts TEXT NOT NULL")
        columns.append("data TEXT NOT NULL")  # JSON 数据
        
        # 创建表
        create_sql = f"""
            CREATE TABLE IF NOT EXISTS {schema.state_table} (
                {', '.join(columns)},
                FOREIGN KEY (twin_id) REFERENCES {schema.table}(id)
            )
        """
        
        cursor.execute(create_sql)
        
        # 创建索引
        cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{schema.state_table}_twin_id
            ON {schema.state_table}(twin_id)
        """)
        
        if schema.mode == "versioned":
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{schema.state_table}_version
                ON {schema.state_table}(twin_id, version)
            """)
        elif schema.mode == "time_series":
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{schema.state_table}_time_key
                ON {schema.state_table}(twin_id, time_key)
            """)
        
        conn.commit()
        conn.close()
    
    def init_database(self):
        """初始化数据库"""
        print(f"初始化数据库: {self.db_path}")
        
        all_twins = self.schema_loader.get_all_twins()
        
        # 先创建所有 Entity Twin 表
        print("创建 Entity Twin 表...")
        for twin_name, twin_def in all_twins.items():
            if twin_def.get("type") == "entity":
                schema = TwinSchema.from_dict(twin_name, twin_def)
                print(f"  创建表: {schema.table}")
                self._create_entity_table(schema)
                print(f"  创建状态表: {schema.state_table}")
                self._create_state_table(schema)
        
        # 再创建所有 Activity Twin 表（因为可能依赖 Entity 表）
        print("创建 Activity Twin 表...")
        for twin_name, twin_def in all_twins.items():
            if twin_def.get("type") == "activity":
                schema = TwinSchema.from_dict(twin_name, twin_def)
                print(f"  创建表: {schema.table}")
                self._create_activity_table(schema)
                print(f"  创建状态表: {schema.state_table}")
                self._create_state_table(schema)
        
        print("数据库初始化完成！")


def init_db(db_path: Optional[str] = None):
    """初始化数据库（便捷函数）"""
    if db_path is None:
        from config import Config
        db_path = str(Config.DATABASE_PATH)
    
    initializer = DatabaseInitializer(db_path)
    initializer.init_database()
