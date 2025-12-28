document.addEventListener('DOMContentLoaded', function () {
    const modals = document.querySelectorAll('.modal');
    M.Modal.init(modals);
    const tabs = document.querySelectorAll('.tabs');
    M.Tabs.init(tabs);
    const selects = document.querySelectorAll('select');
    M.FormSelect.init(selects);

    // 打开创建项目模态框
    const openCreateBtn = document.getElementById('openCreateModal');
    if (openCreateBtn) {
        openCreateBtn.addEventListener('click', () => {
            const instance = M.Modal.getInstance(document.getElementById('createProjectModal'));
            instance.open();
        });
    }

    // 提交创建项目
    const submitCreateBtn = document.getElementById('submitCreateProject');
    if (submitCreateBtn) {
        submitCreateBtn.addEventListener('click', handleCreateProject);
    }

    // 提交编辑项目
    const submitEditBtn = document.getElementById('submitProjectEdit');
    if (submitEditBtn) {
        submitEditBtn.addEventListener('click', handleEditProject);
    }

    // 打开添加人员模态框
    const openAddPersonBtn = document.getElementById('openAddPersonModal');
    if (openAddPersonBtn) {
        openAddPersonBtn.addEventListener('click', () => {
            loadPersonSelect();
            const instance = M.Modal.getInstance(document.getElementById('addPersonModal'));
            instance.open();
        });
    }

    // 提交添加人员
    const submitAddPersonBtn = document.getElementById('submitAddPerson');
    if (submitAddPersonBtn) {
        submitAddPersonBtn.addEventListener('click', handleAddPerson);
    }

    loadProjects();
});

let currentProjectId = null;

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

async function loadProjects() {
    const container = document.getElementById('projectCards');
    try {
        const result = await fetchJSON('/api/projects');
        if (!result.data.length) {
            container.innerHTML = `
                <div class="col s12 center-align grey-text text-darken-1" style="margin-top: 40px;">
                    暂无项目，点击右上角按钮新建
                </div>`;
            return;
        }
        container.innerHTML = result.data.map(project => renderProjectCard(project)).join('');
        
        // 为每个卡片添加点击事件
        result.data.forEach(project => {
            const card = document.querySelector(`[data-project-id="${project.project_id}"]`);
            if (card) {
                card.addEventListener('click', () => openProjectDetail(project.project_id));
            }
        });
    } catch (err) {
        container.innerHTML = `<div class="col s12 red-text center-align">加载失败：${err.message}</div>`;
    }
}

function renderProjectCard(project) {
    const data = project.data || {};
    const contractName = data.contract_name || '-';
    const clientCompany = data.client_company || '-';
    const manager = project.current_manager || null;
    const managerName = manager ? manager.person_name : '-';
    const startDate = data.start_date || '-';
    const endDate = data.end_date || '-';
    
    return `
        <div class="col s12 m6 l4">
            <div class="card project-card hoverable" data-project-id="${project.project_id}" style="cursor: pointer;">
                <div class="card-content">
                    <span class="card-title">${contractName}</span>
                    <div class="project-info-item">
                        <span class="project-info-label">甲方单位：</span>
                        <span>${clientCompany}</span>
                    </div>
                    <div class="project-info-item">
                        <span class="project-info-label">项目经理：</span>
                        <span>${managerName}</span>
                    </div>
                    <div class="project-info-item">
                        <span class="project-info-label">起止时间：</span>
                        <span>${startDate} ~ ${endDate}</span>
                    </div>
                </div>
            </div>
        </div>
    `;
}

async function handleCreateProject() {
    const form = document.getElementById('createProjectForm');
    const formData = new FormData(form);
    const data = {};
    for (const [key, value] of formData.entries()) {
        if (value) {
            data[key] = value;
        }
    }

    if (!data.contract_name) {
        M.toast({html: '合同名称不能为空', classes: 'red'});
        return;
    }

    try {
        await fetchJSON('/api/projects', {
            method: 'POST',
            body: JSON.stringify({project: data}),
        });
        M.toast({html: '创建成功', classes: 'green'});
        const instance = M.Modal.getInstance(document.getElementById('createProjectModal'));
        form.reset();
        M.updateTextFields();
        instance.close();
        loadProjects();
    } catch (err) {
        M.toast({html: `创建失败：${err.message}`, classes: 'red'});
    }
}

