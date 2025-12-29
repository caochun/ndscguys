# 人力资源管理系统 (HRMS)

一个面向"人员状态追踪"的人力资源管理系统，使用 Flask + SQLite 实现 **State Stream（状态流）** 模式：以 `person_id` 为聚合根，把基础信息、岗位信息、薪资、社保、公积金、考核、发薪记录等拆解为独立的 Append-only 流，每次变更只追加新版本，不改写历史，再通过 Web UI + API 展示当前状态及历史沿革。

## 核心设计理念

- **“状态流”驱动**：每个状态类型（基础信息、岗位信息）各自维护只增不改的版本流（`person_basic_history`、`person_position_history`）。每条记录包含 `person_id/ts/version/data(JSON)`，从而实现任意状态的回放、对比与追溯。
- **聚合根 = Person**：一个人是多个状态流的集合，系统根据最新版本汇聚“当前状态”，也可按时间点获取历史状态（`get_at()`）。
- **轻量存储 + JSON 扩展**：状态数据放入 `data` JSON 字段，除核心索引外无需频繁迁表，便于快速迭代模型。
- **Web + API 统一**：同一 Flask 应用既 serve REST API，也提供 Material 风格 UI，便于预览状态流效果并做 Demo。

## 功能概览

- **状态流模型**
  - `person_basic_history`：append-only 存储人员基础信息（姓名、身份证、电话、邮箱等）。
  - `person_position_history`：append-only 存储岗位变动事件（入职 / 转岗 / 转公司 / 停薪留职 / 离职 等），通过最新事件推导当前是否在职以及当前公司/职位。
  - `person_salary_history`：薪资信息状态流，支持月薪制 / 日薪制等类型。
  - `person_social_security_history`：社保基数与各险种公司/个人比例、金额。
  - `person_housing_fund_history`：住房公积金基数与公司/个人比例。
  - `person_assessment_history`：考核状态流（A–E 等级，附带考核日期与备注）。
  - `person_payroll_history`：发薪记录状态流，记录每次批量发放时该员工的应发构成（基数、绩效、社保/公积金个人部分、补扣、应发税前等）。
  - `person_tax_deduction_history`：个税专项附加扣除状态流，包含继续教育、三岁及以下婴幼儿、子女教育、住房贷款利息、住房租金、赡养老人等6项扣除。
- **批量调整与批量发薪**
  - 公积金批量调整：`housing_fund_adjustment_batches` + `housing_fund_batch_items`，支持按公司/部门/员工类别筛选，预览 → 确认 → 执行，将新基数与比例写入 `person_housing_fund_history`。
  - 社保批量调整：`social_security_adjustment_batches` + `social_security_batch_items`，同样采用两阶段预览确认流程，将新社保配置写入 `person_social_security_history`。
  - 个税专项附加扣除批量调整：`tax_deduction_adjustment_batches` + `tax_deduction_batch_items`，支持按月批量设置6项专项附加扣除，预览 → 确认 → 执行，将新扣除数据写入 `person_tax_deduction_history`。
  - 薪酬批量发放：`payroll_batches` + `payroll_batch_items`，根据薪资类型、考核等级、当月考勤/请假、最新社保/公积金等自动计算每人“应发（税前）”，预览后可按人微调补扣，执行时为每人追加一条发薪事件到 `person_payroll_history`。
- **考勤与请假**
  - `attendance_records`：按日记录考勤，包含上下班时间、工作时长、加班时长、状态等，并提供“月度汇总”接口供薪酬计算与前端展示使用。
  - `leave_records`：请假记录，包含日期、类型、时长、审批人与状态等，支持创建/更新/删除与审批流程。
- **服务与 API**
  - `PersonService` 作为聚合根服务，封装各状态流 DAO 的读写，并提供批量调整与批量发放的业务方法（预览、确认、执行）。
  - `AttendanceService`、`LeaveService` 分别负责考勤与请假数据的增删改查与汇总。
  - `api.py` 中提供 `/api/persons`、`/api/attendance`、`/api/leave`、`/api/statistics` 以及 `/api/housing-fund/*`、`/api/social-security/*`、`/api/tax-deduction/*`、`/api/payroll/*` 等 REST 接口。
