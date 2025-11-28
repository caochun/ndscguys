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

