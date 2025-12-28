let leavePersons = [];

document.addEventListener('DOMContentLoaded', () => {
    const modalElem = document.getElementById('leaveModal');
    if (modalElem) {
        M.Modal.init(modalElem);
    }
    M.FormSelect.init(document.querySelectorAll('select'));

    document.getElementById('leaveFilterForm').addEventListener('submit', (e) => {
        e.preventDefault();
        fetchLeaveRecords();
    });
    document.getElementById('leaveForm').addEventListener('submit', handleCreateLeave);
    document.getElementById('openLeaveModal').addEventListener('click', () => {
        const instance = M.Modal.getInstance(modalElem);
        instance.open();
    });

    loadLeavePersons();
});

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

async function loadLeavePersons() {
    try {
        const result = await fetchJSON('/api/persons');
        leavePersons = result.data || [];
        const filterSelect = document.getElementById('leavePersonSelect');
        const formSelect = document.getElementById('leavePersonField');
        renderLeavePersonOptions(filterSelect, leavePersons, true);
        renderLeavePersonOptions(formSelect, leavePersons, true);
        if (leavePersons.length && !filterSelect.value) {
            filterSelect.value = leavePersons[0].person_id;
        }
        if (filterSelect.value && formSelect) {
            formSelect.value = filterSelect.value;
        }
        M.FormSelect.init(document.querySelectorAll('select'));
        if (filterSelect.value) {
            fetchLeaveRecords();
        }
    } catch (err) {
        M.toast({html: err.message, classes: 'red'});
    }
}

function renderLeavePersonOptions(selectElem, persons, withPlaceholder = false) {
    if (!selectElem) return;
    const options = persons
        .map(
            (person) =>
                `<option value="${person.person_id}">${person.name || '未命名'}（ID:${person.person_id}）</option>`
        )
        .join('');
    selectElem.innerHTML = withPlaceholder
        ? `<option value="" disabled selected>请选择人员</option>${options}`
        : options;
}

function getPersonNameFromCache(personId) {
    const person = leavePersons.find((p) => Number(p.person_id) === Number(personId));
    return person ? person.name : `#${personId}`;
}

async function fetchLeaveRecords() {
    const filterSelect = document.getElementById('leavePersonSelect');
    const startDate = document.getElementById('leaveStartDate').value;
    const endDate = document.getElementById('leaveEndDate').value;
    const tableBody = document.getElementById('leaveTableBody');

    if (!filterSelect.value) {
        tableBody.innerHTML =
            '<tr><td colspan="6" class="center-align grey-text">请选择人员后查询</td></tr>';
        return;
    }
    const params = new URLSearchParams({person_id: filterSelect.value});
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    try {
        const result = await fetchJSON(`/api/leave?${params.toString()}`);
        renderLeaveTable(result.data || []);
    } catch (err) {
        tableBody.innerHTML = `<tr><td colspan="6" class="center-align red-text">${err.message}</td></tr>`;
    }
}

function renderLeaveTable(records) {
    const tableBody = document.getElementById('leaveTableBody');
    if (!records.length) {
        tableBody.innerHTML =
            '<tr><td colspan="6" class="center-align grey-text">暂无记录</td></tr>';
        return;
    }
    tableBody.innerHTML = records
        .map(
            (record) => `
        <tr>
            <td>
                <strong>${record.leave_date}</strong><br>
                <span class="grey-text">${getPersonNameFromCache(record.person_id)}</span>
            </td>
            <td>${record.leave_type}</td>
            <td>${record.hours}</td>
            <td>${record.status}</td>
            <td>${record.approver_person_id ? getPersonNameFromCache(record.approver_person_id) : '-'}</td>
            <td>${record.reason || '-'}</td>
        </tr>`
        )
        .join('');
}

async function handleCreateLeave(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const payload = {
        person_id: Number(formData.get('person_id')),
        leave_date: formData.get('leave_date'),
        leave_type: formData.get('leave_type'),
        hours: Number(formData.get('hours') || 0),
        reason: formData.get('reason') || null,
    };

    try {
        await fetchJSON('/api/leave', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
        M.toast({html: '新增请假成功', classes: 'green'});
        e.target.reset();
        M.updateTextFields();
        M.Modal.getInstance(document.getElementById('leaveModal')).close();
        fetchLeaveRecords();
    } catch (err) {
        M.toast({html: err.message, classes: 'red'});
    }
}

