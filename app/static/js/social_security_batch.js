document.addEventListener('DOMContentLoaded', function () {
    const selects = document.querySelectorAll('select');
    M.FormSelect.init(selects);

    const previewBtn = document.getElementById('previewSocialBatchBtn');
    if (previewBtn) {
        previewBtn.addEventListener('click', previewSocialBatch);
    }

    initSocialDefaultDates();
    loadSocialBatchHistory();
});

function initSocialDefaultDates() {
    const effInput = document.getElementById('social_batch_effective_date');
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

async function previewSocialBatch() {
    const form = document.getElementById('socialBatchForm');
    const formData = new FormData(form);
    const payload = {
        effective_date: formData.get('effective_date'),
        min_base_amount: Number(formData.get('min_base_amount') || 0),
        max_base_amount: Number(formData.get('max_base_amount') || 0),
        default_pension_company_rate: numberOrNull(formData.get('default_pension_company_rate')),
        default_pension_personal_rate: numberOrNull(formData.get('default_pension_personal_rate')),
        default_unemployment_company_rate: numberOrNull(formData.get('default_unemployment_company_rate')),
        default_unemployment_personal_rate: numberOrNull(formData.get('default_unemployment_personal_rate')),
        default_medical_company_rate: numberOrNull(formData.get('default_medical_company_rate')),
        default_medical_personal_rate: numberOrNull(formData.get('default_medical_personal_rate')),
        default_maternity_company_rate: numberOrNull(formData.get('default_maternity_company_rate')),
        default_maternity_personal_rate: numberOrNull(formData.get('default_maternity_personal_rate')),
        default_critical_illness_company_amount: numberOrNull(formData.get('default_critical_illness_company_amount')),
        default_critical_illness_personal_amount: numberOrNull(formData.get('default_critical_illness_personal_amount')),
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

    const btn = document.getElementById('previewSocialBatchBtn');
    btn.disabled = true;
    btn.classList.add('disabled');
    try {
        const result = await fetchJSON('/api/social-security/batch-preview', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
        openSocialPreviewModal(result.data, true);
    } catch (err) {
        M.toast({html: '预览失败：' + err.message, classes: 'red'});
    } finally {
        btn.disabled = false;
        btn.classList.remove('disabled');
    }
}

async function loadSocialBatchHistory() {
    const container = document.getElementById('socialBatchHistoryContainer');
    if (!container) return;
    try {
        const result = await fetchJSON('/api/social-security/batches');
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
            btn.addEventListener('click', () => openSocialBatchDetail(Number(btn.dataset.batchId)));
        });
        container.querySelectorAll('button[data-action="execute"]').forEach((btn) => {
            if (!btn.disabled) {
                btn.addEventListener('click', () => executeSocialBatch(Number(btn.dataset.batchId)));
            }
        });
    } catch (err) {
        container.innerHTML = `<p class="red-text">加载失败：${err.message}</p>`;
    }
}

function openSocialPreviewModal(data, editable) {
    const modalElem = document.getElementById('socialBatchPreviewModal');
    const titleElem = document.getElementById('socialBatchPreviewTitle');
    const summaryElem = document.getElementById('socialBatchPreviewSummary');
    const tableContainer = document.getElementById('socialBatchPreviewTableContainer');
    if (!modalElem || !tableContainer) return;

    const items = data.items || [];
    const total = data.total_persons || 0;
    const affected = data.affected_count || items.length;
    summaryElem.textContent = `本次符合条件的员工共 ${total} 人，其中 ${affected} 人有社保记录，将生成调整事件。`;
    titleElem.textContent = editable ? '社保批量调整预览' : `批次 #${data.batch_id} 详情`;

    const rows = items
        .map((item, index) => {
            const cBase = item.current_base_amount ?? '-';
            const cPenC = item.current_pension_company_rate ?? '-';
            const cPenP = item.current_pension_personal_rate ?? '-';
            const cUnC = item.current_unemployment_company_rate ?? '-';
            const cUnP = item.current_unemployment_personal_rate ?? '-';
            const cMedC = item.current_medical_company_rate ?? '-';
            const cMedP = item.current_medical_personal_rate ?? '-';
            const cMatC = item.current_maternity_company_rate ?? '-';
            const cMatP = item.current_maternity_personal_rate ?? '-';
            const cCiC = item.current_critical_illness_company_amount ?? '-';
            const cCiP = item.current_critical_illness_personal_amount ?? '-';

            const nBase = item.new_base_amount ?? '';
            const nPenC = item.new_pension_company_rate ?? '';
            const nPenP = item.new_pension_personal_rate ?? '';
            const nUnC = item.new_unemployment_company_rate ?? '';
            const nUnP = item.new_unemployment_personal_rate ?? '';
            const nMedC = item.new_medical_company_rate ?? '';
            const nMedP = item.new_medical_personal_rate ?? '';
            const nMatC = item.new_maternity_company_rate ?? '';
            const nMatP = item.new_maternity_personal_rate ?? '';
            const nCiC = item.new_critical_illness_company_amount ?? '';
            const nCiP = item.new_critical_illness_personal_amount ?? '';

            const readOnlyAttr = editable ? '' : 'readonly';
            return `
                <tr data-item-id="${item.id}">
                    <td>${index + 1}</td>
                    <td>${item.person_id}</td>
                    <td>${cBase}</td>
                    <td>${cPenC}</td>
                    <td>${cPenP}</td>
                    <td>${cUnC}</td>
                    <td>${cUnP}</td>
                    <td>${cMedC}</td>
                    <td>${cMedP}</td>
                    <td>${cMatC}</td>
                    <td>${cMatP}</td>
                    <td>${cCiC}</td>
                    <td>${cCiP}</td>
                    <td><input type="number" step="0.01" class="new-base browser-default" value="${nBase}" ${readOnlyAttr}></td>
                    <td><input type="number" step="0.001" class="new-pen-c browser-default" value="${nPenC}" ${readOnlyAttr}></td>
                    <td><input type="number" step="0.001" class="new-pen-p browser-default" value="${nPenP}" ${readOnlyAttr}></td>
                    <td><input type="number" step="0.001" class="new-un-c browser-default" value="${nUnC}" ${readOnlyAttr}></td>
                    <td><input type="number" step="0.001" class="new-un-p browser-default" value="${nUnP}" ${readOnlyAttr}></td>
                    <td><input type="number" step="0.001" class="new-med-c browser-default" value="${nMedC}" ${readOnlyAttr}></td>
                    <td><input type="number" step="0.001" class="new-med-p browser-default" value="${nMedP}" ${readOnlyAttr}></td>
                    <td><input type="number" step="0.001" class="new-mat-c browser-default" value="${nMatC}" ${readOnlyAttr}></td>
                    <td><input type="number" step="0.001" class="new-mat-p browser-default" value="${nMatP}" ${readOnlyAttr}></td>
                    <td><input type="number" step="0.01" class="new-ci-c browser-default" value="${nCiC}" ${readOnlyAttr}></td>
                    <td><input type="number" step="0.01" class="new-ci-p browser-default" value="${nCiP}" ${readOnlyAttr}></td>
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
                    <th>养老公</th>
                    <th>养老个</th>
                    <th>失业公</th>
                    <th>失业个</th>
                    <th>医保公</th>
                    <th>医保个</th>
                    <th>生育公</th>
                    <th>生育个</th>
                    <th>大病公</th>
                    <th>大病个</th>
                    <th>新基数</th>
                    <th>新养老公</th>
                    <th>新养老个</th>
                    <th>新失业公</th>
                    <th>新失业个</th>
                    <th>新医保公</th>
                    <th>新医保个</th>
                    <th>新生育公</th>
                    <th>新生育个</th>
                    <th>新大病公</th>
                    <th>新大病个</th>
                </tr>
            </thead>
            <tbody>${rows}</tbody>
        </table>
    `;

    const confirmBtn = document.getElementById('confirmSocialBatchBtn');
    confirmBtn.dataset.batchId = data.batch_id;
    confirmBtn.onclick = editable ? confirmSocialCurrentPreview : () => M.Modal.getInstance(modalElem).close();

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

async function confirmSocialCurrentPreview() {
    const btn = document.getElementById('confirmSocialBatchBtn');
    const batchId = Number(btn.dataset.batchId);
    const modalElem = document.getElementById('socialBatchPreviewModal');
    const tableContainer = document.getElementById('socialBatchPreviewTableContainer');
    const rows = tableContainer.querySelectorAll('tbody tr');
    const items = Array.from(rows).map((row) => {
        const id = Number(row.dataset.itemId);
        const v = (cls) => {
            const el = row.querySelector(cls);
            return el && el.value !== '' ? Number(el.value) : null;
        };
        return {
            id,
            new_base_amount: v('.new-base'),
            new_pension_company_rate: v('.new-pen-c'),
            new_pension_personal_rate: v('.new-pen-p'),
            new_unemployment_company_rate: v('.new-un-c'),
            new_unemployment_personal_rate: v('.new-un-p'),
            new_medical_company_rate: v('.new-med-c'),
            new_medical_personal_rate: v('.new-med-p'),
            new_maternity_company_rate: v('.new-mat-c'),
            new_maternity_personal_rate: v('.new-mat-p'),
            new_critical_illness_company_amount: v('.new-ci-c'),
            new_critical_illness_personal_amount: v('.new-ci-p'),
        };
    });
    btn.disabled = true;
    try {
        await fetchJSON(`/api/social-security/batch-confirm/${batchId}`, {
            method: 'POST',
            body: JSON.stringify({items}),
        });
        M.toast({html: '社保批量调整已确认，可在下方列表中执行', classes: 'green'});
        const modal = M.Modal.getInstance(modalElem);
        modal.close();
        loadSocialBatchHistory();
    } catch (err) {
        M.toast({html: '确认失败：' + err.message, classes: 'red'});
    } finally {
        btn.disabled = false;
    }
}

async function openSocialBatchDetail(batchId) {
    try {
        const batches = await fetchJSON('/api/social-security/batches');
        const batch = (batches.data || []).find((b) => b.id === batchId);
        if (!batch) {
            M.toast({html: '未找到批次', classes: 'red'});
            return;
        }
        const items = await fetchJSON(`/api/social-security/batch-items/${batchId}`);
        openSocialPreviewModal(
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

async function executeSocialBatch(batchId) {
    try {
        const result = await fetchJSON(`/api/social-security/batch-execute/${batchId}`, {
            method: 'POST',
        });
        M.toast({html: `批次 #${batchId} 执行完成，影响 ${result.data.affected_count} 人`, classes: 'green'});
        loadSocialBatchHistory();
    } catch (err) {
        M.toast({html: '执行失败：' + err.message, classes: 'red'});
    }
}


