document.addEventListener('DOMContentLoaded', function () {
    const modals = document.querySelectorAll('.modal');
    M.Modal.init(modals);
    const selects = document.querySelectorAll('select');
    M.FormSelect.init(selects);

    const openCreateBtn = document.getElementById('openCreateModal');
    if (openCreateBtn) {
        openCreateBtn.addEventListener('click', () => {
            const instance = M.Modal.getInstance(document.getElementById('createPersonModal'));
            instance.open();
        });
    }

    document.getElementById('createPersonForm').addEventListener('submit', handleCreatePerson);
    const positionAdjustForm = document.getElementById('positionAdjustForm');
    if (positionAdjustForm) {
        positionAdjustForm.addEventListener('submit', handlePositionAdjustSubmit);
    }
    const salaryAdjustForm = document.getElementById('salaryAdjustForm');
    if (salaryAdjustForm) {
        salaryAdjustForm.addEventListener('submit', handleSalaryAdjustSubmit);
    }
    const socialAdjustForm = document.getElementById('socialAdjustForm');
    if (socialAdjustForm) {
        socialAdjustForm.addEventListener('submit', handleSocialAdjustSubmit);
    }
    const housingAdjustForm = document.getElementById('housingAdjustForm');
    if (housingAdjustForm) {
        housingAdjustForm.addEventListener('submit', handleHousingAdjustSubmit);
    }

    const assessmentForm = document.getElementById('assessmentForm');
    if (assessmentForm) {
        assessmentForm.addEventListener('submit', handleAssessmentSubmit);
    }

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
    const avatar = person.avatar || `https://api.dicebear.com/7.x/initials/svg?seed=${person.name || 'user'}`;
    const company = person.current_company || null;
    let cardCompanyClass = 'company-none';
    if (company) {
        if (company === 'SC高科技公司') {
            cardCompanyClass = 'company-scg';
        } else if (company === 'SC能源科技公司') {
            cardCompanyClass = 'company-sce';
        } else {
            cardCompanyClass = 'company-other';
        }
    }
    const companyText = company ? company : '-';
    const positionText = person.current_position ? person.current_position : '-';
    return `
        <div class="col s12 m6 l4">
            <div class="card person-card ${cardCompanyClass}">
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
                    <p class="grey-text text-darken-1" style="margin:4px 0;">
                        <i class="material-icons tiny" style="vertical-align:middle;">business</i>
                        <span style="vertical-align:middle;">当前公司：${companyText}</span>
                    </p>
                    <p class="grey-text text-darken-1" style="margin:2px 0 0 0;">
                        <i class="material-icons tiny" style="vertical-align:middle;">work</i>
                        <span style="vertical-align:middle;">职位：${positionText}</span>
                    </p>
                </div>
                <div class="card-action" style="display:flex;align-items:center;justify-content:space-between;">
                    <a class="blue-text" onclick="viewPerson(${person.person_id})" title="查看详情">
                        <i class="material-icons tiny">visibility</i>
                    </a>
                    <div>
                        <a class="purple-text text-darken-1" style="margin-right:8px;" onclick="openAssessmentModal(${person.person_id})" title="考核记录">
                            <i class="material-icons tiny">grade</i>
                        </a>
                        <a class="teal-text text-darken-1" style="margin-right:8px;" onclick="openSalaryAdjustModal(${person.person_id})" title="薪资调整">
                            <i class="material-icons tiny">payments</i>
                        </a>
                        <a class="indigo-text text-darken-1" style="margin-right:8px;" onclick="openSocialAdjustModal(${person.person_id})" title="社保调整">
                            <i class="material-icons tiny">shield</i>
                        </a>
                        <a class="green-text text-darken-2" style="margin-right:8px;" onclick="openHousingAdjustModal(${person.person_id})" title="公积金调整">
                            <i class="material-icons tiny">savings</i>
                        </a>
                        <a class="orange-text text-darken-2" onclick="openPositionAdjustModal(${person.person_id})" title="任职调整">
                            <i class="material-icons tiny">work_history</i>
                        </a>
                    </div>
                </div>
            </div>
        </div>
    `;
}

async function openPositionAdjustModal(personId) {
    try {
        const result = await fetchJSON(`/api/persons/${personId}`);
        const position = result.data.position ? result.data.position.data : null;

        document.getElementById('positionAdjustPersonId').value = personId;
        const companyInput = document.getElementById('adj_company_name');
        const empNoInput = document.getElementById('adj_employee_number');
        const deptInput = document.getElementById('adj_department');
        const posInput = document.getElementById('adj_position');
        const changeTypeSelect = document.getElementById('adj_change_type');
        const changeDateInput = document.getElementById('adj_change_date');
        const empTypeSelect = document.getElementById('adj_employee_type');
        const reasonInput = document.getElementById('adj_change_reason');

        // 预填当前岗位信息
        if (position) {
            companyInput.value = position.company_name || '';
            empNoInput.value = position.employee_number || '';
            deptInput.value = position.department || '';
            posInput.value = position.position || '';
            // 默认变动事件：如果当前无岗位则视为入职，否则转岗
            changeTypeSelect.value = '转岗';
            empTypeSelect.value = position.employee_type || '';
            reasonInput.value = '';
        } else {
            companyInput.value = '';
            empNoInput.value = '';
            deptInput.value = '';
            posInput.value = '';
            changeTypeSelect.value = '转岗';
            empTypeSelect.value = '';
            reasonInput.value = '';
        }

        // 变动日期默认今天
        const today = new Date();
        const yyyy = today.getFullYear();
        const mm = String(today.getMonth() + 1).padStart(2, '0');
        const dd = String(today.getDate()).padStart(2, '0');
        changeDateInput.value = `${yyyy}-${mm}-${dd}`;

        M.updateTextFields();
        const selects = document.querySelectorAll('#positionAdjustModal select');
        M.FormSelect.init(selects);

        const modal = M.Modal.getInstance(document.getElementById('positionAdjustModal'));
        modal.open();
    } catch (err) {
        M.toast({html: '加载任职信息失败：' + err.message, classes: 'red'});
    }
}

async function handlePositionAdjustSubmit(e) {
    e.preventDefault();
    const personId = document.getElementById('positionAdjustPersonId').value;
    const formData = new FormData(e.target);
    const payload = {
        company_name: formData.get('company_name') || null,
        employee_number: formData.get('employee_number') || null,
        department: formData.get('department') || null,
        position: formData.get('position') || null,
        change_type: formData.get('change_type') || null,
        change_date: formData.get('change_date') || null,
        employee_type: formData.get('employee_type') || null,
        change_reason: formData.get('change_reason') || null,
    };
    try {
        await fetchJSON(`/api/persons/${personId}/position`, {
            method: 'POST',
            body: JSON.stringify(payload),
        });
        M.toast({html: '任职调整已保存', classes: 'green'});
        const modal = M.Modal.getInstance(document.getElementById('positionAdjustModal'));
        modal.close();
        loadPersons();
    } catch (err) {
        M.toast({html: '保存失败：' + err.message, classes: 'red'});
    }
}

async function openSalaryAdjustModal(personId) {
    try {
        const result = await fetchJSON(`/api/persons/${personId}`);
        const salary = result.data.salary ? result.data.salary.data : null;

        document.getElementById('salaryAdjustPersonId').value = personId;
        const typeSelect = document.getElementById('adj_salary_type');
        const amountInput = document.getElementById('adj_salary_amount');
        const effDateInput = document.getElementById('adj_salary_effective_date');

        if (salary) {
            typeSelect.value = salary.salary_type || '';
            amountInput.value = salary.amount != null ? salary.amount : '';
            effDateInput.value = salary.effective_date || '';
        } else {
            typeSelect.value = '';
            amountInput.value = '';
            const today = new Date();
            const yyyy = today.getFullYear();
            const mm = String(today.getMonth() + 1).padStart(2, '0');
            const dd = String(today.getDate()).padStart(2, '0');
            effDateInput.value = `${yyyy}-${mm}-${dd}`;
        }

        M.updateTextFields();
        const selects = document.querySelectorAll('#salaryAdjustModal select');
        M.FormSelect.init(selects);

        const modal = M.Modal.getInstance(document.getElementById('salaryAdjustModal'));
        modal.open();
    } catch (err) {
        M.toast({html: '加载薪资信息失败：' + err.message, classes: 'red'});
    }
}

async function handleSalaryAdjustSubmit(e) {
    e.preventDefault();
    const personId = document.getElementById('salaryAdjustPersonId').value;
    const formData = new FormData(e.target);
    const payload = {
        salary_type: formData.get('salary_type') || null,
        amount: formData.get('amount') ? Number(formData.get('amount')) : null,
        effective_date: formData.get('effective_date') || null,
    };
    try {
        await fetchJSON(`/api/persons/${personId}/salary`, {
            method: 'POST',
            body: JSON.stringify(payload),
        });
        M.toast({html: '薪资调整已保存', classes: 'green'});
        const modal = M.Modal.getInstance(document.getElementById('salaryAdjustModal'));
        modal.close();
        loadPersons();
    } catch (err) {
        M.toast({html: '保存失败：' + err.message, classes: 'red'});
    }
}

async function openSocialAdjustModal(personId) {
    try {
        const result = await fetchJSON(`/api/persons/${personId}`);
        const social = result.data.social_security ? result.data.social_security.data : null;

        document.getElementById('socialAdjustPersonId').value = personId;
        const baseInput = document.getElementById('adj_social_base_amount');
        const pcr = document.getElementById('adj_pension_company_rate');
        const ppr = document.getElementById('adj_pension_personal_rate');
        const ucr = document.getElementById('adj_unemployment_company_rate');
        const upr = document.getElementById('adj_unemployment_personal_rate');
        const mcr = document.getElementById('adj_medical_company_rate');
        const mpr = document.getElementById('adj_medical_personal_rate');
        const macr = document.getElementById('adj_maternity_company_rate');
        const mapr = document.getElementById('adj_maternity_personal_rate');
        const cic = document.getElementById('adj_critical_illness_company_amount');
        const cip = document.getElementById('adj_critical_illness_personal_amount');

        const s = social || {};
        baseInput.value = s.base_amount != null ? s.base_amount : '';
        pcr.value = s.pension_company_rate != null ? s.pension_company_rate : '';
        ppr.value = s.pension_personal_rate != null ? s.pension_personal_rate : '';
        ucr.value = s.unemployment_company_rate != null ? s.unemployment_company_rate : '';
        upr.value = s.unemployment_personal_rate != null ? s.unemployment_personal_rate : '';
        mcr.value = s.medical_company_rate != null ? s.medical_company_rate : '';
        mpr.value = s.medical_personal_rate != null ? s.medical_personal_rate : '';
        macr.value = s.maternity_company_rate != null ? s.maternity_company_rate : '';
        mapr.value = s.maternity_personal_rate != null ? s.maternity_personal_rate : '';
        cic.value = s.critical_illness_company_amount != null ? s.critical_illness_company_amount : '';
        cip.value = s.critical_illness_personal_amount != null ? s.critical_illness_personal_amount : '';

        M.updateTextFields();
        const modal = M.Modal.getInstance(document.getElementById('socialAdjustModal'));
        modal.open();
    } catch (err) {
        M.toast({html: '加载社保信息失败：' + err.message, classes: 'red'});
    }
}

async function handleSocialAdjustSubmit(e) {
    e.preventDefault();
    const personId = document.getElementById('socialAdjustPersonId').value;
    const formData = new FormData(e.target);
    const payload = {
        base_amount: formData.get('base_amount') ? Number(formData.get('base_amount')) : null,
        pension_company_rate: formData.get('pension_company_rate') ? Number(formData.get('pension_company_rate')) : null,
        pension_personal_rate: formData.get('pension_personal_rate') ? Number(formData.get('pension_personal_rate')) : null,
        unemployment_company_rate: formData.get('unemployment_company_rate') ? Number(formData.get('unemployment_company_rate')) : null,
        unemployment_personal_rate: formData.get('unemployment_personal_rate') ? Number(formData.get('unemployment_personal_rate')) : null,
        medical_company_rate: formData.get('medical_company_rate') ? Number(formData.get('medical_company_rate')) : null,
        medical_personal_rate: formData.get('medical_personal_rate') ? Number(formData.get('medical_personal_rate')) : null,
        maternity_company_rate: formData.get('maternity_company_rate') ? Number(formData.get('maternity_company_rate')) : null,
        maternity_personal_rate: formData.get('maternity_personal_rate') ? Number(formData.get('maternity_personal_rate')) : null,
        critical_illness_company_amount: formData.get('critical_illness_company_amount') ? Number(formData.get('critical_illness_company_amount')) : null,
        critical_illness_personal_amount: formData.get('critical_illness_personal_amount') ? Number(formData.get('critical_illness_personal_amount')) : null,
    };
    try {
        await fetchJSON(`/api/persons/${personId}/social-security`, {
            method: 'POST',
            body: JSON.stringify(payload),
        });
        M.toast({html: '社保调整已保存', classes: 'green'});
        const modal = M.Modal.getInstance(document.getElementById('socialAdjustModal'));
        modal.close();
        loadPersons();
    } catch (err) {
        M.toast({html: '保存失败：' + err.message, classes: 'red'});
    }
}

async function openHousingAdjustModal(personId) {
    try {
        const result = await fetchJSON(`/api/persons/${personId}`);
        const housing = result.data.housing_fund ? result.data.housing_fund.data : null;

        document.getElementById('housingAdjustPersonId').value = personId;
        const baseInput = document.getElementById('adj_housing_base_amount');
        const cr = document.getElementById('adj_housing_company_rate');
        const pr = document.getElementById('adj_housing_personal_rate');

        const h = housing || {};
        baseInput.value = h.base_amount != null ? h.base_amount : '';
        cr.value = h.company_rate != null ? h.company_rate : '';
        pr.value = h.personal_rate != null ? h.personal_rate : '';

        M.updateTextFields();
        const modal = M.Modal.getInstance(document.getElementById('housingAdjustModal'));
        modal.open();
    } catch (err) {
        M.toast({html: '加载公积金信息失败：' + err.message, classes: 'red'});
    }
}

async function handleHousingAdjustSubmit(e) {
    e.preventDefault();
    const personId = document.getElementById('housingAdjustPersonId').value;
    const formData = new FormData(e.target);
    const payload = {
        base_amount: formData.get('base_amount') ? Number(formData.get('base_amount')) : null,
        company_rate: formData.get('company_rate') ? Number(formData.get('company_rate')) : null,
        personal_rate: formData.get('personal_rate') ? Number(formData.get('personal_rate')) : null,
    };
    try {
        await fetchJSON(`/api/persons/${personId}/housing-fund`, {
            method: 'POST',
            body: JSON.stringify(payload),
        });
        M.toast({html: '公积金调整已保存', classes: 'green'});
        const modal = M.Modal.getInstance(document.getElementById('housingAdjustModal'));
        modal.close();
        loadPersons();
    } catch (err) {
        M.toast({html: '保存失败：' + err.message, classes: 'red'});
    }
}

async function openAssessmentModal(personId) {
    try {
        const result = await fetchJSON(`/api/persons/${personId}`);
        const assessment = result.data.assessment ? result.data.assessment.data : null;
        const history = result.data.assessment_history || [];

        document.getElementById('assessmentPersonId').value = personId;
        const gradeSelect = document.getElementById('assessment_grade');
        const dateInput = document.getElementById('assessment_date');
        const noteInput = document.getElementById('assessment_note');

        // 默认考核等级：若有最近一次，则预选其 grade
        if (assessment && assessment.grade) {
            gradeSelect.value = assessment.grade;
        } else {
            gradeSelect.value = '';
        }

        // 默认考核日期：若有最近一次，则用最近一次的 assessment_date，否则用今天
        if (assessment && assessment.assessment_date) {
            dateInput.value = assessment.assessment_date;
        } else {
            const today = new Date();
            const yyyy = today.getFullYear();
            const mm = String(today.getMonth() + 1).padStart(2, '0');
            const dd = String(today.getDate()).padStart(2, '0');
            dateInput.value = `${yyyy}-${mm}-${dd}`;
        }

        noteInput.value = '';

        // 渲染最近一次考核概览
        const latestContainer = document.getElementById('latestAssessmentContainer');
        if (assessment) {
            latestContainer.innerHTML = renderInfoGrid(
                [
                    {label: '最近等级', value: assessment.grade},
                    {label: '考核日期', value: assessment.assessment_date},
                    {label: '备注', value: assessment.note},
                ],
                3
            );
        } else {
            latestContainer.innerHTML = '<p class="grey-text">暂无考核记录</p>';
        }

        // 渲染历史
        const historyContainer = document.getElementById('assessmentHistoryContainer');
        historyContainer.innerHTML = renderHistoryTable(history, '考核信息');

        M.updateTextFields();
        const selects = document.querySelectorAll('#assessmentModal select');
        M.FormSelect.init(selects);

        const modal = M.Modal.getInstance(document.getElementById('assessmentModal'));
        modal.open();
    } catch (err) {
        M.toast({html: '加载考核信息失败：' + err.message, classes: 'red'});
    }
}

async function handleAssessmentSubmit(e) {
    e.preventDefault();
    const personId = document.getElementById('assessmentPersonId').value;
    const formData = new FormData(e.target);
    const payload = {
        grade: formData.get('grade') || null,
        assessment_date: formData.get('assessment_date') || null,
        note: formData.get('note') || null,
    };
    if (!payload.grade) {
        M.toast({html: '请选择考核等级', classes: 'red'});
        return;
    }
    try {
        await fetchJSON(`/api/persons/${personId}/assessment`, {
            method: 'POST',
            body: JSON.stringify(payload),
        });
        M.toast({html: '考核记录已保存', classes: 'green'});
        const modal = M.Modal.getInstance(document.getElementById('assessmentModal'));
        modal.close();
        loadPersons();
    } catch (err) {
        M.toast({html: '保存失败：' + err.message, classes: 'red'});
    }
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
        change_type: '入职',
        change_date: formData.get('change_date') || null,
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
                      { label: '变动事件', value: position.change_type },
                      { label: '变动日期', value: position.change_date },
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
        
        // 懒加载：监听 tab 切换事件
        let currentPersonId = personId;
        let attendanceLoaded = false;
        let leaveLoaded = false;
        
        // 使用 MutationObserver 监听 tab 内容区域的显示
        const attendanceTab = document.getElementById('attendanceTab');
        const leaveTab = document.getElementById('leaveTab');
        
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                const target = mutation.target;
                const isVisible = target.style.display !== 'none' && target.offsetParent !== null;
                
                if (target === attendanceTab && isVisible && !attendanceLoaded) {
                    loadAttendanceSummary(currentPersonId);
                    attendanceLoaded = true;
                } else if (target === leaveTab && isVisible && !leaveLoaded) {
                    loadLeaveList(currentPersonId);
                    leaveLoaded = true;
                }
            });
        });
        
        // 观察两个 tab 的 style 属性变化
        if (attendanceTab) {
            observer.observe(attendanceTab, { 
                attributes: true, 
                attributeFilter: ['style', 'class'],
                attributeOldValue: false
            });
        }
        if (leaveTab) {
            observer.observe(leaveTab, { 
                attributes: true, 
                attributeFilter: ['style', 'class'],
                attributeOldValue: false
            });
        }
        
        // 模态框关闭时断开观察
        const originalOnCloseEnd = modal.options.onCloseEnd;
        modal.options.onCloseEnd = function() {
            observer.disconnect();
            attendanceLoaded = false;
            leaveLoaded = false;
            if (originalOnCloseEnd) {
                originalOnCloseEnd.call(this);
            }
        };
        
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

