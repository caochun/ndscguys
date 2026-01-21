## 概览

这是一个基于 **Schema Driven（Schema 驱动）** 和 **Twin（数字孪生）** 核心设计之上的人力资源管理系统（HRMS）示例项目。

整个系统可以分成两层来看：

- **核心平台层**：一个通用的 Schema 驱动 Twin 平台（不依赖具体业务，只依赖 `twin_schema.yaml`）。
- **HR 业务层**：在该平台之上实现的人力资源业务（人员、聘用、项目、社保、公积金、专项附加扣除、工资等）。

下面先讲清楚“平台能力”，再说明“在这个平台上实现了哪些 HR 业务”。

---

## 一、核心设计：Schema Driven Twin 平台

### 1.1 Schema Driven（Schema 驱动）

**核心思想**：系统的所有行为都基于外部 DSL（`app/schema/twin_schema.yaml`）定义的类型系统，而不是硬编码在 Python / HTML / SQL 中。

#### 1.1.1 Schema 驱动的五个层次

1. **数据模型层**  
   - Schema 决定数据库表结构（注册表 + 状态表）
   - 例如 `person`、`person_company_employment` 对应不同的表组合

2. **数据访问层（DAO）**  
   - `TwinDAO` 负责 Twin 注册表（entity / activity 实例）
   - `TwinStateDAO` 负责 Twin 状态表（历史版本 / 时间序列）

3. **业务逻辑层（Service）**  
   - `TwinService`：完全通用的 Twin 业务接口
   - 只依赖 Schema，不依赖具体业务字段

4. **API 层（REST）**  
   - 统一的 `/api/twins/<twin_name>` 接口
   - 不需要为每个业务类型写一套 CRUD

5. **用户界面层（Templates + JS）**  
   - 模板接收 Schema JSON
   - JS 根据 `schema.fields` 动态绘制表格、表单、详情

#### 1.1.2 Schema 中定义了什么

- **Twin 类型**：`type: entity | activity`
- **字段**：类型、label、验证、UI 组件、存储方式（JSON / 外键 / 唯一键）
- **状态流模式**：`mode: versioned | time_series`
- **唯一键**：如 `[person_id, version]` 或 `[activity_id, period]`
- **关联关系**：Activity Twin 的 `related_entities`（person / company / project 等）

Schema 一改：

- 表结构自动重建（`init_db`）
- DAO、Service、API 自动适配
- 前端 UI 自动感知（字段新增/删除、label、枚举等）

---

### 1.2 Twin（数字孪生）模型

Twin 把“实体”和“活动”统一抽象，统一用一套 DAO/Service/API/UI。

#### 1.2.1 Entity Twin（实体孪生）

代表静态或相对稳定的对象，例如：

- `person`（人员）
- `company`（公司）
- `project`（项目）

**存储结构：**

- 注册表：如 `persons`，只存 `id`
- 状态表：如 `person_history`，存 `twin_id + version/time_key + data(JSON)`

#### 1.2.2 Activity Twin（活动孪生）

代表“行为 / 关系 / 事件”，例如：

- `person_company_employment`（人员-公司聘用）
- `person_project_participation`（人员-项目参与）
- `person_company_attendance`（人员考勤）
- `person_company_payroll`（人员工资发放）

**存储结构：**

- 注册表：如 `person_company_employment_activities`  
  存 `id` + `person_id` + `company_id` 等外键
- 状态表：如 `person_company_employment_history`  
  存 `twin_id + version/time_key + data(JSON)`（只存业务属性，不存外键）

Activity Twin 通过 `related_entities` 描述与 Entity Twin 的关系。

---

### 1.3 状态流（State Stream）

每个 Twin 都有自己的状态流，记录历史：

#### 1.3.1 版本化状态流（Versioned）

- 键：`(twin_id, version)`
- 场景：基本信息、岗位变更、薪资配置、参与项目状态等
- 特点：append-only，每次变更生成新版本

