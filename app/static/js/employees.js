// 员工页面 JavaScript

// 全局变量
let employees = [];
let selectedEmployeeId = null;
let currentHistoryEmployeeId = null;
let currentDetailEmployeeId = null;
let companies = [];
let departments = [];
let companyFilterInstance = null;
let departmentFilterInstance = null;

// Materialize 组件实例
let historySidenavInstance = null;
let employeeDetailModalInstance = null;
let employeeDetailTabsInstance = null;

// DOM 加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initMaterializeComponents();
    initEventListeners();
    loadCompanies();
    loadDepartments();
    loadEmployees();
});

// 初始化 Materialize 组件
function initMaterializeComponents() {
    // 初始化侧边栏（历史记录）
    const historySidenav = document.getElementById('historyDrawer');
    if (historySidenav) {
        historySidenavInstance = M.Sidenav.init(historySidenav, {
            edge: 'right',
            draggable: false
        });
    }
    
    // 初始化员工详情模态框
    const employeeDetailModal = document.getElementById('employeeDetailModal');
    if (employeeDetailModal) {
        employeeDetailModalInstance = M.Modal.init(employeeDetailModal, {
            onOpenStart: function() {
                // 模态框开始打开时，确保激活第一个标签
                setTimeout(() => {
                    if (employeeDetailTabsInstance) {
                        employeeDetailTabsInstance.select('personalInfoTab');
                    }
                }, 50);
            },
            onCloseEnd: function() {
                // 重置标签页到第一个
                if (employeeDetailTabsInstance) {
                    employeeDetailTabsInstance.select('personalInfoTab');
                }
                currentDetailEmployeeId = null;
            }
        });
    }
    
    // 初始化标签页
    const tabs = document.getElementById('employeeDetailTabs');
    if (tabs) {
        employeeDetailTabsInstance = M.Tabs.init(tabs);
    }
    
    // 初始化移动端导航侧边栏
    const mobileNav = document.getElementById('mobile-nav');
    if (mobileNav) {
        M.Sidenav.init(mobileNav);
    }
    
    // 初始化过滤器下拉框
    const companyFilter = document.getElementById('companyFilter');
    if (companyFilter) {
        companyFilterInstance = M.FormSelect.init(companyFilter, {
            dropdownOptions: {
                constrainWidth: false
            }
        });
    }
    
    const departmentFilter = document.getElementById('departmentFilter');
    if (departmentFilter) {
        departmentFilterInstance = M.FormSelect.init(departmentFilter, {
            dropdownOptions: {
                constrainWidth: false
            }
        });
    }
}

// 初始化事件监听器
function initEventListeners() {
    // 卡片点击事件（使用事件委托）
    const container = document.getElementById('employeeCardsContainer');
    if (container) {
        container.addEventListener('click', function(e) {
            // 如果点击的是详情按钮，打开详情模态框
            if (e.target.classList.contains('detail-btn') || e.target.closest('.detail-btn')) {
                const btn = e.target.closest('.detail-btn') || e.target;
                const employeeId = parseInt(btn.dataset.employeeId);
                const employeeName = btn.dataset.employeeName;
                showEmployeeDetail(employeeId, employeeName);
                return;
            }
        });
    }

    // 历史侧边栏关闭按钮（保留以备将来使用）
    const closeBtn = document.getElementById('closeHistoryDrawer');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeHistoryDrawer);
    }
    
    // 过滤器变化事件
    const companyFilter = document.getElementById('companyFilter');
    if (companyFilter) {
        companyFilter.addEventListener('change', function() {
            const selectedCompany = this.value;
            // 当公司改变时，重新加载部门列表
            loadDepartments(selectedCompany);
            // 应用过滤
            applyFilters();
        });
    }
    
    const departmentFilter = document.getElementById('departmentFilter');
    if (departmentFilter) {
        departmentFilter.addEventListener('change', function() {
            applyFilters();
        });
    }
    
    // 清除筛选按钮
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', function() {
            if (companyFilterInstance) {
                companyFilterInstance.setValue('');
                companyFilterInstance.input.value = '';
            }
            if (departmentFilterInstance) {
                departmentFilterInstance.setValue('');
                departmentFilterInstance.input.value = '';
            }
            loadDepartments(); // 重新加载所有部门
            applyFilters();
        });
    }
}