async function openProjectDetail(projectId) {
    currentProjectId = projectId;
    try {
        const result = await fetchJSON(`/api/projects/${projectId}`);
        const project = result.data;
        const data = project.basic.data || {};
        
        // 先打开模态框，确保 DOM 元素已加载
        const modal = document.getElementById('projectDetailModal');
        const instance = M.Modal.getInstance(modal) || M.Modal.init(modal);
        instance.open();
        
        // 等待模态框打开后再填充表单
        setTimeout(() => {
            // 填充编辑表单（添加安全检查）
            const contractNameEl = document.getElementById('edit_contract_name');
            const startDateEl = document.getElementById('edit_start_date');
            const endDateEl = document.getElementById('edit_end_date');
            const clientCompanyEl = document.getElementById('edit_client_company');
            const clientDeptEl = document.getElementById('edit_client_department');
            const clientManagerEl = document.getElementById('edit_client_project_manager');
            
            if (contractNameEl) contractNameEl.value = data.contract_name || '';
            if (startDateEl) startDateEl.value = data.start_date || '';
            if (endDateEl) endDateEl.value = data.end_date || '';
            if (clientCompanyEl) clientCompanyEl.value = data.client_company || '';
            if (clientDeptEl) clientDeptEl.value = data.client_department || '';
            if (clientManagerEl) clientManagerEl.value = data.client_project_manager || '';
            
            // 触发 Materialize 标签动画更新（需要延迟一点确保值已设置）
            setTimeout(() => {
                M.updateTextFields();
            }, 50);
            
            // 更新标题
            const titleEl = document.getElementById('projectDetailTitle');
            if (titleEl) {
                titleEl.textContent = `项目详情 - ${data.contract_name || '未知项目'}`;
            }
            
            // 显示保存按钮
            const submitBtn = document.getElementById('submitProjectEdit');
            if (submitBtn) {
                submitBtn.style.display = 'inline-block';
            }
            
            // 切换到基本信息标签
            const tabsInstance = M.Tabs.getInstance(document.querySelector('.tabs'));
            if (tabsInstance) {
                tabsInstance.select('projectBasicTab');
            }
        }, 100);
        
        // 加载参与人员
        loadProjectPersons(projectId);
        
        // 加载历史记录
        loadProjectHistory(project);
    } catch (err) {
        M.toast({html: `加载失败：${err.message}`, classes: 'red'});
    }
}

async function handleEditProject() {
    if (!currentProjectId) return;
    
    const form = document.getElementById('projectEditForm');
    const formData = new FormData(form);
    const data = {};
    for (const [key, value] of formData.entries()) {
        if (value) {
            data[key] = value;
        }
    }

    if (!data.contract_name) {
        M.toast({html: '合同名称不能为空', classes: 'red'});
        return;
    }

    try {
        await fetchJSON(`/api/projects/${currentProjectId}`, {
            method: 'POST',
            body: JSON.stringify({project: data}),
        });
        M.toast({html: '保存成功', classes: 'green'});
        loadProjects();
        // 重新加载项目详情
        openProjectDetail(currentProjectId);
    } catch (err) {
        M.toast({html: `保存失败：${err.message}`, classes: 'red'});
    }
}

