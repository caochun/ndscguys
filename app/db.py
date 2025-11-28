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

    conn.commit()
    conn.close()


def create_person(conn: sqlite3.Connection) -> int:
    cursor = conn.cursor()
    cursor.execute("INSERT INTO persons DEFAULT VALUES")
    conn.commit()
    return cursor.lastrowid

