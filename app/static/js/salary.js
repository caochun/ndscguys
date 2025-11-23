// 薪资页面脚本

let payrollModalInstance = null;
let payrollRows = [];
let socialSecurityRows = [];
let housingFundRows = [];
let payrollTableBody = null;
let socialSecurityTableBody = null;
let housingFundTableBody = null;
let payrollRecordsTableBody = null;
let statusTextEl = null;
let payrollPeriodInput = null;
let issueDateInput = null;
let payrollNoteInput = null;
let currentPayrollId = null; // 当前查看的批次ID
let isViewMode = false; // 是否为查看模式（false=创建模式，true=查看模式）

const gradeOptions = [
    { value: 'A', label: 'A (150%)' },
    { value: 'B', label: 'B (120%)' },
    { value: 'C', label: 'C (100%)' },
    { value: 'D', label: 'D (80%)' },
    { value: 'E', label: 'E (60%)' },
    { value: 'NONE', label: '无等级 (0%)' }
];

const gradeCoefficient = {
    'A': 1.5,
    'B': 1.2,
    'C': 1.0,
    'D': 0.8,
    'E': 0.6,
    'NONE': 0
};

document.addEventListener('DOMContentLoaded', () => {
    payrollTableBody = document.getElementById('payrollTableBody');
    socialSecurityTableBody = document.getElementById('socialSecurityTableBody');
    housingFundTableBody = document.getElementById('housingFundTableBody');
    payrollRecordsTableBody = document.getElementById('payrollRecordsTableBody');
    statusTextEl = document.getElementById('statusText');
    payrollPeriodInput = document.getElementById('payrollPeriod');
    issueDateInput = document.getElementById('issueDate');
    payrollNoteInput = document.getElementById('payrollNote');
    
    initMaterializeComponents();
    initEventListeners();
    setDefaultPeriod();
    loadPayrollRecords();
});

