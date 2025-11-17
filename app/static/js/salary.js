// 薪资页面脚本

let payrollModalInstance = null;
let payrollRows = [];
let socialSecurityRows = [];
let housingFundRows = [];
let payrollTableBody = null;
let socialSecurityTableBody = null;
let housingFundTableBody = null;
let statusTextEl = null;
let payrollPeriodInput = null;
let issueDateInput = null;
let payrollNoteInput = null;

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
    statusTextEl = document.getElementById('statusText');
    payrollPeriodInput = document.getElementById('payrollPeriod');
    issueDateInput = document.getElementById('issueDate');
    payrollNoteInput = document.getElementById('payrollNote');
    
    initMaterializeComponents();
    initEventListeners();
    setDefaultPeriod();
});

function initMaterializeComponents() {
    const modalElem = document.getElementById('payrollModal');
    if (modalElem) {
        payrollModalInstance = M.Modal.init(modalElem, {
            onOpenStart: () => {
                loadPayrollData();
                const tabs = document.getElementById('payrollTabs');
                if (tabs) {
                    const instance = M.Tabs.getInstance(tabs);
                    if (instance) instance.select('payrollTab');
                }
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
            if (payrollModalInstance) {
                payrollModalInstance.open();
                loadPayrollData();
                const tabs = document.getElementById('payrollTabs');
                if (tabs) {
                    const instance = M.Tabs.getInstance(tabs);
                    if (instance) instance.select('payrollTab');
                }
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
    
    payrollTableBody.innerHTML = '<tr><td colspan="10" class="center-align grey-text">加载中...</td></tr>';
    if (socialSecurityTableBody) {
        socialSecurityTableBody.innerHTML = '<tr><td colspan="10" class="center-align grey-text">加载中...</td></tr>';
    }
    if (housingFundTableBody) {
        housingFundTableBody.innerHTML = '<tr><td colspan="7" class="center-align grey-text">加载中...</td></tr>';
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
                base: toNumber(item.basic_salary),
                company_portion: 0,
                personal_portion: 0
            }));
            
            renderPayrollTable();
            renderSocialSecurityTable();
            renderHousingFundTable();
            updateStatus(`已加载 ${payrollRows.length} 名员工的薪资信息`);
        } else {
            payrollTableBody.innerHTML = `<tr><td colspan="10" class="center-align red-text">加载失败：${result.error}</td></tr>`;
            if (socialSecurityTableBody) {
                socialSecurityTableBody.innerHTML = `<tr><td colspan="10" class="center-align red-text">加载失败：${result.error}</td></tr>`;
            }
            if (housingFundTableBody) {
                housingFundTableBody.innerHTML = `<tr><td colspan="7" class="center-align red-text">加载失败：${result.error}</td></tr>`;
            }
            updateStatus('加载失败');
        }
    } catch (error) {
        payrollTableBody.innerHTML = `<tr><td colspan="10" class="center-align red-text">加载失败：${error.message}</td></tr>`;
        if (socialSecurityTableBody) {
            socialSecurityTableBody.innerHTML = `<tr><td colspan="10" class="center-align red-text">加载失败：${error.message}</td></tr>`;
        }
        if (housingFundTableBody) {
            housingFundTableBody.innerHTML = `<tr><td colspan="7" class="center-align red-text">加载失败：${error.message}</td></tr>`;
        }
        updateStatus('加载失败');
    }
}

function renderPayrollTable() {
    if (!payrollTableBody) return;
    
    if (payrollRows.length === 0) {
        payrollTableBody.innerHTML = '<tr><td colspan="10" class="center-align grey-text">暂无在职员工薪资数据</td></tr>';
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
        socialSecurityTableBody.innerHTML = '<tr><td colspan="10" class="center-align grey-text">暂无社保数据</td></tr>';
        return;
    }
    
    socialSecurityTableBody.innerHTML = socialSecurityRows.map(row => `
        <tr>
            <td>${row.name}</td>
            <td>${row.company_name || '-'}</td>
            <td>${row.department || '-'}</td>
            <td>${row.position || '-'}</td>
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
        housingFundTableBody.innerHTML = '<tr><td colspan="7" class="center-align grey-text">暂无公积金数据</td></tr>';
        return;
    }
    
    housingFundTableBody.innerHTML = housingFundRows.map(row => `
        <tr>
            <td>${row.name}</td>
            <td>${row.company_name || '-'}</td>
            <td>${row.department || '-'}</td>
            <td>${row.position || '-'}</td>
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

async function savePayrollRecord() {
    if (!payrollRows.length) {
        M.toast({ html: '没有可保存的薪资记录', classes: 'red' });
        return;
    }
    
    const periodValue = payrollPeriodInput && payrollPeriodInput.value ? payrollPeriodInput.value : new Date().toISOString().slice(0, 7);
    const issueDateValue = issueDateInput && issueDateInput.value ? issueDateInput.value : null;
    const noteValue = payrollNoteInput && payrollNoteInput.value ? payrollNoteInput.value : null;
    
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
        } else {
            throw new Error(result.error || '保存失败');
        }
    } catch (error) {
        console.error(error);
        M.toast({ html: `保存失败：${error.message}`, classes: 'red' });
        updateStatus('保存失败');
    }
}

