"""
人事管理系统 - 主程序入口
"""
from app import create_app
import os

# 从环境变量获取配置，默认为 development
config_name = os.getenv('FLASK_ENV', 'development')

app = create_app(config_name)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)