function initMaterializeComponents() {
    const modalElem = document.getElementById('payrollModal');
    if (modalElem) {
        payrollModalInstance = M.Modal.init(modalElem, {
            onOpenStart: () => {
                // 如果是创建模式，隐藏所有表格
                if (!isViewMode) {
                    // 显示创建模式按钮，隐藏查看模式按钮
                    const createButtons = document.getElementById('createModeButtons');
                    if (createButtons) {
                        createButtons.style.display = 'block';
                    }
                    const viewFooter = document.getElementById('viewModeFooter');
                    if (viewFooter) {
                        viewFooter.style.display = 'none';
                    }
                    // 显示批次信息区域
                    const infoSection = document.getElementById('payrollInfoSection');
                    if (infoSection) {
                        infoSection.style.display = 'block';
                    }
                    // 隐藏整个表格容器
                    const tablesContainer = document.getElementById('payrollTablesContainer');
                    if (tablesContainer) {
                        tablesContainer.style.display = 'none';
                    }
                    // 隐藏标签页容器
                    const tabsContainer = document.getElementById('payrollTabsContainer');
                    if (tabsContainer) {
                        tabsContainer.style.display = 'none';
                    }
                } else {
                    // 查看模式（从明细按钮点击）：隐藏创建模式按钮，显示查看模式按钮
                    const createButtons = document.getElementById('createModeButtons');
                    if (createButtons) {
                        createButtons.style.display = 'none';
                    }
                    const viewFooter = document.getElementById('viewModeFooter');
                    if (viewFooter) {
                        viewFooter.style.display = 'block';
                    }
                    // 隐藏批次信息区域
                    const infoSection = document.getElementById('payrollInfoSection');
                    if (infoSection) {
                        infoSection.style.display = 'none';
                    }
                    // 显示表格容器，但隐藏标签页容器（明细模式不需要标签页）
                    const tablesContainer = document.getElementById('payrollTablesContainer');
                    if (tablesContainer) {
                        tablesContainer.style.display = 'block';
                    }
                    const tabsContainer = document.getElementById('payrollTabsContainer');
                    if (tabsContainer) {
                        tabsContainer.style.display = 'none';
                    }
                }
            },
            onCloseEnd: () => {
                // 关闭时重置状态
                isViewMode = false;
                currentPayrollId = null;
                const modal = document.getElementById('payrollModal');
                if (modal) {
                    modal.classList.remove('create-mode');
                }
                // 恢复输入框为可编辑
                if (payrollPeriodInput) {
                    payrollPeriodInput.readOnly = false;
                }
                if (issueDateInput) {
                    issueDateInput.readOnly = false;
                }
                if (payrollNoteInput) {
                    payrollNoteInput.readOnly = false;
                }
                // 显示创建模式按钮，隐藏查看模式按钮
                const createButtons = document.getElementById('createModeButtons');
                if (createButtons) {
                    createButtons.style.display = 'block';
                }
                const viewFooter = document.getElementById('viewModeFooter');
                if (viewFooter) {
                    viewFooter.style.display = 'none';
                }
                // 恢复模态框标题和图标
                const modalTitle = document.getElementById('payrollModalTitle');
                if (modalTitle) {
                    modalTitle.textContent = '生成薪资批次';
                }
                const titleIcon = document.querySelector('#payrollModalHeader .material-icons');
                if (titleIcon) {
                    titleIcon.textContent = 'playlist_add';
                }
                // 显示批次信息区域
                const infoSection = document.getElementById('payrollInfoSection');
                if (infoSection) {
                    infoSection.style.display = 'block';
                }
                // 隐藏描述文字
                const description = document.getElementById('payrollModalDescription');
                if (description) {
                    description.style.display = 'none';
                }
                // 显示表格容器（关闭时恢复，创建模式时会在打开时隐藏）
                const tablesContainer = document.getElementById('payrollTablesContainer');
                if (tablesContainer) {
                    tablesContainer.style.display = 'block';
                }
                // 隐藏标签页容器
                const tabsContainer = document.getElementById('payrollTabsContainer');
                if (tabsContainer) {
                    tabsContainer.style.display = 'none';
                }
                // 隐藏所有标签页内容
                const allTabPanels = document.querySelectorAll('.tab-content-panel');
                allTabPanels.forEach(panel => {
                    panel.style.display = 'none';
                });
            }
        });
    }
    
    const payrollTabs = document.getElementById('payrollTabs');
    if (payrollTabs) {
        M.Tabs.init(payrollTabs);
    }
    
    const mobileNav = document.getElementById('mobile-nav');
    if (mobileNav) {
        M.Sidenav.init(mobileNav);
    }
}

function initEventListeners() {
    const newPayrollBtn = document.getElementById('newPayrollBtn');
    if (newPayrollBtn) {
        newPayrollBtn.addEventListener('click', () => {
            // 设置为创建模式
            isViewMode = false;
            currentPayrollId = null;
            // 恢复输入框为可编辑
            if (payrollPeriodInput) {
                payrollPeriodInput.readOnly = false;
            }
            if (issueDateInput) {
                issueDateInput.readOnly = false;
            }
            if (payrollNoteInput) {
                payrollNoteInput.readOnly = false;
            }
            // 显示创建模式按钮，隐藏查看模式按钮
            const createButtons = document.getElementById('createModeButtons');
            if (createButtons) {
                createButtons.style.display = 'block';
            }
            const viewFooter = document.getElementById('viewModeFooter');
            if (viewFooter) {
                viewFooter.style.display = 'none';
            }
            // 恢复模态框标题和图标
            const modalTitle = document.getElementById('payrollModalTitle');
            if (modalTitle) {
                modalTitle.textContent = '生成薪资批次';
            }
            const titleIcon = document.querySelector('#payrollModalHeader .material-icons');
            if (titleIcon) {
                titleIcon.textContent = 'playlist_add';
            }
            // 显示批次信息区域
            const infoSection = document.getElementById('payrollInfoSection');
            if (infoSection) {
                infoSection.style.display = 'block';
            }
            // 隐藏描述文字（创建模式不显示）
            const description = document.getElementById('payrollModalDescription');
            if (description) {
                description.style.display = 'none';
            }
            // 添加创建模式类
            const modal = document.getElementById('payrollModal');
            if (modal) {
                modal.classList.add('create-mode');
            }
            // 隐藏表格容器（创建模式不显示表格）
            const tablesContainer = document.getElementById('payrollTablesContainer');
            if (tablesContainer) {
                tablesContainer.style.display = 'none';
            }
            // 隐藏标签页容器
            const tabsContainer = document.getElementById('payrollTabsContainer');
            if (tabsContainer) {
                tabsContainer.style.display = 'none';
            }
            // 隐藏所有标签页内容
            const allTabPanels = document.querySelectorAll('.tab-content-panel');
            allTabPanels.forEach(panel => {
                panel.style.display = 'none';
            });
            
            if (payrollModalInstance) {
                payrollModalInstance.open();
                // 创建模式不需要加载数据，因为不显示表格
            }
        });
    }
    
    const table = document.getElementById('payrollTableBody');
    if (table) {
        table.addEventListener('change', (event) => {
            const select = event.target.closest('.grade-select');
            if (select) {
                const rowIndex = parseInt(select.dataset.index, 10);
                updateRowGrade(rowIndex, select.value);
            }
        });
    }
    
    const savePayrollBtn = document.getElementById('savePayrollBtn');
    if (savePayrollBtn) {
        savePayrollBtn.addEventListener('click', savePayrollRecord);
    }
}