async function loadProjectPersons(projectId) {
    const container = document.getElementById('projectPersonsList');
    try {
        const result = await fetchJSON(`/api/projects/${projectId}/persons`);
        if (!result.data.length) {
            container.innerHTML = '<p class="grey-text center-align">暂无参与人员</p>';
            return;
        }
        
        // 获取所有人员信息以显示姓名
        const personsResult = await fetchJSON('/api/persons');
        const personsMap = {};
        personsResult.data.forEach(p => {
            personsMap[p.person_id] = p;
        });
        
        container.innerHTML = result.data.map(item => {
            const person = personsMap[item.person_id] || {};
            const data = item.data || {};
            const isManager = data.project_position === "项目经理";
            const positionClass = isManager ? "blue-text text-darken-2" : "grey-text";
            const cardStyle = isManager ? "padding: 12px; margin-bottom: 8px; border-left: 4px solid #1976d2;" : "padding: 12px; margin-bottom: 8px;";
            return `
                <div class="card-panel" style="${cardStyle}">
                    <div class="row valign-wrapper" style="margin-bottom: 0;">
                        <div class="col s10">
                            <strong>${person.name || `ID: ${item.person_id}`}</strong>
                            ${data.project_position ? `<span class="${positionClass}"><strong> - ${data.project_position}</strong></span>` : ''}
                            ${data.assessment_level ? `<span class="grey-text"> - 等级: ${data.assessment_level}</span>` : ''}
                            ${data.unit_price ? `<span class="grey-text"> - 单价: ¥${data.unit_price}</span>` : ''}
                            ${data.process_status ? `<span class="grey-text"> - 状态: ${data.process_status}</span>` : ''}
                        </div>
                        <div class="col s2 right-align">
                            <a href="#!" class="btn-flat btn-small" onclick="viewPersonProjectHistory(${item.person_id}, ${projectId})">
                                <i class="material-icons">history</i>
                            </a>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    } catch (err) {
        container.innerHTML = `<p class="red-text center-align">加载失败：${err.message}</p>`;
    }
}

async function loadProjectHistory(project) {
    const container = document.getElementById('projectHistoryList');
    const history = project.basic_history || [];
    
    if (!history.length) {
        container.innerHTML = '<p class="grey-text center-align">暂无历史记录</p>';
        return;
    }
    
    container.innerHTML = history.map(item => {
        const data = item.data || {};
        return `
            <div class="history-block">
                <div class="row" style="margin-bottom: 0;">
                    <div class="col s12">
                        <strong>版本 ${item.version}</strong>
                        <span class="grey-text right">${item.ts}</span>
                    </div>
                    <div class="col s12" style="margin-top: 8px;">
                        <div class="project-info-item">
                            <span class="project-info-label">合同名称：</span>
                            <span>${data.contract_name || '-'}</span>
                        </div>
                        ${data.start_date || data.end_date ? `
                        <div class="project-info-item">
                            <span class="project-info-label">起止时间：</span>
                            <span>${data.start_date || '-'} ~ ${data.end_date || '-'}</span>
                        </div>
                        ` : ''}
                        ${data.client_company ? `
                        <div class="project-info-item">
                            <span class="project-info-label">甲方单位：</span>
                            <span>${data.client_company}</span>
                        </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

async function loadPersonSelect() {
    const select = document.getElementById('personSelect');
    try {
        const result = await fetchJSON('/api/persons');
        select.innerHTML = '<option value="" disabled selected>请选择人员</option>' +
            result.data.map(p => 
                `<option value="${p.person_id}">${p.name || `ID: ${p.person_id}`}</option>`
            ).join('');
        M.FormSelect.init(select);
    } catch (err) {
        M.toast({html: `加载人员列表失败：${err.message}`, classes: 'red'});
    }
}

async function handleAddPerson() {
    if (!currentProjectId) {
        M.toast({html: '请先选择项目', classes: 'red'});
        return;
    }
    
    const form = document.getElementById('addPersonForm');
    const formData = new FormData(form);
    const personId = formData.get('person_id');
    
    if (!personId) {
        M.toast({html: '请选择人员', classes: 'red'});
        return;
    }
    
    const data = {
        project_id: parseInt(currentProjectId),
    };
    for (const [key, value] of formData.entries()) {
        if (key !== 'person_id' && value) {
            data[key] = value;
        }
    }
    
    try {
        await fetchJSON(`/api/persons/${personId}/projects`, {
            method: 'POST',
            body: JSON.stringify({project: data}),
        });
        M.toast({html: '添加成功', classes: 'green'});
        const instance = M.Modal.getInstance(document.getElementById('addPersonModal'));
        form.reset();
        M.updateTextFields();
        const selects = document.querySelectorAll('#addPersonModal select');
        M.FormSelect.init(selects);
        instance.close();
        loadProjectPersons(currentProjectId);
    } catch (err) {
        M.toast({html: `添加失败：${err.message}`, classes: 'red'});
    }
}

async function viewPersonProjectHistory(personId, projectId) {
    try {
        const result = await fetchJSON(`/api/persons/${personId}/projects/${projectId}/history`);
        const history = result.data || [];
        
        let historyHtml = '<h6>参与项目历史记录</h6>';
        if (history.length === 0) {
            historyHtml += '<p class="grey-text">暂无历史记录</p>';
        } else {
            historyHtml += history.map(item => {
                const data = item.data || {};
                return `
                    <div class="history-block">
                        <div class="row" style="margin-bottom: 0;">
                            <div class="col s12">
                                <strong>版本 ${item.version}</strong>
                                <span class="grey-text right">${item.ts}</span>
                            </div>
                            <div class="col s12" style="margin-top: 8px;">
                                ${data.project_position ? `
                                <div class="project-info-item">
                                    <span class="project-info-label">入项岗位：</span>
                                    <span>${data.project_position}</span>
                                </div>
                                ` : ''}
                                ${data.assessment_level ? `
                                <div class="project-info-item">
                                    <span class="project-info-label">评定等级：</span>
                                    <span>${data.assessment_level}</span>
                                </div>
                                ` : ''}
                                ${data.unit_price ? `
                                <div class="project-info-item">
                                    <span class="project-info-label">评定单价：</span>
                                    <span>¥${data.unit_price}</span>
                                </div>
                                ` : ''}
                                ${data.process_status ? `
                                <div class="project-info-item">
                                    <span class="project-info-label">流程状态：</span>
                                    <span>${data.process_status}</span>
                                </div>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        // 使用 Materialize 的模态框显示历史记录
        const modalHtml = `
            <div id="personProjectHistoryModal" class="modal">
                <div class="modal-content">
                    ${historyHtml}
                </div>
                <div class="modal-footer">
                    <a href="#!" class="modal-close waves-effect waves-grey btn-flat">关闭</a>
                </div>
            </div>
        `;
        
        // 移除旧的模态框（如果存在）
        const oldModal = document.getElementById('personProjectHistoryModal');
        if (oldModal) {
            oldModal.remove();
        }
        
        // 添加新模态框
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        const modal = document.getElementById('personProjectHistoryModal');
        const instance = M.Modal.init(modal, {
            onCloseEnd: function() {
                modal.remove();
            }
        });
        instance.open();
    } catch (err) {
        M.toast({html: `加载历史记录失败：${err.message}`, classes: 'red'});
    }
}

