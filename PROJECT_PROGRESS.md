# 人力资源管理系统 (HRMS) - 项目进度

## 项目进度概览

- **状态流拓展**  
  - 除基础、岗位、薪资外，新建“社保信息”“住房公积金”两条状态流，数据库表与 DAO 均沿用统一 `PersonState` 抽象，保证任意维度的历史可追溯。
- **数据校验集中化**  
  - `app/models/person_payloads.py` 定义基础/岗位/薪资/社保/公积金的字段清洗与校验规则，`PersonService` 在创建流程中统一调用，避免脏数据写库。
- **前端与 API 联动**  
  - `/api/persons` 支持新字段；`templates/persons.html` 与 `static/js/persons.js` 增加社保、公积金表单与详情标签页，实现前端可视化录入与查看。
- **数据初始化**  
  - `seed.py` 生成符合规则的社保、公积金基数与比例，实习生、负责人等场景均具备样例，便于展示。
- **测试保障**  
  - 新增 `tests/test_person_payloads.py`、`tests/test_person_service.py`，覆盖字段校验、服务流程与异常路径；`pytest` 全量通过共 12 项用例。

## 新增能力（最近进展）

- **岗位/薪资/社保/公积金/考核状态流完善**  
  - 统一使用通用 `PersonState`，并通过 `PersonBasicState / PersonPositionState / PersonSalaryState / PersonSocialSecurityState / PersonHousingFundState / PersonAssessmentState` 语义别名表达不同维度。  
  - `person_position_history` 改造为“变动事件流”（入职/转岗/转公司/停薪留职/离职），通过 `change_type + change_date` 推导当前是否在职。  
  - 新增考核状态流 `person_assessment_history`，支持 A–E 等级与考核日期、备注。  

- **批量调整：公积金与社保**  
  - 设计并落地两阶段流程：**预览 → 确认 → 执行**。  
  - 表结构：  
    - 公积金：`housing_fund_adjustment_batches` + `housing_fund_batch_items`。  
    - 社保：`social_security_adjustment_batches` + `social_security_batch_items`。  
  - 模型层：`HousingFundBatch / HousingFundBatchItem / SocialSecurityBatch / SocialSecurityBatchItem` 作为 dataclass 领域对象；对应 DAO 负责批次与明细的 CRUD。  
  - Service：`PersonService.preview_housing_fund_batch / execute_housing_fund_batch` 与社保同名方法，按照当前状态 + 默认规则生成新基数/比例，并在执行阶段为每人追加一条状态记录。  
  - 前端页面：`housing_fund_batch.html`、`social_security_batch.html`，使用 Materialize modal 展示预览明细，支持在确认前调整单人数据。  

- **考勤与请假子系统**  
  - 新建考勤表 `attendance_records` 与请假表 `leave_records`，分别配套 `AttendanceDAO/Service` 与 `LeaveDAO/Service`。  
  - Web 页面：`attendance.html`、`leave.html`，并在主导航添加入口。  
  - 人员详情弹窗增加“考勤”“请假”标签页，采用懒加载（首点时通过 API 拉取：`/api/attendance/monthly-summary` 与 `/api/leave`）。  

- **人员卡片优化与操作入口**  
  - `persons` 页面卡片展示当前任职公司与职位，并按公司维度使用不同背景色，无任职公司使用浅灰色，保证高度一致。  
  - 卡片 action 区加入多个图标按钮：  
    - 任职调整（岗位事件追加）、薪资调整、社保调整、公积金调整、考核记录查看。  
  - “考核记录”按钮弹出 modal，展示最近一次考核及历史列表。  