async function loadPayrollData() {
    if (!payrollTableBody) return;
    
    payrollTableBody.innerHTML = '<tr><td colspan="11" class="center-align grey-text">加载中...</td></tr>';
    if (socialSecurityTableBody) {
        socialSecurityTableBody.innerHTML = '<tr><td colspan="11" class="center-align grey-text">加载中...</td></tr>';
    }
    if (housingFundTableBody) {
        housingFundTableBody.innerHTML = '<tr><td colspan="8" class="center-align grey-text">加载中...</td></tr>';
    }
    updateStatus('正在加载薪资数据...');
    
    try {
        const response = await fetch('/api/salary/current');
        const result = await response.json();
        if (result.success) {
            payrollRows = (result.data || []).map((item) => calculateRow({
                employee_id: item.employee_id,
                person_id: item.person_id,
                name: item.name || '未知',
                company_name: item.company_name,
                department: item.department,
                position: item.position,
                employee_type: item.employee_type || '正式员工',
                basic_salary: toNumber(item.basic_salary),
                performance_base: toNumber(item.performance_salary),
                grade: 'C',
                performance_pay: 0,
                adjustment: 0,
                total_pay: 0
            }));
            
            socialSecurityRows = (result.data || []).map(item => ({
                employee_id: item.employee_id,
                name: item.name || '未知',
                company_name: item.company_name,
                department: item.department,
                position: item.position,
                employee_type: item.employee_type || '正式员工',
                base: toNumber(item.basic_salary),
                pension: 0,
                injury: 0,
                medical: 0,
                unemployment: 0,
                maternity: 0
            }));
            
            housingFundRows = (result.data || []).map(item => ({
                employee_id: item.employee_id,
                name: item.name || '未知',
                company_name: item.company_name,
                department: item.department,
                position: item.position,
                employee_type: item.employee_type || '正式员工',
                base: toNumber(item.basic_salary),
                company_portion: 0,
                personal_portion: 0
            }));
            
            renderPayrollTable();
            renderSocialSecurityTable();
            renderHousingFundTable();
            updateStatus(`已加载 ${payrollRows.length} 名员工的薪资信息`);
        } else {
            payrollTableBody.innerHTML = `<tr><td colspan="11" class="center-align red-text">加载失败：${result.error}</td></tr>`;
            if (socialSecurityTableBody) {
                socialSecurityTableBody.innerHTML = `<tr><td colspan="11" class="center-align red-text">加载失败：${result.error}</td></tr>`;
            }
            if (housingFundTableBody) {
                housingFundTableBody.innerHTML = `<tr><td colspan="8" class="center-align red-text">加载失败：${result.error}</td></tr>`;
            }
            updateStatus('加载失败');
        }
    } catch (error) {
        payrollTableBody.innerHTML = `<tr><td colspan="11" class="center-align red-text">加载失败：${error.message}</td></tr>`;
        if (socialSecurityTableBody) {
            socialSecurityTableBody.innerHTML = `<tr><td colspan="11" class="center-align red-text">加载失败：${error.message}</td></tr>`;
        }
        if (housingFundTableBody) {
            housingFundTableBody.innerHTML = `<tr><td colspan="8" class="center-align red-text">加载失败：${error.message}</td></tr>`;
        }
        updateStatus('加载失败');
    }
}

