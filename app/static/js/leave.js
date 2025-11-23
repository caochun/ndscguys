// 请假管理页面 JavaScript

// 全局变量
let leaveList = [];
let selectedLeaveId = null;
let isEditMode = false;
let companies = [];
let persons = [];
let personMap = {};

// Materialize 组件实例
let leaveModalInstance = null;
let paidHoursCardElement = null;
let paidHoursOverlayElement = null;

// DOM 加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initMaterializeComponents();
    initEventListeners();
    loadCompanies();
    loadPersons();
    loadLeaveRecords();
});

// 初始化 Materialize 组件
function initMaterializeComponents() {
    // 初始化请假模态框
    const leaveModal = document.getElementById('leaveModal');
    if (leaveModal) {
        leaveModalInstance = M.Modal.init(leaveModal, {
            onCloseEnd: function() {
                document.getElementById('leaveForm').reset();
                M.updateTextFields();
                isEditMode = false;
                selectedLeaveId = null;
            }
        });
    }
    
    // 获取带薪时长卡片和遮罩层元素
    paidHoursCardElement = document.getElementById('paidHoursCard');
    paidHoursOverlayElement = document.getElementById('paidHoursOverlay');
    
    // 点击遮罩层关闭卡片
    if (paidHoursOverlayElement) {
        paidHoursOverlayElement.addEventListener('click', closePaidHoursCard);
    }
    
    // 关闭按钮
    const closeBtn = document.querySelector('.paid-hours-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', closePaidHoursCard);
    }
    
    // 历史记录切换
    const historyToggle = document.getElementById('paidHoursHistoryToggle');
    if (historyToggle) {
        historyToggle.addEventListener('click', function() {
            const history = document.getElementById('paidHoursHistory');
            if (history.style.display === 'none') {
                history.style.display = 'block';
                historyToggle.innerHTML = '<i class="material-icons tiny">expand_less</i> 收起历史';
            } else {
                history.style.display = 'none';
                historyToggle.innerHTML = '<i class="material-icons tiny">history</i> 查看历史';
            }
        });
    }
    
    // 初始化移动端导航侧边栏
    const mobileNav = document.getElementById('mobile-nav');
    if (mobileNav) {
        M.Sidenav.init(mobileNav);
    }
    
    // 初始化日期选择器
    const datepickers = document.querySelectorAll('.datepicker');
    M.Datepicker.init(datepickers, {
        format: 'yyyy-mm-dd',
        autoClose: true
    });
}

// 初始化事件监听器
function initEventListeners() {
    // 查询按钮
    const searchBtn = document.getElementById('searchBtn');
    if (searchBtn) {
        searchBtn.addEventListener('click', loadLeaveRecords);
    }
    
    // 新增请假按钮
    const addLeaveBtn = document.getElementById('addLeaveBtn');
    if (addLeaveBtn) {
        addLeaveBtn.addEventListener('click', showAddLeaveModal);
    }
    
    // 模态框关闭按钮
    const cancelBtn = document.getElementById('cancelLeaveBtn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            if (leaveModalInstance) {
                leaveModalInstance.close();
            }
        });
    }

    // 表单提交
    const leaveForm = document.getElementById('leaveForm');
    if (leaveForm) {
        leaveForm.addEventListener('submit', saveLeaveRecord);
    }

    // 人员选择变化时，更新公司列表
    const leavePersonSelect = document.getElementById('leavePersonSelect');
    if (leavePersonSelect) {
        leavePersonSelect.addEventListener('change', function() {
            updateCompanyOptions();
        });
    }
    
    // 带薪时长保存和取消按钮
    const savePaidHoursBtn = document.getElementById('savePaidHoursBtn');
    if (savePaidHoursBtn) {
        savePaidHoursBtn.addEventListener('click', savePaidHours);
    }
    
    const cancelPaidHoursBtn = document.getElementById('cancelPaidHoursBtn');
    if (cancelPaidHoursBtn) {
        cancelPaidHoursBtn.addEventListener('click', closePaidHoursCard);
    }
    
    // 使用事件委托处理带薪时长的点击事件
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('paid-hours-clickable') || 
            e.target.parentElement?.classList.contains('paid-hours-clickable')) {
            const target = e.target.classList.contains('paid-hours-clickable') ? e.target : e.target.parentElement;
            const leaveId = parseInt(target.getAttribute('data-leave-id'));
            const currentPaidHours = parseFloat(target.getAttribute('data-paid-hours')) || 0;
            const rect = target.getBoundingClientRect();
            showPaidHoursCard(leaveId, currentPaidHours, rect);
        }
    });
}

