let attendancePersons = [];

document.addEventListener('DOMContentLoaded', () => {
    const modalElem = document.getElementById('attendanceModal');
    if (modalElem) {
        M.Modal.init(modalElem);
            }
    const selects = document.querySelectorAll('select');
    M.FormSelect.init(selects);

    document.getElementById('attendanceFilterForm').addEventListener('submit', (e) => {
        e.preventDefault();
        fetchAttendanceRecords();
    });

    document.getElementById('attendanceForm').addEventListener('submit', handleCreateAttendance);
    document.getElementById('openAttendanceModal').addEventListener('click', () => {
        const instance = M.Modal.getInstance(modalElem);
        instance.open();
    });

    loadAttendancePersons();
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

async function loadAttendancePersons() {
    try {
        const result = await fetchJSON('/api/persons');
        attendancePersons = result.data || [];
        const filterSelect = document.getElementById('attendancePersonSelect');
        const formSelect = document.getElementById('attendancePersonField');
        renderPersonOptions(filterSelect, attendancePersons, true);
        renderPersonOptions(formSelect, attendancePersons, true);
        if (attendancePersons.length && !filterSelect.value) {
            filterSelect.value = attendancePersons[0].person_id;
        }
        if (filterSelect.value && formSelect) {
            formSelect.value = filterSelect.value;
        }
        M.FormSelect.init(document.querySelectorAll('select'));
        if (filterSelect.value) {
            fetchAttendanceRecords();
        }
    } catch (err) {
        M.toast({html: err.message, classes: 'red'});
    }
}

function renderPersonOptions(selectElem, persons, withPlaceholder = false) {
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

function getPersonName(personId) {
    const person = attendancePersons.find((p) => Number(p.person_id) === Number(personId));
    return person ? person.name : `#${personId}`;
}

async function fetchAttendanceRecords() {
    const filterSelect = document.getElementById('attendancePersonSelect');
    const startDate = document.getElementById('attendanceStartDate').value;
    const endDate = document.getElementById('attendanceEndDate').value;
    const tableBody = document.getElementById('attendanceTableBody');

    if (!filterSelect.value) {
        tableBody.innerHTML =
            '<tr><td colspan="7" class="center-align grey-text">请选择人员后查询</td></tr>';
        return;
    }
    const params = new URLSearchParams({person_id: filterSelect.value});
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    try {
        const result = await fetchJSON(`/api/attendance?${params.toString()}`);
        renderAttendanceTable(result.data || []);
    } catch (err) {
        tableBody.innerHTML = `<tr><td colspan="7" class="center-align red-text">${err.message}</td></tr>`;
    }
}

function renderAttendanceTable(records) {
    const tableBody = document.getElementById('attendanceTableBody');
    if (!records.length) {
        tableBody.innerHTML =
            '<tr><td colspan="7" class="center-align grey-text">暂无记录</td></tr>';
        return;
    }
    tableBody.innerHTML = records
        .map((record) => {
            const workHours =
                record.work_hours !== null && record.work_hours !== undefined
                    ? record.work_hours
                    : 0;
            const overtimeHours =
                record.overtime_hours !== null && record.overtime_hours !== undefined
                    ? record.overtime_hours
                    : 0;
            return `
        <tr>
            <td>
                <strong>${record.date}</strong><br>
                <span class="grey-text">${getPersonName(record.person_id)}</span>
            </td>
            <td>${record.check_in_time || '-'}</td>
            <td>${record.check_out_time || '-'}</td>
            <td>${workHours}</td>
            <td>${overtimeHours}</td>
            <td>${record.status}</td>
            <td>${record.note || '-'}</td>
        </tr>`
        })
        .join('');
    }
    
async function handleCreateAttendance(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const payload = {
        person_id: Number(formData.get('person_id')),
        date: formData.get('date'),
        check_in_time: formData.get('check_in_time') || null,
        check_out_time: formData.get('check_out_time') || null,
        work_hours: Number(formData.get('work_hours') || 0),
        overtime_hours: Number(formData.get('overtime_hours') || 0),
        status: formData.get('status') || '正常',
        note: formData.get('note') || null,
    };
    
    try {
        await fetchJSON('/api/attendance', {
                method: 'POST',
            body: JSON.stringify(payload),
            });
        M.toast({html: '新增考勤成功', classes: 'green'});
        e.target.reset();
        M.updateTextFields();
        M.Modal.getInstance(document.getElementById('attendanceModal')).close();
        fetchAttendanceRecords();
    } catch (err) {
        M.toast({html: err.message, classes: 'red'});
    }
}