function renderPayrollTable() {
    if (!payrollTableBody) return;
    
    if (payrollRows.length === 0) {
        payrollTableBody.innerHTML = '<tr><td colspan="11" class="center-align grey-text">暂无在职员工薪资数据</td></tr>';
        return;
    }
    
    payrollTableBody.innerHTML = payrollRows.map((row, index) => `
        <tr>
            <td>
                <div style="font-weight: 600;">${row.name}</div>
            </td>
            <td>${row.company_name || '-'}</td>
            <td>${row.department || '-'}</td>
            <td>${row.position || '-'}</td>
            <td>${row.employee_type || '正式员工'}</td>
            <td><input type="number" class="browser-default readonly-field" value="${formatMoney(row.basic_salary)}" readonly></td>
            <td><input type="number" class="browser-default readonly-field" value="${formatMoney(row.performance_base)}" readonly></td>
            <td>
                <select class="grade-select browser-default" data-index="${index}">
                    ${gradeOptions.map(option => `
                        <option value="${option.value}" ${option.value === row.grade ? 'selected' : ''}>${option.label}</option>
                    `).join('')}
                </select>
            </td>
            <td><input type="number" class="browser-default readonly-field" value="${formatMoney(row.performance_pay)}" readonly></td>
            <td><input type="number" class="browser-default readonly-field" value="${formatMoney(row.adjustment)}" readonly></td>
            <td><input type="number" class="browser-default readonly-field" value="${formatMoney(row.total_pay)}" readonly></td>
        </tr>
    `).join('');
    
    // 保持原生 select，避免重复初始化
}

function updateRowGrade(index, grade) {
    if (Number.isNaN(index) || !payrollRows[index]) return;
    payrollRows[index].grade = grade;
    calculateRow(payrollRows[index]);
    renderPayrollTable();
}

function renderSocialSecurityTable() {
    if (!socialSecurityTableBody) return;
    
    if (socialSecurityRows.length === 0) {
        socialSecurityTableBody.innerHTML = '<tr><td colspan="11" class="center-align grey-text">暂无社保数据</td></tr>';
        return;
    }
    
    socialSecurityTableBody.innerHTML = socialSecurityRows.map(row => `
        <tr>
            <td>${row.name}</td>
            <td>${row.company_name || '-'}</td>
            <td>${row.department || '-'}</td>
            <td>${row.position || '-'}</td>
            <td>${row.employee_type || '正式员工'}</td>
            <td>${formatMoney(row.base)}</td>
            <td>${formatMoney(row.pension)}</td>
            <td>${formatMoney(row.injury)}</td>
            <td>${formatMoney(row.medical)}</td>
            <td>${formatMoney(row.unemployment)}</td>
            <td>${formatMoney(row.maternity)}</td>
        </tr>
    `).join('');
}

function renderHousingFundTable() {
    if (!housingFundTableBody) return;
    
    if (housingFundRows.length === 0) {
        housingFundTableBody.innerHTML = '<tr><td colspan="8" class="center-align grey-text">暂无公积金数据</td></tr>';
        return;
    }
    
    housingFundTableBody.innerHTML = housingFundRows.map(row => `
        <tr>
            <td>${row.name}</td>
            <td>${row.company_name || '-'}</td>
            <td>${row.department || '-'}</td>
            <td>${row.position || '-'}</td>
            <td>${row.employee_type || '正式员工'}</td>
            <td>${formatMoney(row.base)}</td>
            <td>${formatMoney(row.company_portion)}</td>
            <td>${formatMoney(row.personal_portion)}</td>
        </tr>
    `).join('');
}

