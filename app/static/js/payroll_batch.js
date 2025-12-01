document.addEventListener('DOMContentLoaded', function () {
    const previewBtn = document.getElementById('previewPayrollBatchBtn');
    if (previewBtn) {
        previewBtn.addEventListener('click', previewPayrollBatch);
    }
    initDefaultBatchPeriod();
    loadPayrollBatchHistory();
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

    const rows = items.map((item, index) => {
        const readOnlyAttr = editable ? '' : 'readonly';
        return `
            <tr data-item-id="${item.id}">
                <td>${index + 1}</td>
                <td>${item.person_id}</td>
                <td>${item.salary_base_amount ?? '-'}</td>
                <td>${item.salary_performance_base ?? '-'}</td>
                <td>${item.performance_factor ?? '-'}</td>
                <td>${item.performance_amount ?? '-'}</td>
                <td>${item.gross_amount_before_deductions ?? '-'}</td>
                <td>${item.attendance_deduction ?? 0}</td>
                <td>${item.social_personal_amount ?? 0}</td>
                <td>${item.housing_personal_amount ?? 0}</td>
                <td>
                    <input type="number" step="0.01" class="other-deduction browser-default"
                           value="${item.other_deduction ?? 0}" ${readOnlyAttr}>
                </td>
                <td>${item.net_amount_before_tax ?? '-'}</td>
            </tr>
        `;
    }).join('');

    tableContainer.innerHTML = `
        <table class="striped responsive-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th>人员ID</th>
                    <th>基数部分</th>
                    <th>绩效基数</th>
                    <th>绩效系数</th>
                    <th>绩效金额</th>
                    <th>扣前应发</th>
                    <th>考勤扣款</th>
                    <th>个人社保</th>
                    <th>个人公积金</th>
                    <th>其他补扣</th>
                    <th>应发（税前）</th>
                </tr>
            </thead>
            <tbody>${rows}</tbody>
        </table>
    `;

    const confirmBtn = document.getElementById('confirmPayrollBatchBtn');
    confirmBtn.dataset.batchId = data.batch_id;
    confirmBtn.onclick = editable ? confirmPayrollCurrentPreview : () => M.Modal.getInstance(modalElem).close();

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

async function confirmPayrollCurrentPreview() {
    const btn = document.getElementById('confirmPayrollBatchBtn');
    const batchId = Number(btn.dataset.batchId);
    const tableContainer = document.getElementById('payrollBatchPreviewTableContainer');
    const rows = tableContainer.querySelectorAll('tbody tr');
    const items = Array.from(rows).map((row) => {
        const id = Number(row.dataset.itemId);
        const otherDeduction = Number(row.querySelector('.other-deduction').value || 0);
        return {
            id,
            other_deduction: otherDeduction,
        };
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