示例（person）：

```yaml
person:
  mode: versioned
  unique_key: [person_id, version]
```

#### 1.3.2 时间序列状态流（Time-Series）

- 键：`(twin_id, time_key)`（例如 date、batch_period、period）
- 场景：打卡、工资单等“按时间点/周期”的记录

示例（考勤）：

```yaml
person_company_attendance:
  mode: time_series
  unique_key: [activity_id, date]
```

示例（工资单）：

```yaml
person_company_payroll:
  mode: time_series
  unique_key: [activity_id, period]
```

---

### 1.4 核心组件

#### 1.4.1 Schema Loader（`app/schema/loader.py`）

**职责：**

- 读取 `twin_schema.yaml`
- 解析为 `TwinSchema / FieldDefinition` 对象
- 提供查询函数：`get_twin_schema(name)` / `list_entity_twins()` / `list_activity_twins()`

#### 1.4.2 TwinDAO（`app/daos/twins/twin_dao.py`）

**职责：**

- 创建 Entity Twin：在对应注册表插入一条记录，返回 `id`
- 创建 Activity Twin：在注册表插入记录并写入关联的 entity id
- 查询 Twin 是否存在、获取注册信息

#### 1.4.3 TwinStateDAO（`app/daos/twins/state_dao.py`）

**核心接口：**

- `append(twin_name, twin_id, data, time_key=None)`  
  自动根据 `mode` 选择 version / time_key
- `get_latest(twin_name, twin_id)`  
  获取某个 Twin 的最新状态
- `list_states(twin_name, twin_id)`  
  获取历史记录
- `query_states(...)` / `query_latest_states(...)`  
  按字段过滤、按版本/时间排序
- `query_latest_states_with_enrich(...)`  
  对 Activity Twin 做 **JOIN enrich**：
  - 根据 `related_entities` JOIN 对应 Entity 注册表和状态表
  - 支持 versioned 和 time_series 两种模式
  - 返回字段形如：`person_name`、`company_name`

#### 1.4.4 TwinService（`app/services/twin_service.py`）

**完全通用的 Service 层：**

- `list_twins(twin_name, filters=None, enrich=None)`
- `get_twin(twin_name, twin_id)`
- `create_twin(twin_name, data)`
- `update_twin(twin_name, twin_id, data)`
- `_apply_auto_fields(...)`：根据 `auto: date/timestamp` 自动补充字段

Service 不写任何业务 if/else，全靠 Schema。

#### 1.4.5 API 层（`app/api.py`）

**统一的 Twin API：**

- `GET /api/twins/<twin_name>`  
  - 支持查询参数过滤  
  - 支持 `enrich=true` 或 `enrich=person,company`
- `GET /api/twins/<twin_name>/<id>`
- `POST /api/twins/<twin_name>`
- `PUT /api/twins/<twin_name>/<id>`

**统一响应格式：**

```json
{
  "success": true,
  "data": [...],
  "count": 10
}
```

#### 1.4.6 前端模板层（`app/templates/*.html`）

通用思路：

- 后端把 Twin 的 Schema 通过 `schema | tojson` 注入模板
- JS 使用 schema 的字段定义：
  - 动态生成表头和列
  - 根据 `type` / `enum` / `ui.component` 渲染展示和格式化
  - 表单校验可以基于 `validation` 定义逐步完善

---

### 1.5 数据库存储模式（抽象层）

#### 1.5.1 Entity Twin

- 注册表：`<entity_table>(id)`
- 状态表：`<state_table>(twin_id, version/time_key, ts, data JSON)`

#### 1.5.2 Activity Twin

- 注册表：`<activity_table>(id, person_id, company_id, ...)`
- 状态表：`<state_table>(twin_id, version/time_key, ts, data JSON)`
- `related_entities` 字段（person_id、company_id 等）**只在注册表中存一份**，状态表只保存业务属性

---

