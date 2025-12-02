document.addEventListener('DOMContentLoaded', function () {
    const previewBtn = document.getElementById('previewTaxDeductionBatchBtn');
    if (previewBtn) {
        previewBtn.addEventListener('click', previewTaxDeductionBatch);
    }
    loadTaxDeductionBatchHistory();
    initDefaultDates();
});

function initDefaultDates() {
    const effInput = document.getElementById('tax_deduction_effective_date');
    if (effInput && !effInput.value) {
        const today = new Date();
        const yyyy = today.getFullYear();
        const mm = String(today.getMonth() + 1).padStart(2, '0');
        const dd = String(today.getDate()).padStart(2, '0');
        effInput.value = `${yyyy}-${mm}-${dd}`;
        M.updateTextFields();
    }
    const monthInput = document.getElementById('tax_deduction_effective_month');
    if (monthInput && !monthInput.value) {
        const today = new Date();
        const yyyy = today.getFullYear();
        const mm = String(today.getMonth() + 1).padStart(2, '0');
        monthInput.value = `${yyyy}-${mm}`;
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

async function previewTaxDeductionBatch() {
    const form = document.getElementById('taxDeductionBatchForm');
    const formData = new FormData(form);
    const payload = {
        effective_date: formData.get('effective_date'),
        effective_month: formData.get('effective_month'),
        target_company: formData.get('target_company') || null,
        target_department: formData.get('target_department') || null,
        target_employee_type: formData.get('target_employee_type') || null,
        note: formData.get('note') || null,
        default_continuing_education: formData.get('default_continuing_education') ? Number(formData.get('default_continuing_education')) : null,
        default_infant_care: formData.get('default_infant_care') ? Number(formData.get('default_infant_care')) : null,
        default_children_education: formData.get('default_children_education') ? Number(formData.get('default_children_education')) : null,
        default_housing_loan_interest: formData.get('default_housing_loan_interest') ? Number(formData.get('default_housing_loan_interest')) : null,
        default_housing_rent: formData.get('default_housing_rent') ? Number(formData.get('default_housing_rent')) : null,
        default_elderly_support: formData.get('default_elderly_support') ? Number(formData.get('default_elderly_support')) : null,
    };

    if (!payload.effective_date) {
        M.toast({html: '请填写生效日期', classes: 'red'});
        return;
    }
    if (!payload.effective_month) {
        M.toast({html: '请填写生效月份（YYYY-MM格式）', classes: 'red'});
        return;
    }

    const btn = document.getElementById('previewTaxDeductionBatchBtn');
    btn.disabled = true;
    btn.classList.add('disabled');
    try {
        const result = await fetchJSON('/api/tax-deduction/batch-preview', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
        openTaxDeductionPreviewModal(result.data, true);
    } catch (err) {
        M.toast({html: '预览失败：' + err.message, classes: 'red'});
    } finally {
        btn.disabled = false;
        btn.classList.remove('disabled');
    }
}

async function loadTaxDeductionBatchHistory() {
    const container = document.getElementById('taxDeductionBatchHistoryContainer');
    if (!container) return;
    try {
        const result = await fetchJSON('/api/tax-deduction/batches');
        const batches = result.data || [];
        if (!batches.length) {
            container.innerHTML = '<p class="grey-text">暂无批量调整记录</p>';
            return;
        }
        const rows = batches.map((b) => {
            const canExecute = b.status !== 'applied' && b.affected_count > 0;
            const executeBtn = canExecute
                ? `<button class="btn-small waves-effect waves-light" data-batch-id="${b.id}" data-action="execute">
                       执行调整
                   </button>`
                : `<button class="btn-small disabled" disabled>已执行</button>`;
            return `
                <tr>
                    <td>${b.id}</td>
                    <td>${b.created_at}</td>
                    <td>${b.effective_date}</td>
                    <td>${b.effective_month}</td>
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
                        <th>生效日期</th>
                        <th>生效月份</th>
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
            btn.addEventListener('click', () => openTaxDeductionBatchDetail(Number(btn.dataset.batchId)));
        });
        container.querySelectorAll('button[data-action="execute"]').forEach((btn) => {
            if (!btn.disabled) {
                btn.addEventListener('click', () => executeTaxDeductionBatch(Number(btn.dataset.batchId)));
            }
        });
    } catch (err) {
        container.innerHTML = `<p class="red-text">加载失败：${err.message}</p>`;
    }
}

async function executeTaxDeductionBatch(batchId) {
    try {
        const result = await fetchJSON(`/api/tax-deduction/batch-execute/${batchId}`, {
            method: 'POST',
        });
        M.toast({html: `批次 #${batchId} 执行完成，影响 ${result.data.affected_count} 人`, classes: 'green'});
        loadTaxDeductionBatchHistory();
    } catch (err) {
        M.toast({html: '执行失败：' + err.message, classes: 'red'});
    }
}

function openTaxDeductionPreviewModal(data, editable) {
    const modalElem = document.getElementById('taxDeductionBatchPreviewModal');
    const titleElem = document.getElementById('taxDeductionBatchPreviewTitle');
    const summaryElem = document.getElementById('taxDeductionBatchPreviewSummary');
    const tableContainer = document.getElementById('taxDeductionBatchPreviewTableContainer');
    if (!modalElem || !tableContainer) return;

    const items = data.items || [];
    const total = data.total_persons || 0;
    const affected = data.affected_count || items.length;
    summaryElem.textContent = `本次批次共扫描 ${total} 人，其中 ${affected} 人生成调整明细。`;
    titleElem.textContent = editable ? '个税专项附加扣除批量调整预览' : `批次 #${data.batch_id} 详情`;

    const formatNumber = (val) => {
        if (val === null || val === undefined || val === '-') return '-';
        return typeof val === 'number' ? val.toFixed(2) : val;
    };

    const rows = items.map((item, index) => {
        const readOnlyAttr = editable ? '' : 'readonly';
        return `
            <tr data-item-id="${item.id}">
                <td>${index + 1}</td>
                <td>${item.person_id}</td>
                <td>${formatNumber(item.current_continuing_education)}</td>
                <td>${formatNumber(item.current_infant_care)}</td>
                <td>${formatNumber(item.current_children_education)}</td>
                <td>${formatNumber(item.current_housing_loan_interest)}</td>
                <td>${formatNumber(item.current_housing_rent)}</td>
                <td>${formatNumber(item.current_elderly_support)}</td>
                <td>
                    <input type="number" step="0.01" class="new-continuing-education browser-default"
                           value="${item.new_continuing_education ?? 0}" ${readOnlyAttr} style="width:80px;">
                </td>
                <td>
                    <input type="number" step="0.01" class="new-infant-care browser-default"
                           value="${item.new_infant_care ?? 0}" ${readOnlyAttr} style="width:80px;">
                </td>
                <td>
                    <input type="number" step="0.01" class="new-children-education browser-default"
                           value="${item.new_children_education ?? 0}" ${readOnlyAttr} style="width:80px;">
                </td>
                <td>
                    <input type="number" step="0.01" class="new-housing-loan-interest browser-default"
                           value="${item.new_housing_loan_interest ?? 0}" ${readOnlyAttr} style="width:80px;">
                </td>
                <td>
                    <input type="number" step="0.01" class="new-housing-rent browser-default"
                           value="${item.new_housing_rent ?? 0}" ${readOnlyAttr} style="width:80px;">
                </td>
                <td>
                    <input type="number" step="0.01" class="new-elderly-support browser-default"
                           value="${item.new_elderly_support ?? 0}" ${readOnlyAttr} style="width:80px;">
                </td>
            </tr>
        `;
    }).join('');

    tableContainer.innerHTML = `
        <table class="striped responsive-table tax-deduction-table" style="font-size: 12px;">
            <thead>
                <tr>
                    <th>#</th>
                    <th>人员ID</th>
                    <th>继续教育（当前）</th>
                    <th>三岁及以下婴幼儿（当前）</th>
                    <th>子女教育（当前）</th>
                    <th>住房贷款利息（当前）</th>
                    <th>住房租金（当前）</th>
                    <th>赡养老人（当前）</th>
                    <th>继续教育（新值）</th>
                    <th>三岁及以下婴幼儿（新值）</th>
                    <th>子女教育（新值）</th>
                    <th>住房贷款利息（新值）</th>
                    <th>住房租金（新值）</th>
                    <th>赡养老人（新值）</th>
                </tr>
            </thead>
            <tbody>${rows}</tbody>
        </table>
    `;

    const confirmBtn = document.getElementById('confirmTaxDeductionBatchBtn');
    confirmBtn.dataset.batchId = data.batch_id;
    confirmBtn.onclick = editable ? confirmTaxDeductionCurrentPreview : () => M.Modal.getInstance(modalElem).close();

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

async function confirmTaxDeductionCurrentPreview() {
    const btn = document.getElementById('confirmTaxDeductionBatchBtn');
    const batchId = Number(btn.dataset.batchId);
    const tableContainer = document.getElementById('taxDeductionBatchPreviewTableContainer');
    const rows = tableContainer.querySelectorAll('tbody tr');
    const items = Array.from(rows).map((row) => {
        const id = Number(row.dataset.itemId);
        return {
            id,
            new_continuing_education: Number(row.querySelector('.new-continuing-education').value || 0),
            new_infant_care: Number(row.querySelector('.new-infant-care').value || 0),
            new_children_education: Number(row.querySelector('.new-children-education').value || 0),
            new_housing_loan_interest: Number(row.querySelector('.new-housing-loan-interest').value || 0),
            new_housing_rent: Number(row.querySelector('.new-housing-rent').value || 0),
            new_elderly_support: Number(row.querySelector('.new-elderly-support').value || 0),
        };
    });
    btn.disabled = true;
    try {
        await fetchJSON(`/api/tax-deduction/batch-confirm/${batchId}`, {
            method: 'POST',
            body: JSON.stringify({items}),
        });
        M.toast({html: '批次已确认', classes: 'green'});
        const modalElem = document.getElementById('taxDeductionBatchPreviewModal');
        const modal = M.Modal.getInstance(modalElem);
        modal.close();
        loadTaxDeductionBatchHistory();
    } catch (err) {
        M.toast({html: '确认失败：' + err.message, classes: 'red'});
    } finally {
        btn.disabled = false;
    }
}

async function openTaxDeductionBatchDetail(batchId) {
    try {
        const batches = await fetchJSON('/api/tax-deduction/batches');
        const batch = (batches.data || []).find((b) => b.id === batchId);
        if (!batch) {
            M.toast({html: '未找到批次', classes: 'red'});
            return;
        }
        const items = await fetchJSON(`/api/tax-deduction/batch-items/${batchId}`);
        openTaxDeductionPreviewModal(
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

