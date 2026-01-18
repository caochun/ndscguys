# 人力资源管理系统 (HRMS)

一个基于 **Schema Driven（Schema 驱动）** 和 **Twin（数字孪生）** 概念的人力资源管理系统。系统通过外部 DSL（YAML Schema）定义所有实体和活动的类型系统，实现完全由 Schema 驱动的数据模型、数据访问、业务逻辑和用户界面。

## 核心设计理念

### Schema Driven（Schema 驱动）

**核心思想**：系统的所有行为都基于外部 DSL（`app/schema/twin_schema.yaml`）定义的类型系统，而不是硬编码在代码中。

#### Schema 驱动的层次

1. **数据模型层**：Schema 定义决定了数据库表结构（注册表和状态表）
2. **数据访问层（DAO）**：通用的 `TwinDAO` 和 `TwinStateDAO` 根据 Schema 动态操作不同类型的数据
3. **业务逻辑层（Service）**：通用的 `TwinService` 基于 Schema 提供统一的业务接口
4. **API 层**：API 端点基于 Schema 动态处理请求，无需为每种类型编写专门代码
5. **用户界面层**：前端模板根据 Schema 动态渲染表单、列表和详情页

#### Schema 定义的内容

- **Twin 类型**：Entity（实体）或 Activity（活动）
- **字段定义**：字段类型、验证规则、UI 组件、存储方式
- **状态流模式**：版本化（Versioned）或时间序列（Time-Series）
- **关联关系**：Activity Twin 关联的 Entity Twin
- **元数据**：标签、描述、表名等

### Twin（数字孪生）

**Twin** 是对现实世界中观察对象的抽象表示。系统将所有实体和活动都统一抽象为 Twin，使用统一的数据访问模式。

#### Entity Twin（实体孪生）

代表现实世界中的**实体对象**，如：
- `person`（人员）
- `company`（公司）
- `project`（项目）

**特点**：
- 有独立的注册表（如 `persons` 表），存储 `twin_id`
- 有独立的状态流表（如 `person_history`），记录状态变更历史
- 状态数据存储在 JSON 字段中，支持灵活扩展

#### Activity Twin（活动孪生）

代表现实世界中的**活动/关系**，如：
- `person_company_employment`（人员-公司雇佣关系）
- `person_project_participation`（人员-项目参与活动）
- `person_company_attendance`（人员-公司考勤记录）

**特点**：
- 有独立的注册表（如 `person_company_employment_activities`），存储 `activity_id` 和关联的 Entity Twin ID
- 有独立的状态流表（如 `person_company_employment_history`），记录活动状态变更历史
- 通过 `related_entities` 定义关联的 Entity Twin（如 `person_id`、`company_id`）

### 状态流（State Stream）

每个 Twin 都有自己的**状态流**，记录状态的变更历史。状态流有两种模式：

#### 版本化状态流（Versioned）

- **版本号**：使用递增的 `version` 作为版本号
- **唯一键**：`(twin_id, version)`
- **适用场景**：基础信息变更、岗位信息变更、薪资配置变更等需要完整历史记录的场景
- **特点**：Append-only，每次变更追加新版本，保留完整历史

**示例**：人员基本信息变更
```yaml
person:
  mode: versioned
  unique_key: [person_id, version]
```

#### 时间序列状态流（Time-Series）

- **时间键**：使用时间维度（如 `date`、`batch_period`）作为唯一键
- **唯一键**：`(twin_id, time_key)`
- **适用场景**：打卡记录、薪酬记录等时间序列事件
- **特点**：每个时间点一条记录，记录该时间点的事件

**示例**：考勤记录
```yaml
person_company_attendance:
  mode: time_series
  unique_key: [person_id, company_id, date]
```

## Schema 定义示例

### Entity Twin Schema

```yaml
person:
  type: entity
  label: "人员"
  description: "人员实体"
  table: "persons"                    # 注册表名
  state_table: "person_history"        # 状态流表名
  mode: versioned                      # 状态流模式
  unique_key: [person_id, version]    # 唯一键
  
  fields:
    name:
      type: string
      required: true
      label: "姓名"
      validation:
        min_length: 1
        max_length: 50
      ui:
        component: text_input
    
    phone:
      type: string
      required: false
      label: "电话"
      validation:
        pattern: "^1[3-9]\\d{9}$"
      ui:
        component: tel_input
    
    avatar:
      type: string
      required: false
      label: "头像"
      ui:
        component: image_url
```

