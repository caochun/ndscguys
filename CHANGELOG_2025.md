# 项目变更日志 - 2025年

## 2025-01-XX - 项目管理功能完善与代码重构

### 新增功能

#### 1. 项目管理页面
- **前端页面**：创建了 `projects.html` 项目管理页面
  - 项目列表以卡片形式展示，显示合同名称、甲方单位、项目经理、起止时间
  - 支持创建新项目（模态框表单）
  - 项目详情模态框包含三个标签页：
    - **基本信息**：可编辑项目信息（合同名称、起止时间、甲方信息等）
    - **参与人员**：显示项目参与人员列表，支持添加新人员，项目经理以蓝色高亮显示
    - **历史记录**：显示项目信息变更历史
  - 添加参与人员模态框，支持设置入项岗位、评定等级、单价、流程状态等信息

- **前端逻辑**：创建了 `projects.js` 实现完整的项目管理交互
  - 项目列表加载与渲染
  - 项目创建、编辑、详情查看
  - 参与人员管理（添加、查看历史）
  - 项目历史记录展示

- **导航菜单**：在 `layout.html` 中添加了"项目"导航菜单项

- **路由配置**：在 `routes.py` 中添加了 `/projects` 路由

#### 2. 项目种子数据
- 在 `seed.py` 中添加了 `seed_projects()` 函数
- 自动创建 6 个示例项目，每个项目分配 3-8 名参与人员
- 确保每个项目至少有一个人员被设置为"项目经理"
- 为部分项目添加信息变更历史记录

### 架构优化

#### 1. 项目相关逻辑分离
- **创建新模块**：`app/models/project_payloads.py`
  - 将项目相关的 payload 校验逻辑从 `person_payloads.py` 中分离出来
  - 包含 `sanitize_project_payload()` 和 `sanitize_person_project_payload()` 两个函数
  - 从 `person_payloads.py` 导入共享的工具函数和异常类

- **更新引用**：
  - `app/services/project_service.py` - 改为从 `project_payloads` 导入
  - `app/services/person_service.py` - 改为从 `project_payloads` 导入 `sanitize_person_project_payload`

- **设计优势**：
  - 职责更清晰：`person_payloads.py` 只处理人员相关，`project_payloads.py` 只处理项目相关
  - 模块一致性：与 `project_states/` 目录结构对应
  - 更易维护：项目相关校验逻辑独立，便于扩展

#### 2. 项目设计思路调整
- **移除 `our_project_manager` 字段**：
  - 从 `project_basic_history` 中移除了"我方项目经理"字段
  - 项目作为独立实体，只包含项目本身的信息（合同、甲方、时间等）
  - 人员参与项目的过程作为事件记录在 `person_project_history` 中
  - 项目经理信息通过 `person_project_history` 中的 `project_position` 字段来记录

- **服务层增强**：
  - 在 `ProjectService` 中添加了 `get_current_project_manager()` 方法
  - 从 `person_project_history` 中查询当前项目经理（角色为"项目经理"的最新记录）
  - `list_projects()` 和 `get_project()` 方法返回数据中包含 `current_manager` 字段

- **前端优化**：
  - 项目卡片和详情中从 `current_manager` 获取项目经理信息
  - 参与人员列表中，项目经理以蓝色高亮显示，并添加左侧边框

### Bug 修复

#### 1. 模态框标签重叠问题
- **问题**：Materialize CSS 的标签在模态框打开时与输入框重叠，需要点击输入框后标签才会动画移动到上方

- **修复方案**：
  - 移除了所有不必要的 `class="active"` 标签（特别是日期字段）
  - 调整了所有打开模态框并填充数据的函数：
    - 先打开模态框
    - 延迟 100ms 后调用 `M.updateTextFields()` 更新标签位置
  - 表单重置后也调用 `M.updateTextFields()`

- **修复的模态框**：
  - 项目相关：创建项目、编辑项目、添加参与人员
  - 人员相关：创建人员、任职调整、薪资调整、社保调整、公积金调整、考核记录、个税抵扣
  - 考勤相关：新增考勤
  - 请假相关：新增请假

### 技术细节

#### 1. 项目状态管理
- 项目基础信息存储在 `project_basic_history` 表中
- 人员参与项目信息存储在 `person_project_history` 表中（复合键：`person_id` + `project_id`）
- 支持项目信息变更的历史追溯
- 支持人员参与项目的历史追溯

#### 2. 项目经理查询逻辑
```python
def get_current_project_manager(self, project_id: int) -> Optional[Dict[str, Any]]:
    """从 person_project_history 中查询当前项目经理"""
    # 查找角色为"项目经理"的最新记录
    # 返回人员ID、姓名、角色、时间戳等信息
```

#### 3. 前端标签动画处理
```javascript
// 先打开模态框
modal.open();

// 延迟更新标签位置
setTimeout(() => {
    M.updateTextFields();
}, 100);
```

### 文件变更清单

#### 新增文件
- `app/models/project_payloads.py` - 项目相关 payload 校验
- `app/templates/projects.html` - 项目管理页面模板
- `app/static/js/projects.js` - 项目管理前端逻辑

#### 修改文件
- `app/templates/layout.html` - 添加项目导航菜单
- `app/routes.py` - 添加项目页面路由
- `app/models/person_payloads.py` - 移除项目相关函数
- `app/services/project_service.py` - 更新导入，添加项目经理查询方法
- `app/services/person_service.py` - 更新导入
- `app/seed.py` - 添加项目种子数据生成
- `app/templates/persons.html` - 移除不必要的 `class="active"` 标签
- `app/templates/projects.html` - 移除不必要的 `class="active"` 标签
- `app/templates/attendance.html` - 移除不必要的 `class="active"` 标签
- `app/templates/leave.html` - 移除不必要的 `class="active"` 标签
- `app/static/js/persons.js` - 修复模态框标签动画，调整 `M.updateTextFields()` 调用时机
- `app/static/js/projects.js` - 修复模态框标签动画，添加项目经理显示逻辑
- `app/static/js/attendance.js` - 修复表单重置后的标签更新
- `app/static/js/leave.js` - 修复表单重置后的标签更新

### 设计理念

1. **职责分离**：项目相关逻辑独立成模块，与人员相关逻辑分离
2. **事件溯源**：人员参与项目作为事件记录，支持历史追溯
3. **数据一致性**：项目经理信息统一在 `person_project_history` 中，避免数据冗余
4. **用户体验**：修复所有模态框的标签显示问题，提升交互体验

### 下一步建议

1. 考虑添加项目状态管理（进行中、已完成、暂停等）
2. 支持项目参与人员的角色变更（如从"前端开发"变更为"技术负责人"）
3. 添加项目统计功能（按项目统计参与人员、按人员统计参与项目等）
4. 优化项目经理查询性能（如果数据量大，可以考虑缓存）