// 加载公司列表
async function loadCompanies() {
    try {
        const response = await fetch('/api/companies');
        const result = await response.json();

        if (result.success) {
            companies = result.data;
            const companyFilter = document.getElementById('companyFilter');
            if (companyFilter) {
                // 保留"全部公司"选项，添加公司列表
                companyFilter.innerHTML = '<option value="">全部公司</option>';
                companies.forEach(company => {
                    const option = document.createElement('option');
                    option.value = company;
                    option.textContent = company;
                    companyFilter.appendChild(option);
                });
                // 重新初始化下拉框
                if (companyFilterInstance) {
                    companyFilterInstance.destroy();
                }
                companyFilterInstance = M.FormSelect.init(companyFilter);
            }
        } else {
            console.error('加载公司列表失败：' + result.error);
        }
    } catch (error) {
        console.error('加载公司列表失败：' + error.message);
    }
}

// 加载部门列表
async function loadDepartments(companyName = null) {
    try {
        let url = '/api/departments';
        if (companyName) {
            url += `?company_name=${encodeURIComponent(companyName)}`;
        }
        
        const response = await fetch(url);
        const result = await response.json();

        if (result.success) {
            departments = result.data;
            const departmentFilter = document.getElementById('departmentFilter');
            if (departmentFilter) {
                // 保留"全部部门"选项，添加部门列表
                departmentFilter.innerHTML = '<option value="">全部部门</option>';
                departments.forEach(department => {
                    const option = document.createElement('option');
                    option.value = department;
                    option.textContent = department;
                    departmentFilter.appendChild(option);
                });
                // 重新初始化下拉框
                if (departmentFilterInstance) {
                    departmentFilterInstance.destroy();
                }
                departmentFilterInstance = M.FormSelect.init(departmentFilter);
            }
        } else {
            console.error('加载部门列表失败：' + result.error);
        }
    } catch (error) {
        console.error('加载部门列表失败：' + error.message);
    }
}

