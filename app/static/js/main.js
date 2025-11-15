// 全局变量
let employees = [];
let selectedEmployeeId = null;
let isEditMode = false;
let selectedCompany = '';  // 当前选择的公司
let currentHistoryEmployeeId = null;  // 当前查看历史的员工ID

// DOM 加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initEventListeners();
    loadCompanies();
    loadEmployees();
    loadSupervisors();
});

// 初始化事件监听器
function initEventListeners() {
    // 公司筛选
    document.getElementById('companyFilter').addEventListener('change', function(e) {
        selectedCompany = e.target.value;
        loadEmployees();
    });

    // 工具栏按钮
    document.getElementById('addBtn').addEventListener('click', showAddModal);
    document.getElementById('editBtn').addEventListener('click', showEditModal);
    document.getElementById('deleteBtn').addEventListener('click', deleteEmployee);
    document.getElementById('refreshBtn').addEventListener('click', loadEmployees);

    // 模态框
    const modal = document.getElementById('employeeModal');
    const closeBtn = document.querySelector('.close');
    const cancelBtn = document.getElementById('cancelBtn');

    closeBtn.addEventListener('click', closeModal);
    cancelBtn.addEventListener('click', closeModal);
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            closeModal();
        }
    });

    // 表单提交
    document.getElementById('employeeForm').addEventListener('submit', saveEmployee);

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

    // 历史抽屉关闭按钮
    document.getElementById('closeHistoryDrawer').addEventListener('click', closeHistoryDrawer);
    document.querySelector('.drawer-overlay').addEventListener('click', closeHistoryDrawer);
}

// 加载公司列表
async function loadCompanies() {
    try {
        const response = await fetch('/api/companies');
        const result = await response.json();

        if (result.success) {
            const companySelect = document.getElementById('companyFilter');
            // 保留"全部公司"选项，添加其他公司
            companySelect.innerHTML = '<option value="">全部公司</option>';
            result.data.forEach(company => {
                const option = document.createElement('option');
                option.value = company;
                option.textContent = company;
                companySelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('加载公司列表失败：', error);
    }
}

// 加载员工列表
async function loadEmployees() {
    try {
        updateStatus('加载中...');
        // 根据选择的公司构建URL
        let url = '/api/employees';
        if (selectedCompany) {
            url += `?company_name=${encodeURIComponent(selectedCompany)}`;
        }
        
        const response = await fetch(url);
        const result = await response.json();

        if (result.success) {
            employees = result.data;
            renderEmployeeTable(employees);
            const companyText = selectedCompany ? `（${selectedCompany}）` : '';
            updateStatus(`已加载 ${employees.length} 名员工${companyText}`);
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
        tbody.innerHTML = '<tr><td colspan="11" class="loading">暂无员工数据</td></tr>';
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
    
    // 如果已选择公司，默认填充公司名称
    if (selectedCompany) {
        document.getElementById('companyName').value = selectedCompany;
    }
    
    // 重新加载上级列表（根据选择的公司）
    loadSupervisors();
    
    document.getElementById('employeeModal').style.display = 'block';
}

// 显示编辑模态框
async function showEditModal() {
    if (!selectedEmployeeId) {
        alert('请先选择要编辑的员工');
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
            document.getElementById('supervisor').value = emp.supervisor_id || '';
            document.getElementById('changeReason').value = '';
            document.getElementById('changeReasonRow').style.display = 'block';
            
            // 重新加载上级列表（根据员工的公司）
            loadSupervisors(emp.company_name);
            
            document.getElementById('employeeModal').style.display = 'block';
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
    document.getElementById('employeeModal').style.display = 'none';
    document.getElementById('employeeForm').reset();
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
            updateStatus(isEditMode ? '员工信息更新成功' : '员工添加成功');
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
    
    return `
        <div class="history-list">
            ${history.map((h) => `
                <div class="history-item ${h.is_current ? 'current' : ''}">
                    <div class="history-header">
                        <span class="history-version">版本 ${h.version}</span>
                        ${h.is_current ? '<span class="history-badge">当前</span>' : ''}
                        <span class="history-date">${formatDate(h.changed_at)}</span>
                    </div>
                    <div class="history-details">
                        <div class="history-row">
                            <span class="history-label">公司：</span>
                            <span class="history-value">${h.company_name || '-'}</span>
                        </div>
                        <div class="history-row">
                            <span class="history-label">部门：</span>
                            <span class="history-value">${h.department || '-'}</span>
                        </div>
                        <div class="history-row">
                            <span class="history-label">职位：</span>
                            <span class="history-value">${h.position || '-'}</span>
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
            `).join('')}
        </div>
    `;
}

// 关闭历史抽屉
function closeHistoryDrawer() {
    const drawer = document.getElementById('historyDrawer');
    drawer.classList.remove('active');
    currentHistoryEmployeeId = null;
}
