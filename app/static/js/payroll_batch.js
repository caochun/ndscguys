document.addEventListener('DOMContentLoaded', function () {
    const previewBtn = document.getElementById('previewPayrollBatchBtn');
    if (previewBtn) {
        previewBtn.addEventListener('click', previewPayrollBatch);
    }
    const previewInternBtn = document.getElementById('previewPayrollBatchInternBtn');
    if (previewInternBtn) {
        previewInternBtn.addEventListener('click', previewPayrollBatchIntern);
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
        
        // 如果用户没有指定 target_employee_type，则排除实习生
        if (!payload.target_employee_type) {
            // 过滤掉实习生
            const filteredData = {
                ...result.data,
                items: (result.data.items || []).filter(item => item.employee_type !== '实习生'),
            };
            // 更新受影响人数
            filteredData.affected_count = filteredData.items.length;
            filteredData.total_persons = filteredData.items.length;
            openPayrollPreviewModal(filteredData, true, '员工薪酬批量发放预览');
        } else {
            openPayrollPreviewModal(result.data, true, '员工薪酬批量发放预览');
        }
    } catch (err) {
        M.toast({html: '预览失败：' + err.message, classes: 'red'});
    } finally {
        btn.disabled = false;
        btn.classList.remove('disabled');
    }
}

async function previewPayrollBatchIntern() {
    const form = document.getElementById('payrollBatchForm');
    const formData = new FormData(form);
    const payload = {
        batch_period: formData.get('batch_period'),
        effective_date: formData.get('effective_date') || null,
        target_company: formData.get('target_company') || null,
        target_department: formData.get('target_department') || null,
        target_employee_type: '实习生',  // 强制设置为实习生
        note: formData.get('note') || null,
    };

    if (!payload.batch_period) {
        M.toast({html: '请填写批次（例如 2025-11）', classes: 'red'});
        return;
    }

    const btn = document.getElementById('previewPayrollBatchInternBtn');
    btn.disabled = true;
    btn.classList.add('disabled');
    try {
        const result = await fetchJSON('/api/payroll/batch-preview', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
        openPayrollPreviewModal(result.data, true, '实习生薪酬批量发放预览');
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

// 保存预览时的临时数据
let previewBatchData = null;

function openPayrollPreviewModal(data, editable, customTitle = null) {
    const modalElem = document.getElementById('payrollBatchPreviewModal');
    const titleElem = document.getElementById('payrollBatchPreviewTitle');
    const summaryElem = document.getElementById('payrollBatchPreviewSummary');
    const tableContainer = document.getElementById('payrollBatchPreviewTableContainer');
    if (!modalElem || !tableContainer) return;

    const items = data.items || [];
    const total = data.total_persons || 0;
    const affected = data.affected_count || items.length;
    summaryElem.textContent = `本次批次共扫描 ${total} 人，其中 ${affected} 人生成薪酬发放明细。`;
    if (customTitle) {
        titleElem.textContent = customTitle;
    } else {
        titleElem.textContent = editable ? '薪酬批量发放预览' : `批次 #${data.batch_id} 详情`;
    }
    
    // 如果是预览模式（可编辑），保存临时数据
    if (editable) {
        previewBatchData = {
            batch_period: data.batch_period,
            effective_date: data.effective_date,
            target_company: data.target_company,
            target_department: data.target_department,
            target_employee_type: data.target_employee_type,
            note: data.note,
            items: items,
        };
    }

    const formatNumber = (val) => {
        if (val === null || val === undefined || val === '-') return '-';
        return typeof val === 'number' ? val.toFixed(2) : val;
    };

    const rows = items.map((item, index) => {
        const readOnlyAttr = editable ? '' : 'readonly';
        const isDailySalary = item.salary_type === '日薪制';
        // 预览模式使用索引作为临时ID，详情模式使用数据库ID
        const itemId = editable ? index : (item.id || index);
        
        // 计算基数部分的 tooltip 文本
        let baseAmountTooltip = '';
        if (!isDailySalary && item.adjusted_salary_amount !== null && item.adjusted_salary_amount !== undefined 
            && item.base_ratio !== null && item.base_ratio !== undefined) {
            const adjustedSalary = Number(item.adjusted_salary_amount);
            const baseRatio = Number(item.base_ratio);
            const calculatedBase = adjustedSalary * baseRatio;
            baseAmountTooltip = `调整后薪资 ${adjustedSalary.toFixed(2)} × 基数比例 ${baseRatio.toFixed(1)} = ${calculatedBase.toFixed(2)}`;
        }
        
        // 计算绩效基数的 tooltip 文本
        let performanceBaseTooltip = '';
        if (!isDailySalary && item.adjusted_salary_amount !== null && item.adjusted_salary_amount !== undefined 
            && item.perf_ratio !== null && item.perf_ratio !== undefined) {
            const adjustedSalary = Number(item.adjusted_salary_amount);
            const perfRatio = Number(item.perf_ratio);
            const calculatedPerfBase = adjustedSalary * perfRatio;
            performanceBaseTooltip = `调整后薪资 ${adjustedSalary.toFixed(2)} × 绩效比例 ${perfRatio.toFixed(1)} = ${calculatedPerfBase.toFixed(2)}`;
        }
        
        // 计算绩效金额的 tooltip 文本
        let performanceAmountTooltip = '';
        if (!isDailySalary && item.salary_performance_base !== null && item.salary_performance_base !== undefined 
            && item.performance_factor !== null && item.performance_factor !== undefined) {
            const perfBase = Number(item.salary_performance_base);
            const perfFactor = Number(item.performance_factor);
            const calculatedPerfAmount = perfBase * perfFactor;
            performanceAmountTooltip = `绩效基数 ${perfBase.toFixed(2)} × 考核系数 ${perfFactor.toFixed(2)} = ${calculatedPerfAmount.toFixed(2)}`;
        }
        
        // 计算扣前应发的 tooltip 文本
        let grossAmountTooltip = '';
        if (!isDailySalary && item.salary_base_amount !== null && item.salary_base_amount !== undefined 
            && item.performance_amount !== null && item.performance_amount !== undefined) {
            const baseAmount = Number(item.salary_base_amount);
            const perfAmount = Number(item.performance_amount);
            const calculatedGross = baseAmount + perfAmount;
            grossAmountTooltip = `基数部分 ${baseAmount.toFixed(2)} + 绩效金额 ${perfAmount.toFixed(2)} = ${calculatedGross.toFixed(2)}`;
        }
        
        // 计算个人社保的 tooltip 文本
        let socialPersonalTooltip = '';
        if (item.social_base_amount !== null && item.social_base_amount !== undefined 
            && item.social_personal_amount !== null && item.social_personal_amount !== undefined) {
            const socialBase = Number(item.social_base_amount);
            const socialPersonal = Number(item.social_personal_amount);
            if (socialBase > 0) {
                const socialRate = (socialPersonal / socialBase * 100).toFixed(2);
                socialPersonalTooltip = `社保基数 ${socialBase.toFixed(2)} × 个人费率 ${socialRate}% = ${socialPersonal.toFixed(2)}`;
            } else if (socialPersonal > 0) {
                socialPersonalTooltip = `个人社保金额：${socialPersonal.toFixed(2)}`;
            }
        }
        
        // 计算个人公积金的 tooltip 文本
        let housingPersonalTooltip = '';
        if (item.housing_base_amount !== null && item.housing_base_amount !== undefined 
            && item.housing_personal_amount !== null && item.housing_personal_amount !== undefined) {
            const housingBase = Number(item.housing_base_amount);
            const housingPersonal = Number(item.housing_personal_amount);
            if (housingBase > 0) {
                const housingRate = (housingPersonal / housingBase * 100).toFixed(2);
                housingPersonalTooltip = `公积金基数 ${housingBase.toFixed(2)} × 个人费率 ${housingRate}% = ${housingPersonal.toFixed(2)}`;
            } else if (housingPersonal > 0) {
                housingPersonalTooltip = `个人公积金金额：${housingPersonal.toFixed(2)}`;
            }
        }
        
        return `
            <tr data-item-id="${itemId}" data-person-id="${item.person_id || ''}">
                <td>${index + 1}</td>
                <td>${item.person_name || `ID:${item.person_id}`}</td>
                <td>${item.employee_type || '-'}</td>
                <td>${item.salary_type || '-'}</td>
                <td>${formatNumber(item.original_salary_amount)}</td>
                <td>${isDailySalary ? '-' : formatNumber(item.adjusted_salary_amount)}</td>
                <td>
                    ${isDailySalary ? '-' : (editable ? `
                        <select class="assessment-grade-select browser-default" data-item-id="${itemId}" style="width:45px; font-size:10px; padding:2px 2px;">
                            <option value="">-</option>
                            ${Object.keys(performanceFactors).map(grade => 
                                `<option value="${grade}" ${item.assessment_grade === grade ? 'selected' : ''}>${grade}(${performanceFactors[grade]})</option>`
                            ).join('')}
                        </select>
                    ` : `${item.assessment_grade || '-'}(${formatNumber(item.performance_factor)})`)}
                </td>
                <td>${(item.actual_days !== undefined && item.actual_days !== null) ? Number(item.actual_days).toFixed(1) : '-'}/${(item.absent_days !== undefined && item.absent_days !== null) ? Number(item.absent_days).toFixed(1) : (isDailySalary ? '0.0' : '-')}</td>
                <td>${formatNumber(item.attendance_deduction)}</td>
                <td ${baseAmountTooltip ? `class="tooltipped" data-tooltip="${baseAmountTooltip}"` : ''} style="cursor: ${baseAmountTooltip ? 'help' : 'default'};">${formatNumber(item.salary_base_amount)}</td>
                <td ${performanceBaseTooltip ? `class="tooltipped" data-tooltip="${performanceBaseTooltip}"` : ''} style="cursor: ${performanceBaseTooltip ? 'help' : 'default'};">${formatNumber(item.salary_performance_base)}</td>
                <td ${performanceAmountTooltip ? `class="tooltipped performance-amount-tooltip" data-tooltip="${performanceAmountTooltip}" data-item-id="${itemId}"` : ''} style="cursor: ${performanceAmountTooltip ? 'help' : 'default'};">${formatNumber(item.performance_amount)}</td>
                <td ${grossAmountTooltip ? `class="tooltipped gross-amount-tooltip" data-tooltip="${grossAmountTooltip}" data-item-id="${itemId}"` : ''} style="cursor: ${grossAmountTooltip ? 'help' : 'default'};">${formatNumber(item.gross_amount_before_deductions)}</td>
                <td ${socialPersonalTooltip ? `class="tooltipped" data-tooltip="${socialPersonalTooltip}"` : ''} style="cursor: ${socialPersonalTooltip ? 'help' : 'default'};">${formatNumber(item.social_personal_amount)}</td>
                <td ${housingPersonalTooltip ? `class="tooltipped" data-tooltip="${housingPersonalTooltip}"` : ''} style="cursor: ${housingPersonalTooltip ? 'help' : 'default'};">${formatNumber(item.housing_personal_amount)}</td>
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
                    <th colspan="6">基础信息</th>
                    <th colspan="2">考勤信息</th>
                    <th colspan="4">薪资构成</th>
                    <th colspan="3">扣款项</th>
                    <th rowspan="2">应发（税前）</th>
                </tr>
                <tr class="header-detail-row">
                    <th>姓名</th>
                    <th>员工类别</th>
                    <th>薪资类型</th>
                    <th>原始薪资</th>
                    <th>调整后薪资</th>
                    <th>考核</th>
                    <th>出勤/缺勤</th>
                    <th>考勤扣款</th>
                    <th>基数部分</th>
                    <th>绩效基数</th>
                    <th>绩效金额</th>
                    <th>扣前应发</th>
                    <th>个人社保</th>
                    <th>个人公积金</th>
                    <th>其他补扣</th>
                </tr>
            </thead>
            <tbody>${rows}</tbody>
        </table>
    `;

    const confirmBtn = document.getElementById('confirmPayrollBatchBtn');
    // 预览模式不需要batch_id，详情模式需要
    if (data.batch_id) {
        confirmBtn.dataset.batchId = data.batch_id;
    } else {
        confirmBtn.removeAttribute('data-batch-id');
    }
    confirmBtn.onclick = editable ? confirmPayrollCurrentPreview : () => M.Modal.getInstance(modalElem).close();

    // 如果是可编辑模式，绑定考核等级下拉列表的change事件
    if (editable) {
        tableContainer.querySelectorAll('.assessment-grade-select').forEach(select => {
            select.addEventListener('change', function() {
                updateAssessmentGrade(this);
            });
        });
    }

    // 初始化 tooltip（用于显示基数部分的计算公式）
    tableContainer.querySelectorAll('.tooltipped').forEach(elem => {
        M.Tooltip.init(elem, {
            position: 'top',
            html: false
        });
    });

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
    
    // 获取当前行的所有单元格
    const cells = row.querySelectorAll('td');
    
    // 列索引（从0开始，td[0]是序号）：
    // td[0]: #, td[1]: 姓名, td[2]: 员工类别, td[3]: 薪资类型, td[4]: 原始薪资, td[5]: 调整后薪资
    // td[6]: 考核, td[7]: 出勤/缺勤, td[8]: 考勤扣款
    // td[9]: 基数部分, td[10]: 绩效基数, td[11]: 绩效金额, td[12]: 扣前应发
    // td[13]: 个人社保, td[14]: 个人公积金, td[15]: 其他补扣, td[16]: 应发（税前）
    const salaryBaseAmount = parseFloat(cells[9].textContent) || 0;  // 基数部分
    const salaryPerformanceBase = parseFloat(cells[10].textContent) || 0;  // 绩效基数
    
    // 调试：记录绩效基数的原始值，确保不会被修改
    const originalPerformanceBase = salaryPerformanceBase;
    console.log('考核等级选择 - 原始绩效基数:', originalPerformanceBase, '绩效系数:', performanceFactor);
    
    if (salaryPerformanceBase > 0) {
        const newPerformanceAmount = salaryPerformanceBase * performanceFactor;
        const grossAmount = salaryBaseAmount + newPerformanceAmount;
        
        // 更新表格中的绩效金额和扣前应发
        cells[11].textContent = newPerformanceAmount.toFixed(2);  // 绩效金额
        cells[12].textContent = grossAmount.toFixed(2);  // 扣前应发
        
        // 更新绩效金额的 tooltip
        const performanceAmountCell = cells[11];
        if (performanceAmountCell.classList.contains('performance-amount-tooltip')) {
            // 销毁旧的 tooltip 实例
            const tooltipInstance = M.Tooltip.getInstance(performanceAmountCell);
            if (tooltipInstance) {
                tooltipInstance.destroy();
            }
            // 更新 tooltip 文本
            const newTooltipText = `绩效基数 ${originalPerformanceBase.toFixed(2)} × 考核系数 ${performanceFactor.toFixed(2)} = ${newPerformanceAmount.toFixed(2)}`;
            performanceAmountCell.setAttribute('data-tooltip', newTooltipText);
            // 重新初始化 tooltip
            M.Tooltip.init(performanceAmountCell, {
                position: 'top',
                html: false
            });
        }
        
        // 更新扣前应发的 tooltip
        const grossAmountCell = cells[12];
        if (grossAmountCell.classList.contains('gross-amount-tooltip')) {
            // 销毁旧的 tooltip 实例
            const tooltipInstance = M.Tooltip.getInstance(grossAmountCell);
            if (tooltipInstance) {
                tooltipInstance.destroy();
            }
            // 更新 tooltip 文本
            const newGrossTooltipText = `基数部分 ${salaryBaseAmount.toFixed(2)} + 绩效金额 ${newPerformanceAmount.toFixed(2)} = ${grossAmount.toFixed(2)}`;
            grossAmountCell.setAttribute('data-tooltip', newGrossTooltipText);
            // 重新初始化 tooltip
            M.Tooltip.init(grossAmountCell, {
                position: 'top',
                html: false
            });
        }
        
        // 重新计算应发（税前）
        const attendanceDeduction = parseFloat(cells[8].textContent) || 0;  // 考勤扣款
        const socialPersonal = parseFloat(cells[13].textContent) || 0;  // 个人社保
        const housingPersonal = parseFloat(cells[14].textContent) || 0;  // 个人公积金
        const otherDeductionInput = row.querySelector('.other-deduction');
        const otherDeduction = parseFloat(otherDeductionInput ? otherDeductionInput.value : 0) || 0;
        
        const netAmount = grossAmount - attendanceDeduction - socialPersonal - housingPersonal - otherDeduction;
        cells[16].textContent = netAmount.toFixed(2);  // 应发（税前）
        
        // 调试：验证绩效基数是否被意外修改
        const afterPerformanceBase = parseFloat(cells[10].textContent) || 0;
        if (Math.abs(afterPerformanceBase - originalPerformanceBase) > 0.01) {
            console.warn('警告：绩效基数被意外修改！原始值:', originalPerformanceBase, '修改后:', afterPerformanceBase);
            // 如果被修改了，恢复原始值
            cells[10].textContent = originalPerformanceBase.toFixed(2);
        }
    }
}

async function confirmPayrollCurrentPreview() {
    const btn = document.getElementById('confirmPayrollBatchBtn');
    const tableContainer = document.getElementById('payrollBatchPreviewTableContainer');
    const rows = tableContainer.querySelectorAll('tbody tr');
    
    if (!previewBatchData) {
        M.toast({html: '预览数据丢失，请重新预览', classes: 'red'});
        return;
    }
    
    // 构建items数据，包含原始计算数据和用户修改的数据
    const items = Array.from(rows).map((row, index) => {
        const personId = Number(row.dataset.personId);
        const otherDeduction = Number(row.querySelector('.other-deduction').value || 0);
        const assessmentSelect = row.querySelector('.assessment-grade-select');
        const assessmentGrade = assessmentSelect ? assessmentSelect.value : null;
        const performanceFactor = assessmentGrade && performanceFactors[assessmentGrade] ? performanceFactors[assessmentGrade] : null;
        
        // 获取原始item数据
        const originalItem = previewBatchData.items[index];
        if (!originalItem) {
            return null;
        }
        
        // 构建item数据，包含所有原始计算字段
        const item = {
            person_id: personId,
            salary_base_amount: originalItem.salary_base_amount || 0,
            salary_performance_base: originalItem.salary_performance_base || 0,
            performance_factor: originalItem.performance_factor || 0,
            performance_amount: originalItem.performance_amount || 0,
            gross_amount_before_deductions: originalItem.gross_amount_before_deductions || 0,
            attendance_deduction: originalItem.attendance_deduction || 0,
            social_personal_amount: originalItem.social_personal_amount || 0,
            housing_personal_amount: originalItem.housing_personal_amount || 0,
            other_deduction: otherDeduction,
            net_amount_before_tax: originalItem.net_amount_before_tax || 0,
        };
        
        // 如果修改了考核等级，需要重新计算绩效相关字段
        if (assessmentGrade && performanceFactor !== null) {
            const salaryPerformanceBase = originalItem.salary_performance_base || 0;
            const salaryBaseAmount = originalItem.salary_base_amount || 0;
            const newPerformanceAmount = salaryPerformanceBase * performanceFactor;
            const grossAmount = salaryBaseAmount + newPerformanceAmount;
            const netAmount = grossAmount - (originalItem.attendance_deduction || 0) 
                            - (originalItem.social_personal_amount || 0) 
                            - (originalItem.housing_personal_amount || 0) 
                            - otherDeduction;
            
            item.assessment_grade = assessmentGrade;
            item.performance_factor = performanceFactor;
            item.performance_amount = newPerformanceAmount;
            item.gross_amount_before_deductions = grossAmount;
            item.net_amount_before_tax = netAmount;
        } else {
            // 只修改了other_deduction，重新计算应发金额
            const grossAmount = originalItem.gross_amount_before_deductions || 0;
            const netAmount = grossAmount - (originalItem.attendance_deduction || 0) 
                            - (originalItem.social_personal_amount || 0) 
                            - (originalItem.housing_personal_amount || 0) 
                            - otherDeduction;
            item.net_amount_before_tax = netAmount;
        }
        
        return item;
    }).filter(item => item !== null);
    
    btn.disabled = true;
    try {
        // 发送批次参数和items数据
        const payload = {
            batch_period: previewBatchData.batch_period,
            effective_date: previewBatchData.effective_date,
            target_company: previewBatchData.target_company,
            target_department: previewBatchData.target_department,
            target_employee_type: previewBatchData.target_employee_type,
            note: previewBatchData.note,
            items: items,
        };
        
        const result = await fetchJSON('/api/payroll/batch-confirm', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
        
        M.toast({html: `批次已确认，共 ${result.data.affected_count} 人`, classes: 'green'});
        const modalElem = document.getElementById('payrollBatchPreviewModal');
        const modal = M.Modal.getInstance(modalElem);
        modal.close();
        previewBatchData = null; // 清空临时数据
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


