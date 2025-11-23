// 全局变量
let employees = [];
let persons = [];
let selectedEmployeeId = null;
let selectedPersonId = null;
let isEditMode = false;
let selectedCompany = '';  // 当前选择的公司
let currentHistoryEmployeeId = null;  // 当前查看历史的员工ID
let currentTab = 'employees';  // 当前标签页：'employees' 或 'persons'

// Materialize 组件实例
let employeeModalInstance = null;
let personModalInstance = null;
let historySidenavInstance = null;

// DOM 加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始化 Materialize 组件
    initMaterializeComponents();
    initEventListeners();
    loadEmployees();
});

// 初始化 Materialize 组件
function initMaterializeComponents() {
    // 初始化模态框
    const employeeModal = document.getElementById('employeeModal');
    employeeModalInstance = M.Modal.init(employeeModal, {
        onCloseEnd: function() {
            document.getElementById('employeeForm').reset();
            M.updateTextFields();
        }
    });
    
    const personModal = document.getElementById('personModal');
    personModalInstance = M.Modal.init(personModal, {
        onCloseEnd: function() {
            document.getElementById('personForm').reset();
            M.updateTextFields();
        }
    });
    
    // 初始化侧边栏（历史记录）
    const historySidenav = document.getElementById('historyDrawer');
    historySidenavInstance = M.Sidenav.init(historySidenav, {
        edge: 'right',
        draggable: false
    });
    
    // 初始化移动端导航侧边栏
    const mobileNav = document.getElementById('mobile-nav');
    M.Sidenav.init(mobileNav);
    
    // 初始化选择框
    M.FormSelect.init(document.querySelectorAll('select'));
    
    // 初始化日期选择器
    M.Datepicker.init(document.querySelectorAll('.datepicker'), {
        format: 'yyyy-mm-dd',
        autoClose: true,
        i18n: {
            cancel: '取消',
            clear: '清除',
            done: '确定',
            months: ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月'],
            monthsShort: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'],
            weekdays: ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六'],
            weekdaysShort: ['日', '一', '二', '三', '四', '五', '六'],
            weekdaysAbbrev: ['日', '一', '二', '三', '四', '五', '六']
        }
    });
}

// 初始化事件监听器
function initEventListeners() {
    // 导航链接切换
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const tab = this.dataset.tab;
            switchTab(tab);
        });
    });

    // 人员页面工具栏按钮
    document.getElementById('addPersonBtn').addEventListener('click', showAddPersonModal);
    document.getElementById('editPersonBtn').addEventListener('click', showEditPersonModal);
    document.getElementById('refreshPersonsBtn').addEventListener('click', loadPersons);

    // 模态框关闭按钮（Materialize会自动处理，这里保留以防需要额外逻辑）
    document.getElementById('cancelBtn').addEventListener('click', function() {
        if (employeeModalInstance) {
            employeeModalInstance.close();
        }
    });
    
    document.getElementById('cancelPersonBtn').addEventListener('click', function() {
        if (personModalInstance) {
            personModalInstance.close();
        }
    });

    // 表单提交
    document.getElementById('employeeForm').addEventListener('submit', saveEmployee);
    document.getElementById('personForm').addEventListener('submit', savePerson);

    // 表格行点击选择和历史按钮点击（使用事件委托）
    document.getElementById('employeeTableBody').addEventListener('click', function(e) {
        // 如果点击的是历史按钮，打开历史抽屉
        if (e.target.classList.contains('history-btn')) {
            const employeeId = parseInt(e.target.dataset.employeeId);
            const employeeName = e.target.dataset.employeeName;
            showHistoryDrawer(employeeId, employeeName);
            return;
        }
        
        // 否则触发行选择
        const row = e.target.closest('tr');
        if (row && row.dataset.employeeId) {
            // 移除之前的选中状态
            document.querySelectorAll('tbody tr').forEach(r => r.classList.remove('selected'));
            // 添加选中状态
            row.classList.add('selected');
            selectedEmployeeId = parseInt(row.dataset.employeeId);
        }
    });

    // 历史侧边栏关闭按钮
    document.getElementById('closeHistoryDrawer').addEventListener('click', closeHistoryDrawer);

    // 人员表格行点击选择（使用事件委托）
    document.getElementById('personTableBody').addEventListener('click', function(e) {
        const row = e.target.closest('tr');
        if (row && row.dataset.personId) {
            // 移除之前的选中状态
            document.querySelectorAll('#personTableBody tr').forEach(r => r.classList.remove('selected'));
            // 添加选中状态
            row.classList.add('selected');
            selectedPersonId = parseInt(row.dataset.personId);
        }
    });
}