function calculateRow(row) {
    const coeff = gradeCoefficient[row.grade] ?? 0;
    row.performance_pay = round(row.performance_base * coeff);
    row.adjustment = row.adjustment ?? 0;
    row.total_pay = round(row.basic_salary + row.performance_pay + row.adjustment);
    return row;
}

function toNumber(value) {
    const num = Number(value);
    return Number.isFinite(num) ? num : 0;
}

function round(value) {
    return Math.round((Number(value) || 0) * 100) / 100;
}

function formatMoney(value) {
    return round(value).toFixed(2);
}

function updateStatus(text) {
    if (statusTextEl) {
        statusTextEl.textContent = text;
    }
}

function setDefaultPeriod() {
    if (payrollPeriodInput) {
        const now = new Date();
        const defaultValue = formatPeriod(now);
        payrollPeriodInput.value = defaultValue;
    }
    if (issueDateInput) {
        issueDateInput.value = '';
    }
    if (payrollNoteInput) {
        payrollNoteInput.value = '';
    }
    if (typeof M !== 'undefined' && M.updateTextFields) {
        M.updateTextFields();
    }
}

function formatPeriod(date) {
    const year = date.getFullYear();
    const month = `${date.getMonth() + 1}`.padStart(2, '0');
    return `${year}-${month}`;
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN');
}

function formatDateTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
}

function getStatusLabel(status) {
    const statusMap = {
        'draft': '草稿',
        'confirmed': '已确认',
        'paid': '已发放',
        'cancelled': '已取消'
    };
    return statusMap[status] || status;
}

function getStatusClass(status) {
    const classMap = {
        'draft': 'orange-text',
        'confirmed': 'blue-text',
        'paid': 'green-text',
        'cancelled': 'red-text'
    };
    return classMap[status] || '';
}

async function loadPayrollRecords() {
    if (!payrollRecordsTableBody) return;
    
    // 销毁现有的 tooltip 实例
    const existingTooltips = document.querySelectorAll('.tooltipped');
    existingTooltips.forEach(el => {
        const instance = M.Tooltip.getInstance(el);
        if (instance) {
            instance.destroy();
        }
    });
    
    payrollRecordsTableBody.innerHTML = '<tr><td colspan="8" class="center-align grey-text">加载中...</td></tr>';
    
    try {
        const response = await fetch('/api/payroll');
        const result = await response.json();
        
        if (result.success) {
            const records = result.data || [];
            
            if (records.length === 0) {
                payrollRecordsTableBody.innerHTML = '<tr><td colspan="8" class="center-align grey-text">暂无薪资批次记录</td></tr>';
                return;
            }
            
            payrollRecordsTableBody.innerHTML = records.map(record => `
                <tr>
                    <td><strong>${record.period || '-'}</strong></td>
                    <td>${formatDate(record.issue_date)}</td>
                    <td>¥${formatMoney(record.total_gross_amount || 0)}</td>
                    <td>¥${formatMoney(record.total_net_amount || 0)}</td>
                    <td><span class="${getStatusClass(record.status || 'draft')}">${getStatusLabel(record.status || 'draft')}</span></td>
                    <td>${record.note || '-'}</td>
                    <td>${formatDateTime(record.created_at)}</td>
                    <td>
                        <button class="btn-small waves-effect waves-light teal tooltipped" 
                                data-tooltip="薪资" 
                                data-position="top"
                                onclick="showPayrollTab(${record.id}, 'payroll')" 
                                style="margin: 2px;">
                            <i class="material-icons">attach_money</i>
                        </button>
                        <button class="btn-small waves-effect waves-light green tooltipped" 
                                data-tooltip="社保" 
                                data-position="top"
                                onclick="showPayrollTab(${record.id}, 'social')" 
                                style="margin: 2px;">
                            <i class="material-icons">shield</i>
                        </button>
                        <button class="btn-small waves-effect waves-light blue tooltipped" 
                                data-tooltip="公积金" 
                                data-position="top"
                                onclick="showPayrollTab(${record.id}, 'housing')" 
                                style="margin: 2px;">
                            <i class="material-icons">account_balance</i>
                        </button>
                        <button class="btn-small waves-effect waves-light purple tooltipped" 
                                data-tooltip="个税" 
                                data-position="top"
                                onclick="showPayrollTab(${record.id}, 'tax')" 
                                style="margin: 2px;">
                            <i class="material-icons">assessment</i>
                        </button>
                    </td>
                </tr>
            `).join('');
            
            // 初始化新的 tooltip
            const tooltips = payrollRecordsTableBody.querySelectorAll('.tooltipped');
            M.Tooltip.init(tooltips, {
                position: 'top',
                exitDelay: 0
            });
        } else {
            payrollRecordsTableBody.innerHTML = `<tr><td colspan="8" class="center-align red-text">加载失败：${result.error}</td></tr>`;
        }
    } catch (error) {
        console.error('加载薪资批次列表失败:', error);
        payrollRecordsTableBody.innerHTML = `<tr><td colspan="8" class="center-align red-text">加载失败：${error.message}</td></tr>`;
    }
}