- **前端界面（Material 风格）**
  - 统一使用 `layout.html` 提供导航栏，包含“人员 / 考勤 / 请假 / 统计 / 薪酬（下拉：公积金批量 / 社保批量 / 个税专项附加扣除 / 薪酬批量发放）”入口。
  - 人员列表页 `persons.html`：卡片展示人员基础信息、当前公司与职位，按公司着色；卡片操作区提供“详情”“任职调整”“薪资调整”“社保调整”“公积金调整”“个税抵扣信息”“考核记录”等快捷入口。各调整模态框均显示历史记录列表。
  - 人员详情 Modal：按 Tab 展示基础信息、岗位信息、薪资信息、社保、公积金、考勤、请假等，并显示各自的历史版本。
  - 公积金 / 社保批量调整页面：以卡片 + Modal 的方式展示批次参数与预览明细表，可逐人调整 new_* 字段，再确认并执行。
  - 个税专项附加扣除批量调整页面：支持按月批量设置6项专项附加扣除，预览 → 确认 → 执行流程。
  - 薪酬批量发放页面：填写批次（年月）与筛选条件，一键预览本次发薪明细（区分月薪制/日薪制算法），预览表格显示员工姓名和所有计算相关属性，确认后在列表中执行“发放”。
  - 统计页面 `statistics.html`：展示人员在各个维度的统计信息（总体概况、性别、年龄、组织架构、薪资、考核等），支持指定日期查询历史时间点的统计。
- **种子数据**
  - 启动时自动初始化多名测试人员与岗位、薪资、社保、公积金、考勤、请假等数据：
    - 多家公司（如 "SC高科技公司""SC能源科技公司"）、多部门、多员工类型（含部门负责人）。
    - 部分人员含岗位变动事件（含离职）、基础信息变更、不同薪资类型与考核等级。
    - 自动生成一定规模的考勤与请假记录，便于观察统计效果与发薪计算。
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

## 项目结构（简要）

```
app/
├── api.py                 # REST API 蓝图（persons / attendance / leave / 批量调整与发放）
├── routes.py              # Web 页面路由（人员、考勤、请假、薪酬相关页面）
├── db.py                  # SQLite 初始化工具（所有状态流与批次表结构）
├── seed.py                # 种子数据生成（基础/岗位/薪资/社保/公积金/考勤/请假等）
├── services/
│   ├── person_service.py      # 人员聚合根服务 + 批量调整与批量发放逻辑
│   ├── attendance_service.py  # 考勤服务
│   └── leave_service.py       # 请假服务
├── daos/
│   ├── base_dao.py
│   ├── entity_state/
│   │   └── base.py            # 通用状态流 DAO
│   ├── person_state_dao.py    # 各 person_*_history 的具体 DAO
│   ├── housing_fund_batch_dao.py
│   ├── social_security_batch_dao.py
│   ├── tax_deduction_batch_dao.py
│   └── payroll_batch_dao.py
├── models/
│   ├── person_states/         # 所有人员状态流模型（basic/position/salary/social_security/housing_fund/assessment/payroll/tax_deduction）
│   ├── person_payloads.py     # 各状态流 payload 的清洗与校验
│   └── batches.py             # 公积金/社保/个税专项附加扣除/薪酬批次与明细的 dataclass 模型
├── templates/
│   ├── layout.html            # 通用布局与导航
│   ├── persons.html           # 人员列表与详情 Modal
│   ├── attendance.html        # 考勤页面
│   ├── leave.html             # 请假页面
│   ├── housing_fund_batch.html
│   ├── social_security_batch.html
│   ├── tax_deduction_batch.html
│   ├── payroll_batch.html
│   └── statistics.html
└── static/
    ├── js/persons.js
    ├── js/attendance.js
    ├── js/leave.js
    ├── js/housing_fund_batch.js
    ├── js/social_security_batch.js
    ├── js/tax_deduction_batch.js
    ├── js/payroll_batch.js
    └── js/statistics.js
```

## 测试

使用 pytest 验证状态流 DAO、服务层与批量调整/发放流程：

```bash
pytest
```

当前提供包括但不限于：

- `tests/test_entity_state_dao.py`：确保通用状态流 DAO 的 append / list / get_at 行为正确。
- `tests/test_person_payloads.py`：覆盖基础/岗位/薪资/社保/公积金/考核等 payload 的清洗与校验。
- `tests/test_person_service.py`：验证创建人员、状态流追加、数据聚合、考核与批量操作集成流程。
- `tests/test_batches.py`：针对公积金/社保/薪酬批次的 preview/confirm/execute 整体流程进行回归测试。

## 备注

- 数据库文件默认位于 `data/person_state.db`，可删除后重启以重新生成种子数据。
- 这是一个演示性质的原型，为多状态流（基础、岗位、薪资、社保、公积金、考核、个税专项附加扣除、发薪记录等）提供骨架，并通过批量调整与批量发放场景展示“事件流 + 状态流”的组合玩法。已实现统计页面支持按日期查询历史状态，后续可继续扩展税务计算、工资条查看等功能。