// 加载员工列表
async function loadEmployees() {
    try {
        updateStatus('加载中...');
        const response = await fetch('/api/employees');
        const result = await response.json();

        if (result.success) {
            employees = result.data;
            renderEmployeeCards(employees);
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

// 应用过滤器
async function applyFilters() {
    try {
        updateStatus('筛选中...');
        
        const companyFilter = document.getElementById('companyFilter');
        const departmentFilter = document.getElementById('departmentFilter');
        const selectedCompany = companyFilter ? companyFilter.value : '';
        const selectedDepartment = departmentFilter ? departmentFilter.value : '';
        
        // 构建查询参数
        const params = new URLSearchParams();
        if (selectedCompany) {
            params.append('company_name', selectedCompany);
        }
        if (selectedDepartment) {
            params.append('department', selectedDepartment);
        }
        
        const url = `/api/employees${params.toString() ? '?' + params.toString() : ''}`;
        const response = await fetch(url);
        const result = await response.json();

        if (result.success) {
            employees = result.data;
            renderEmployeeCards(employees);
            
            // 更新状态信息
            let statusMsg = `已显示 ${employees.length} 名员工`;
            if (selectedCompany || selectedDepartment) {
                const filters = [];
                if (selectedCompany) filters.push(`公司: ${selectedCompany}`);
                if (selectedDepartment) filters.push(`部门: ${selectedDepartment}`);
                statusMsg += ` (${filters.join(', ')})`;
            }
            updateStatus(statusMsg);
        } else {
            showError('筛选员工列表失败：' + result.error);
            updateStatus('筛选失败');
        }
    } catch (error) {
        showError('筛选员工列表失败：' + error.message);
        updateStatus('筛选失败');
    }
}

// 生成头像URL（使用DiceBear API）
function getAvatarUrl(employeeId, name) {
    const seed = employeeId.toString();
    return `https://api.dicebear.com/7.x/avataaars/svg?seed=${seed}&backgroundColor=b6e3f4,c0aede,d1d4f9,ffd5dc,ffdfbf`;
}

// 渲染员工卡片
function renderEmployeeCards(employees) {
    const container = document.getElementById('employeeCardsContainer');
    if (!container) return;
    
    if (employees.length === 0) {
        container.innerHTML = '<div class="col s12 center-align"><p class="grey-text">暂无员工数据</p></div>';
        return;
    }

    container.innerHTML = employees.map(emp => {
        const avatarUrl = getAvatarUrl(emp.id, emp.name);
        return `
        <div class="col s12 m6 l4">
            <div class="card employee-card hoverable">
                <div class="card-content">
                    <div class="row" style="margin-bottom: 0;">
                        <div class="col s4 center-align">
                            <img src="${avatarUrl}" alt="${emp.name || '员工'}" class="employee-avatar" 
                                 onerror="this.src='https://api.dicebear.com/7.x/initials/svg?seed=${emp.id}&backgroundColor=b6e3f4'">
                        </div>
                        <div class="col s8">
                            <span class="card-title employee-name">${emp.name || '未知'}</span>
                            <p class="employee-number grey-text">${emp.employee_number || '-'}</p>
                        </div>
                    </div>
                    <div class="divider" style="margin: 15px 0;"></div>
                    <div class="employee-info">
                        <p><i class="material-icons tiny">person</i> <strong>性别：</strong>${emp.gender || '-'}</p>
                        <p><i class="material-icons tiny">business</i> <strong>公司：</strong>${emp.company_name || '-'}</p>
                        <p><i class="material-icons tiny">domain</i> <strong>部门：</strong>${emp.department || '-'}</p>
                        <p><i class="material-icons tiny">work</i> <strong>职位：</strong>${emp.position || '-'}</p>
                        <p><i class="material-icons tiny">badge</i> <strong>类型：</strong>${emp.employee_type || '正式员工'}</p>
                    </div>
                </div>
                <div class="card-action">
                    <button class="btn waves-effect waves-light blue detail-btn" 
                            data-employee-id="${emp.id}" 
                            data-employee-name="${emp.name || '员工'}">
                        <i class="material-icons left">info</i>详情
                    </button>
                </div>
            </div>
        </div>
        `;
    }).join('');
}

// 显示员工详情模态框
async function showEmployeeDetail(employeeId, employeeName) {
    currentDetailEmployeeId = employeeId;
    
    // 设置标题
    const title = document.getElementById('employeeDetailTitle');
    if (title) {
        title.textContent = `${employeeName} - 员工详情`;
    }
    
    // 重置所有标签页内容为加载状态
    document.getElementById('personalInfoContent').innerHTML = '<div class="center-align"><div class="preloader-wrapper active"><div class="spinner-layer spinner-blue-only"><div class="circle-clipper left"><div class="circle"></div></div><div class="gap-patch"><div class="circle"></div></div><div class="circle-clipper right"><div class="circle"></div></div></div></div><p>加载中...</p></div>';
    document.getElementById('employmentInfoContent').innerHTML = '<div class="center-align"><div class="preloader-wrapper active"><div class="spinner-layer spinner-blue-only"><div class="circle-clipper left"><div class="circle"></div></div><div class="gap-patch"><div class="circle"></div></div><div class="circle-clipper right"><div class="circle"></div></div></div></div><p>加载中...</p></div>';
    document.getElementById('attendanceSummaryContent').innerHTML = '<div class="col s12 center-align grey-text" style="padding: 30px 0;"><div class="preloader-wrapper active"><div class="spinner-layer spinner-blue-only"><div class="circle-clipper left"><div class="circle"></div></div><div class="gap-patch"><div class="circle"></div></div><div class="circle-clipper right"><div class="circle"></div></div></div></div><p>加载考勤数据...</p></div>';
    document.getElementById('attendanceTableBody').innerHTML = '<tr><td colspan="7" class="center-align grey-text">加载中...</td></tr>';
    
    // 重新初始化标签页
    const tabs = document.getElementById('employeeDetailTabs');
    if (tabs && employeeDetailTabsInstance) {
        employeeDetailTabsInstance.destroy();
        employeeDetailTabsInstance = M.Tabs.init(tabs);
        // 确保激活第一个标签
        employeeDetailTabsInstance.select('personalInfoTab');
    }
    
    // 打开模态框
    if (employeeDetailModalInstance) {
        employeeDetailModalInstance.open();
    }
    
    // 加载员工详细信息
    try {
        const response = await fetch(`/api/employees/${employeeId}`);
        const result = await response.json();
        
        if (result.success) {
            const emp = result.data;
            
            // 渲染个人信息
            renderPersonalInfo(emp);
            
            // 渲染任职信息
            renderEmploymentInfo(emp);
            
            // 渲染薪资信息
            renderSalaryInfo(emp.salary);
            loadAndRenderSalaryHistory(employeeId);
            
            // 加载并渲染任职历史
            await loadAndRenderHistory(employeeId);
            
            // 加载考勤信息
            loadAndRenderAttendance(employeeId);
        } else {
            showError('加载员工信息失败：' + result.error);
        }
    } catch (error) {
        showError('加载员工信息失败：' + error.message);
    }
}

// 渲染个人信息
function renderPersonalInfo(emp) {
    const content = document.getElementById('personalInfoContent');
    if (!content) return;
    
    const avatarUrl = getAvatarUrl(emp.id, emp.name);
    
    content.innerHTML = `
        <div class="row" style="margin-bottom: 10px;">
            <div class="col s12 m4 center-align" style="display: flex; flex-direction: column; align-items: center; justify-content: center;">
                <img src="${avatarUrl}" alt="${emp.name || '员工'}" class="employee-avatar-compact" 
                     onerror="this.src='https://api.dicebear.com/7.x/initials/svg?seed=${emp.id}&backgroundColor=b6e3f4'">
            </div>
            <div class="col s12 m8">
                <div class="info-grid">
                    <div class="info-item">
                        <span class="info-label-compact">姓名：</span>
                        <span class="info-value">${emp.name || '-'}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label-compact">性别：</span>
                        <span class="info-value">${emp.gender || '-'}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label-compact">出生日期：</span>
                        <span class="info-value">${emp.birth_date || '-'}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label-compact">手机：</span>
                        <span class="info-value">${emp.phone || '-'}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label-compact">邮箱：</span>
                        <span class="info-value">${emp.email || '-'}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label-compact">家庭住址：</span>
                        <span class="info-value">${emp.address || '-'}</span>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// 渲染任职信息
function renderEmploymentInfo(emp) {
    const content = document.getElementById('employmentInfoContent');
    if (!content) return;
    
    content.innerHTML = `
        <div class="info-grid">
            <div class="info-item">
                <span class="info-label-compact">员工编号：</span>
                <span class="info-value">${emp.employee_number || '-'}</span>
            </div>
            <div class="info-item">
                <span class="info-label-compact">公司：</span>
                <span class="info-value">${emp.company_name || '-'}</span>
            </div>
            <div class="info-item">
                <span class="info-label-compact">部门：</span>
                <span class="info-value">${emp.department || '-'}</span>
            </div>
            <div class="info-item">
                <span class="info-label-compact">职位：</span>
                <span class="info-value">${emp.position || '-'}</span>
            </div>
            <div class="info-item">
                <span class="info-label-compact">入职时间：</span>
                <span class="info-value">${emp.hire_date || '-'}</span>
            </div>
            <div class="info-item">
                <span class="info-label-compact">员工类型：</span>
                <span class="info-value">${emp.employee_type || '正式员工'}</span>
            </div>
            <div class="info-item">
                <span class="info-label-compact">上级ID：</span>
                <span class="info-value">${emp.supervisor_id || '-'}</span>
            </div>
        </div>
        <div class="divider" style="margin: 20px 0;"></div>
        <h6 class="blue-text text-darken-2" style="font-weight: 600;">任职历史</h6>
        <div id="employmentHistoryContent" class="history-content" style="margin-top: 10px;">
            <div class="center-align grey-text">
                <div class="preloader-wrapper active">
                    <div class="spinner-layer spinner-blue-only">
                        <div class="circle-clipper left"><div class="circle"></div></div>
                        <div class="gap-patch"><div class="circle"></div></div>
                        <div class="circle-clipper right"><div class="circle"></div></div>
                    </div>
                </div>
                <p>加载中...</p>
            </div>
        </div>
    `;
}

function formatCurrency(value) {
    if (value === null || value === undefined || value === '') {
        return '-';
    }
    const number = Number(value);
    if (Number.isNaN(number)) {
        return '-';
    }
    return `¥${number.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function renderSalaryInfo(salary) {
    const content = document.getElementById('salaryInfoContent');
    if (!content) return;
    
    if (!salary) {
        content.innerHTML = `
            <div class="card-panel grey lighten-4 center-align" style="margin-bottom: 16px;">
                <i class="material-icons large grey-text text-lighten-1">account_balance_wallet</i>
                <p class="grey-text text-darken-1" style="margin-top: 10px;">暂无薪资信息</p>
            </div>
            <div class="card">
                <div class="card-content">
                    <h6 class="grey-text text-darken-2" style="margin: 0;">薪资历史</h6>
                    <div id="salaryHistoryList" class="history-content" style="margin-top: 15px;">
                        <div class="center-align grey-text">加载历史记录...</div>
                    </div>
                </div>
            </div>
        `;
        return;
    }
    
    content.innerHTML = `
        <div class="card-panel blue lighten-5" style="margin-bottom: 16px;">
            <div class="row" style="margin-bottom: 0;">
                <div class="col s12 m4 center-align" style="padding: 20px 10px;">
                    <i class="material-icons large blue-text text-darken-2">account_balance_wallet</i>
                    <p style="font-size: 1.6rem; font-weight: 600; margin: 10px 0 4px 0;">
                        ${formatCurrency(salary.base_amount)}
                    </p>
                    <p class="grey-text text-darken-2" style="margin: 0;">月薪基数</p>
                    <span class="badge blue white-text" style="margin-top: 8px;">当前生效</span>
                </div>
                <div class="col s12 m8">
                    <div class="info-grid">
                        <div class="info-item">
                            <span class="info-label-compact">基本工资 (60%)：</span>
                            <span class="info-value">${formatCurrency(salary.basic_salary)}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label-compact">绩效基数 (40%)：</span>
                            <span class="info-value">${formatCurrency(salary.performance_salary)}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label-compact">生效日期：</span>
                            <span class="info-value">${salary.effective_date || '-'}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label-compact">变更原因：</span>
                            <span class="info-value">${salary.change_reason || '—'}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label-compact">版本号：</span>
                            <span class="info-value">${salary.version || '-'}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="card">
            <div class="card-content">
                <h6 class="grey-text text-darken-2" style="margin: 0;">薪资历史</h6>
                <div id="salaryHistoryList" class="history-content" style="margin-top: 15px;">
                    <div class="center-align grey-text">加载历史记录...</div>
                </div>
            </div>
        </div>
    `;
}

async function loadAndRenderSalaryHistory(employeeId) {
    const historyContainer = document.getElementById('salaryHistoryList');
    if (!historyContainer) return;
    
    historyContainer.innerHTML = '<div class="center-align grey-text">加载历史记录...</div>';
    
    try {
        const response = await fetch(`/api/employees/${employeeId}/salary/history`);
        const result = await response.json();
        
        if (result.success) {
            if (result.data.length === 0) {
                historyContainer.innerHTML = '<div class="center-align grey-text">暂无薪资历史</div>';
            } else {
                historyContainer.innerHTML = renderSalaryHistoryList(result.data);
            }
        } else {
            historyContainer.innerHTML = `<div class="center-align red-text">加载失败：${result.error}</div>`;
        }
    } catch (error) {
        historyContainer.innerHTML = `<div class="center-align red-text">加载失败：${error.message}</div>`;
    }
}

function renderSalaryHistoryList(history) {
    return `
        <div class="table-responsive">
            <table class="striped highlight responsive-table">
                <thead>
                    <tr>
                        <th>版本</th>
                        <th>月薪基数</th>
                        <th>基本工资</th>
                        <th>绩效基数</th>
                        <th>生效日期</th>
                        <th>结束日期</th>
                        <th>变更原因</th>
                        <th>状态</th>
                    </tr>
                </thead>
                <tbody>
                    ${history.map(item => `
                        <tr class="${item.status === 'active' ? 'current-row' : ''}">
                            <td>${item.version || '-'}</td>
                            <td>${formatCurrency(item.base_amount)}</td>
                            <td>${formatCurrency(item.basic_salary)}</td>
                            <td>${formatCurrency(item.performance_salary)}</td>
                            <td>${item.effective_date || '-'}</td>
                            <td>${item.end_date || '-'}</td>
                            <td>${item.change_reason || '-'}</td>
                            <td>
                                ${item.status === 'active'
                                    ? '<span class="badge blue white-text">当前</span>'
                                    : '<span class="badge grey white-text">历史</span>'}
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

// 加载并渲染历史记录
async function loadAndRenderHistory(employeeId) {
    const content = document.getElementById('employmentHistoryContent');
    if (!content) return;
    
    try {
        const response = await fetch(`/api/employees/${employeeId}/history`);
        const result = await response.json();
        
        if (result.success) {
            content.innerHTML = result.data.length > 0
                ? renderHistoryList(result.data)
                : '<div class="center-align grey-text">暂无历史记录</div>';
        } else {
            content.innerHTML = `<div class="center-align red-text">加载失败：${result.error}</div>`;
        }
    } catch (error) {
        content.innerHTML = `<div class="center-align red-text">加载失败：${error.message}</div>`;
    }
}

async function loadAndRenderAttendance(employeeId) {
    const summaryContainer = document.getElementById('attendanceSummaryContent');
    const tableBody = document.getElementById('attendanceTableBody');
    if (!summaryContainer || !tableBody) return;
    
    summaryContainer.innerHTML = '<div class="col s12 center-align grey-text" style="padding: 30px 0;"><div class="preloader-wrapper active"><div class="spinner-layer spinner-blue-only"><div class="circle-clipper left"><div class="circle"></div></div><div class="gap-patch"><div class="circle"></div></div><div class="circle-clipper right"><div class="circle"></div></div></div></div><p>加载考勤数据...</p></div>';
    tableBody.innerHTML = '<tr><td colspan="7" class="center-align grey-text">加载中...</td></tr>';
    
    try {
        const response = await fetch(`/api/employees/${employeeId}/attendance/monthly`);
        const result = await response.json();
        if (result.success) {
            renderAttendanceSummary(result.summary);
            renderAttendanceTable(result.data || []);
        } else {
            summaryContainer.innerHTML = `<div class="col s12 center-align red-text" style="padding: 20px 0;">加载失败：${result.error}</div>`;
            tableBody.innerHTML = '<tr><td colspan="7" class="center-align red-text">加载失败</td></tr>';
        }
    } catch (error) {
        summaryContainer.innerHTML = `<div class="col s12 center-align red-text" style="padding: 20px 0;">加载失败：${error.message}</div>`;
        tableBody.innerHTML = '<tr><td colspan="7" class="center-align red-text">加载失败</td></tr>';
    }
}

function renderAttendanceSummary(summary) {
    const container = document.getElementById('attendanceSummaryContent');
    if (!container) return;
    if (!summary) {
        container.innerHTML = '<div class="col s12 center-align grey-text" style="padding: 20px 0;">暂无考勤数据</div>';
        return;
    }
    
    const summaryCards = [
        {
            label: '有效工作时长',
            value: summary.effective_hours,
            colorClass: 'blue-text text-darken-2'
        },
        {
            label: '工作时长',
            value: summary.work_hours,
            colorClass: 'grey-text text-darken-3'
        },
        {
            label: '未带薪时长',
            value: summary.unpaid_leave_hours,
            colorClass: 'orange-text text-darken-2'
        },
        {
            label: '加班时长',
            value: summary.overtime_hours,
            colorClass: 'purple-text text-darken-2'
        }
    ];
    
    container.innerHTML = `
        <div class="col s12" style="margin-bottom: 10px;">
            <span class="attendance-summary-period">${summary.year} 年 ${summary.month} 月考勤（${summary.record_count || 0} 条记录，${summary.days_attended || 0} 天出勤）</span>
        </div>
        ${summaryCards.map(card => `
            <div class="col s12 m6 l3" style="margin-bottom: 10px;">
                <div class="attendance-summary-card">
                    <p class="attendance-summary-value ${card.colorClass}">${formatHours(card.value)}</p>
                    <p class="attendance-summary-label">${card.label}</p>
                </div>
            </div>
        `).join('')}
    `;
}

function renderAttendanceTable(records) {
    const tableBody = document.getElementById('attendanceTableBody');
    if (!tableBody) return;
    
    if (!records || records.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="7" class="center-align grey-text">本月暂无考勤数据</td></tr>';
        return;
    }
    
    tableBody.innerHTML = records.map(record => `
        <tr>
            <td>${record.attendance_date || '-'}</td>
            <td>${formatDateTime(record.check_in_time)}</td>
            <td>${formatDateTime(record.check_out_time)}</td>
            <td>${formatHours(record.work_hours)}</td>
            <td>${formatHours(record.leave_hours)}</td>
            <td>${formatHours(record.overtime_hours)}</td>
            <td>${getAttendanceStatusChip(record.status)}</td>
        </tr>
    `).join('');
}

function formatDateTime(value) {
    if (!value) return '-';
    try {
        const dateObj = new Date(value);
        if (Number.isNaN(dateObj.getTime())) return '-';
        return dateObj.toLocaleString('zh-CN', { hour12: false });
    } catch (error) {
        return '-';
    }
}

function formatHours(value) {
    const num = Number(value) || 0;
    return num.toFixed(2);
}

function getAttendanceStatusChip(status) {
    const statusMap = {
        'normal': { text: '正常', cls: 'status-normal', icon: 'check_circle' },
        'late': { text: '迟到', cls: 'status-late', icon: 'schedule' },
        'early_leave': { text: '早退', cls: 'status-early-leave', icon: 'exit_to_app' },
        'absent': { text: '缺勤', cls: 'status-absent', icon: 'cancel' },
        'leave': { text: '请假', cls: 'status-leave', icon: 'event_busy' },
        'partial_leave': { text: '部分请假', cls: 'status-partial-leave', icon: 'event_available' },
        'incomplete': { text: '未完成', cls: 'status-incomplete', icon: 'hourglass_empty' },
        'overtime': { text: '加班', cls: 'status-overtime', icon: 'work' }
    };
    const info = statusMap[status] || { text: status || '未知', cls: 'status-unknown', icon: 'help' };
    return `<span class="attendance-status-badge ${info.cls}"><i class="material-icons tiny">${info.icon}</i>${info.text}</span>`;
}

// 显示任职历史抽屉（保留以备将来使用）
async function showHistoryDrawer(employeeId, employeeName) {
    currentHistoryEmployeeId = employeeId;
    const title = document.getElementById('historyDrawerTitle');
    const content = document.getElementById('historyContent');
    
    if (!title || !content) return;
    
    title.textContent = `${employeeName} - 任职历史`;
    content.innerHTML = '<div class="center-align">加载中...</div>';
    
    if (historySidenavInstance) {
        historySidenavInstance.open();
    }
    
    try {
        const response = await fetch(`/api/employees/${employeeId}/history`);
        const result = await response.json();
        
        if (result.success) {
            if (result.data.length === 0) {
                content.innerHTML = '<div class="center-align">暂无历史记录</div>';
            } else {
                content.innerHTML = renderHistoryList(result.data);
            }
        } else {
            content.innerHTML = `<div class="center-align red-text">加载失败：${result.error}</div>`;
        }
    } catch (error) {
        content.innerHTML = `<div class="center-align red-text">加载失败：${error.message}</div>`;
    }
}

// 渲染历史记录列表（表格形式）
function renderHistoryList(history) {
    const formatDate = (dateStr) => {
        if (!dateStr) return '-';
        const date = new Date(dateStr);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    };
    
    if (history.length === 0) {
        return '<div class="center-align grey-text">暂无历史记录</div>';
    }
    
    let prevCompany = null;
    
    return `
        <div class="table-responsive">
            <table class="striped highlight responsive-table">
                <thead>
                    <tr>
                        <th>版本</th>
                        <th>状态</th>
                        <th>变更时间</th>
                        <th>公司</th>
                        <th>员工编号</th>
                        <th>部门</th>
                        <th>职位</th>
                        <th>员工类型</th>
                        <th>入职时间</th>
                        <th>变更原因</th>
                    </tr>
                </thead>
                <tbody>
                    ${history.map((h, index) => {
                        const isCompanyChange = prevCompany && prevCompany !== h.company_name;
                        prevCompany = h.company_name;
                        
                        return `
                        <tr class="${h.is_current ? 'current-row' : ''} ${isCompanyChange ? 'company-change-row' : ''}">
                            <td>${h.version || '-'}</td>
                            <td>
                                ${h.is_current ? '<span class="badge blue white-text">当前</span>' : '<span class="badge grey white-text">历史</span>'}
                                ${isCompanyChange ? '<span class="badge red white-text" style="margin-left: 5px;">换公司</span>' : ''}
                            </td>
                            <td>${formatDate(h.changed_at)}</td>
                            <td class="${isCompanyChange ? 'company-change-cell' : ''}">${h.company_name || '-'}</td>
                            <td>${h.employee_number || '-'}</td>
                            <td>${h.department || '-'}</td>
                            <td>${h.position || '-'}</td>
                            <td>${h.employee_type || '正式员工'}</td>
                            <td>${h.hire_date || '-'}</td>
                            <td>${h.change_reason || '-'}</td>
                        </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
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

// 更新状态栏
function updateStatus(message) {
    const statusText = document.getElementById('statusText');
    if (statusText) {
        statusText.textContent = message;
    }
}

// 显示错误消息
function showError(message) {
    console.error(message);
    M.toast({html: message, classes: 'red'});
    updateStatus('错误：' + message);
}

