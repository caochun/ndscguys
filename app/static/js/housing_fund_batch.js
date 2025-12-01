document.addEventListener('DOMContentLoaded', function () {
    const selects = document.querySelectorAll('select');
    M.FormSelect.init(selects);

    const previewBtn = document.getElementById('previewHousingBatchBtn');
    if (previewBtn) {
        previewBtn.addEventListener('click', previewHousingBatch);
    }

    loadBatchHistory();
    initDefaultDates();
});

function initDefaultDates() {
    const effInput = document.getElementById('batch_effective_date');
    if (effInput && !effInput.value) {
        const today = new Date();
        const yyyy = today.getFullYear();
        const mm = String(today.getMonth() + 1).padStart(2, '0');
        const dd = String(today.getDate()).padStart(2, '0');
        effInput.value = `${yyyy}-${mm}-${dd}`;
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

async function previewHousingBatch() {
    const form = document.getElementById('housingBatchForm');
    const formData = new FormData(form);
    const payload = {
        effective_date: formData.get('effective_date'),
        min_base_amount: Number(formData.get('min_base_amount') || 0),
        max_base_amount: Number(formData.get('max_base_amount') || 0),
        default_company_rate: Number(formData.get('default_company_rate') || 0),
        default_personal_rate: Number(formData.get('default_personal_rate') || 0),
        target_company: formData.get('target_company') || null,
        target_department: formData.get('target_department') || null,
        target_employee_type: formData.get('target_employee_type') || null,
        note: formData.get('note') || null,
    };

    if (!payload.effective_date) {
        M.toast({html: '请填写生效日期', classes: 'red'});
        return;
    }
    if (payload.min_base_amount <= 0 || payload.max_base_amount <= 0 || payload.max_base_amount < payload.min_base_amount) {
        M.toast({html: '请填写合理的基数上下限', classes: 'red'});
        return;
    }

    const btn = document.getElementById('previewHousingBatchBtn');
    btn.disabled = true;
    btn.classList.add('disabled');
    try {
        const result = await fetchJSON('/api/housing-fund/batch-preview', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
        openPreviewModal(result.data, true);
    } catch (err) {
        M.toast({html: '执行失败：' + err.message, classes: 'red'});
    } finally {
        btn.disabled = false;
        btn.classList.remove('disabled');
    }
}

async function loadBatchHistory() {
    const container = document.getElementById('batchHistoryContainer');
    if (!container) return;
    try {
        const result = await fetchJSON('/api/housing-fund/batches');
        const batches = result.data || [];
        if (!batches.length) {
            container.innerHTML = '<p class="grey-text">暂无批量调整记录</p>';
            return;
        }
        const rows = batches
            .map((b) => {
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
                        <td>${b.min_base_amount} ~ ${b.max_base_amount}</td>
                        <td>${(b.default_company_rate * 100).toFixed(2)}%</td>
                        <td>${(b.default_personal_rate * 100).toFixed(2)}%</td>
                        <td>${b.target_company || '-'}</td>
                        <td>${b.target_department || '-'}</td>
                        <td>${b.target_employee_type || '-'}</td>
                        <td>${b.status}</td>
                        <td>${b.affected_count}</td>
                        <td>
                            <button class="btn-flat blue-text" data-batch-id="${b.id}" data-action="detail">详情</button>
                            ${executeBtn}
                        </td>
                    </tr>`;
            })
            .join('');
        container.innerHTML = `
            <table class="striped responsive-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>创建时间</th>
                        <th>生效日期</th>
                        <th>基数区间</th>
                        <th>默认公司比例</th>
                        <th>默认个人比例</th>
                        <th>公司</th>
                        <th>部门</th>
                        <th>员工类别</th>
                        <th>状态</th>
                        <th>影响人数</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        `;
        container.querySelectorAll('button[data-action="detail"]').forEach((btn) => {
            btn.addEventListener('click', () => openBatchDetail(Number(btn.dataset.batchId)));
        });
        container.querySelectorAll('button[data-action="execute"]').forEach((btn) => {
            if (!btn.disabled) {
                btn.addEventListener('click', () => executeBatch(Number(btn.dataset.batchId)));
            }
        });
    } catch (err) {
        container.innerHTML = `<p class="red-text">加载失败：${err.message}</p>`;
    }
}

function openPreviewModal(data, editable) {
    const modalElem = document.getElementById('housingBatchPreviewModal');
    const titleElem = document.getElementById('housingBatchPreviewTitle');
    const summaryElem = document.getElementById('housingBatchPreviewSummary');
    const tableContainer = document.getElementById('housingBatchPreviewTableContainer');
    if (!modalElem || !tableContainer) return;

    const items = data.items || [];
    const total = data.total_persons || 0;
    const affected = data.affected_count || items.length;
    summaryElem.textContent = `本次符合条件的员工共 ${total} 人，其中 ${affected} 人有公积金记录，将生成调整事件。`;
    titleElem.textContent = editable ? '公积金批量调整预览' : `批次 #${data.batch_id} 详情`;

    const rows = items
        .map((item, index) => {
            const currentBase = item.current_base_amount ?? '-';
            const currentCompany = item.current_company_rate ?? '-';
            const currentPersonal = item.current_personal_rate ?? '-';
            const newBase = item.new_base_amount ?? '';
            const newCompany = item.new_company_rate ?? '';
            const newPersonal = item.new_personal_rate ?? '';
            const readOnlyAttr = editable ? '' : 'readonly';
            const disabledAttr = editable ? '' : 'disabled';
            return `
                <tr data-item-id="${item.id}">
                    <td>${index + 1}</td>
                    <td>${item.person_id}</td>
                    <td>${currentBase}</td>
                    <td>${currentCompany}</td>
                    <td>${currentPersonal}</td>
                    <td><input type="number" step="0.01" class="new-base browser-default" value="${newBase}" ${readOnlyAttr}></td>
                    <td><input type="number" step="0.001" class="new-company browser-default" value="${newCompany}" ${readOnlyAttr}></td>
                    <td><input type="number" step="0.001" class="new-personal browser-default" value="${newPersonal}" ${readOnlyAttr}></td>
                </tr>
            `;
        })
        .join('');
    tableContainer.innerHTML = `
        <table class="striped responsive-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th>人员ID</th>
                    <th>当前基数</th>
                    <th>当前公司比例</th>
                    <th>当前个人比例</th>
                    <th>调整后基数</th>
                    <th>调整后公司比例</th>
                    <th>调整后个人比例</th>
                </tr>
            </thead>
            <tbody>${rows}</tbody>
        </table>
    `;

    const confirmBtn = document.getElementById('confirmHousingBatchBtn');
    confirmBtn.dataset.batchId = data.batch_id;
    confirmBtn.onclick = editable ? confirmCurrentPreview : () => M.Modal.getInstance(modalElem).close();

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

async function confirmCurrentPreview() {
    const btn = document.getElementById('confirmHousingBatchBtn');
    const batchId = Number(btn.dataset.batchId);
    const modalElem = document.getElementById('housingBatchPreviewModal');
    const tableContainer = document.getElementById('housingBatchPreviewTableContainer');
    const rows = tableContainer.querySelectorAll('tbody tr');
    const items = Array.from(rows).map((row) => {
        const id = Number(row.dataset.itemId);
        const newBase = Number(row.querySelector('.new-base').value || 0);
        const newCompany = Number(row.querySelector('.new-company').value || 0);
        const newPersonal = Number(row.querySelector('.new-personal').value || 0);
        return {
            id,
            new_base_amount: newBase,
            new_company_rate: newCompany,
            new_personal_rate: newPersonal,
        };
    });
    btn.disabled = true;
    try {
        await fetchJSON(`/api/housing-fund/batch-confirm/${batchId}`, {
            method: 'POST',
            body: JSON.stringify({items}),
        });
        M.toast({html: '批量调整已确认，可在下方列表中执行', classes: 'green'});
        const modal = M.Modal.getInstance(modalElem);
        modal.close();
        loadBatchHistory();
    } catch (err) {
        M.toast({html: '确认失败：' + err.message, classes: 'red'});
    } finally {
        btn.disabled = false;
    }
}

async function openBatchDetail(batchId) {
    try {
        const batches = await fetchJSON('/api/housing-fund/batches');
        const batch = (batches.data || []).find((b) => b.id === batchId);
        if (!batch) {
            M.toast({html: '未找到批次', classes: 'red'});
            return;
        }
        const items = await fetchJSON(`/api/housing-fund/batch-items/${batchId}`);
        openPreviewModal(
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

async function executeBatch(batchId) {
    try {
        const result = await fetchJSON(`/api/housing-fund/batch-execute/${batchId}`, {
            method: 'POST',
        });
        M.toast({html: `批次 #${batchId} 执行完成，影响 ${result.data.affected_count} 人`, classes: 'green'});
        loadBatchHistory();
    } catch (err) {
        M.toast({html: '执行失败：' + err.message, classes: 'red'});
    }
}


