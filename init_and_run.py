"""
初始化数据并启动应用
"""
import os
import sys
from pathlib import Path

from config import Config
from app.seed import seed_initial_data

def main():
    # 获取数据库路径
    db_path = Config.DATABASE_PATH
    
    # 删除旧数据库（如果存在）
    if os.path.exists(db_path):
        print(f"删除旧数据库: {db_path}")
        os.remove(db_path)
    
    # 初始化数据
    print("开始初始化数据...")
    seed_initial_data(db_path, target_count=30)
    print("数据初始化完成！")
    
    # 启动应用
    print("启动应用...")
    from main import app
    app.run(host="0.0.0.0", port=5000, debug=True)

if __name__ == "__main__":
    main()