function viewPayrollDetail(payrollId) {
    // 默认显示薪资标签页
    showPayrollTab(payrollId, 'payroll');
}

async function showPayrollTab(payrollId, tabName) {
    // 设置查看模式
    currentPayrollId = payrollId;
    isViewMode = true;
    
    // 加载批次详情
    try {
        const response = await fetch(`/api/payroll/${payrollId}`);
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || '加载失败');
        }
        
        const detail = result.data;
        const payroll = detail.payroll;
        const items = detail.items || [];
        
        // 定义标签页名称映射
        const tabNameMap = {
            'payroll': { title: '薪资明细', icon: 'attach_money' },
            'social': { title: '社保明细', icon: 'shield' },
            'housing': { title: '公积金明细', icon: 'account_balance' },
            'tax': { title: '个税明细', icon: 'assessment' }
        };
        
        const tabInfo = tabNameMap[tabName] || tabNameMap['payroll'];
        
        // 更新模态框标题
        const modalTitle = document.getElementById('payrollModalTitle');
        if (modalTitle) {
            modalTitle.textContent = `${tabInfo.title} - ${payroll.period}`;
        }
        
        // 更新标题图标
        const titleIcon = document.querySelector('#payrollModalHeader .material-icons');
        if (titleIcon) {
            titleIcon.textContent = tabInfo.icon;
        }
        
        // 隐藏批次信息区域和标签页容器
        const headerSection = document.getElementById('payrollModalHeader');
        if (headerSection) {
            headerSection.style.display = 'block'; // 保留标题区域
        }
        const infoSection = document.getElementById('payrollInfoSection');
        if (infoSection) {
            infoSection.style.display = 'none'; // 隐藏批次信息区域
        }
        const tabsContainer = document.getElementById('payrollTabsContainer');
        if (tabsContainer) {
            tabsContainer.style.display = 'none'; // 隐藏标签页容器
        }
        const description = document.getElementById('payrollModalDescription');
        if (description) {
            description.style.display = 'none'; // 隐藏描述文字
        }
        
        // 隐藏创建模式按钮，显示查看模式按钮
        const createButtons = document.getElementById('createModeButtons');
        if (createButtons) {
            createButtons.style.display = 'none';
        }
        const viewFooter = document.getElementById('viewModeFooter');
        if (viewFooter) {
            viewFooter.style.display = 'block';
        }
        
        // 显示表格容器，但隐藏所有标签页内容
        const tablesContainer = document.getElementById('payrollTablesContainer');
        if (tablesContainer) {
            tablesContainer.style.display = 'block';
        }
        
        // 隐藏所有标签页内容
        const allTabPanels = document.querySelectorAll('.tab-content-panel');
        allTabPanels.forEach(panel => {
            panel.style.display = 'none';
        });
        
        // 根据标签页名称渲染并显示对应的表格
        if (tabName === 'payroll') {
            renderPayrollItemsTable(items);
            const payrollTab = document.getElementById('payrollTab');
            if (payrollTab) {
                payrollTab.style.display = 'block';
            }
        } else if (tabName === 'social') {
            renderSocialSecurityItemsTable(items);
            const socialTab = document.getElementById('socialSecurityTab');
            if (socialTab) {
                socialTab.style.display = 'block';
            }
        } else if (tabName === 'housing') {
            renderHousingFundItemsTable(items);
            const housingTab = document.getElementById('housingFundTab');
            if (housingTab) {
                housingTab.style.display = 'block';
            }
        } else if (tabName === 'tax') {
            renderTaxItemsTable(items);
            const taxTab = document.getElementById('taxTab');
            if (taxTab) {
                taxTab.style.display = 'block';
            }
        }
        
        // 打开模态框
        if (payrollModalInstance) {
            payrollModalInstance.open();
        }
        
    } catch (error) {
        console.error('加载批次详情失败:', error);
        M.toast({ html: `加载失败：${error.message}`, classes: 'red' });
    }
}

