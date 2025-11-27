"""
基础 DAO：提供 SQLite 连接
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Optional


class BaseDAO:
    """所有 DAO 的基础类"""

    def __init__(self, db_path: Optional[str] = None):
        # 默认读取环境变量 APP_DB_PATH，若没有则使用内存数据库
        self.db_path = db_path or os.getenv("APP_DB_PATH", ":memory:")
        self._connection: Optional[sqlite3.Connection] = None

    def get_connection(self) -> sqlite3.Connection:
        if self._connection is None:
            if self.db_path != ":memory:":
                Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
        return self._connection

    def close(self):
        if self._connection is not None:
            self._connection.close()
            self._connection = None