## 二、HR 业务：在 Twin 平台上的具体实现

在以上通用设计之上，本项目实现了一套“人力资源管理”业务，所有业务对象都通过 Twin 来描述和驱动。

### 2.1 核心业务 Twin 一览

#### 2.1.1 Entity Twins

- **`person`**：人员基础信息（姓名、证件、联系方式、头像等）
- **`company`**：公司基础信息
- **`project`**：项目（类型、内部/外部项目名、项目编号、状态、起止日期、预算等）

#### 2.1.2 Activity Twins

- **就业与任职： `person_company_employment`**
  - 关联：`person`、`company`
  - 字段：职位、部门、员工号、员工类别、薪资类型（年薪/月薪/日薪）、薪资金额、变动类型、变动日期等
  - 模式：`mode: versioned`，记录历次变更（入职、转岗、离职等）

- **项目参与： `person_project_participation`**
  - 关联：`person`、`project`
  - 字段：参与状态（入项 / 出项）、变动日期、劳务定价（劳务型项目适用）
  - 模式：`versioned`

- **考勤： `person_company_attendance`**
  - 关联：`person`、`company`
  - 字段：日期、上下班时间、工时等
  - 模式：`time_series`，按天记录

- **人员考核： `person_assessment`**
  - 关联：`person`
  - 字段：考核周期、日期、等级（优秀/良好/合格/不合格）、评语等
  - 模式：`versioned`

- **社保基数： `person_company_social_security_base`**
  - 关联：`person`、`company`
  - 字段：缴费基数、生效日期等
  - 模式：`versioned`

- **公积金基数： `person_company_housing_fund_base`**
  - 关联：`person`、`company`
  - 字段：缴费基数、生效日期等

- **专项附加扣除： `person_tax_deduction`**
  - 关联：`person`
  - 字段：扣除类型、金额、生效/失效日期、状态、备注等

- **工资单： `person_company_payroll`**
  - 关联：`person`、`company`
  - 模式：`time_series`，按 `period=YYYY-MM` 记录
  - 字段分两类：
    - **计算依据快照**：`base_salary`、`salary_type`、`assessment_grade`、`social_security_base`、`housing_fund_base`、`tax_deduction_total`
    - **计算结果**：`base_amount`、`performance_bonus`、`social_security_deduction`、`housing_fund_deduction`、`taxable_income`、`tax_deduction`、`total_amount`
    - **状态信息**：`payment_date`、`status`、`remarks`

以上所有 Twin 定义都只存在于 `twin_schema.yaml` 中，其余层（DAO/Service/API/UI）全部是通用代码。

---

### 2.2 业务服务层：PayrollService 等

在通用 `TwinService` 之上，项目增加了一个**少量业务逻辑更强的服务**：

#### 2.2.1 `PayrollService`（`app/services/payroll_service.py`）

**职责：**

- 从各类 Activity Twin 中读取“最新有效状态”：
  - 最新聘用薪资（`person_company_employment`）
  - 最新考核（`person_assessment`）
  - 最新社保、公积金基数（`person_company_social_security_base` / `person_company_housing_fund_base`）
  - 当前有效的专项附加扣除（`person_tax_deduction`）
- 按既定规则计算当月工资（预览 / 入库）：
  - 绩效奖金（根据考核等级）
  - 社保、公积金扣除（按基数按比例计算）
  - 个税应纳税所得额 + 个税金额
  - 实发工资合计
- 将当期用于计算的“输入值”以快照形式写入 `person_company_payroll`，保证**历史可追溯**，不依赖后续 Activity Twin 的修改。

**对平台的复用：**

- 所有底层读写仍通过 `TwinService` + `TwinDAO` + `TwinStateDAO`
- 业务只负责“如何用现有 Twin 组合出工资单”

---

### 2.3 业务 API

除了统一的 `/api/twins/<twin_name>` 接口外，针对工资做了两个业务 API：

