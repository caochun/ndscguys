# 人事管理系统

一个基于 Python 和 PyQt6 的桌面人事管理系统，支持 macOS 和 Windows 平台。

## 功能特性

### 已实现功能

1. **员工基本信息管理**
   - 个人信息（不变动）：姓名、出生日期、性别、手机、邮箱、员工编号
   - 入职信息（会变动）：部门、职位、上级、入职时间
   - 支持新增、编辑、删除员工
   - 入职信息变更自动记录历史版本

2. **入职信息版本管理**
   - 每次入职信息变更都会记录历史版本
   - 可以查看员工的入职信息变更历史
   - 变更时支持填写变更原因

## 技术栈

- Python 3.12+
- PyQt6 - GUI 框架
- SQLite - 数据库

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行应用

```bash
python main.py
```

## 数据库

数据库文件默认存储在：
- **macOS**: `~/Library/Application Support/HRSystem/hr_system.db`
- **Windows**: `%APPDATA%/HRSystem/hr_system.db`

## 项目结构

```
ndscguys/
├── main.py                 # 主程序入口
├── database.py             # 数据库初始化和连接管理
├── models.py               # 数据模型类
├── employee_service.py     # 员工信息管理服务
├── ui/
│   ├── main_window.py      # 主窗口
│   └── employee_dialog.py  # 员工信息编辑对话框
└── requirements.txt        # 依赖包列表
```

## 数据模型

### employees 表（员工个人信息）
- id: 主键
- employee_number: 员工编号（唯一）
- name: 姓名
- birth_date: 出生日期
- gender: 性别
- phone: 手机
- email: 邮箱
- created_at, updated_at: 时间戳

### employment_info 表（当前入职信息）
- id: 主键
- employee_id: 员工ID（外键）
- department: 部门
- position: 职位
- supervisor_id: 上级员工ID（外键）
- hire_date: 入职时间
- version: 当前版本号
- created_at, updated_at: 时间戳

### employment_info_history 表（入职信息历史）
- id: 主键
- employee_id: 员工ID（外键）
- department: 部门
- position: 职位
- supervisor_id: 上级员工ID（外键）
- hire_date: 入职时间
- version: 版本号
- changed_at: 变更时间
- change_reason: 变更原因
- created_at: 创建时间

## 使用说明

1. **新增员工**
   - 点击"新增员工"按钮
   - 填写个人信息和入职信息
   - 点击"保存"

2. **编辑员工**
   - 在员工列表中选择要编辑的员工
   - 点击"编辑员工"按钮
   - 修改信息后点击"保存"
   - 如果修改了入职信息，系统会自动记录历史版本

3. **删除员工**
   - 在员工列表中选择要删除的员工
   - 点击"删除员工"按钮
   - 确认删除操作

## 待实现功能

- 薪资计算功能
- 薪资发放记录
- 历史记录查询界面
- 报表统计功能

