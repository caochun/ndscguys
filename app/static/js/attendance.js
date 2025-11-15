// 考勤页面 JavaScript

// 全局变量
let attendanceList = [];
let selectedAttendanceId = null;
let isEditMode = false;
let companies = [];

// Materialize 组件实例
let attendanceModalInstance = null;

// DOM 加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initMaterializeComponents();
    initEventListeners();
    loadCompanies();
    loadAttendance();
});

// 初始化 Materialize 组件
function initMaterializeComponents() {
    // 初始化考勤模态框
    const attendanceModal = document.getElementById('attendanceModal');
    if (attendanceModal) {
        attendanceModalInstance = M.Modal.init(attendanceModal, {
            onCloseEnd: function() {
                document.getElementById('attendanceForm').reset();
                M.updateTextFields();
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
        searchBtn.addEventListener('click', loadAttendance);
    }
    
    // 模态框关闭按钮
    const cancelBtn = document.getElementById('cancelAttendanceBtn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            if (attendanceModalInstance) {
                attendanceModalInstance.close();
            }
        });
    }

    // 表单提交
    const attendanceForm = document.getElementById('attendanceForm');
    if (attendanceForm) {
        attendanceForm.addEventListener('submit', saveAttendance);
    }

    // 考勤表格行点击选择（使用事件委托）
    const attendanceTableBody = document.getElementById('attendanceTableBody');
    if (attendanceTableBody) {
        attendanceTableBody.addEventListener('click', function(e) {
            const row = e.target.closest('tr');
            if (row && row.dataset.attendanceId) {
                // 移除之前的选中状态
                document.querySelectorAll('#attendanceTableBody tr').forEach(r => r.classList.remove('selected'));
                // 添加选中状态
                row.classList.add('selected');
                selectedAttendanceId = parseInt(row.dataset.attendanceId);
            }
        });
    }
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
            
            // 填充公司下拉框
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

// 加载考勤记录
async function loadAttendance() {
    try {
        updateStatus('加载中...');
        
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        const companyName = document.getElementById('companyFilter').value;
        
        // 如果没有选择日期范围，默认查询最近30天
        let queryStartDate = startDate;
        let queryEndDate = endDate;
        
        if (!queryStartDate && !queryEndDate) {
            const today = new Date();
            queryEndDate = today.toISOString().split('T')[0];
            const thirtyDaysAgo = new Date(today);
            thirtyDaysAgo.setDate(today.getDate() - 30);
            queryStartDate = thirtyDaysAgo.toISOString().split('T')[0];
        }
        
        let url = '/api/attendance?';
        const params = [];
        
        // 使用日期范围查询
        if (queryStartDate) params.push(`start_date=${queryStartDate}`);
        if (queryEndDate) params.push(`end_date=${queryEndDate}`);
        if (companyName) params.push(`company_name=${encodeURIComponent(companyName)}`);
        
        url += params.join('&');
        
        const response = await fetch(url);
        const result = await response.json();

        if (result.success) {
            attendanceList = result.data;
            renderAttendanceTable(attendanceList);
            updateStatus(`已加载 ${attendanceList.length} 条考勤记录`);
        } else {
            showError('加载考勤记录失败：' + result.error);
            updateStatus('加载失败');
        }
    } catch (error) {
        showError('加载考勤记录失败：' + error.message);
        updateStatus('加载失败');
    }
}

// 渲染考勤表格
function renderAttendanceTable(attendanceList) {
    const tbody = document.getElementById('attendanceTableBody');
    if (!tbody) return;
    
    if (attendanceList.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="center-align">暂无考勤数据</td></tr>';
        return;
    }

    // 需要获取人员姓名，先加载所有人员
    fetch('/api/persons')
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                const personMap = {};
                result.data.forEach(person => {
                    personMap[person.id] = person.name;
                });
                
                tbody.innerHTML = attendanceList.map(attendance => {
                    const statusBadge = getStatusBadge(attendance.status);
                    const checkInTime = attendance.check_in_time ? 
                        new Date(attendance.check_in_time).toLocaleString('zh-CN', {hour12: false}) : '-';
                    const checkOutTime = attendance.check_out_time ? 
                        new Date(attendance.check_out_time).toLocaleString('zh-CN', {hour12: false}) : '-';
                    const workHours = attendance.work_hours ? attendance.work_hours.toFixed(2) : '-';
                    const leaveHours = attendance.leave_hours ? attendance.leave_hours.toFixed(2) : '-';
                    const overtimeHours = attendance.overtime_hours ? attendance.overtime_hours.toFixed(2) : '-';
                    
                    return `
                    <tr data-attendance-id="${attendance.id}">
                        <td>${attendance.attendance_date}</td>
                        <td>${personMap[attendance.person_id] || '-'}</td>
                        <td>${attendance.company_name || '-'}</td>
                        <td>${checkInTime}</td>
                        <td>${checkOutTime}</td>
                        <td>${workHours}</td>
                        <td>${leaveHours}</td>
                        <td>${overtimeHours}</td>
                        <td>${statusBadge}</td>
                        <td>
                            <button class="btn-small waves-effect waves-light blue" onclick="showAttendanceDetail(${attendance.id})">
                                <i class="material-icons">edit</i>
                            </button>
                        </td>
                    </tr>
                    `;
                }).join('');
            }
        })
        .catch(error => {
            console.error('加载人员信息失败：', error);
            tbody.innerHTML = '<tr><td colspan="10" class="center-align">加载失败</td></tr>';
        });
}