### Activity Twin Schema

```yaml
person_company_employment:
  type: activity
  label: "人员-公司雇佣活动"
  table: "person_company_employment_activities"  # 注册表名
  
  # 关联的 Entity Twin
  related_entities:
    - entity: person
      role: employee
      key: person_id
      required: true
    - entity: company
      role: employer
      key: company_id
      required: true
  
  state_table: "person_company_employment_history"  # 状态流表名
  mode: versioned
  unique_key: [activity_id, version]
  
  fields:
    person_id:
      type: reference
      reference_entity: person
      required: true
      storage: foreign_key              # 存储在注册表中
    
    company_id:
      type: reference
      reference_entity: company
      required: true
      storage: foreign_key
    
    position:
      type: string
      required: false
      label: "职位"
      ui:
        component: text_input
    
    change_type:
      type: enum
      required: true
      label: "变动类型"
      options: ["入职", "转岗", "离职"]
      ui:
        component: select
    
    change_date:
      type: date
      required: true
      label: "变动日期"
      ui:
        component: date_picker
```

## 架构设计

### 分层架构

```
┌─────────────────────────────────────────┐
│         用户界面层（Templates）          │
│   基于 Schema 动态渲染表单、列表、详情    │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│            API 层（api.py）              │
│   统一的 REST API，基于 Schema 处理请求   │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│        服务层（TwinService）             │
│   通用的业务逻辑，基于 Schema 操作 Twin   │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│   数据访问层（TwinDAO, TwinStateDAO）    │
│   通用的数据访问，基于 Schema 操作数据库   │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Schema 层（SchemaLoader）        │
│   加载和解析 YAML Schema 定义            │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         数据库层（SQLite）               │
│   根据 Schema 动态创建的表结构            │
└─────────────────────────────────────────┘
```

### 核心组件

#### 1. Schema Loader（`app/schema/loader.py`）

负责加载和解析 YAML Schema 文件：

```python
schema_loader = SchemaLoader()
person_schema = schema_loader.get_twin_schema("person")
```

**功能**：
- 加载 `twin_schema.yaml` 文件
- 解析 Twin 定义
- 提供查询接口（获取指定 Twin 的 Schema、列出所有 Entity/Activity Twin）

#### 2. Twin DAO（`app/daos/twins/twin_dao.py`）

通用的 Twin 数据访问对象，处理所有 Twin 类型的创建和查询：

```python
twin_dao = TwinDAO(db_path)
person_id = twin_dao.create_entity_twin("person")
employment_id = twin_dao.create_activity_twin(
    "person_company_employment",
    {"person_id": 1, "company_id": 2}
)
```

**特点**：
- 根据 Schema 动态创建 Entity 或 Activity Twin
- 自动处理注册表的插入
- 支持查询 Twin 信息

#### 3. Twin State DAO（`app/daos/twins/state_dao.py`）

通用的状态流数据访问对象，处理所有 Twin 的状态变更：

```python
state_dao = TwinStateDAO(db_path)
state_dao.append("person", person_id, {"name": "张三", "phone": "13800138000"})
latest_state = state_dao.get_latest("person", person_id)
all_states = state_dao.list_states("person", person_id)
```

**功能**：
- `append()`：追加状态变更（自动处理版本号或时间键）
- `get_latest()`：获取最新状态
- `list_states()`：列出所有历史状态
- `query_latest_states()`：查询最新状态（支持过滤）

**智能过滤**：
- 对于 Entity Twin：直接过滤 `data` JSON 字段
- 对于 Activity Twin：自动识别 `related_entities` 的 key（如 `person_id`），先查询注册表获取 `twin_id` 列表，再过滤状态表

#### 4. Twin Service（`app/services/twin_service.py`）

通用的业务逻辑层，提供统一的业务接口：

```python
service = TwinService(db_path)
persons = service.list_twins("person")
person = service.get_twin("person", person_id)
employments = service.list_twins("person_company_employment", filters={"person_id": 1})
```