// 切换标签页
function switchTab(tab) {
    currentTab = tab;
    
    // 更新导航链接状态（包括桌面端和移动端）
    document.querySelectorAll('.nav-link').forEach(link => {
        if (link.dataset.tab === tab) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
    
    // 更新页面内容显示
    document.querySelectorAll('.tab-content').forEach(content => {
        if (content.id === tab + 'Page') {
            content.classList.add('active');
        } else {
            content.classList.remove('active');
        }
    });
    
    // 关闭移动端侧边栏（如果打开）
    const mobileNav = M.Sidenav.getInstance(document.getElementById('mobile-nav'));
    if (mobileNav && mobileNav.isOpen) {
        mobileNav.close();
    }
    
    // 根据标签页加载数据
    if (tab === 'employees') {
        loadEmployees();
    } else if (tab === 'persons') {
        loadPersons();
    }
}

// 加载人员列表
async function loadPersons() {
    try {
        updateStatus('加载中...');
        const response = await fetch('/api/persons');
        const result = await response.json();

        if (result.success) {
            persons = result.data;
            renderPersonTable(persons);
            updateStatus(`已加载 ${persons.length} 名人员`);
        } else {
            showError('加载人员列表失败：' + result.error);
            updateStatus('加载失败');
        }
    } catch (error) {
        showError('加载人员列表失败：' + error.message);
        updateStatus('加载失败');
    }
}

// 渲染人员表格
function renderPersonTable(persons) {
    const tbody = document.getElementById('personTableBody');
    
    if (persons.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="loading">暂无人员数据</td></tr>';
        return;
    }

    tbody.innerHTML = persons.map(person => {
        return `
        <tr data-person-id="${person.id}">
            <td>${person.id}</td>
            <td>${person.name || '-'}</td>
            <td>${person.birth_date || '-'}</td>
            <td>${person.gender || '-'}</td>
            <td>${person.phone || '-'}</td>
            <td>${person.email || '-'}</td>
            <td>${person.created_at || '-'}</td>
            <td>${person.updated_at || '-'}</td>
        </tr>
        `;
    }).join('');
}

// 显示新增人员模态框
function showAddPersonModal() {
    isEditMode = false;
    selectedPersonId = null;
    document.getElementById('personModalTitle').textContent = '新增人员';
    document.getElementById('personForm').reset();
    document.getElementById('personId').value = '';
    document.getElementById('personModal').style.display = 'block';
}

// 显示编辑人员模态框
function showEditPersonModal() {
    if (!selectedPersonId) {
        M.toast({html: '请先选择要编辑的人员', classes: 'orange'});
        return;
    }
    
    isEditMode = true;
    const person = persons.find(p => p.id === selectedPersonId);
    if (!person) {
        M.toast({html: '人员不存在', classes: 'red'});
        return;
    }
    
    document.getElementById('personModalTitle').textContent = '编辑人员';
    document.getElementById('personId').value = person.id;
    document.getElementById('personName').value = person.name || '';
    document.getElementById('personBirthDate').value = person.birth_date || '';
    document.getElementById('personGender').value = person.gender || '';
    document.getElementById('personPhone').value = person.phone || '';
    document.getElementById('personEmail').value = person.email || '';
    
    M.updateTextFields();
    M.FormSelect.init(document.getElementById('personGender'));
    if (personModalInstance) {
        personModalInstance.open();
    }
}

// 关闭人员模态框
function closePersonModal() {
    if (personModalInstance) {
        personModalInstance.close();
    }
    isEditMode = false;
    selectedPersonId = null;
}

// 保存人员
async function savePerson(e) {
    e.preventDefault();
    
    const personId = document.getElementById('personId').value;
    const name = document.getElementById('personName').value.trim();
    
    if (!name) {
        alert('姓名不能为空');
        return;
    }
    
    const personData = {
        name: name,
        birth_date: document.getElementById('personBirthDate').value || null,
        gender: document.getElementById('personGender').value || null,
        phone: document.getElementById('personPhone').value || null,
        email: document.getElementById('personEmail').value || null
    };
    
    try {
        updateStatus('保存中...');
        let response;
        
        if (personId) {
            // 更新
            response = await fetch(`/api/persons/${personId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(personData)
            });
        } else {
            // 创建
            response = await fetch('/api/persons', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(personData)
            });
        }
        
        const result = await response.json();
        
        if (result.success) {
            updateStatus(result.message || '保存成功');
            closePersonModal();
            loadPersons();
        } else {
            showError('保存失败：' + result.error);
            updateStatus('保存失败');
        }
    } catch (error) {
        showError('保存失败：' + error.message);
        updateStatus('保存失败');
    }
}

// 加载公司列表（已废弃，保留以备将来使用）
async function loadCompanies() {
    try {
        const response = await fetch('/api/companies');
        const result = await response.json();
        if (result.success) {
            // 公司下拉框已移除，此函数保留以备将来使用
            return result.data;
        }
    } catch (error) {
        console.error('加载公司列表失败：', error);
    }
    return [];
}

// 加载员工列表
async function loadEmployees() {
    try {
        updateStatus('加载中...');
        const response = await fetch('/api/employees');
        const result = await response.json();

        if (result.success) {
            employees = result.data;
            renderEmployeeTable(employees);
            updateStatus(`已加载 ${employees.length} 名员工`);
        } else {
            showError('加载员工列表失败：' + result.error);
            updateStatus('加载失败');
        }
    } catch (error) {
        showError('加载员工列表失败：' + error.message);
        updateStatus('加载失败');
    }
}

// 生成头像URL（使用DiceBear API）
function getAvatarUrl(employeeId, name) {
    // 使用员工ID作为种子，确保每个员工有固定的头像
    // 使用 initials 风格，显示首字母
    const seed = employeeId.toString();
    // 获取名字的首字符（支持中文）
    const initial = name ? name.charAt(0) : 'U';
    // 使用 avataaars 风格（更美观的卡通头像）
    return `https://api.dicebear.com/7.x/avataaars/svg?seed=${seed}&backgroundColor=b6e3f4,c0aede,d1d4f9,ffd5dc,ffdfbf`;
}

// 渲染员工表格
function renderEmployeeTable(employees) {
    const tbody = document.getElementById('employeeTableBody');
    
    if (employees.length === 0) {
        tbody.innerHTML = '<tr><td colspan="12" class="loading">暂无员工数据</td></tr>';
        return;
    }

    tbody.innerHTML = employees.map(emp => {
        const avatarUrl = getAvatarUrl(emp.id, emp.name);
        const historyBtn = emp.has_history 
            ? `<button class="history-btn" data-employee-id="${emp.id}" data-employee-name="${emp.name || '员工'}">任职历史</button>`
            : '<span class="no-history">-</span>';
        return `
        <tr data-employee-id="${emp.id}">
            <td class="avatar-cell">
                <img src="${avatarUrl}" alt="${emp.name || '员工'}" class="avatar-img" 
                     onerror="this.src='https://api.dicebear.com/7.x/initials/svg?seed=${emp.id}&backgroundColor=b6e3f4'">
            </td>
            <td>${emp.id}</td>
            <td>${emp.employee_number || ''}</td>
            <td>${emp.name || ''}</td>
            <td>${emp.gender || ''}</td>
            <td>${emp.phone || ''}</td>
            <td>${emp.email || ''}</td>
            <td>${emp.company_name || ''}</td>
            <td>${emp.department || ''}</td>
            <td>${emp.position || ''}</td>
            <td>${emp.employee_type || '正式员工'}</td>
            <td class="action-cell">${historyBtn}</td>
        </tr>
        `;
    }).join('');
}

// 加载上级列表
async function loadSupervisors(companyName = null) {
    try {
        // 根据选择的公司加载上级列表
        let url = '/api/supervisors';
        const company = companyName || selectedCompany;
        if (company) {
            url += `?company_name=${encodeURIComponent(company)}`;
        }
        
        const response = await fetch(url);
        const result = await response.json();

        if (result.success) {
            const supervisorSelect = document.getElementById('supervisor');
            supervisorSelect.innerHTML = '<option value="">（无）</option>';
            
            result.data.forEach(emp => {
                // 编辑模式下，排除自己
                if (isEditMode && emp.id === selectedEmployeeId) {
                    return;
                }
                const option = document.createElement('option');
                option.value = emp.id;
                option.textContent = `${emp.name} (${emp.employee_number})`;
                supervisorSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('加载上级列表失败：', error);
    }
}

// 显示新增模态框
function showAddModal() {
    isEditMode = false;
    selectedEmployeeId = null;
    
    document.getElementById('modalTitle').textContent = '新增员工';
    document.getElementById('employeeForm').reset();
    document.getElementById('employeeId').value = '';
    document.getElementById('employeeNumber').disabled = false;
    document.getElementById('changeReasonRow').style.display = 'none';
    
    // 设置默认日期为今天
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('hireDate').value = today;
    
    // 如果已选择公司，默认填充公司名称（新增模式下）
    if (selectedCompany) {
        document.getElementById('companyName').value = selectedCompany;
    } else {
        document.getElementById('companyName').value = '';
    }
    
    // 重新加载上级列表（根据选择的公司）
    loadSupervisors();
    
    M.updateTextFields();
    M.FormSelect.init(document.querySelectorAll('select'));
    if (employeeModalInstance) {
        employeeModalInstance.open();
    }
}

// 显示编辑模态框
async function showEditModal() {
    if (!selectedEmployeeId) {
        M.toast({html: '请先选择要编辑的员工', classes: 'orange'});
        return;
    }

    isEditMode = true;
    
    try {
        updateStatus('加载员工信息...');
        const response = await fetch(`/api/employees/${selectedEmployeeId}`);
        const result = await response.json();

        if (result.success) {
            const emp = result.data;
            
            document.getElementById('modalTitle').textContent = '编辑员工信息';
            document.getElementById('employeeId').value = emp.id;
            document.getElementById('employeeNumber').value = emp.employee_number;
            document.getElementById('employeeNumber').disabled = true;
            document.getElementById('name').value = emp.name || '';
            document.getElementById('birthDate').value = emp.birth_date || '';
            document.getElementById('gender').value = emp.gender || '';
            document.getElementById('phone').value = emp.phone || '';
            document.getElementById('email').value = emp.email || '';
            document.getElementById('companyName').value = emp.company_name || '';
            document.getElementById('department').value = emp.department || '';
            document.getElementById('position').value = emp.position || '';
            document.getElementById('hireDate').value = emp.hire_date || '';
            document.getElementById('employeeType').value = emp.employee_type || '正式员工';
            document.getElementById('supervisor').value = emp.supervisor_id || '';
            document.getElementById('changeReason').value = '';
            document.getElementById('changeReasonRow').style.display = 'block';
            
            // 重新加载上级列表（根据员工的公司）
            loadSupervisors(emp.company_name);
            
            M.updateTextFields();
            M.FormSelect.init(document.querySelectorAll('select'));
            if (employeeModalInstance) {
                employeeModalInstance.open();
            }
            updateStatus('就绪');
        } else {
            showError('加载员工信息失败：' + result.error);
        }
    } catch (error) {
        showError('加载员工信息失败：' + error.message);
    }
}

// 关闭模态框
function closeModal() {
    if (employeeModalInstance) {
        employeeModalInstance.close();
    }
    selectedEmployeeId = null;
}

// 保存员工
async function saveEmployee(e) {
    e.preventDefault();

    const formData = {
        employee_number: document.getElementById('employeeNumber').value.trim(),
        name: document.getElementById('name').value.trim(),
        birth_date: document.getElementById('birthDate').value || null,
        gender: document.getElementById('gender').value || null,
        phone: document.getElementById('phone').value.trim() || null,
        email: document.getElementById('email').value.trim() || null,
        company_name: document.getElementById('companyName').value.trim(),
        department: document.getElementById('department').value.trim(),
        position: document.getElementById('position').value.trim(),
        hire_date: document.getElementById('hireDate').value,
        employee_type: document.getElementById('employeeType').value || '正式员工',
        supervisor_id: document.getElementById('supervisor').value || null,
        change_reason: document.getElementById('changeReason').value.trim() || null
    };

    // 验证必填字段
    if (!formData.employee_number && !isEditMode) {
        alert('员工编号不能为空');
        return;
    }
    if (!formData.name) {
        alert('姓名不能为空');
        return;
    }
    if (!formData.company_name) {
        alert('公司名称不能为空');
        return;
    }
    if (!formData.department) {
        alert('部门不能为空');
        return;
    }
    if (!formData.position) {
        alert('职位不能为空');
        return;
    }
    if (!formData.hire_date) {
        alert('入职时间不能为空');
        return;
    }

    try {
        updateStatus('保存中...');
        const url = isEditMode 
            ? `/api/employees/${selectedEmployeeId}`
            : '/api/employees';
        const method = isEditMode ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (result.success) {
            closeModal();
            loadEmployees();
            if (result.new_employee_id) {
                // 换公司成功，提示用户
                updateStatus('员工换公司成功，已创建新的员工记录');
            } else {
                updateStatus(isEditMode ? '员工信息更新成功' : '员工添加成功');
            }
        } else {
            showError('保存失败：' + result.error);
            updateStatus('保存失败');
        }
    } catch (error) {
        showError('保存失败：' + error.message);
        updateStatus('保存失败');
    }
}

// 删除员工
async function deleteEmployee() {
    if (!selectedEmployeeId) {
        alert('请先选择要删除的员工');
        return;
    }

    const employee = employees.find(emp => emp.id === selectedEmployeeId);
    if (!employee) {
        alert('员工不存在');
        return;
    }

    if (!confirm(`确定要删除员工 ${employee.name} (${employee.employee_number}) 吗？\n此操作不可恢复！`)) {
        return;
    }

    try {
        updateStatus('删除中...');
        const response = await fetch(`/api/employees/${selectedEmployeeId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            selectedEmployeeId = null;
            loadEmployees();
            updateStatus('员工删除成功');
        } else {
            showError('删除失败：' + result.error);
            updateStatus('删除失败');
        }
    } catch (error) {
        showError('删除失败：' + error.message);
        updateStatus('删除失败');
    }
}

// 更新状态栏
function updateStatus(message) {
    document.getElementById('statusBar').textContent = message;
}

// 显示错误消息
function showError(message) {
    alert(message);
    console.error(message);
}


// 显示任职历史抽屉
async function showHistoryDrawer(employeeId, employeeName) {
    currentHistoryEmployeeId = employeeId;
    const drawer = document.getElementById('historyDrawer');
    const title = document.getElementById('historyDrawerTitle');
    const content = document.getElementById('historyContent');
    
    title.textContent = `${employeeName} - 任职历史`;
    content.innerHTML = '<div class="loading">加载中...</div>';
    drawer.classList.add('active');
    
    try {
        const response = await fetch(`/api/employees/${employeeId}/history`);
        const result = await response.json();
        
        if (result.success) {
            if (result.data.length === 0) {
                content.innerHTML = '<div class="no-history-msg">暂无历史记录</div>';
            } else {
                content.innerHTML = renderHistoryList(result.data);
            }
        } else {
            content.innerHTML = `<div class="error-msg">加载失败：${result.error}</div>`;
        }
    } catch (error) {
        content.innerHTML = `<div class="error-msg">加载失败：${error.message}</div>`;
    }
}

// 渲染历史记录列表
function renderHistoryList(history) {
    // 数据已经在后端按时间排序，直接使用
    // 格式化时间显示
    const formatDate = (dateStr) => {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    };
    
    // 检测换公司（通过比较相邻记录的公司名称）
    let prevCompany = null;
    
    return `
        <div class="history-list">
            ${history.map((h, index) => {
                const isCompanyChange = prevCompany && prevCompany !== h.company_name;
                prevCompany = h.company_name;
                
                return `
                <div class="history-item ${h.is_current ? 'current' : ''} ${isCompanyChange ? 'company-change' : ''}">
                    ${isCompanyChange ? '<div class="company-change-badge">换公司</div>' : ''}
                    <div class="history-header">
                        <span class="history-version">版本 ${h.version}</span>
                        ${h.is_current ? '<span class="history-badge">当前</span>' : ''}
                        <span class="history-date">${formatDate(h.changed_at)}</span>
                    </div>
                    <div class="history-details">
                        <div class="history-row">
                            <span class="history-label">公司：</span>
                            <span class="history-value ${isCompanyChange ? 'highlight' : ''}">${h.company_name || '-'}</span>
                        </div>
                        ${h.employee_number ? `
                        <div class="history-row">
                            <span class="history-label">员工编号：</span>
                            <span class="history-value">${h.employee_number}</span>
                        </div>
                        ` : ''}
                        <div class="history-row">
                            <span class="history-label">部门：</span>
                            <span class="history-value">${h.department || '-'}</span>
                        </div>
                        <div class="history-row">
                            <span class="history-label">职位：</span>
                            <span class="history-value">${h.position || '-'}</span>
                        </div>
                        <div class="history-row">
                            <span class="history-label">员工类型：</span>
                            <span class="history-value">${h.employee_type || '正式员工'}</span>
                        </div>
                        <div class="history-row">
                            <span class="history-label">入职时间：</span>
                            <span class="history-value">${h.hire_date || '-'}</span>
                        </div>
                        ${h.change_reason ? `
                        <div class="history-row">
                            <span class="history-label">变更原因：</span>
                            <span class="history-value">${h.change_reason}</span>
                        </div>
                        ` : ''}
                    </div>
                </div>
            `;
            }).join('')}
        </div>
    `;
}

// 关闭历史抽屉
function closeHistoryDrawer() {
    if (historySidenavInstance) {
        historySidenavInstance.close();
    }
    currentHistoryEmployeeId = null;
}