async function loadAttendanceSummary(personId) {
    const container = document.getElementById('attendanceSummaryContent');
    container.innerHTML = '<p class="grey-text">加载中...</p>';
    
    try {
        const now = new Date();
        const year = now.getFullYear();
        const month = now.getMonth() + 1;
        const result = await fetchJSON(`/api/attendance/monthly-summary?person_id=${personId}&year=${year}&month=${month}`);
        const summary = result.data;
        
        const statusItems = Object.entries(summary.status_count || {}).map(([status, count]) => ({
            label: status,
            value: `${count} 天`
        }));
        
        container.innerHTML = renderInfoGrid(
            [
                { label: '统计月份', value: `${summary.year}年${summary.month}月` },
                { label: '出勤天数', value: summary.total_days },
                { label: '总工作时长', value: `${summary.total_work_hours.toFixed(1)} 小时` },
                { label: '总加班时长', value: `${summary.total_overtime_hours.toFixed(1)} 小时` },
                ...statusItems
            ],
            2
        );
    } catch (err) {
        container.innerHTML = `<p class="red-text">加载失败：${err.message}</p>`;
    }
}

async function loadLeaveList(personId) {
    const container = document.getElementById('leaveListContent');
    container.innerHTML = '<p class="grey-text">加载中...</p>';
    
    try {
        const now = new Date();
        const year = now.getFullYear();
        const month = now.getMonth() + 1;
        const startDate = `${year}-${String(month).padStart(2, '0')}-01`;
        const endDate = `${year}-${String(month).padStart(2, '0')}-${new Date(year, month, 0).getDate()}`;
        
        const result = await fetchJSON(`/api/leave?person_id=${personId}&start_date=${startDate}&end_date=${endDate}`);
        const records = result.data;
        
        if (!records || records.length === 0) {
            container.innerHTML = '<p class="grey-text">本月暂无请假记录</p>';
            return;
        }
        
        const rows = records.map(record => `
            <tr>
                <td>${record.leave_date}</td>
                <td>${record.leave_type}</td>
                <td>${record.hours} 小时</td>
                <td><span class="badge ${getStatusBadgeClass(record.status)}">${record.status}</span></td>
                <td>${record.reason || '-'}</td>
            </tr>
        `).join('');
        
        container.innerHTML = `
            <table class="striped responsive-table">
                <thead>
                    <tr>
                        <th>请假日期</th>
                        <th>请假类型</th>
                        <th>时长</th>
                        <th>状态</th>
                        <th>原因</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        `;
    } catch (err) {
        container.innerHTML = `<p class="red-text">加载失败：${err.message}</p>`;
    }
}

function getStatusBadgeClass(status) {
    const statusMap = {
        '待审批': 'orange',
        '已批准': 'green',
        '已拒绝': 'red'
    };
    return statusMap[status] || 'grey';
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

