# 人员状态管理原型

一个面向“人员状态追踪”的原型系统，使用 Flask + SQLite 实现 **State Stream（状态流）** 模式：以 `person_id` 为聚合根，把基础信息、岗位信息等拆解为独立的 Append-only 流，每次变更只追加新版本，不改写历史，再通过 Web UI + API 展示当前状态及历史沿革。

## 核心设计理念

- **“状态流”驱动**：每个状态类型（基础信息、岗位信息）各自维护只增不改的版本流（`person_basic_history`、`person_position_history`）。每条记录包含 `person_id/ts/version/data(JSON)`，从而实现任意状态的回放、对比与追溯。
- **聚合根 = Person**：一个人是多个状态流的集合，系统根据最新版本汇聚“当前状态”，也可按时间点获取历史状态（`get_at()`）。
- **轻量存储 + JSON 扩展**：状态数据放入 `data` JSON 字段，除核心索引外无需频繁迁表，便于快速迭代模型。
- **Web + API 统一**：同一 Flask 应用既 serve REST API，也提供 Material 风格 UI，便于预览状态流效果并做 Demo。

## 功能概览

- **状态流模型**
  - `person_basic_history`：append-only 存储人员基础信息（姓名、身份证、电话、邮箱等），每次变更生成新版本。
  - `person_position_history`：append-only 存储岗位信息（公司、员工号、部门、职位等），支持跨公司变动。
- **服务与 API**
  - `PersonService` 封装状态流的读写，提供列表、创建、详情查询。
  - `/api/persons` REST 接口：列出人员、创建人员、查看人员详情。
- **前端界面（Material 风格）**
  - 卡片式人员列表（展示姓名、身份证、电话、头像）。
  - Modal 中以 Tab 方式区分基础信息和岗位信息，并显示历史表格。
- **种子数据**
  - 启动时自动初始化 30 名测试人员：
    - 90% 拥有岗位信息，其中 45% 归属 “SC高科技公司”，45% 归属 “SC能源科技公司”。
    - 50% 的岗位记录会追加至少一次职位变动（可能跨公司）。
    - 20% 的人员会追加基础信息变更（电话、地址）。
    - 头像使用 DiceBear “micah” 风格自动生成。

## 运行方式

```bash
# 1. 创建虚拟环境（可选）
python3 -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动应用
# 默认端口 5000，可通过 PORT 环境变量覆盖
python main.py

# 或指定端口
PORT=5001 python main.py
```

启动后访问 `http://localhost:5000`（或对应端口）即可看到界面。

## 项目结构

```
app/
├── api.py                 # REST API 蓝图
├── routes.py              # Web 页面路由
├── db.py                  # SQLite 初始化工具
├── seed.py                # 种子数据生成
├── services/
│   └── person_service.py  # 人员状态服务
├── daos/
│   ├── base_dao.py
│   ├── entity_state/
│   │   └── base.py        # 通用状态流 DAO
│   └── person_state_dao.py
├── models/
│   └── person_states/
│       ├── base.py
│       ├── basic.py
│       └── position.py
├── templates/
│   └── persons.html
└── static/
    └── js/persons.js
```

## 测试

使用 pytest 验证状态流 DAO 的 append / list / get_at 等基础行为：

```bash
pytest
```

当前提供 `tests/test_entity_state_dao.py`，确保核心 DAO 的功能正常。

## 备注

- 数据库文件默认位于 `data/person_state.db`，可删除后重启以重新生成种子数据。
- 这是一个演示性质的原型，为多状态流（基础信息、岗位信息等）提供骨架，后续可继续扩展薪资、考核等状态流以及更丰富的界面交互。

