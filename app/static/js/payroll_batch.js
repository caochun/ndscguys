document.addEventListener('DOMContentLoaded', function () {
    const previewBtn = document.getElementById('previewPayrollBatchBtn');
    if (previewBtn) {
        previewBtn.addEventListener('click', previewPayrollBatch);
    }
    initDefaultBatchPeriod();
    loadPayrollBatchHistory();
    loadPerformanceFactors(); // 加载绩效系数配置
});

function initDefaultBatchPeriod() {
    const input = document.getElementById('batch_period');
    if (input && !input.value) {
        const today = new Date();
        const yyyy = today.getFullYear();
        const mm = String(today.getMonth() + 1).padStart(2, '0');
        input.value = `${yyyy}-${mm}`;
        M.updateTextFields();
    }
}

async function fetchJSON(url, options = {}) {
    const resp = await fetch(url, {
        headers: {'Content-Type': 'application/json'},
        ...options,
    });
    const data = await resp.json();
    if (!resp.ok) {
        throw new Error(data.error || '请求失败');
    }
    return data;
}

async function previewPayrollBatch() {
    const form = document.getElementById('payrollBatchForm');
    const formData = new FormData(form);
    const payload = {
        batch_period: formData.get('batch_period'),
        effective_date: formData.get('effective_date') || null,
        target_company: formData.get('target_company') || null,
        target_department: formData.get('target_department') || null,
        target_employee_type: formData.get('target_employee_type') || null,
        note: formData.get('note') || null,
    };

    if (!payload.batch_period) {
        M.toast({html: '请填写批次（例如 2025-11）', classes: 'red'});
        return;
    }

    const btn = document.getElementById('previewPayrollBatchBtn');
    btn.disabled = true;
    btn.classList.add('disabled');
    try {
        const result = await fetchJSON('/api/payroll/batch-preview', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
        openPayrollPreviewModal(result.data, true);
    } catch (err) {
        M.toast({html: '预览失败：' + err.message, classes: 'red'});
    } finally {
        btn.disabled = false;
        btn.classList.remove('disabled');
    }
}

async function loadPayrollBatchHistory() {
    const container = document.getElementById('payrollBatchHistoryContainer');
    if (!container) return;
    try {
        const result = await fetchJSON('/api/payroll/batches');
        const batches = result.data || [];
        if (!batches.length) {
            container.innerHTML = '<p class="grey-text">暂无薪酬批次记录</p>';
            return;
        }
        const rows = batches.map((b) => {
            const canExecute = b.status !== 'applied' && b.affected_count > 0;
            const executeBtn = canExecute
                ? `<button class="btn-small waves-effect waves-light" data-batch-id="${b.id}" data-action="execute">
                       执行发放
                   </button>`
                : `<button class="btn-small disabled" disabled>已执行</button>`;
            return `
                <tr>
                    <td>${b.id}</td>
                    <td>${b.created_at}</td>
                    <td>${b.batch_period}</td>
                    <td>${b.effective_date || '-'}</td>
                    <td>${b.target_company || '-'}</td>
                    <td>${b.target_department || '-'}</td>
                    <td>${b.target_employee_type || '-'}</td>
                    <td>${b.status}</td>
                    <td>${b.affected_count}</td>
                    <td>
                        <button class="btn-flat blue-text" data-batch-id="${b.id}" data-action="detail">详情</button>
                        ${executeBtn}
                    </td>
                </tr>
            `;
        }).join('');
        container.innerHTML = `
            <table class="striped responsive-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>创建时间</th>
                        <th>批次</th>
                        <th>生效日期</th>
                        <th>公司</th>
                        <th>部门</th>
                        <th>员工类别</th>
                        <th>状态</th>
                        <th>人数</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        `;
        container.querySelectorAll('button[data-action="detail"]').forEach((btn) => {
            btn.addEventListener('click', () => openPayrollBatchDetail(Number(btn.dataset.batchId)));
        });
        container.querySelectorAll('button[data-action="execute"]').forEach((btn) => {
            if (!btn.disabled) {
                btn.addEventListener('click', () => executePayrollBatch(Number(btn.dataset.batchId)));
            }
        });
    } catch (err) {
        container.innerHTML = `<p class="red-text">加载失败：${err.message}</p>`;
    }
}

async function executePayrollBatch(batchId) {
    try {
        const result = await fetchJSON(`/api/payroll/batch-execute/${batchId}`, {
            method: 'POST',
        });
        M.toast({html: `批次 #${batchId} 执行完成，影响 ${result.data.affected_count} 人`, classes: 'green'});
        loadPayrollBatchHistory();
    } catch (err) {
        M.toast({html: '执行失败：' + err.message, classes: 'red'});
    }
}

async function loadPerformanceFactors() {
    try {
        const result = await fetchJSON('/api/payroll/config/performance-factors');
        if (result.success) {
            performanceFactors = result.data;
        }
    } catch (err) {
        console.error('Failed to load performance factors:', err);
        // 使用默认值
        performanceFactors = { A: 1.2, B: 1.0, C: 0.8, D: 0.5, E: 0.0 };
    }
}

function openPayrollPreviewModal(data, editable) {
    const modalElem = document.getElementById('payrollBatchPreviewModal');
    const titleElem = document.getElementById('payrollBatchPreviewTitle');
    const summaryElem = document.getElementById('payrollBatchPreviewSummary');
    const tableContainer = document.getElementById('payrollBatchPreviewTableContainer');
    if (!modalElem || !tableContainer) return;

    const items = data.items || [];
    const total = data.total_persons || 0;
    const affected = data.affected_count || items.length;
    summaryElem.textContent = `本次批次共扫描 ${total} 人，其中 ${affected} 人生成薪酬发放明细。`;
    titleElem.textContent = editable ? '薪酬批量发放预览' : `批次 #${data.batch_id} 详情`;

    const formatNumber = (val) => {
        if (val === null || val === undefined || val === '-') return '-';
        return typeof val === 'number' ? val.toFixed(2) : val;
    };

    const rows = items.map((item, index) => {
        const readOnlyAttr = editable ? '' : 'readonly';
        const isDailySalary = item.salary_type === '日薪制度';
        return `
            <tr data-item-id="${item.id}">
                <td>${index + 1}</td>
                <td>${item.person_name || `ID:${item.person_id}`}</td>
                <td>${item.salary_type || '-'}</td>
                <td>${formatNumber(item.original_salary_amount)}</td>
                <td>${isDailySalary ? '-' : formatNumber(item.adjusted_salary_amount)}</td>
                <td>${item.employee_type || '-'}</td>
                <td>${formatNumber(item.expected_days)}/${formatNumber(item.actual_days)}/${formatNumber(item.absent_days !== undefined ? item.absent_days : (isDailySalary ? 0 : '-'))}</td>
                <td>${formatNumber(item.social_base_amount)}</td>
                <td>${formatNumber(item.housing_base_amount)}</td>
                <td>${isDailySalary ? '-' : `${formatNumber(item.base_ratio)}/${formatNumber(item.perf_ratio)}`}</td>
                <td>
                    ${isDailySalary ? '-' : (editable ? `
                        <select class="assessment-grade-select browser-default" data-item-id="${item.id}" style="width:80px; font-size:12px;">
                            <option value="">-</option>
                            ${Object.keys(performanceFactors).map(grade => 
                                `<option value="${grade}" ${item.assessment_grade === grade ? 'selected' : ''}>${grade}(${performanceFactors[grade]})</option>`
                            ).join('')}
                        </select>
                    ` : `${item.assessment_grade || '-'}(${formatNumber(item.performance_factor)})`)}
                </td>
                <td>${formatNumber(item.salary_base_amount)}</td>
                <td>${formatNumber(item.salary_performance_base)}</td>
                <td>${formatNumber(item.performance_amount)}</td>
                <td>${formatNumber(item.gross_amount_before_deductions)}</td>
                <td>${formatNumber(item.attendance_deduction)}</td>
                <td>${formatNumber(item.social_personal_amount)}</td>
                <td>${formatNumber(item.housing_personal_amount)}</td>
                <td>
                    <input type="number" step="0.01" class="other-deduction browser-default"
                           value="${item.other_deduction ?? 0}" ${readOnlyAttr} style="width:80px;">
                </td>
                <td>${formatNumber(item.net_amount_before_tax)}</td>
            </tr>
        `;
    }).join('');

    tableContainer.innerHTML = `
        <table class="striped responsive-table payroll-batch-table" style="font-size: 12px;">
            <thead>
                <tr class="header-group-row">
                    <th rowspan="2">#</th>
                    <th colspan="5">基础信息</th>
                    <th colspan="1">考勤信息</th>
                    <th colspan="2">社保公积金基数</th>
                    <th colspan="2">月薪制计算参数</th>
                    <th colspan="4">薪资构成</th>
                    <th colspan="4">扣款项</th>
                    <th rowspan="2">应发（税前）</th>
                </tr>
                <tr class="header-detail-row">
                    <th>姓名</th>
                    <th>薪资类型</th>
                    <th>原始薪资</th>
                    <th>调整后薪资</th>
                    <th>员工类别</th>
                    <th>预期/实际/缺勤</th>
                    <th>社保基数</th>
                    <th>公积金基数</th>
                    <th>基数/绩效比例</th>
                    <th>考核</th>
                    <th>基数部分</th>
                    <th>绩效基数</th>
                    <th>绩效金额</th>
                    <th>扣前应发</th>
                    <th>考勤扣款</th>
                    <th>个人社保</th>
                    <th>个人公积金</th>
                    <th>其他补扣</th>
                </tr>
            </thead>
            <tbody>${rows}</tbody>
        </table>
    `;

    const confirmBtn = document.getElementById('confirmPayrollBatchBtn');
    confirmBtn.dataset.batchId = data.batch_id;
    confirmBtn.onclick = editable ? confirmPayrollCurrentPreview : () => M.Modal.getInstance(modalElem).close();

    // 如果是可编辑模式，绑定考核等级下拉列表的change事件
    if (editable) {
        tableContainer.querySelectorAll('.assessment-grade-select').forEach(select => {
            select.addEventListener('change', function() {
                updateAssessmentGrade(this);
            });
        });
    }

    const modalInstance = M.Modal.getInstance(modalElem);
    const modal = modalInstance || M.Modal.init(modalElem, {
        opacity: 0.4,
        inDuration: 200,
        outDuration: 150,
        startingTop: '5%',
        endingTop: '5%',
    });
    modal.open();
}

function updateAssessmentGrade(selectElement) {
    const itemId = Number(selectElement.dataset.itemId);
    const selectedGrade = selectElement.value;
    const row = selectElement.closest('tr');
    
    if (!selectedGrade || !performanceFactors[selectedGrade]) {
        return;
    }
    
    const performanceFactor = performanceFactors[selectedGrade];
    
    // 获取当前行的所有单元格（索引从1开始）
    const cells = row.querySelectorAll('td');
    
    // 列索引：基数部分(11), 绩效基数(12), 绩效金额(13), 扣前应发(14)
    // 考勤扣款(15), 个人社保(16), 个人公积金(17), 其他补扣(18), 应发税前(19)
    const salaryBaseAmount = parseFloat(cells[10].textContent) || 0;  // 基数部分
    const salaryPerformanceBase = parseFloat(cells[11].textContent) || 0;  // 绩效基数
    
    if (salaryPerformanceBase > 0) {
        const newPerformanceAmount = salaryPerformanceBase * performanceFactor;
        const grossAmount = salaryBaseAmount + newPerformanceAmount;
        
        // 更新表格中的绩效金额和扣前应发
        cells[12].textContent = newPerformanceAmount.toFixed(2);  // 绩效金额
        cells[13].textContent = grossAmount.toFixed(2);  // 扣前应发
        
        // 重新计算应发（税前）
        const attendanceDeduction = parseFloat(cells[14].textContent) || 0;  // 考勤扣款
        const socialPersonal = parseFloat(cells[15].textContent) || 0;  // 个人社保
        const housingPersonal = parseFloat(cells[16].textContent) || 0;  // 个人公积金
        const otherDeductionInput = row.querySelector('.other-deduction');
        const otherDeduction = parseFloat(otherDeductionInput ? otherDeductionInput.value : 0) || 0;
        
        const netAmount = grossAmount - attendanceDeduction - socialPersonal - housingPersonal - otherDeduction;
        cells[18].textContent = netAmount.toFixed(2);  // 应发（税前）
    }
}

async function confirmPayrollCurrentPreview() {
    const btn = document.getElementById('confirmPayrollBatchBtn');
    const batchId = Number(btn.dataset.batchId);
    const tableContainer = document.getElementById('payrollBatchPreviewTableContainer');
    const rows = tableContainer.querySelectorAll('tbody tr');
    const items = Array.from(rows).map((row) => {
        const id = Number(row.dataset.itemId);
        const otherDeduction = Number(row.querySelector('.other-deduction').value || 0);
        const assessmentSelect = row.querySelector('.assessment-grade-select');
        const assessmentGrade = assessmentSelect ? assessmentSelect.value : null;
        const performanceFactor = assessmentGrade && performanceFactors[assessmentGrade] ? performanceFactors[assessmentGrade] : null;
        
        const item = {
            id,
            other_deduction: otherDeduction,
        };
        
        // 如果修改了考核等级，需要重新计算并更新
        if (assessmentGrade && performanceFactor !== null) {
            item.assessment_grade = assessmentGrade;
            item.performance_factor = performanceFactor;
        }
        
        return item;
    });
    btn.disabled = true;
    try {
        // 目前只支持更新 other_deduction，后端可以按需要进一步调整
        await fetchJSON(`/api/payroll/batch-confirm/${batchId}`, {
            method: 'POST',
            body: JSON.stringify({items}),
        });
        M.toast({html: '批次已确认（目前仅保存预览结果，执行发放逻辑可后续补充）', classes: 'green'});
        const modalElem = document.getElementById('payrollBatchPreviewModal');
        const modal = M.Modal.getInstance(modalElem);
        modal.close();
        loadPayrollBatchHistory();
    } catch (err) {
        M.toast({html: '确认失败：' + err.message, classes: 'red'});
    } finally {
        btn.disabled = false;
    }
}

async function openPayrollBatchDetail(batchId) {
    try {
        const batches = await fetchJSON('/api/payroll/batches');
        const batch = (batches.data || []).find((b) => b.id === batchId);
        if (!batch) {
            M.toast({html: '未找到批次', classes: 'red'});
            return;
        }
        const items = await fetchJSON(`/api/payroll/batch-items/${batchId}`);
        openPayrollPreviewModal(
            {
                batch_id: batchId,
                affected_count: batch.affected_count,
                total_persons: batch.affected_count,
                items: items.data || [],
            },
            false
        );
    } catch (err) {
        M.toast({html: '加载批次详情失败：' + err.message, classes: 'red'});
    }
}


