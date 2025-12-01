"""
数据库初始化
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional


def init_db(db_path: str):
    """初始化项目所需的表"""
    path = Path(db_path)
    if db_path != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 人员注册表（仅用于生成 person_id）
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS persons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # 基础信息状态流
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS person_basic_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            version INTEGER NOT NULL,
            ts TEXT NOT NULL,
            data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (person_id) REFERENCES persons(id),
            UNIQUE(person_id, version)
        )
        """
    )

    # 岗位信息状态流
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS person_position_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            version INTEGER NOT NULL,
            ts TEXT NOT NULL,
            data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (person_id) REFERENCES persons(id),
            UNIQUE(person_id, version)
        )
        """
    )

    # 薪资信息状态流
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS person_salary_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            version INTEGER NOT NULL,
            ts TEXT NOT NULL,
            data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (person_id) REFERENCES persons(id),
            UNIQUE(person_id, version)
        )
        """
    )

    # 考核状态流
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS person_assessment_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            version INTEGER NOT NULL,
            ts TEXT NOT NULL,
            data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (person_id) REFERENCES persons(id),
            UNIQUE(person_id, version)
        )
        """
    )

    # 社保信息状态流
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS person_social_security_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            version INTEGER NOT NULL,
            ts TEXT NOT NULL,
            data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (person_id) REFERENCES persons(id),
            UNIQUE(person_id, version)
        )
        """
    )

    # 公积金信息状态流
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS person_housing_fund_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            version INTEGER NOT NULL,
            ts TEXT NOT NULL,
            data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (person_id) REFERENCES persons(id),
            UNIQUE(person_id, version)
        )
        """
    )

    # 发薪记录状态流（每次批量发放会为每人追加一条记录）
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS person_payroll_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            version INTEGER NOT NULL,
            ts TEXT NOT NULL,
            data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (person_id) REFERENCES persons(id),
            UNIQUE(person_id, version)
        )
        """
    )

    # 公积金批量调整批次表
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS housing_fund_adjustment_batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            effective_date TEXT NOT NULL,
            min_base_amount REAL NOT NULL,
            max_base_amount REAL NOT NULL,
            default_company_rate REAL NOT NULL,
            default_personal_rate REAL NOT NULL,
            target_company TEXT,
            target_department TEXT,
            target_employee_type TEXT,
            note TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            affected_count INTEGER DEFAULT 0
        )
        """
    )

    # 公积金批量调整明细表
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS housing_fund_batch_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id INTEGER NOT NULL,
            person_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            current_base_amount REAL,
            current_company_rate REAL,
            current_personal_rate REAL,
            new_base_amount REAL NOT NULL,
            new_company_rate REAL NOT NULL,
            new_personal_rate REAL NOT NULL,
            applied INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (batch_id) REFERENCES housing_fund_adjustment_batches(id),
            FOREIGN KEY (person_id) REFERENCES persons(id)
        )
        """
    )

    # 社保批量调整批次表
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS social_security_adjustment_batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            effective_date TEXT NOT NULL,
            min_base_amount REAL NOT NULL,
            max_base_amount REAL NOT NULL,
            -- 默认公司/个人比例，可作为兜底值
            default_pension_company_rate REAL,
            default_pension_personal_rate REAL,
            default_unemployment_company_rate REAL,
            default_unemployment_personal_rate REAL,
            default_medical_company_rate REAL,
            default_medical_personal_rate REAL,
            default_maternity_company_rate REAL,
            default_maternity_personal_rate REAL,
            default_critical_illness_company_amount REAL,
            default_critical_illness_personal_amount REAL,
            target_company TEXT,
            target_department TEXT,
            target_employee_type TEXT,
            note TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            affected_count INTEGER DEFAULT 0
        )
        """
    )

    # 社保批量调整明细表
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS social_security_batch_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id INTEGER NOT NULL,
            person_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            current_base_amount REAL,
            current_pension_company_rate REAL,
            current_pension_personal_rate REAL,
            current_unemployment_company_rate REAL,
            current_unemployment_personal_rate REAL,
            current_medical_company_rate REAL,
            current_medical_personal_rate REAL,
            current_maternity_company_rate REAL,
            current_maternity_personal_rate REAL,
            current_critical_illness_company_amount REAL,
            current_critical_illness_personal_amount REAL,
            new_base_amount REAL NOT NULL,
            new_pension_company_rate REAL,
            new_pension_personal_rate REAL,
            new_unemployment_company_rate REAL,
            new_unemployment_personal_rate REAL,
            new_medical_company_rate REAL,
            new_medical_personal_rate REAL,
            new_maternity_company_rate REAL,
            new_maternity_personal_rate REAL,
            new_critical_illness_company_amount REAL,
            new_critical_illness_personal_amount REAL,
            applied INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (batch_id) REFERENCES social_security_adjustment_batches(id),
            FOREIGN KEY (person_id) REFERENCES persons(id)
        )
        """
    )

    # 薪酬批量发放批次表
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS payroll_batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            batch_period TEXT NOT NULL, -- 批次标识，一般为 YYYY-MM
            effective_date TEXT,        -- 生效日期，可选
            target_company TEXT,
            target_department TEXT,
            target_employee_type TEXT,
            note TEXT,
            status TEXT NOT NULL DEFAULT 'pending', -- pending, applied
            affected_count INTEGER DEFAULT 0
        )
        """
    )

    # 薪酬批量发放明细表（预览/确认阶段存放每人一行的发放计划）
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS payroll_batch_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id INTEGER NOT NULL,
            person_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            -- 组成部分：基数 + 绩效 + 各类扣减
            salary_base_amount REAL,              -- 基础工资部分（主要针对月薪制）
            salary_performance_base REAL,        -- 绩效基数部分（主要针对月薪制）
            performance_factor REAL,             -- 绩效系数（由考核等级映射）
            performance_amount REAL,             -- 实际绩效工资
            gross_amount_before_deductions REAL, -- 扣除前应发（基数 + 绩效）
            attendance_deduction REAL,           -- 考勤/请假扣款（>0 表示扣减）
            social_personal_amount REAL,         -- 个人承担社保
            housing_personal_amount REAL,        -- 个人承担公积金
            other_deduction REAL,                -- 其他补扣（可人工调整）
            net_amount_before_tax REAL,          -- 扣除后应发（未考虑个税）
            applied INTEGER NOT NULL DEFAULT 0,  -- 是否已写入个人发薪记录
            FOREIGN KEY (batch_id) REFERENCES payroll_batches(id),
            FOREIGN KEY (person_id) REFERENCES persons(id)
        )
        """
    )

    # 出勤记录表
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS attendance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            check_in_time TEXT,
            check_out_time TEXT,
            work_hours REAL DEFAULT 0.0,
            overtime_hours REAL DEFAULT 0.0,
            status TEXT NOT NULL DEFAULT '正常',
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (person_id) REFERENCES persons(id),
            UNIQUE(person_id, date)
        )
        """
    )

    # 请假记录表
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS leave_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            leave_date TEXT NOT NULL,
            leave_type TEXT NOT NULL,
            hours REAL NOT NULL,
            status TEXT NOT NULL DEFAULT '待审批',
            approver_person_id INTEGER,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (person_id) REFERENCES persons(id),
            FOREIGN KEY (approver_person_id) REFERENCES persons(id)
        )
        """
    )

    # 创建索引以优化查询
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_attendance_person_date ON attendance_records(person_id, date)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_leave_person_date ON leave_records(person_id, leave_date)"
    )

    conn.commit()
    conn.close()


def create_person(conn: sqlite3.Connection) -> int:
    cursor = conn.cursor()
    cursor.execute("INSERT INTO persons DEFAULT VALUES")
    conn.commit()
    return cursor.lastrowid

