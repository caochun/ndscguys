document.addEventListener('DOMContentLoaded', function () {
    const modals = document.querySelectorAll('.modal');
    M.Modal.init(modals);
    const selects = document.querySelectorAll('select');
    M.FormSelect.init(selects);
    const sidenav = document.querySelectorAll('.sidenav');
    M.Sidenav.init(sidenav);

    document.getElementById('openCreateModal').addEventListener('click', () => {
        const instance = M.Modal.getInstance(document.getElementById('createPersonModal'));
        instance.open();
    });
    document.getElementById('openCreateModalMobile').addEventListener('click', () => {
        const instance = M.Modal.getInstance(document.getElementById('createPersonModal'));
        instance.open();
    });

    document.getElementById('createPersonForm').addEventListener('submit', handleCreatePerson);

    loadPersons();
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

async function loadPersons() {
    const container = document.getElementById('personCards');
    try {
        const result = await fetchJSON('/api/persons');
        if (!result.data.length) {
            container.innerHTML = `
                <div class="col s12 center-align grey-text text-darken-1" style="margin-top: 40px;">
                    暂无人员，点击右上角按钮新建
                </div>`;
            return;
        }
        container.innerHTML = result.data.map(person => renderPersonCard(person)).join('');
    } catch (err) {
        container.innerHTML = `<div class="col s12 red-text center-align">加载失败：${err.message}</div>`;
    }
}

function renderPersonCard(person) {
    const initials = (person.name || '?').charAt(0);
    const avatar = person.avatar || `https://api.dicebear.com/7.x/initials/svg?seed=${person.name || 'user'}`;
    return `
        <div class="col s12 m6 l4">
            <div class="card person-card">
                <div class="card-content">
                    <div class="row valign-wrapper" style="margin-bottom: 12px;">
                        <div class="col s3">
                            <img src="${avatar}" alt="${person.name || ''}" class="circle responsive-img" style="width:48px;height:48px;object-fit:cover;">
                        </div>
                        <div class="col s9">
                            <span class="card-title" style="margin:0;font-size:18px;">${person.name || '-'}</span>
                            <p class="grey-text" style="margin:0;">ID: ${person.person_id}</p>
                        </div>
                    </div>
                    <p class="grey-text text-darken-1" style="margin:4px 0;">
                        <i class="material-icons tiny" style="vertical-align:middle;">credit_card</i>
                        <span style="vertical-align:middle;">${person.id_card || '-'}</span>
                    </p>
                    <p class="grey-text text-darken-1" style="margin:4px 0;">
                        <i class="material-icons tiny" style="vertical-align:middle;">phone</i>
                        <span style="vertical-align:middle;">${person.phone || '-'}</span>
                    </p>
                    <div class="status-chip">基础信息版本 / ${person.ts}</div>
                </div>
                <div class="card-action right-align">
                    <a class="blue-text" onclick="viewPerson(${person.person_id})">
                        <i class="material-icons tiny left">visibility</i>详情
                    </a>
                </div>
            </div>
        </div>
    `;
}

async function handleCreatePerson(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const basic = {
        name: formData.get('name'),
        id_card: formData.get('id_card'),
        birth_date: formData.get('birth_date') || null,
        gender: formData.get('gender') || null,
        phone: formData.get('phone') || null,
        email: formData.get('email') || null,
        address: formData.get('address') || null,
    };
    const position = {
        company_name: formData.get('company_name') || null,
        employee_number: formData.get('employee_number') || null,
        department: formData.get('department') || null,
        position: formData.get('position') || null,
        supervisor_employee_id: formData.get('supervisor_employee_id') || null,
        hire_date: formData.get('hire_date') || null,
        employee_type: formData.get('employee_type') || null,
    };
    const hasPosition = Object.values(position).some((v) => v);
    const salaryAmountRaw = formData.get('salary_amount');
    const salary = {
        salary_type: formData.get('salary_type') || null,
        amount: salaryAmountRaw ? Number(salaryAmountRaw) : null,
        effective_date: formData.get('salary_start_date') || null,
    };
    const hasSalary =
        (salary.salary_type && salary.salary_type.trim()) ||
        salary.amount !== null ||
        (salary.effective_date && salary.effective_date.trim());

    const social = {
        base_amount: numberOrNull(formData.get('social_base_amount')),
        pension_company_rate: numberOrNull(formData.get('pension_company_rate')),
        pension_personal_rate: numberOrNull(formData.get('pension_personal_rate')),
        unemployment_company_rate: numberOrNull(formData.get('unemployment_company_rate')),
        unemployment_personal_rate: numberOrNull(formData.get('unemployment_personal_rate')),
        medical_company_rate: numberOrNull(formData.get('medical_company_rate')),
        medical_personal_rate: numberOrNull(formData.get('medical_personal_rate')),
        maternity_company_rate: numberOrNull(formData.get('maternity_company_rate')),
        maternity_personal_rate: numberOrNull(formData.get('maternity_personal_rate')),
        critical_illness_company_amount: numberOrNull(formData.get('critical_illness_company_amount')),
        critical_illness_personal_amount: numberOrNull(formData.get('critical_illness_personal_amount')),
    };
    const hasSocial = Object.values(social).some((v) => v !== null);

    const housing = {
        base_amount: numberOrNull(formData.get('housing_base_amount')),
        company_rate: numberOrNull(formData.get('housing_company_rate')),
        personal_rate: numberOrNull(formData.get('housing_personal_rate')),
    };
    const hasHousing = Object.values(housing).some((v) => v !== null);
    try {
        await fetchJSON('/api/persons', {
            method: 'POST',
            body: JSON.stringify({
                basic,
                position: hasPosition ? position : null,
                salary: hasSalary ? salary : null,
                social_security: hasSocial ? social : null,
                housing_fund: hasHousing ? housing : null,
            }),
        });
        M.toast({html: '创建成功', classes: 'green'});
        e.target.reset();
        const modal = M.Modal.getInstance(document.getElementById('createPersonModal'));
        modal.close();
        loadPersons();
    } catch (err) {
        M.toast({html: err.message, classes: 'red'});
    }
}

async function viewPerson(personId) {
    try {
        const result = await fetchJSON(`/api/persons/${personId}`);
        const detail = document.getElementById('detailContent');
        const tabsContainer = document.getElementById('detailTabs');
        const basicInfo = document.getElementById('basicInfoContent');
        const basicHistory = document.getElementById('basicHistoryContent');
        const positionInfo = document.getElementById('positionInfoContent');
        const positionHistory = document.getElementById('positionHistoryContent');
        const salaryInfo = document.getElementById('salaryInfoContent');
        const salaryHistory = document.getElementById('salaryHistoryContent');
        const socialInfo = document.getElementById('socialInfoContent');
        const socialHistory = document.getElementById('socialHistoryContent');
        const housingInfo = document.getElementById('housingInfoContent');
        const housingHistory = document.getElementById('housingHistoryContent');

        const basic = result.data.basic.data;
        const position = result.data.position ? result.data.position.data : null;
        const salary = result.data.salary ? result.data.salary.data : null;
        const social = result.data.social_security ? result.data.social_security.data : null;
        const housing = result.data.housing_fund ? result.data.housing_fund.data : null;
        const avatar =
            basic.avatar ||
            `https://api.dicebear.com/7.x/micah/svg?backgroundColor=bde0fe&seed=${basic.name || 'user'}`;

        detail.innerHTML = `
            <div class="row valign-wrapper">
                <div class="col s3 m2">
                    <img src="${avatar}" class="circle responsive-img" style="width:64px;height:64px;object-fit:cover;">
                </div>
                <div class="col s9 m10">
                    <h5>${basic.name || '未命名'} <span class="grey-text text-darken-1" style="font-size:14px;">#${personId}</span></h5>
                    <p class="grey-text" style="margin-bottom:0;">最后更新时间：${result.data.basic.ts}</p>
                </div>
            </div>
        `;

        tabsContainer.style.display = 'block';

        basicInfo.innerHTML = renderInfoGrid(
            [
                { label: '身份证', value: basic.id_card },
                { label: '电话', value: basic.phone },
                { label: '邮箱', value: basic.email },
                { label: '地址', value: basic.address },
                { label: '出生日期', value: basic.birth_date },
                { label: '性别', value: basic.gender },
            ],
            3
        );
        basicHistory.innerHTML = renderHistoryTable(result.data.basic_history, '基础信息');

        positionInfo.innerHTML = position
            ? renderInfoGrid(
                  [
                      { label: '公司', value: position.company_name },
                      { label: '员工号', value: position.employee_number },
                      { label: '部门', value: position.department },
                      { label: '职位', value: position.position },
                      { label: '员工类别', value: position.employee_type },
                      { label: '任职日期', value: position.hire_date },
                  ],
                  2
              )
            : '<p class="grey-text">暂无岗位信息</p>';
        positionHistory.innerHTML = renderHistoryTable(result.data.position_history, '岗位信息');

        salaryInfo.innerHTML = salary
            ? renderInfoGrid(
                  [
                      { label: '薪资类型', value: salary.salary_type },
                      { label: '薪资金额', value: salary.amount },
                      { label: '起薪日期', value: salary.effective_date },
                  ],
                  2
              )
            : '<p class="grey-text">暂无薪资信息</p>';
        salaryHistory.innerHTML = renderHistoryTable(result.data.salary_history, '薪资信息');

        socialInfo.innerHTML = social
            ? renderInfoGrid(
                  [
                      { label: '社保基数', value: social.base_amount },
                      { label: '养老公司比例', value: percentText(social.pension_company_rate) },
                      { label: '养老个人比例', value: percentText(social.pension_personal_rate) },
                      { label: '失业公司比例', value: percentText(social.unemployment_company_rate) },
                      { label: '失业个人比例', value: percentText(social.unemployment_personal_rate) },
                      { label: '医疗公司比例', value: percentText(social.medical_company_rate) },
                      { label: '医疗个人比例', value: percentText(social.medical_personal_rate) },
                      { label: '生育公司比例', value: percentText(social.maternity_company_rate) },
                      { label: '生育个人比例', value: percentText(social.maternity_personal_rate) },
                      { label: '大病险公司金额', value: social.critical_illness_company_amount },
                      { label: '大病险个人金额', value: social.critical_illness_personal_amount },
                  ],
                  2
              )
            : '<p class="grey-text">暂无社保信息</p>';
        socialHistory.innerHTML = renderHistoryTable(result.data.social_security_history, '社保信息');

        housingInfo.innerHTML = housing
            ? renderInfoGrid(
                  [
                      { label: '公积金基数', value: housing.base_amount },
                      { label: '公司比例', value: percentText(housing.company_rate) },
                      { label: '个人比例', value: percentText(housing.personal_rate) },
                  ],
                  2
              )
            : '<p class="grey-text">暂无公积金信息</p>';
        housingHistory.innerHTML = renderHistoryTable(result.data.housing_fund_history, '公积金信息');

        const tabs = document.querySelectorAll('#detailTabs .tabs');
        M.Tabs.init(tabs);

        const modal = M.Modal.getInstance(document.getElementById('detailModal'));
        modal.open();
    } catch (err) {
        M.toast({html: '加载详情失败：' + err.message, classes: 'red'});
    }
}

function renderHistoryTable(historyList, title) {
    if (!historyList || !historyList.length) {
        return `<div class="history-block grey-text">暂无${title}历史</div>`;
    }
    const columns = Array.from(
        historyList.reduce((set, item) => {
            Object.keys(item.data || {}).forEach((key) => {
                if (title === "基础信息" && key === "avatar") return;
                set.add(key);
            });
            return set;
        }, new Set())
    );
    const rows = historyList
        .map((item) => {
            const cells = columns
                .map((key) => `<td>${(item.data || {})[key] || "-"}</td>`)
                .join("");
            return `
                <tr>
                    <td>${item.version}</td>
                    <td>${item.ts}</td>
                    ${cells}
                </tr>`;
        })
        .join("");
    const headerCells = columns.map((key) => `<th>${key}</th>`).join("");
    return `
        <table class="striped responsive-table">
            <thead>
                <tr>
                    <th>版本</th>
                    <th>时间</th>
                    ${headerCells}
                </tr>
            </thead>
            <tbody>${rows}</tbody>
        </table>
    `;
}

function renderInfoGrid(items, columns = 2) {
    const filtered = items.filter((item) => item && item.label);
    if (!filtered.length) {
        return '<p class="grey-text">暂无数据</p>';
    }
    const chunkSize = columns;
    const rows = [];
    for (let i = 0; i < filtered.length; i += chunkSize) {
        rows.push(filtered.slice(i, i + chunkSize));
    }
    return rows
        .map(
            (row) => `
            <div class="row" style="margin-bottom:0;">
                ${row
                    .map(
                        (item) => `
                        <div class="col s12 m${12 / columns}">
                            <p style="margin:4px 0;"><strong>${item.label}：</strong> ${item.value || '-'}</p>
                        </div>
                    `
                    )
                    .join('')}
            </div>`
        )
        .join('');
}

function numberOrNull(value) {
    if (value === null || value === undefined || value === '') {
        return null;
    }
    const n = Number(value);
    return Number.isNaN(n) ? null : n;
}

function percentText(value) {
    if (value === null || value === undefined || value === '') return '-';
    return `${(Number(value) * 100).toFixed(2)}%`;
}