**功能**：
- `list_twins()`：列出所有 Twin 及其最新状态（支持过滤）
- `get_twin()`：获取指定 Twin 的详情（包含完整历史）
- `query_twins()`：基于过滤条件查询 Twin

**特点**：
- 自动处理 Entity 和 Activity Twin 的差异
- 自动展开状态数据
- 自动添加 Activity Twin 的关联实体 ID

#### 5. API 层（`app/api.py`）

统一的 REST API 端点，基于 Schema 处理请求：

```python
@api_bp.route("/persons", methods=["GET"])
def list_persons():
    service = get_twin_service()
    persons = service.list_twins("person")
    return jsonify({"success": True, "data": persons})
```

**特点**：
- 所有端点都使用统一的 `TwinService`
- 在 API 层进行数据增强（关联、合并）
- 统一的错误处理和响应格式

#### 6. 用户界面层（`app/templates/`）

基于 Schema 动态渲染的 HTML 模板：

```html
<!-- 前端 JavaScript 根据 Schema 动态生成表格 -->
<script>
  const schema = {{ schema | tojson }};
  // 根据 schema.fields 动态生成表头和表格行
</script>
```

**特点**：
- 模板接收 Schema 对象
- JavaScript 根据 Schema 动态渲染表单、列表、详情页
- 支持字段类型、验证规则、UI 组件的动态渲染

## 项目结构

```
app/
├── __init__.py                 # Flask 应用工厂
├── models/
│   └── twins/                  # Twin 模型
│       ├── base.py             # Twin 基类
│       ├── entity.py            # Entity Twin
│       ├── activity.py          # Activity Twin
│       └── state.py             # Twin State（状态记录）
├── schema/
│   ├── twin_schema.yaml         # Twin 类型系统定义（YAML DSL）
│   ├── loader.py                # Schema 加载器
│   └── models.py                # Schema 数据结构（FieldDefinition, TwinSchema）
├── daos/
│   ├── base_dao.py              # 基础 DAO
│   └── twins/
│       ├── twin_dao.py          # Twin DAO（创建、查询 Twin）
│       └── state_dao.py         # 状态流 DAO（管理状态变更、查询）
├── services/
│   └── twin_service.py          # 通用 Twin 服务层
├── api.py                       # REST API 端点
├── routes.py                    # Web 页面路由
├── db.py                        # 数据库初始化（基于 Schema）
├── seed.py                      # 测试数据生成
└── templates/                   # HTML 模板（基于 Schema 动态渲染）
    ├── base.html
    ├── persons.html
    ├── employments.html
    └── projects.html
```

## 数据存储设计

### Entity Twin 存储

**注册表**（如 `persons`）：
```sql
CREATE TABLE persons (
    id INTEGER PRIMARY KEY AUTOINCREMENT
);
```

**状态流表**（如 `person_history`）：
```sql
CREATE TABLE person_history (
    twin_id INTEGER NOT NULL,
    version INTEGER NOT NULL,
    ts TEXT NOT NULL,
    data TEXT NOT NULL,  -- JSON 格式
    PRIMARY KEY (twin_id, version),
    FOREIGN KEY (twin_id) REFERENCES persons(id)
);
```

### Activity Twin 存储

**注册表**（如 `person_company_employment_activities`）：
```sql
CREATE TABLE person_company_employment_activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER NOT NULL,
    company_id INTEGER NOT NULL,
    FOREIGN KEY (person_id) REFERENCES persons(id),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);
```

**状态流表**（如 `person_company_employment_history`）：
```sql
CREATE TABLE person_company_employment_history (
    twin_id INTEGER NOT NULL,
    version INTEGER NOT NULL,
    ts TEXT NOT NULL,
    data TEXT NOT NULL,  -- JSON 格式（不包含 person_id, company_id）
    PRIMARY KEY (twin_id, version),
    FOREIGN KEY (twin_id) REFERENCES person_company_employment_activities(id)
);
```

**注意**：`related_entities` 的字段（如 `person_id`、`company_id`）存储在注册表中，而不是状态表的 `data` JSON 中。

## 核心功能

### ✅ 已实现