- `POST /api/payroll/calculate`  
  - 入参：`person_id`, `company_id`, `period`（YYYY-MM）  
  - 行为：调用 `PayrollService.calculate_payroll`，只算不落库

- `POST /api/payroll/generate`  
  - 入参同上  
  - 行为：调用 `PayrollService.generate_payroll`，生成一条 `person_company_payroll` Activity Twin + 对应 state

其他页面（聘用列表、项目参与、社保/公积金/专项扣除）主要通过统一的 Twin API + enrich 实现。

---

### 2.4 业务 UI 页面

UI 层全部是“在 Schema + Twin 平台之上”的具体业务实现。

#### 2.4.1 人员管理（`persons.html`）

- 使用 `person` Schema 驱动：
  - 人员卡片列表（头像、姓名、核心信息）
  - 详情弹窗：当前信息 + 历史记录（根据 TwinState 历史）
  - 布局针对 HR 场景做了优化（紧凑、4 列卡片、头像 URL 在编辑表单中维护）

#### 2.4.2 聘用管理（`employments.html`）

- 使用 `person_company_employment` Schema：
  - 主表格：按 `person` 聚合，只显示每人最新聘用状态
  - 点击行：弹窗展示该人员全部聘用历史
  - 显示薪资类型 + 薪资金额（格式化为 “¥金额 / 年|月|日”）

#### 2.4.3 项目管理（`projects.html`）

- 使用 `project` + `person_project_participation` Schema：
  - Tab1：项目列表（基本字段 +状态）
  - Tab2：“人员在项”：按人维度查看各项目参与状态
  - 点击项目行：展示该项目参与人员列表
  - 点击人员参与记录：展示该人该项目的完整参与历史
  - 对“专项型”项目，劳务价展示为 “N/A”

#### 2.4.4 缴费与扣除（`contributions.html`）

统一页面下的三个标签：

- “社保基数” Tab → `person_company_social_security_base`
- “公积金基数” Tab → `person_company_housing_fund_base`
- “专项附加扣除” Tab → `person_tax_deduction`

实现方式：

- 每个板块内部本质上是一个“小页面”：有自己的过滤栏、表格、详情弹窗、表单
- 但不再使用 iframe，而是把三块内容嵌入同一 DOM 中，通过 Tab 控制显示/隐藏
- 所有表格和表单字段都由对应 Schema 决定

#### 2.4.5 工资管理（`payroll.html`）

两个标签页：

1. **“生成工资单”**
   - 选择周期、公司、人员
   - 调用 `/api/payroll/calculate` 展示“计算依据 + 计算结果”
   - 用户确认后调用 `/api/payroll/generate` 落库

2. **“工资单列表”**
   - 使用 `person_company_payroll` Schema + enrich（person, company）
   - 过滤条件：周期、公司名、人员名、状态
   - 列表展示关键字段：周期、人员、公司、应发、实发、状态、发放日期
   - 详情弹窗展示完整快照（输入 & 结果），用于审计和追溯

---

## 三、项目结构（平台 + 业务混合）

```text
app/
├── __init__.py                  # Flask 应用工厂，注册 web / api 蓝图
├── db.py                        # 根据 Schema 初始化数据库
├── seed.py                      # 基于 Schema 生成测试数据
├── schema/
│   ├── twin_schema.yaml         # Twin 类型系统定义（平台 + HR 业务）
│   ├── loader.py                # SchemaLoader（平台核心）
│   └── models.py                # Schema 数据结构
├── models/
│   └── twins/
│       ├── base.py              # Twin 基类
│       ├── entity.py            # Entity Twin
│       ├── activity.py          # Activity Twin
│       └── state.py             # Twin State（状态记录）
├── daos/
│   ├── base_dao.py
│   └── twins/
│       ├── twin_dao.py          # TwinDAO（平台）
│       └── state_dao.py         # TwinStateDAO（平台）
├── services/
│   ├── twin_service.py          # 通用 TwinService（平台）
│   └── payroll_service.py       # PayrollService（HR 业务）
├── api.py                       # 统一 Twin API + payroll 专用 API
├── routes.py                    # Web 页面路由（HR 业务 UI）
└── templates/
    ├── base.html                # 通用布局 + 导航
    ├── persons.html             # 人员管理（HR 业务）
    ├── employments.html         # 聘用管理
    ├── projects.html            # 项目 & 人员在项
    ├── contributions.html       # 社保 / 公积金 / 专项扣除 标签页
    └── payroll.html             # 工资管理
```