// 加载公司列表
async function loadCompanies() {
    try {
        const response = await fetch('/api/employees');
        const result = await response.json();
        
        if (result.success) {
            const companySet = new Set();
            result.data.forEach(emp => {
                if (emp.company_name) {
                    companySet.add(emp.company_name);
                }
            });
            companies = Array.from(companySet).sort();
            
            // 填充公司筛选下拉框
            const companyFilter = document.getElementById('companyFilter');
            if (companyFilter) {
                companies.forEach(company => {
                    const option = document.createElement('option');
                    option.value = company;
                    option.textContent = company;
                    companyFilter.appendChild(option);
                });
                M.FormSelect.init(companyFilter);
            }
        }
    } catch (error) {
        console.error('加载公司列表失败：', error);
    }
}

// 加载人员列表
async function loadPersons() {
    try {
        const response = await fetch('/api/persons');
        const result = await response.json();
        
        if (result.success) {
            persons = result.data || [];
            personMap = {};
            persons.forEach(person => {
                personMap[person.id] = person.name;
            });
        }
    } catch (error) {
        console.error('加载人员列表失败：', error);
    }
}

// 更新公司选项（根据选择的人员）
async function updateCompanyOptions() {
    const personId = document.getElementById('leavePersonSelect').value;
    const companySelect = document.getElementById('leaveCompanySelect');
    
    if (!personId || !companySelect) return;
    
    // 清空现有选项
    companySelect.innerHTML = '<option value="">请选择公司</option>';
    
    try {
        // 获取该人员的员工记录
        const response = await fetch(`/api/employees?person_id=${personId}`);
        const result = await response.json();
        
        if (result.success) {
            const companySet = new Set();
            result.data.forEach(emp => {
                if (emp.company_name) {
                    companySet.add(emp.company_name);
                }
            });
            
            Array.from(companySet).sort().forEach(company => {
                const option = document.createElement('option');
                option.value = company;
                option.textContent = company;
                companySelect.appendChild(option);
            });
            
            M.FormSelect.init(companySelect);
        }
    } catch (error) {
        console.error('加载公司选项失败：', error);
    }
}

// 加载请假记录
async function loadLeaveRecords() {
    try {
        updateStatus('加载中...');
        
        let startDate = document.getElementById('startDate').value;
        let endDate = document.getElementById('endDate').value;
        const companyName = document.getElementById('companyFilter').value;
        
        // 如果没有选择日期范围，默认查询最近30天
        if (!startDate && !endDate) {
            const today = new Date();
            endDate = today.toISOString().split('T')[0];
            const thirtyDaysAgo = new Date(today);
            thirtyDaysAgo.setDate(today.getDate() - 30);
            startDate = thirtyDaysAgo.toISOString().split('T')[0];
            
            // 设置到输入框中
            document.getElementById('startDate').value = startDate;
            document.getElementById('endDate').value = endDate;
        }
        
        // 构建查询参数
        let url = '/api/leave-records?';
        const params = [];
        
        if (startDate) params.push(`start_date=${startDate}`);
        if (endDate) params.push(`end_date=${endDate}`);
        if (companyName) params.push(`company_name=${encodeURIComponent(companyName)}`);
        
        url += params.join('&');
        
        const response = await fetch(url);
        const result = await response.json();
        
        if (result.success) {
            leaveList = result.data || [];
            
            renderLeaveTable(leaveList);
            updateStatus(`共 ${leaveList.length} 条记录`);
        } else {
            updateStatus('加载失败：' + result.error);
            document.getElementById('leaveTableBody').innerHTML = 
                '<tr><td colspan="12" class="center-align red-text">加载失败：' + result.error + '</td></tr>';
        }
    } catch (error) {
        console.error('加载请假记录失败：', error);
        updateStatus('加载失败：' + error.message);
        document.getElementById('leaveTableBody').innerHTML = 
            '<tr><td colspan="12" class="center-align red-text">加载失败：' + error.message + '</td></tr>';
    }
}

