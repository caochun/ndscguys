#!/bin/sh
# docker-entrypoint.sh
# 容器启动时自动初始化数据库（Volume 已挂载后执行）

set -e

DB_PATH="/app/data/twin.db"

if [ ! -f "$DB_PATH" ]; then
    echo "[entrypoint] 数据库不存在，初始化中..."
    python3 -c "from app.db import init_db; init_db()"

    # 如需写入测试数据，取消下面这行注释：
    # python3 -c "from app.seed import generate_test_data; generate_test_data()"

    echo "[entrypoint] 初始化完成"
else
    echo "[entrypoint] 数据库已存在，跳过初始化"
fi

exec gunicorn -w 2 -b 0.0.0.0:8080 main:app