---

## 四、安装与运行

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化数据库（根据 Schema 自动建表）
python -c "from app.db import init_db; from config import Config; init_db(str(Config.DATABASE_PATH))"

# 4. 生成测试数据（可选）
python -c \"from app.seed import generate_test_data; from config import Config; generate_test_data(str(Config.DATABASE_PATH))\"

# 5. 启动应用
python main.py
# 或指定端口
PORT=5001 python main.py
```

访问 `http://localhost:5000` 或 `http://localhost:5001` 查看 Web UI。

---

## 五、统一 Twin API 使用说明

### 5.1 列出 Twin

```text
GET /api/twins/<twin_name>?field1=value1&field2=value2&enrich=true
```

**参数：**

- `field1`, `field2`：字段过滤（支持 entity / activity）
- `enrich`（仅对 Activity Twin 有效）：
  - `enrich=true`：enrich 所有关联实体
  - `enrich=person,company`：只 enrich 指定实体

**示例：**

```text
# 所有人
GET /api/twins/person

# 所有聘用记录（enrich 人员和公司）
GET /api/twins/person_company_employment?enrich=true

# 某人所有聘用记录
GET /api/twins/person_company_employment?person_id=1&enrich=person,company

# 某项目所有参与记录
GET /api/twins/person_project_participation?project_id=1&enrich=person,project
```

### 5.2 获取 Twin 详情

```text
GET /api/twins/<twin_name>/<twin_id>
```

返回：

- `id`：Twin ID
- `current`：当前状态
- `history`：历史状态数组（包含 version / ts / data）

### 5.3 创建 / 更新 Twin

```text
POST /api/twins/<twin_name>
PUT  /api/twins/<twin_name>/<twin_id>
Content-Type: application/json
```

对于 Activity Twin，请在 body 中包含所有 required 的 `related_entities` id，比如：

```json
{
  "person_id": 1,
  "company_id": 2,
  "change_type": "入职",
  "change_date": "2024-01-01"
}
```

更新会**追加新状态**，不会覆盖历史。

### 5.4 业务专用端点（示例）

- `GET /api/persons/<person_id>/employments`  
  获取某人的所有聘用记录（包含公司信息）
- `GET /api/projects/<project_id>`  
  获取项目详情（包含参与人员列表）
- `POST /api/payroll/calculate` / `POST /api/payroll/generate`  
  工资计算与生成（见上文说明）

---

## 六、扩展指南：在平台上加新业务

1. 在 `twin_schema.yaml` 中新增 Twin 定义（entity 或 activity）。
2. 重新执行数据库初始化（或迁移）。
3. 使用 `TwinService` / `/api/twins/<twin_name>` 即可进行 CRUD。
4. 如有复杂业务规则，可增加专用 Service（类似 `PayrollService`）。
5. 如需前端界面，在 `routes.py` 新增路由，传入对应 Schema，前端 JS 按同样模式动态渲染即可。

---

## 七、技术栈

- **Python 3.9+**
- **Flask 3.0.0**
- **SQLite + JSON1 扩展**
- **PyYAML 6.0.1**
- **Tailwind CSS（通过 CDN 用于示例 UI）**
- **pytest 8.3.3**

（本项目主要目的是演示一个“Schema Driven Twin 平台 + HR 业务”的整体设计，并非生产级 HRMS。） 