// 渲染请假表格
function renderLeaveTable(leaveRecords) {
    const tbody = document.getElementById('leaveTableBody');
    if (!tbody) return;
    
    if (leaveRecords.length === 0) {
        tbody.innerHTML = '<tr><td colspan="12" class="center-align grey-text">暂无请假记录</td></tr>';
        return;
    }
    
    tbody.innerHTML = leaveRecords.map(leave => {
        const personName = personMap[leave.person_id] || '-';
        const startTime = leave.start_time ? formatDateTime(leave.start_time) : '-';
        const endTime = leave.end_time ? formatDateTime(leave.end_time) : '-';
        const unpaidHours = (leave.leave_hours - (leave.paid_hours || 0)).toFixed(1);
        const statusBadge = getStatusBadge(leave.status);
        const typeBadge = getTypeBadge(leave.leave_type);
        
        return `
            <tr data-leave-id="${leave.id}">
                <td>${leave.leave_date}</td>
                <td>${personName}</td>
                <td>${leave.company_name || '-'}</td>
                <td>${typeBadge}</td>
                <td>${startTime}</td>
                <td>${endTime}</td>
                <td>${leave.leave_hours.toFixed(1)} 小时</td>
                <td>
                    <span class="paid-hours-clickable" 
                          data-leave-id="${leave.id}" 
                          data-paid-hours="${leave.paid_hours || 0}"
                          style="cursor: pointer; color: #1976d2; text-decoration: underline;"
                          title="点击修改带薪时长">
                        ${(leave.paid_hours || 0).toFixed(1)} 小时
                    </span>
                </td>
                <td>${unpaidHours} 小时</td>
                <td>${statusBadge}</td>
                <td>${leave.reason || '-'}</td>
                <td>
                    <button class="btn-small waves-effect waves-light blue" onclick="showEditLeaveModal(${leave.id})" style="margin: 2px;">
                        <i class="material-icons tiny">edit</i>
                    </button>
                    <button class="btn-small waves-effect waves-light red" onclick="deleteLeaveRecord(${leave.id})" style="margin: 2px;">
                        <i class="material-icons tiny">delete</i>
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

// 获取状态徽章
function getStatusBadge(status) {
    const statusMap = {
        'approved': '<span class="green-text">已批准</span>',
        'pending': '<span class="orange-text">待审批</span>',
        'rejected': '<span class="red-text">已拒绝</span>'
    };
    return statusMap[status] || status;
}

// 获取类型徽章
function getTypeBadge(type) {
    const typeColors = {
        '病假': 'red-text',
        '事假': 'orange-text',
        '年假': 'blue-text',
        '调休': 'green-text',
        '产假': 'pink-text',
        '婚假': 'purple-text'
    };
    const color = typeColors[type] || '';
    return `<span class="${color}">${type}</span>`;
}

// 格式化日期时间
function formatDateTime(dateTimeStr) {
    if (!dateTimeStr) return '-';
    const date = new Date(dateTimeStr);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// 显示新增请假模态框
function showAddLeaveModal() {
    isEditMode = false;
    selectedLeaveId = null;
    
    const modalTitle = document.getElementById('leaveModalTitle');
    if (modalTitle) {
        modalTitle.textContent = '新增请假记录';
    }
    
    // 填充人员下拉框
    const personSelect = document.getElementById('leavePersonSelect');
    if (personSelect) {
        personSelect.innerHTML = '<option value="">请选择人员</option>';
        persons.forEach(person => {
            const option = document.createElement('option');
            option.value = person.id;
            option.textContent = person.name;
            personSelect.appendChild(option);
        });
        M.FormSelect.init(personSelect);
    }
    
    // 清空公司下拉框
    const companySelect = document.getElementById('leaveCompanySelect');
    if (companySelect) {
        companySelect.innerHTML = '<option value="">请选择公司</option>';
        M.FormSelect.init(companySelect);
    }
    
    // 重置表单
    document.getElementById('leaveForm').reset();
    M.updateTextFields();
    
    if (leaveModalInstance) {
        leaveModalInstance.open();
    }
}

// 显示编辑请假模态框
async function showEditLeaveModal(leaveId) {
    try {
        isEditMode = true;
        selectedLeaveId = leaveId;
        
        const response = await fetch(`/api/leave-records/${leaveId}`);
        const result = await response.json();
        
        if (!result.success) {
            M.toast({html: '加载请假记录失败：' + result.error, classes: 'red'});
            return;
        }
        
        const leave = result.data;
        
        const modalTitle = document.getElementById('leaveModalTitle');
        if (modalTitle) {
            modalTitle.textContent = '编辑请假记录';
        }
        
        // 填充表单
        document.getElementById('leaveId').value = leave.id;
        document.getElementById('leavePersonId').value = leave.person_id;
        document.getElementById('leaveEmployeeId').value = leave.employee_id || '';
        
        // 填充人员下拉框
        const personSelect = document.getElementById('leavePersonSelect');
        if (personSelect) {
            personSelect.innerHTML = '<option value="">请选择人员</option>';
            persons.forEach(person => {
                const option = document.createElement('option');
                option.value = person.id;
                option.textContent = person.name;
                if (person.id === leave.person_id) {
                    option.selected = true;
                }
                personSelect.appendChild(option);
            });
            M.FormSelect.init(personSelect);
        }
        
        // 更新公司选项
        await updateCompanyOptions();
        
        // 设置公司
        const companySelect = document.getElementById('leaveCompanySelect');
        if (companySelect) {
            companySelect.value = leave.company_name;
            M.FormSelect.init(companySelect);
        }
        
        // 设置其他字段
        document.getElementById('leaveDate').value = leave.leave_date;
        document.getElementById('leaveType').value = leave.leave_type;
        document.getElementById('startTime').value = leave.start_time ? leave.start_time.substring(0, 16) : '';
        document.getElementById('endTime').value = leave.end_time ? leave.end_time.substring(0, 16) : '';
        document.getElementById('leaveHours').value = leave.leave_hours;
        document.getElementById('paidHours').value = leave.paid_hours || 0;
        document.getElementById('leaveStatus').value = leave.status;
        document.getElementById('leaveReason').value = leave.reason || '';
        
        M.updateTextFields();
        
        if (leaveModalInstance) {
            leaveModalInstance.open();
        }
    } catch (error) {
        console.error('加载请假记录失败：', error);
        M.toast({html: '加载请假记录失败：' + error.message, classes: 'red'});
    }
}

// 保存请假记录
async function saveLeaveRecord(e) {
    e.preventDefault();
    
    try {
        const personId = parseInt(document.getElementById('leavePersonSelect').value);
        const companyName = document.getElementById('leaveCompanySelect').value;
        
        // 根据person_id和company_name查找employee_id
        let employeeId = null;
        if (personId && companyName) {
            try {
                const empResponse = await fetch(`/api/employees?person_id=${personId}&company_name=${encodeURIComponent(companyName)}`);
                const empResult = await empResponse.json();
                if (empResult.success && empResult.data && empResult.data.length > 0) {
                    employeeId = empResult.data[0].id;
                }
            } catch (error) {
                console.warn('查找员工ID失败，将使用null:', error);
            }
        }
        
        const formData = {
            person_id: personId,
            employee_id: employeeId,
            company_name: companyName,
            leave_date: document.getElementById('leaveDate').value,
            leave_type: document.getElementById('leaveType').value,
            start_time: document.getElementById('startTime').value || null,
            end_time: document.getElementById('endTime').value || null,
            leave_hours: parseFloat(document.getElementById('leaveHours').value),
            paid_hours: parseFloat(document.getElementById('paidHours').value) || 0,
            reason: document.getElementById('leaveReason').value || null,
            status: document.getElementById('leaveStatus').value
        };
        
        // 验证带薪时长不能超过请假时长
        if (formData.paid_hours > formData.leave_hours) {
            M.toast({html: '带薪时长不能超过请假时长', classes: 'orange'});
            return;
        }
        
        let url = '/api/leave-records';
        let method = 'POST';
        
        if (isEditMode && selectedLeaveId) {
            url = `/api/leave-records/${selectedLeaveId}`;
            method = 'PUT';
        }
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            M.toast({html: result.message || '保存成功', classes: 'green'});
            if (leaveModalInstance) {
                leaveModalInstance.close();
            }
            loadLeaveRecords();
        } else {
            M.toast({html: '保存失败：' + result.error, classes: 'red'});
        }
    } catch (error) {
        console.error('保存请假记录失败：', error);
        M.toast({html: '保存失败：' + error.message, classes: 'red'});
    }
}

// 删除请假记录
async function deleteLeaveRecord(leaveId) {
    if (!confirm('确定要删除这条请假记录吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/leave-records/${leaveId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            M.toast({html: '删除成功', classes: 'green'});
            loadLeaveRecords();
        } else {
            M.toast({html: '删除失败：' + result.error, classes: 'red'});
        }
    } catch (error) {
        console.error('删除请假记录失败：', error);
        M.toast({html: '删除失败：' + error.message, classes: 'red'});
    }
}

// 显示带薪时长编辑卡片
async function showPaidHoursCard(leaveId, currentPaidHours, rect) {
    try {
        // 获取请假记录详情（包含历史记录）
        const response = await fetch(`/api/leave-records/${leaveId}`);
        const result = await response.json();
        
        if (!result.success) {
            M.toast({html: '加载请假记录失败：' + result.error, classes: 'red'});
            return;
        }
        
        const leave = result.data;
        const history = leave.paid_hours_history || [];
        
        // 使用从API获取的实际值，而不是表格中的值
        const actualPaidHours = leave.paid_hours || 0;
        
        // 设置当前值
        document.getElementById('paidHoursLeaveId').value = leaveId;
        document.getElementById('paidHoursCurrentValue').value = actualPaidHours;
        document.getElementById('paidHoursNewValue').value = actualPaidHours;
        document.getElementById('paidHoursChangeReason').value = '';
        
        // 渲染历史记录
        const historyContainer = document.getElementById('paidHoursHistory');
        const historyToggle = document.getElementById('paidHoursHistoryToggle');
        
        if (history.length > 0) {
            historyContainer.innerHTML = history.map((item, index) => `
                <div class="paid-hours-history-item">
                    <div>
                        <span class="value-change">
                            ${item.old_value !== null && item.old_value !== undefined ? item.old_value.toFixed(1) : '初始'} 
                            → ${item.new_value.toFixed(1)}
                        </span>
                        <span class="time">${item.changed_at}</span>
                    </div>
                    <div class="reason">${item.change_reason || '无'} (${item.changed_by || 'system'})</div>
                </div>
            `).join('');
            historyToggle.style.display = 'block';
            historyContainer.style.display = 'none';
        } else {
            historyContainer.innerHTML = '<div style="text-align: center; color: #999; padding: 8px; font-size: 12px;">暂无修改历史</div>';
            historyToggle.style.display = 'none';
            historyContainer.style.display = 'block';
        }
        
        // 计算卡片位置（在点击元素附近）
        const cardWidth = 320;
        const cardHeight = 200; // 估算高度
        let left = rect.left + rect.width / 2 - cardWidth / 2;
        let top = rect.bottom + 8;
        
        // 确保不超出视口
        if (left < 10) left = 10;
        if (left + cardWidth > window.innerWidth - 10) {
            left = window.innerWidth - cardWidth - 10;
        }
        if (top + cardHeight > window.innerHeight - 10) {
            top = rect.top - cardHeight - 8;
        }
        
        // 设置位置并显示
        if (paidHoursCardElement) {
            paidHoursCardElement.style.left = left + 'px';
            paidHoursCardElement.style.top = top + 'px';
            paidHoursCardElement.style.display = 'block';
        }
        
        if (paidHoursOverlayElement) {
            paidHoursOverlayElement.style.display = 'block';
        }
        
        // 聚焦到输入框
        setTimeout(() => {
            document.getElementById('paidHoursNewValue').focus();
        }, 100);
    } catch (error) {
        console.error('加载请假记录失败：', error);
        M.toast({html: '加载请假记录失败：' + error.message, classes: 'red'});
    }
}

// 关闭带薪时长编辑卡片
function closePaidHoursCard() {
    if (paidHoursCardElement) {
        paidHoursCardElement.style.display = 'none';
    }
    if (paidHoursOverlayElement) {
        paidHoursOverlayElement.style.display = 'none';
    }
    // 重置表单
    document.getElementById('paidHoursForm').reset();
    document.getElementById('paidHoursHistory').innerHTML = '';
}

// 保存带薪时长
async function savePaidHours() {
    try {
        const leaveId = parseInt(document.getElementById('paidHoursLeaveId').value);
        const currentValue = parseFloat(document.getElementById('paidHoursCurrentValue').value);
        const newValue = parseFloat(document.getElementById('paidHoursNewValue').value);
        const changeReason = document.getElementById('paidHoursChangeReason').value.trim();
        
        // 验证
        if (!leaveId) {
            M.toast({html: '请假记录ID无效', classes: 'orange'});
            return;
        }
        
        if (isNaN(newValue) || newValue < 0) {
            M.toast({html: '请输入有效的带薪时长', classes: 'orange'});
            return;
        }
        
        if (!changeReason) {
            M.toast({html: '请输入修改原因', classes: 'orange'});
            return;
        }
        
        // 获取请假记录以验证带薪时长不能超过请假时长
        const getResponse = await fetch(`/api/leave-records/${leaveId}`);
        const getResult = await getResponse.json();
        
        if (!getResult.success) {
            M.toast({html: '获取请假记录失败：' + getResult.error, classes: 'red'});
            return;
        }
        
        const leave = getResult.data;
        if (newValue > leave.leave_hours) {
            M.toast({html: '带薪时长不能超过请假时长', classes: 'orange'});
            return;
        }
        
        // 使用从API获取的实际值进行比较，而不是隐藏字段的值
        const actualCurrentValue = leave.paid_hours || 0;
        if (Math.abs(newValue - actualCurrentValue) < 0.001) {
            M.toast({html: '带薪时长未发生变化', classes: 'orange'});
            return;
        }
        
        // 更新请假记录
        const updateData = {
            paid_hours: newValue,
            paid_hours_change_reason: changeReason
        };
        
        const response = await fetch(`/api/leave-records/${leaveId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-User': 'admin'  // 可以从登录信息中获取
            },
            body: JSON.stringify(updateData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            M.toast({html: '带薪时长更新成功', classes: 'green'});
            closePaidHoursCard();
            loadLeaveRecords();  // 重新加载列表
        } else {
            M.toast({html: '更新失败：' + result.error, classes: 'red'});
        }
    } catch (error) {
        console.error('保存带薪时长失败：', error);
        M.toast({html: '保存失败：' + error.message, classes: 'red'});
    }
}

// 更新状态栏
function updateStatus(message) {
    const statusText = document.getElementById('statusText');
    if (statusText) {
        statusText.textContent = message;
    }
}