- **薪酬批量发放与发薪事件流**  
  - 新建薪酬批量发放批次与明细表：`payroll_batches` + `payroll_batch_items`。  
  - 设计两阶段流程：参数填写 → “预览批量发放” → 在 modal 中查看/微调每人发放明细 → 确认 → 在“最近薪酬批次”列表中执行发放。  
  - 计算规则（核心）：  
    - 月薪制：以月薪为基数，根据员工类型拆分“基数部分 / 绩效部分”，绩效部分再按最近考核等级映射系数（A–E）后叠加；结合当月考勤（缺勤天数×日薪）、最新社保/公积金个人部分以及手工补扣，得到“应发（税前）”。  
    - 日薪制：根据当月实际工作天数 × 日薪得到应发，不再拆基数/绩效，也不看考核；仍扣除个人社保、公积金和手工补扣。  
  - 新增发薪状态流表 `person_payroll_history` 与 `PersonPayrollState`，`PersonPayrollStateDAO` 负责写入。执行批次发放时：  
    - 遍历该批次的 `payroll_batch_items`，为每个未 `applied` 的人员追加一条发薪事件（包含批次信息与各薪资构成字段）。  
    - 将明细标记为 `applied = 1`，批次状态更新为 `applied`，并记录影响人数。  
  - 前端页面 `payroll_batch.html`：  
    - 提供批次参数表单（批次年月 / 生效日期 / 公司 / 部门 / 员工类别 / 备注）、“预览批量发放”按钮。  
    - 下方“最近薪酬批次”列表每行提供“详情”与“执行发放”按钮。  

- **导航与信息架构**  
  - 顶部导航新增“薪酬”下拉菜单，包含“公积金批量”“社保批量”“薪酬批量发放”三个子项，统一薪酬相关功能入口。  
  - 所有页面统一继承 `layout.html`，使用 Materialize 的导航、下拉菜单和响应式布局。  

## 新增能力（最新进展）

- **个税专项附加扣除状态流与批量管理**  
  - 新增 `person_tax_deduction_history` 状态流表，存储6项专项附加扣除：继续教育、三岁及以下婴幼儿、子女教育、住房贷款利息、住房租金、赡养老人。  
  - 批量调整功能：`tax_deduction_adjustment_batches` + `tax_deduction_batch_items`，支持按月批量设置扣除金额，采用预览 → 确认 → 执行流程。  
  - 人员页面添加“个税抵扣信息”按钮，支持查看和编辑个人个税抵扣信息，并显示历史记录。  
  - 在导航菜单“薪酬”下拉中添加“个税专项附加扣除”入口。

- **薪酬计算逻辑优化**  
  - 月薪制计算中，试用期员工先按80%打折，然后再进行基数/绩效拆分和后续计算。  
  - 薪酬批量发放预览表格中显示员工姓名和所有计算相关属性（薪资类型、原始薪资、员工类别、考核等级、工作天数、社保/公积金基数、计算参数、计算结果等），便于审核和追溯。

- **历史记录显示增强**  
  - 所有调整模态框（任职调整、薪资调整、社保调整、公积金调整、个税抵扣信息、考核记录）均显示对应的历史记录列表。  
  - 保存新调整后自动刷新历史记录，保持数据同步。

- **统计页面**  
  - 新增统计页面 `statistics.html`，展示人员在各个维度的统计信息：
    - 总体概况（总数、在职、离职）
    - 性别分布
    - 年龄分布（7个年龄段）
    - 组织架构统计（按公司、部门、员工类别）
    - 薪资统计（类型分布、薪资区间分布、平均薪资）
    - 考核等级分布
    - 社保/公积金基数分布
  - 支持指定日期查询历史时间点的统计信息，使用状态流的 `get_at()` 方法获取指定时间点的状态。
  - 可视化展示：使用进度条样式展示各维度的分布情况。

## 下一步建议

1. 将 `datetime.utcnow()` 替换为时区感知时间，消除残留的 DeprecationWarning。  
2. 在薪酬发放事件流基础上，引入个税计算与正式的“工资条”查看页面，为每个发薪事件生成对员工可见的明细视图。
3. 考虑添加更多统计维度，如按入职时间统计、按离职原因统计等。
4. 优化统计页面的性能，对于大量数据可以考虑分页或缓存。