- **Schema 系统**：YAML Schema 定义、加载器、解析器
- **Twin 模型**：Entity Twin、Activity Twin、Twin State
- **数据访问层**：通用的 TwinDAO 和 TwinStateDAO
- **服务层**：通用的 TwinService
- **API 层**：REST API 端点（人员、雇佣关系、项目）
- **Web UI**：基于 Schema 动态渲染的页面（人员列表、雇佣关系、项目列表）
- **数据库初始化**：根据 Schema 自动创建表结构
- **测试数据生成**：基于 Schema 生成测试数据

### ⏳ 待实现

- **字段验证器**：基于 Schema 的字段验证（类型、格式、必填等）
- **创建/编辑功能**：基于 Schema 动态生成表单，支持创建和编辑 Twin
- **高级查询**：更复杂的过滤和排序功能
- **权限控制**：基于角色的访问控制

## Schema Driven 的优势

1. **无需修改代码即可扩展**：添加新的 Twin 类型只需在 Schema 文件中定义，系统自动支持
2. **统一的访问模式**：所有 Twin 类型使用相同的 DAO、Service 和 API 接口
3. **类型安全**：基于 Schema 的字段验证和类型检查
4. **动态 UI**：前端根据 Schema 自动渲染表单和列表，无需为每种类型编写专门代码
5. **灵活的数据模型**：JSON 字段存储状态数据，支持灵活扩展，无需频繁修改表结构
6. **完整的历史记录**：状态流模式自动记录所有变更历史
7. **易于维护**：Schema 集中管理，修改类型定义只需更新 YAML 文件

## 技术栈

- **Python 3.9+**
- **Flask 3.0.0** - Web 框架
- **SQLite** - 数据库（支持 JSON1 扩展）
- **PyYAML 6.0.1** - YAML Schema 解析
- **Tailwind CSS** - 前端样式框架（CDN）
- **pytest 8.3.3** - 测试框架

## 安装和运行

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化数据库（自动根据 Schema 创建表结构）
python -c "from app.db import init_db; from config import Config; init_db(str(Config.DATABASE_PATH))"

# 4. 生成测试数据（可选）
python -c "from app.seed import generate_test_data; from config import Config; generate_test_data(str(Config.DATABASE_PATH))"

# 5. 运行应用
python main.py
# 或指定端口
PORT=5001 python main.py
```

访问 `http://localhost:5000`（或指定端口）查看 Web UI。

## API 端点

### 人员相关
- `GET /api/persons` - 获取人员列表
- `GET /api/persons/<person_id>` - 获取人员详情（含历史）

### 雇佣关系相关
- `GET /api/employments` - 获取雇佣关系列表
- `GET /api/employments/<employment_id>` - 获取雇佣关系详情
- `GET /api/persons/<person_id>/employments` - 获取指定人员的所有雇佣关系

### 项目相关
- `GET /api/projects` - 获取项目列表
- `GET /api/projects/<project_id>` - 获取项目详情（含参与人员）
- `GET /api/projects/<project_id>/persons/<person_id>/participations` - 获取指定人员在项目中的参与记录
- `GET /api/person-project-status` - 获取所有人员在项目中的参与状态

## 开发指南

### 添加新的 Twin 类型

1. **在 `app/schema/twin_schema.yaml` 中添加定义**：

```yaml
my_new_twin:
  type: entity  # 或 activity
  label: "我的新 Twin"
  table: "my_new_twins"
  state_table: "my_new_twin_history"
  mode: versioned
  unique_key: [twin_id, version]
  fields:
    field1:
      type: string
      required: true
      label: "字段1"
```

2. **重新初始化数据库**（会自动创建新表）：
```bash
python -c "from app.db import init_db; from config import Config; init_db(str(Config.DATABASE_PATH))"
```

3. **使用通用接口操作**：
```python
service = TwinService()
twins = service.list_twins("my_new_twin")
```

4. **（可选）添加 API 端点和 Web UI**：
```python
@api_bp.route("/my-new-twins", methods=["GET"])
def list_my_new_twins():
    service = get_twin_service()
    twins = service.list_twins("my_new_twin")
    return jsonify({"success": True, "data": twins})
```

## 许可证

（待定）