// 获取状态徽章
function getStatusBadge(status) {
    const statusMap = {
        'normal': '<span class="attendance-status-badge status-normal"><i class="material-icons tiny">check_circle</i>正常</span>',
        'late': '<span class="attendance-status-badge status-late"><i class="material-icons tiny">schedule</i>迟到</span>',
        'early_leave': '<span class="attendance-status-badge status-early-leave"><i class="material-icons tiny">exit_to_app</i>早退</span>',
        'absent': '<span class="attendance-status-badge status-absent"><i class="material-icons tiny">cancel</i>缺勤</span>',
        'leave': '<span class="attendance-status-badge status-leave"><i class="material-icons tiny">event_busy</i>请假</span>',
        'partial_leave': '<span class="attendance-status-badge status-partial-leave"><i class="material-icons tiny">event_available</i>部分请假</span>',
        'incomplete': '<span class="attendance-status-badge status-incomplete"><i class="material-icons tiny">hourglass_empty</i>未完成</span>',
        'overtime': '<span class="attendance-status-badge status-overtime"><i class="material-icons tiny">work</i>加班</span>'
    };
    return statusMap[status] || '<span class="attendance-status-badge status-unknown"><i class="material-icons tiny">help</i>' + (status || '未知') + '</span>';
}

// 显示考勤详情
async function showAttendanceDetail(attendanceId) {
    try {
        const response = await fetch(`/api/attendance/${attendanceId}`);
        const result = await response.json();
        
        if (result.success) {
            const attendance = result.data;
            isEditMode = true;
            selectedAttendanceId = attendanceId;
            
            document.getElementById('attendanceModalTitle').textContent = '编辑考勤记录';
            document.getElementById('attendanceId').value = attendance.id;
            document.getElementById('attendancePersonId').value = attendance.person_id;
            document.getElementById('attendanceCompanyName').value = attendance.company_name;
            document.getElementById('attendanceDate').value = attendance.attendance_date;
            
            // 加载人员姓名
            const personResponse = await fetch(`/api/persons`);
            const personResult = await personResponse.json();
            if (personResult.success) {
                const person = personResult.data.find(p => p.id === attendance.person_id);
                document.getElementById('attendancePersonName').value = person ? person.name : '-';
            }
            
            // 处理时间格式（从 'YYYY-MM-DD HH:MM:SS' 转换为 'YYYY-MM-DDTHH:MM'）
            if (attendance.check_in_time) {
                const checkIn = new Date(attendance.check_in_time);
                document.getElementById('checkInTime').value = checkIn.toISOString().slice(0, 16);
            } else {
                document.getElementById('checkInTime').value = '';
            }
            
            if (attendance.check_out_time) {
                const checkOut = new Date(attendance.check_out_time);
                document.getElementById('checkOutTime').value = checkOut.toISOString().slice(0, 16);
            } else {
                document.getElementById('checkOutTime').value = '';
            }
            
            document.getElementById('standardHours').value = attendance.standard_hours || 8.0;
            document.getElementById('attendanceStatus').value = getStatusText(attendance.status);
            document.getElementById('attendanceRemark').value = attendance.remark || '';
            
            M.updateTextFields();
            if (attendanceModalInstance) {
                attendanceModalInstance.open();
            }
        } else {
            M.toast({html: '加载考勤记录失败：' + result.error, classes: 'red'});
        }
    } catch (error) {
        M.toast({html: '加载考勤记录失败：' + error.message, classes: 'red'});
    }
}

// 获取状态文本
function getStatusText(status) {
    const statusMap = {
        'normal': '正常',
        'late': '迟到',
        'early_leave': '早退',
        'absent': '缺勤',
        'leave': '请假',
        'partial_leave': '部分请假',
        'incomplete': '未完成',
        'overtime': '加班'
    };
    return statusMap[status] || status || '未知';
}

// 保存考勤记录
async function saveAttendance(e) {
    e.preventDefault();
    
    const attendanceId = document.getElementById('attendanceId').value;
    const personId = document.getElementById('attendancePersonId').value;
    const companyName = document.getElementById('attendanceCompanyName').value;
    const attendanceDate = document.getElementById('attendanceDate').value;
    
    if (!attendanceDate) {
        M.toast({html: '考勤日期不能为空', classes: 'orange'});
        return;
    }
    
    // 处理时间格式（从 'YYYY-MM-DDTHH:MM' 转换为 'YYYY-MM-DD HH:MM:SS'）
    let checkInTime = document.getElementById('checkInTime').value;
    if (checkInTime) {
        checkInTime = checkInTime.replace('T', ' ') + ':00';
    }
    
    let checkOutTime = document.getElementById('checkOutTime').value;
    if (checkOutTime) {
        checkOutTime = checkOutTime.replace('T', ' ') + ':00';
    }
    
    const attendanceData = {
        person_id: parseInt(personId),
        company_name: companyName,
        attendance_date: attendanceDate,
        check_in_time: checkInTime || null,
        check_out_time: checkOutTime || null,
        standard_hours: parseFloat(document.getElementById('standardHours').value) || 8.0,
        remark: document.getElementById('attendanceRemark').value || null
    };
    
    try {
        updateStatus('保存中...');
        let response;
        
        if (attendanceId) {
            // 更新
            response = await fetch(`/api/attendance/${attendanceId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(attendanceData)
            });
        } else {
            // 创建
            response = await fetch('/api/attendance', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(attendanceData)
            });
        }
        
        const result = await response.json();
        
        if (result.success) {
            M.toast({html: result.message || '保存成功', classes: 'green'});
            updateStatus(result.message || '保存成功');
            if (attendanceModalInstance) {
                attendanceModalInstance.close();
            }
            loadAttendance();
        } else {
            M.toast({html: '保存失败：' + result.error, classes: 'red'});
            updateStatus('保存失败');
        }
    } catch (error) {
        M.toast({html: '保存失败：' + error.message, classes: 'red'});
        updateStatus('保存失败');
    }
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