function renderPayrollItemsTable(items) {
    if (!payrollTableBody) return;
    
    if (items.length === 0) {
        payrollTableBody.innerHTML = '<tr><td colspan="11" class="center-align grey-text">暂无数据</td></tr>';
        return;
    }
    
    payrollTableBody.innerHTML = items.map(item => `
        <tr>
            <td><strong>${item.name || '未知'}</strong></td>
            <td>${item.company_name || '-'}</td>
            <td>${item.department || '-'}</td>
            <td>${item.position || '-'}</td>
            <td>${item.employee_type || '正式员工'}</td>
            <td>¥${formatMoney(item.basic_salary || 0)}</td>
            <td>¥${formatMoney(item.performance_base || 0)}</td>
            <td>${item.performance_grade || 'C'}</td>
            <td>¥${formatMoney(item.performance_pay || 0)}</td>
            <td>¥${formatMoney(item.adjustment || 0)}</td>
            <td>¥${formatMoney(item.gross_pay || 0)}</td>
        </tr>
    `).join('');
}

function renderSocialSecurityItemsTable(items) {
    if (!socialSecurityTableBody) return;
    
    if (items.length === 0) {
        socialSecurityTableBody.innerHTML = '<tr><td colspan="11" class="center-align grey-text">暂无数据</td></tr>';
        return;
    }
    
    // 计算各项社保（这里使用基本工资作为基数，实际应该根据业务规则计算）
    socialSecurityTableBody.innerHTML = items.map(item => {
        const base = item.basic_salary || 0;
        const pension = item.social_security_employee || 0; // 养老（个人部分）
        const injury = 0; // 工伤（单位部分）
        const medical = 0; // 医疗（个人+单位）
        const unemployment = 0; // 失业（个人+单位）
        const maternity = 0; // 生育（单位部分）
        
        return `
        <tr>
            <td>${item.name || '未知'}</td>
            <td>${item.company_name || '-'}</td>
            <td>${item.department || '-'}</td>
            <td>${item.position || '-'}</td>
            <td>${item.employee_type || '正式员工'}</td>
            <td>¥${formatMoney(base)}</td>
            <td>¥${formatMoney(pension)}</td>
            <td>¥${formatMoney(injury)}</td>
            <td>¥${formatMoney(medical)}</td>
            <td>¥${formatMoney(unemployment)}</td>
            <td>¥${formatMoney(maternity)}</td>
        </tr>
    `;
    }).join('');
}

