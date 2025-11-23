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
            # 使用配置中的数据库路径
            from config import Config
            db_path = Config.get_db_path()
        
        self.db_path = db_path
        self.conn = None
        self._init_database()
    
    def _init_database(self):
        """初始化数据库，创建表结构"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # 使用Row工厂，方便访问列
        
        cursor = self.conn.cursor()
        
        # 创建人员基本信息表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS persons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                birth_date DATE,
                gender TEXT,
                phone TEXT,
                email TEXT,
                address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 如果表已存在但没有 address 列，则添加该列
        try:
            cursor.execute("ALTER TABLE persons ADD COLUMN address TEXT")
        except sqlite3.OperationalError:
            # 列已存在，忽略错误
            pass
        
        # 创建员工表（关联人员和公司）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER NOT NULL,
                company_name TEXT NOT NULL,
                employee_number TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE,
                UNIQUE(company_name, employee_number)
            )
        """)
        
        # 创建当前入职信息表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                department TEXT NOT NULL,
                position TEXT NOT NULL,
                supervisor_id INTEGER,
                hire_date DATE NOT NULL,
                employee_type TEXT NOT NULL DEFAULT '正式员工',
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
            CREATE TABLE IF NOT EXISTS employment_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                department TEXT NOT NULL,
                position TEXT NOT NULL,
                supervisor_id INTEGER,
                hire_date DATE NOT NULL,
                employee_type TEXT NOT NULL DEFAULT '正式员工',
                version INTEGER NOT NULL,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                change_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
                FOREIGN KEY (supervisor_id) REFERENCES employees(id) ON DELETE SET NULL
            )
        """)
        
        # 创建考勤记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER NOT NULL,
                employee_id INTEGER,
                company_name TEXT NOT NULL,
                attendance_date DATE NOT NULL,
                check_in_time TIMESTAMP,
                check_out_time TIMESTAMP,
                status TEXT,
                work_hours REAL,
                standard_hours REAL DEFAULT 8.0,
                overtime_hours REAL DEFAULT 0.0,
                leave_hours REAL DEFAULT 0.0,
                remark TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE,
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE SET NULL,
                UNIQUE(person_id, company_name, attendance_date)
            )
        """)
        
        # 创建请假记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leave_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER NOT NULL,
                employee_id INTEGER,
                company_name TEXT NOT NULL,
                leave_date DATE NOT NULL,
                leave_type TEXT NOT NULL,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                leave_hours REAL NOT NULL,
                paid_hours REAL DEFAULT 0.0,
                reason TEXT,
                status TEXT DEFAULT 'approved',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE,
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE SET NULL
            )
        """)
        
        # 创建索引以提高查询性能
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_person_name ON persons(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_employee_person_id ON employees(person_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_employee_company ON employees(company_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_employment_employee_id ON employment(employee_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_employee_id ON employment_history(employee_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_version ON employment_history(employee_id, version)")
        
        # 为旧版本数据库添加 employee_type 列
        try:
            cursor.execute("ALTER TABLE employment ADD COLUMN employee_type TEXT NOT NULL DEFAULT '正式员工'")
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute("ALTER TABLE employment_history ADD COLUMN employee_type TEXT NOT NULL DEFAULT '正式员工'")
        except sqlite3.OperationalError:
            pass
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_person_id ON attendance(person_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_employee_id ON attendance(employee_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(attendance_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_company ON attendance(company_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_leave_person_id ON leave_records(person_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_leave_employee_id ON leave_records(employee_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_leave_date ON leave_records(leave_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_leave_company ON leave_records(company_name)")
        
        # 为旧版本数据库添加 paid_hours 列
        try:
            cursor.execute("ALTER TABLE leave_records ADD COLUMN paid_hours REAL DEFAULT 0.0")
        except sqlite3.OperationalError:
            pass

        # 创建薪资记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS salary_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                base_amount REAL NOT NULL,
                basic_salary REAL NOT NULL,
                performance_salary REAL NOT NULL,
                effective_date DATE NOT NULL,
                end_date DATE,
                change_reason TEXT,
                version INTEGER NOT NULL DEFAULT 1,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_salary_employee_id ON salary_records(employee_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_salary_effective_date ON salary_records(effective_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_salary_status ON salary_records(status)")

        # 创建 payroll_record 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payroll_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                period TEXT NOT NULL UNIQUE,
                issue_date DATE,
                total_gross_amount REAL DEFAULT 0.0,
                total_net_amount REAL DEFAULT 0.0,
                status TEXT NOT NULL DEFAULT 'draft',
                note TEXT,
                created_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建 payroll_items 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payroll_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payroll_id INTEGER NOT NULL,
                employee_id INTEGER NOT NULL,
                basic_salary REAL NOT NULL,
                performance_base REAL NOT NULL,
                performance_grade TEXT NOT NULL,
                performance_pay REAL NOT NULL,
                adjustment REAL DEFAULT 0.0,
                gross_pay REAL NOT NULL,
                social_security_employee REAL DEFAULT 0.0,
                social_security_employer REAL DEFAULT 0.0,
                housing_fund_employee REAL DEFAULT 0.0,
                housing_fund_employer REAL DEFAULT 0.0,
                taxable_income REAL DEFAULT 0.0,
                income_tax REAL DEFAULT 0.0,
                net_pay REAL DEFAULT 0.0,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (payroll_id) REFERENCES payroll_records(id) ON DELETE CASCADE,
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
            )
        """)

        # period 字段已有 UNIQUE 约束，不需要额外索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_payroll_status ON payroll_records(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_payroll_item_payroll_id ON payroll_items(payroll_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_payroll_item_employee_id ON payroll_items(employee_id)")
        
        # 如果表已存在但没有 UNIQUE 约束，尝试添加（SQLite 不支持直接添加 UNIQUE 约束，需要重建表）
        # 这里我们通过代码逻辑来保证唯一性
        
        self.conn.commit()
    
    def get_connection(self):
        """获取数据库连接"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
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

