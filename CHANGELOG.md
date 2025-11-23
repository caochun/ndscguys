# 更新日志

## 2025-01-23 - 带薪时长历史记录功能

### 新增功能

#### 1. 带薪时长修改历史记录
- **实现方式**: 使用JSON字段存储历史记录（`paid_hours_history`）
- **数据库变更**: 
  - 在 `leave_records` 表中添加 `paid_hours_history` 字段（TEXT类型，存储JSON数组）
  - 支持数据库自动迁移，兼容旧数据

#### 2. 轻量化带薪时长编辑界面
- **设计特点**: 
  - 浮动卡片设计（320px宽度），非全屏模态框
  - 在点击位置附近显示，不遮挡主要内容
  - 历史记录可折叠，默认隐藏
  - 简洁的表单输入，使用原生样式

- **交互功能**:
  - 点击表格中的带薪时长即可编辑
  - 自动加载当前值和历史记录
  - 支持查看历史记录（可展开/折叠）
  - 输入新值和修改原因后保存
  - 保存后自动刷新列表

### 技术实现

#### 后端实现

1. **数据库层** (`app/database.py`)
   - 添加 `paid_hours_history` 字段到 `leave_records` 表
   - 支持自动迁移（兼容旧数据库）

2. **模型层** (`app/models/leave_record.py`)
   - 添加 `paid_hours_history` 属性
   - 实现 `get_paid_hours_history()` 方法：返回解析后的历史记录列表
   - 实现 `add_paid_hours_history()` 方法：添加新的历史记录
   - `to_dict()` 方法自动包含历史记录

3. **数据访问层** (`app/daos/leave_record_dao.py`)
   - `create()` 方法支持保存 `paid_hours_history` 字段
   - `update()` 方法支持更新 `paid_hours_history` 字段

4. **服务层** (`app/services/attendance_service.py`)
   - `create_leave_record()`: 创建时如果设置了 `paid_hours > 0`，自动记录初始历史
   - `update_leave_record()`: 更新时如果 `paid_hours` 发生变化，自动记录历史
   - 支持传递修改原因（`change_reason`）和修改人（`changed_by`）

5. **路由层** (`app/routes.py`)
   - 更新请假记录API支持 `paid_hours_change_reason` 参数
   - 修改人从请求头 `X-User` 获取（默认为 'system'）

#### 前端实现

1. **HTML模板** (`app/templates/leave.html`)
   - 添加带薪时长编辑浮动卡片组件
   - 表格中的带薪时长可点击（蓝色下划线样式）

2. **JavaScript** (`app/static/js/leave.js`)
   - `showPaidHoursCard()`: 显示编辑卡片，加载历史记录
   - `savePaidHours()`: 保存带薪时长修改
   - `closePaidHoursCard()`: 关闭编辑卡片
   - 事件委托处理带薪时长点击
   - 历史记录折叠/展开功能

3. **CSS样式** (`app/static/css/style.css`)
   - 带薪时长点击样式（蓝色下划线，悬停效果）
   - 浮动卡片样式（固定定位，阴影，动画）
   - 历史记录样式（紧凑布局，可滚动）
   - 遮罩层样式（半透明背景）

### 数据结构

#### 历史记录JSON格式
```json
[
    {
        "old_value": null,
        "new_value": 8.0,
        "change_reason": "初始设置",
        "changed_by": "system",
        "changed_at": "2025-01-10 09:00:00"
    },
    {
        "old_value": 8.0,
        "new_value": 6.0,
        "change_reason": "根据公司政策调整",
        "changed_by": "admin",
        "changed_at": "2025-01-15 10:30:00"
    }
]
```

### 功能特点

1. **自动记录历史**
   - 创建请假记录时，如果设置了带薪时长，自动记录初始历史
   - 更新带薪时长时，自动记录变更历史
   - 历史记录按时间倒序排列（最新的在前）

2. **轻量化设计**
   - 小尺寸浮动卡片（320px），不遮挡主要内容
   - 历史记录默认折叠，按需查看
   - 简洁的表单输入，无冗余元素

3. **用户体验优化**
   - 点击即可编辑，无需打开完整表单
   - 自动聚焦到输入框
   - 实时验证（带薪时长不能超过请假时长）
   - 保存后自动刷新列表

### 修复的问题

1. **保存时比较逻辑问题**
   - 问题：使用表格中的值进行比较，可能与数据库实际值不一致
   - 修复：使用从API获取的实际值进行比较，确保准确性

### 使用说明

1. **查看历史记录**
   - 点击表格中的带薪时长
   - 在弹出的浮动卡片中点击"查看历史"
   - 历史记录以时间线形式展示

2. **修改带薪时长**
   - 点击表格中的带薪时长
   - 在浮动卡片中输入新值和修改原因
   - 点击保存按钮
   - 系统自动记录历史并更新

### API变更

#### PUT /api/leave-records/:id
新增请求参数：
- `paid_hours_change_reason` (可选): 修改原因

新增请求头：
- `X-User` (可选): 修改人，默认为 'system'

响应数据新增字段：
- `paid_hours_history`: 历史记录数组

### 文件变更清单

#### 新增/修改的文件
- `app/database.py` - 数据库表结构更新
- `app/models/leave_record.py` - 模型增强
- `app/daos/leave_record_dao.py` - DAO层更新
- `app/services/attendance_service.py` - 服务层逻辑
- `app/routes.py` - API路由更新
- `app/templates/leave.html` - HTML模板更新
- `app/static/js/leave.js` - JavaScript逻辑
- `app/static/css/style.css` - 样式更新

### 后续优化建议

1. **功能扩展**
   - 支持批量修改带薪时长
   - 支持导出历史记录
   - 支持历史记录搜索和过滤

2. **性能优化**
   - 如果历史记录数量很大，考虑分页加载
   - 考虑使用专门的历史表（如果查询需求增加）

3. **用户体验**
   - 添加键盘快捷键支持（ESC关闭，Enter保存）
   - 添加输入验证提示
   - 优化移动端显示

### 技术决策

#### 为什么选择JSON方案？
1. **需求明确**: 只需要展示历史，不需要复杂查询
2. **数据量小**: 一个请假记录的修改次数通常很少（1-5次）
3. **实现简单**: 开发成本低，无需额外表
4. **性能可接受**: 对于展示场景足够

#### 如果未来需要更复杂的查询
- 可以迁移到专门的历史表
- 或者使用通用审计日志表
- 当前JSON方案可以平滑迁移