function renderHousingFundItemsTable(items) {
    if (!housingFundTableBody) return;
    
    if (items.length === 0) {
        housingFundTableBody.innerHTML = '<tr><td colspan="8" class="center-align grey-text">暂无数据</td></tr>';
        return;
    }
    
    housingFundTableBody.innerHTML = items.map(item => `
        <tr>
            <td>${item.name || '未知'}</td>
            <td>${item.company_name || '-'}</td>
            <td>${item.department || '-'}</td>
            <td>${item.position || '-'}</td>
            <td>${item.employee_type || '正式员工'}</td>
            <td>¥${formatMoney(item.basic_salary || 0)}</td>
            <td>¥${formatMoney(item.housing_fund_employer || 0)}</td>
            <td>¥${formatMoney(item.housing_fund_employee || 0)}</td>
        </tr>
    `).join('');
}

function renderTaxItemsTable(items) {
    const taxTab = document.getElementById('taxTab');
    if (!taxTab) return;
    
    if (items.length === 0) {
        taxTab.innerHTML = '<div class="card-panel grey lighten-4 center-align" style="color: #757575;"><i class="material-icons large grey-text text-lighten-1">assessment</i><p>暂无个税数据</p></div>';
        return;
    }
    
    // TODO: 实现个税表格渲染
    taxTab.innerHTML = '<div class="card-panel grey lighten-4 center-align" style="color: #757575;"><i class="material-icons large grey-text text-lighten-1">assessment</i><p>个税申报功能待实现</p></div>';
}

async function savePayrollRecord() {
    const periodValue = payrollPeriodInput && payrollPeriodInput.value ? payrollPeriodInput.value : new Date().toISOString().slice(0, 7);
    const issueDateValue = issueDateInput && issueDateInput.value ? issueDateInput.value : null;
    const noteValue = payrollNoteInput && payrollNoteInput.value ? payrollNoteInput.value : null;
    
    // 如果是创建模式且没有加载数据，先加载当前有效员工的薪资数据
    if (!isViewMode && payrollRows.length === 0) {
        try {
            updateStatus('正在加载员工薪资数据...');
            const response = await fetch('/api/salary/current');
            const result = await response.json();
            if (result.success) {
                payrollRows = (result.data || []).map((item) => calculateRow({
                    employee_id: item.employee_id,
                    person_id: item.person_id,
                    name: item.name || '未知',
                    company_name: item.company_name,
                    department: item.department,
                    position: item.position,
                    employee_type: item.employee_type || '正式员工',
                    basic_salary: toNumber(item.basic_salary),
                    performance_base: toNumber(item.performance_salary),
                    grade: 'C',
                    performance_pay: 0,
                    adjustment: 0,
                    total_pay: 0
                }));
            } else {
                throw new Error(result.error || '加载失败');
            }
        } catch (error) {
            console.error('加载薪资数据失败:', error);
            M.toast({ html: `加载薪资数据失败：${error.message}`, classes: 'red' });
            return;
        }
    }
    
    if (!payrollRows.length) {
        M.toast({ html: '没有可保存的薪资记录', classes: 'red' });
        return;
    }
    
    const payload = {
        period: periodValue,
        issue_date: issueDateValue,
        note: noteValue,
        items: payrollRows.map(row => ({
            employee_id: row.employee_id,
            basic_salary: row.basic_salary,
            performance_base: row.performance_base,
            grade: row.grade,
            performance_pay: row.performance_pay,
            adjustment: row.adjustment,
            total_pay: row.total_pay
        }))
    };
    
    try {
        updateStatus('正在保存批次...');
        const response = await fetch('/api/payroll', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await response.json();
        if (result.success) {
            M.toast({ html: '薪资批次保存成功', classes: 'green' });
            updateStatus(`批次 ${periodValue} 保存成功 (ID: ${result.id})`);
            if (payrollModalInstance) {
                payrollModalInstance.close();
            }
            // 刷新批次列表
            loadPayrollRecords();
        } else {
            throw new Error(result.error || '保存失败');
        }
    } catch (error) {
        console.error(error);
        M.toast({ html: `保存失败：${error.message}`, classes: 'red' });
        updateStatus('保存失败');
    }
}

