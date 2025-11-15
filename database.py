"""
数据库初始化和连接管理
"""
import sqlite3
import os
from pathlib import Path
from datetime import datetime


class Database:
    """数据库管理类"""
    
    def __init__(self, db_path=None):
        """
        初始化数据库连接
        
        Args:
            db_path: 数据库文件路径，如果为None则使用默认路径
        """
        if db_path is None:
            # macOS默认路径：~/Library/Application Support/HRSystem/
            app_data_dir = Path.home() / "Library" / "Application Support" / "HRSystem"
            app_data_dir.mkdir(parents=True, exist_ok=True)
            db_path = app_data_dir / "hr_system.db"
        
        self.db_path = db_path
        self.conn = None
        self._init_database()
    
    def _init_database(self):
        """初始化数据库，创建表结构"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # 使用Row工厂，方便访问列
        
        cursor = self.conn.cursor()
        
        # 创建员工个人信息表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_number TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                birth_date DATE,
                gender TEXT,
                phone TEXT,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建当前入职信息表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employment_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                department TEXT NOT NULL,
                position TEXT NOT NULL,
                supervisor_id INTEGER,
                hire_date DATE NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
                FOREIGN KEY (supervisor_id) REFERENCES employees(id) ON DELETE SET NULL,
                UNIQUE(employee_id)
            )
        """)
        
        # 创建入职信息历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employment_info_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                department TEXT NOT NULL,
                position TEXT NOT NULL,
                supervisor_id INTEGER,
                hire_date DATE NOT NULL,
                version INTEGER NOT NULL,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                change_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
                FOREIGN KEY (supervisor_id) REFERENCES employees(id) ON DELETE SET NULL
            )
        """)
        
        # 创建索引以提高查询性能
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_employee_number ON employees(employee_number)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_employment_employee_id ON employment_info(employee_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_employee_id ON employment_info_history(employee_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_version ON employment_info_history(employee_id, version)")
        
        self.conn.commit()
    
    def get_connection(self):
        """获取数据库连接"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None


# 全局数据库实例
_db_instance = None


def get_db():
    """获取全局数据库实例（单例模式）"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance

