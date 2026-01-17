// 项目人员分配关系图 - 第一部分：基础工具函数和全局变量
document.addEventListener('DOMContentLoaded', function () {
    initMaterialize();
    initEventListeners();
    loadRelationData();
});

// 全局数据
let personsData = [];
let projectsData = [];
let relations = []; // {person_id, project_id, data, ts}
let selectedPersonId = null;
let selectedProjectId = null;
let currentProjectId = null; // 用于项目详情模态框

// 初始化 Materialize 组件
function initMaterialize() {
    // 初始化所有模态框，但为特定模态框设置关闭回调
    const allModals = document.querySelectorAll('.modal');
    allModals.forEach(modal => {
        const modalId = modal.id;
        if (modalId === 'personProjectHistoryModal' || modalId === 'projectPersonsModal') {
            // 为这两个模态框设置关闭回调
            M.Modal.init(modal, {
                onCloseEnd: function() {
                    // 模态框关闭时，重新加载关系数据并更新连线
                    loadRelationData();
                }
            });
        } else {
            // 其他模态框正常初始化
            M.Modal.init(modal);
        }
    });
    M.Tabs.init(document.querySelectorAll('.tabs'));
    M.FormSelect.init(document.querySelectorAll('select'));
}

// 初始化事件监听器
function initEventListeners() {
    // 登记人员入项按钮
    const addPersonToProjectBtn = document.getElementById('addPersonToProjectBtn');
    if (addPersonToProjectBtn) {
        addPersonToProjectBtn.addEventListener('click', openAddPersonToProjectModal);
    }
    
    // 创建项目按钮
    const createProjectBtn = document.getElementById('createProjectBtn');
    if (createProjectBtn) {
        createProjectBtn.addEventListener('click', () => {
            const instance = M.Modal.getInstance(document.getElementById('createProjectModal'));
            instance.open();
        });
    }
    
    // 提交创建项目
    const submitCreateBtn = document.getElementById('submitCreateProject');
    if (submitCreateBtn) {
        submitCreateBtn.addEventListener('click', handleCreateProject);
    }
    
    // 分配项目按钮
    const assignBtn = document.getElementById('assignBtn');
    if (assignBtn) {
        assignBtn.addEventListener('click', showAssignModal);
    }
    
    // 提交分配
    const submitAssign = document.getElementById('submitAssign');
    if (submitAssign) {
        submitAssign.addEventListener('click', handleAssign);
    }
    
    // 项目详情相关
    const submitEditBtn = document.getElementById('submitProjectEdit');
    if (submitEditBtn) {
        submitEditBtn.addEventListener('click', handleEditProject);
    }
    
    const openAddPersonBtn = document.getElementById('openAddPersonModal');
    if (openAddPersonBtn) {
        openAddPersonBtn.addEventListener('click', () => {
            loadPersonSelect();
            const instance = M.Modal.getInstance(document.getElementById('addPersonModal'));
            instance.open();
        });
    }
    
    const submitAddPersonBtn = document.getElementById('submitAddPerson');
    if (submitAddPersonBtn) {
        submitAddPersonBtn.addEventListener('click', handleAddPerson);
    }
    
    const submitEditPersonBtn = document.getElementById('submitEditPerson');
    if (submitEditPersonBtn) {
        submitEditPersonBtn.addEventListener('click', handleEditPerson);
    }
    
    // 人员项目历史相关
    const submitAddProjectBtn = document.getElementById('submitAddProject');
    if (submitAddProjectBtn) {
        submitAddProjectBtn.addEventListener('click', handleAddProject);
    }
    
    // 监听项目选择变化，根据项目类型显示不同字段
    const addProjectSelect = document.getElementById('addProjectSelect');
    if (addProjectSelect) {
        addProjectSelect.addEventListener('change', handleAddProjectSelectChange);
    }
    
    const addAttendanceMethodSelect = document.getElementById('add_attendance_method');
    if (addAttendanceMethodSelect) {
        addAttendanceMethodSelect.addEventListener('change', handleAttendanceMethodChange);
    }
    
    // 项目人员相关
    const submitAddPersonToProjectBtn = document.getElementById('submitAddPersonToProject');
    if (submitAddPersonToProjectBtn) {
        submitAddPersonToProjectBtn.addEventListener('click', handleAddPersonToProject);
    }
    
    // 登记人员入项主表单
    const submitAddPersonToProjectMainBtn = document.getElementById('submitAddPersonToProjectMain');
    if (submitAddPersonToProjectMainBtn) {
        submitAddPersonToProjectMainBtn.addEventListener('click', handleAddPersonToProjectMain);
    }
    
    // 监听项目选择变化
    const addProjectToPersonMainSelect = document.getElementById('addProjectToPersonMainSelect');
    if (addProjectToPersonMainSelect) {
        addProjectToPersonMainSelect.addEventListener('change', handleAddProjectToPersonMainSelectChange);
    }
    
    // 监听打卡方式变化
    const addPersonToProjectAttendanceMethod = document.getElementById('addPersonToProject_attendance_method');
    if (addPersonToProjectAttendanceMethod) {
        addPersonToProjectAttendanceMethod.addEventListener('change', handleAddPersonToProjectAttendanceMethodChange);
    }
    
}

// 工具函数：fetchJSON
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

// 第二部分：数据加载函数
async function loadRelationData() {
    try {
        // 并行加载所有数据
        const [personsResult, projectsResult] = await Promise.all([
            fetchJSON('/api/persons'),
            fetchJSON('/api/projects')
        ]);
        
        personsData = personsResult.data || [];
        projectsData = projectsResult.data || [];
        
        console.log(`加载完成：${personsData.length} 个人员，${projectsData.length} 个项目`);
        
        // 加载所有关系
        await loadAllRelations();
        
        // 渲染矩阵视图
        renderMatrixView();
    } catch (err) {
        console.error('加载数据失败:', err);
        M.toast({html: '加载失败：' + err.message, classes: 'red'});
    }
}

async function loadAllRelations() {
    relations = [];
    
    // 为每个人员加载参与的项目（只加载活跃关系，排除已退出的）
    for (const person of personsData) {
        try {
            const result = await fetchJSON(`/api/persons/${person.person_id}/projects`);
            if (result.data && result.data.length > 0) {
                result.data.forEach(project => {
                    // 过滤已退出的关系
                    if (project.data?.project_position === '已退出') {
                        return;
                    }
                    relations.push({
                        person_id: Number(person.person_id),
                        project_id: Number(project.project_id),
                        data: project.data || {},
                        ts: project.ts
                    });
                });
            }
        } catch (err) {
            console.warn(`加载人员 ${person.person_id} 的项目失败:`, err);
        }
    }
    
    console.log(`加载完成：共 ${relations.length} 条人员-项目关系`);
}

function renderMatrixView() {
    
    const thead = document.getElementById('matrixTableHead');
    const tbody = document.getElementById('matrixTableBody');
    
    if (!thead || !tbody) return;
    
    // 获取过滤后的人员和项目
    const filteredPersons = getFilteredPersons();
    const filteredProjects = getFilteredProjects();
    
    console.log(`渲染矩阵视图：${filteredPersons.length} 个人员，${filteredProjects.length} 个项目，${relations.length} 条关系`);
    if (relations.length > 0) {
        console.log('关系示例:', relations.slice(0, 3));
    }
    
    // 渲染表头
    thead.innerHTML = `
        <tr>
            <th>人员</th>
            ${filteredProjects.map(project => {
                const projectName = project.data?.internal_project_name || project.data?.contract_name || `项目 #${project.project_id}`;
                return `<th title="${projectName}" 
                            style="cursor: pointer;" 
                            onclick="selectProject(${project.project_id})">${projectName}</th>`;
            }).join('')}
        </tr>
    `;
    
    // 渲染表格内容
    tbody.innerHTML = filteredPersons.map(person => {
        const personName = person.name || `ID: ${person.person_id}`;
        const personCompany = person.current_company || '未分配';
        
        return `
            <tr>
                <td style="cursor: pointer;" onclick="selectPerson(${person.person_id})">
                    <div style="display: flex; align-items: center;">
                        <img src="${person.avatar || 'https://api.dicebear.com/7.x/micah/svg?seed=' + (person.name || 'user')}" 
                             class="person-avatar" 
                             alt="${person.name}"
                             onerror="this.src='https://api.dicebear.com/7.x/micah/svg?seed=user'"
                             style="width: 24px; height: 24px; margin-right: 8px;">
                        <div>
                            <div style="font-weight: 500;">${personName}</div>
                            <div style="font-size: 11px; color: #757575;">${personCompany}</div>
                        </div>
                    </div>
                </td>
                ${filteredProjects.map(project => {
                    // 确保类型一致（都转为数字）
                    const personId = Number(person.person_id);
                    const projectId = Number(project.project_id);
                    const relation = relations.find(r => 
                        Number(r.person_id) === personId && 
                        Number(r.project_id) === projectId
                    );
                    
                    if (relation) {
                        const position = relation.data?.project_position || '';
                        const isManager = position === '项目经理';
                        const cellClass = isManager ? 'matrix-cell has-relation manager' : 'matrix-cell has-relation';
                        
                        return `
                            <td class="${cellClass}" 
                                title="${isManager ? '项目经理' : position}">
                                <div class="cell-content">
                                    ${isManager ? '<span style="font-size: 16px;">👑</span>' : '<span>✓</span>'}
                                    ${position ? `<span class="position">${position}</span>` : ''}
                                </div>
                            </td>
                        `;
                    }
                    return '<td class="matrix-cell no-relation">-</td>';
                }).join('')}
            </tr>
        `;
    }).join('');
}


function selectPerson(personId) {
    selectedPersonId = personId;
    selectedProjectId = null;
    const assignBtn = document.getElementById('assignBtn');
    if (assignBtn) {
        assignBtn.style.display = 'inline-block';
    }
    
    // 打开人员项目历史模态框
    openPersonProjectHistoryModal(personId);
    
    const person = personsData.find(p => p.person_id === personId);
    const assignPersonName = document.getElementById('assignPersonName');
    if (assignPersonName) {
        assignPersonName.textContent = person?.name || `ID: ${personId}`;
    }
    
    // 重新渲染矩阵视图
    renderMatrixView();
}

function selectProject(projectId) {
    selectedProjectId = projectId;
    selectedPersonId = null;
    const assignBtn = document.getElementById('assignBtn');
    if (assignBtn) {
        assignBtn.style.display = 'none';
    }
    
    // 打开项目人员模态框
    openProjectPersonsModal(projectId);
    
    // 重新渲染矩阵视图
    renderMatrixView();
}

// 第五部分：筛选和工具函数
function getFilteredPersons() {
    // 返回所有人员（不再筛选）
    return [...personsData];
}

function getFilteredProjects() {
    // 返回所有项目（不再筛选）
    return [...projectsData];
}


// 第六部分：项目创建和编辑
async function handleCreateProject() {
    const form = document.getElementById('createProjectForm');
    if (!form) return;
    
    const formData = new FormData(form);
    const data = {};
    for (const [key, value] of formData.entries()) {
        if (value) {
            data[key] = value;
        }
    }

    if (!data.project_type) {
        M.toast({html: '项目类型不能为空', classes: 'red'});
        return;
    }
    if (!data.internal_project_name) {
        M.toast({html: '项目名称不能为空', classes: 'red'});
        return;
    }
    if (!data.internal_department) {
        M.toast({html: '归属部门不能为空', classes: 'red'});
        return;
    }
    if (!data.internal_project_manager) {
        M.toast({html: '项目经理不能为空', classes: 'red'});
        return;
    }
    if (!data.external_project_name) {
        M.toast({html: '甲方项目名称不能为空', classes: 'red'});
        return;
    }
    if (!data.external_company) {
        M.toast({html: '甲方单位不能为空', classes: 'red'});
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
        M.FormSelect.init(document.querySelectorAll('#createProjectModal select'));
        instance.close();
        loadRelationData();
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
        
        const modal = document.getElementById('projectDetailModal');
        const instance = M.Modal.getInstance(modal) || M.Modal.init(modal);
        instance.open();
        
        setTimeout(() => {
            const projectTypeEl = document.getElementById('edit_project_type');
            const internalProjectNameEl = document.getElementById('edit_internal_project_name');
            const internalDeptEl = document.getElementById('edit_internal_department');
            const internalManagerEl = document.getElementById('edit_internal_project_manager');
            const externalProjectNameEl = document.getElementById('edit_external_project_name');
            const externalCompanyEl = document.getElementById('edit_external_company');
            const externalDeptEl = document.getElementById('edit_external_department');
            const externalManagerEl = document.getElementById('edit_external_manager');
            const externalOrderNumberEl = document.getElementById('edit_external_order_number');
            const executionStartDateEl = document.getElementById('edit_execution_start_date');
            const executionEndDateEl = document.getElementById('edit_execution_end_date');
            
            if (projectTypeEl) projectTypeEl.value = data.project_type || '';
            if (internalProjectNameEl) internalProjectNameEl.value = data.internal_project_name || '';
            if (internalDeptEl) internalDeptEl.value = data.internal_department || '';
            if (internalManagerEl) internalManagerEl.value = data.internal_project_manager || '';
            if (externalProjectNameEl) externalProjectNameEl.value = data.external_project_name || '';
            if (externalCompanyEl) externalCompanyEl.value = data.external_company || '';
            if (externalDeptEl) externalDeptEl.value = data.external_department || '';
            if (externalManagerEl) externalManagerEl.value = data.external_manager || '';
            if (externalOrderNumberEl) externalOrderNumberEl.value = data.external_order_number || '';
            if (executionStartDateEl) executionStartDateEl.value = data.execution_start_date || '';
            if (executionEndDateEl) executionEndDateEl.value = data.execution_end_date || '';
            
            setTimeout(() => {
                M.updateTextFields();
                M.FormSelect.init(document.querySelectorAll('#projectDetailModal select'));
            }, 50);
            
            const titleEl = document.getElementById('projectDetailTitle');
            if (titleEl) {
                titleEl.textContent = `项目详情 - ${data.internal_project_name || '未知项目'}`;
            }
            
            const submitBtn = document.getElementById('submitProjectEdit');
            if (submitBtn) {
                submitBtn.style.display = 'inline-block';
            }
            
            const tabsInstance = M.Tabs.getInstance(document.querySelector('.tabs'));
            if (tabsInstance) {
                tabsInstance.select('projectBasicTab');
            }
        }, 100);
        
        loadProjectPersons(projectId);
        loadProjectHistory(project);
    } catch (err) {
        M.toast({html: `加载失败：${err.message}`, classes: 'red'});
    }
}

async function handleEditProject() {
    if (!currentProjectId) return;
    
    const form = document.getElementById('projectEditForm');
    if (!form) return;
    
    const formData = new FormData(form);
    const data = {};
    for (const [key, value] of formData.entries()) {
        if (value) {
            data[key] = value;
        }
    }

    if (!data.project_type) {
        M.toast({html: '项目类型不能为空', classes: 'red'});
        return;
    }
    if (!data.internal_project_name) {
        M.toast({html: '项目名称不能为空', classes: 'red'});
        return;
    }
    if (!data.internal_department) {
        M.toast({html: '归属部门不能为空', classes: 'red'});
        return;
    }
    if (!data.internal_project_manager) {
        M.toast({html: '项目经理不能为空', classes: 'red'});
        return;
    }
    if (!data.external_project_name) {
        M.toast({html: '甲方项目名称不能为空', classes: 'red'});
        return;
    }
    if (!data.external_company) {
        M.toast({html: '甲方单位不能为空', classes: 'red'});
        return;
    }

    try {
        await fetchJSON(`/api/projects/${currentProjectId}`, {
            method: 'POST',
            body: JSON.stringify({project: data}),
        });
        M.toast({html: '保存成功', classes: 'green'});
        loadRelationData();
        openProjectDetail(currentProjectId);
    } catch (err) {
        M.toast({html: `保存失败：${err.message}`, classes: 'red'});
    }
}

// 第七部分：人员分配相关
async function showAssignModal() {
    if (!selectedPersonId) {
        M.toast({html: '请先选择人员', classes: 'red'});
        return;
    }
    
    const assignProjectSelect = document.getElementById('assignProjectSelect');
    if (!assignProjectSelect) return;
    
    // 加载项目列表
    assignProjectSelect.innerHTML = '<option value="" disabled selected>请选择项目</option>' +
        projectsData.map(p => 
            `<option value="${p.project_id}">${p.data?.internal_project_name || p.data?.contract_name || `项目 #${p.project_id}`}</option>`
        ).join('');
    M.FormSelect.init(assignProjectSelect);
    
    const instance = M.Modal.getInstance(document.getElementById('assignModal'));
    instance.open();
}

async function handleAssign() {
    if (!selectedPersonId) {
        M.toast({html: '请先选择人员', classes: 'red'});
        return;
    }
    
    const form = document.getElementById('assignForm');
    if (!form) return;
    
    const formData = new FormData(form);
    const projectId = formData.get('project_id');
    
    if (!projectId) {
        M.toast({html: '请选择项目', classes: 'red'});
        return;
    }
    
    const data = {
        project_id: parseInt(projectId),
    };
    for (const [key, value] of formData.entries()) {
        if (key !== 'project_id' && value) {
            data[key] = value;
        }
    }
    
    try {
        await fetchJSON(`/api/persons/${selectedPersonId}/projects`, {
            method: 'POST',
            body: JSON.stringify({project: data}),
        });
        M.toast({html: '分配成功', classes: 'green'});
        const instance = M.Modal.getInstance(document.getElementById('assignModal'));
        form.reset();
        M.updateTextFields();
        const selects = document.querySelectorAll('#assignModal select');
        M.FormSelect.init(selects);
        instance.close();
        loadRelationData();
    } catch (err) {
        M.toast({html: `分配失败：${err.message}`, classes: 'red'});
    }
}

// 项目详情模态框中的添加人员
async function loadPersonSelect() {
    const select = document.getElementById('personSelect');
    if (!select) return;
    
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
    if (!form) return;
    
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
        loadRelationData();
    } catch (err) {
        M.toast({html: `添加失败：${err.message}`, classes: 'red'});
    }
}

// 第八部分：编辑和移除人员
let currentEditPersonId = null;
let currentEditProjectId = null;

async function editPersonInProject(personId, projectId) {
    currentEditPersonId = personId;
    currentEditProjectId = projectId;
    
    try {
        const personResult = await fetchJSON(`/api/persons/${personId}`);
        const personName = personResult.data.basic.data.name || `ID: ${personId}`;
        
        const projectPersonsResult = await fetchJSON(`/api/projects/${projectId}/persons`);
        const personData = projectPersonsResult.data.find(p => p.person_id === personId);
        const data = personData ? personData.data : {};
        
        document.getElementById('edit_person_name').value = personName;
        document.getElementById('edit_project_position').value = data.project_position || '';
        document.getElementById('edit_material_submit_date').value = data.material_submit_date || '';
        document.getElementById('edit_assessment_level').value = data.assessment_level || '';
        document.getElementById('edit_unit_price').value = data.unit_price || '';
        document.getElementById('edit_process_status').value = data.process_status || '';
        
        M.updateTextFields();
        
        const instance = M.Modal.getInstance(document.getElementById('editPersonModal'));
        instance.open();
    } catch (err) {
        M.toast({html: `加载失败：${err.message}`, classes: 'red'});
    }
}

async function handleEditPerson() {
    if (!currentEditPersonId || !currentEditProjectId) {
        M.toast({html: '请先选择人员和项目', classes: 'red'});
        return;
    }
    
    const form = document.getElementById('editPersonForm');
    if (!form) return;
    
    const formData = new FormData(form);
    
    const data = {
        project_id: parseInt(currentEditProjectId),
    };
    for (const [key, value] of formData.entries()) {
        if (value) {
            data[key] = value;
        }
    }
    
    try {
        await fetchJSON(`/api/persons/${currentEditPersonId}/projects`, {
            method: 'POST',
            body: JSON.stringify({project: data}),
        });
        M.toast({html: '更新成功', classes: 'green'});
        const instance = M.Modal.getInstance(document.getElementById('editPersonModal'));
        instance.close();
        loadProjectPersons(currentEditProjectId);
        loadRelationData();
    } catch (err) {
        M.toast({html: `更新失败：${err.message}`, classes: 'red'});
    }
}

async function removePersonFromProject(personId, projectId) {
    if (!confirm('确定要移除该人员吗？这将记录一条退出项目的状态。')) {
        return;
    }
    
    try {
        await fetchJSON(`/api/persons/${personId}/projects`, {
            method: 'POST',
            body: JSON.stringify({
                project: {
                    project_id: projectId,
                    project_position: '已退出',
                    process_status: '已退出项目'
                }
            }),
        });
        M.toast({html: '移除成功', classes: 'green'});
        loadProjectPersons(projectId);
        loadRelationData();
    } catch (err) {
        M.toast({html: `移除失败：${err.message}`, classes: 'red'});
    }
}

async function loadProjectPersons(projectId) {
    const container = document.getElementById('projectPersonsList');
    if (!container) return;
    
    try {
        const result = await fetchJSON(`/api/projects/${projectId}/persons`);
        if (!result.data.length) {
            container.innerHTML = '<p class="grey-text center-align">暂无参与人员</p>';
            return;
        }
        
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
                        <div class="col s8">
                            <strong>${person.name || `ID: ${item.person_id}`}</strong>
                            ${data.project_position ? `<span class="${positionClass}"><strong> - ${data.project_position}</strong></span>` : ''}
                            ${data.assessment_level ? `<span class="grey-text"> - 等级: ${data.assessment_level}</span>` : ''}
                            ${data.unit_price ? `<span class="grey-text"> - 单价: ¥${data.unit_price}</span>` : ''}
                            ${data.process_status ? `<span class="grey-text"> - 状态: ${data.process_status}</span>` : ''}
                        </div>
                        <div class="col s4 right-align">
                            <a href="#!" class="btn-flat btn-small" onclick="editPersonInProject(${item.person_id}, ${projectId})" title="编辑">
                                <i class="material-icons">edit</i>
                            </a>
                            <a href="#!" class="btn-flat btn-small" onclick="viewPersonProjectHistory(${item.person_id}, ${projectId})" title="历史">
                                <i class="material-icons">history</i>
                            </a>
                            <a href="#!" class="btn-flat btn-small red-text" onclick="removePersonFromProject(${item.person_id}, ${projectId})" title="移除">
                                <i class="material-icons">delete</i>
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
    if (!container) return;
    
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
                            <span>${data.internal_project_name || data.contract_name || '-'}</span>
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
        
        const oldModal = document.getElementById('personProjectHistoryModal');
        if (oldModal) {
            oldModal.remove();
        }
        
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


// 第八部分：人员项目历史相关
async function openPersonProjectHistoryModal(personId) {
    const modal = document.getElementById('personProjectHistoryModal');
    const title = document.getElementById('personProjectHistoryTitle');
    const person = personsData.find(p => p.person_id === personId);
    
    if (title) {
        title.textContent = `${person?.name || `ID: ${personId}`} - 项目参与历史`;
    }
    
    // 打开模态框（关闭回调已在 initMaterialize 中设置）
    let instance = M.Modal.getInstance(modal);
    if (!instance) {
        instance = M.Modal.init(modal, {
            onCloseEnd: function() {
                loadRelationData();
            }
        });
    }
    instance.open();
    
    // 加载数据
    await loadPersonProjectHistory(personId);
}

async function loadPersonProjectHistory(personId) {
    const content = document.getElementById('personProjectHistoryContent');
    const addFormSection = document.getElementById('addProjectFormSection');
    
    if (!content) return;
    
    try {
        // 获取人员参与的所有项目（最新状态）
        const result = await fetchJSON(`/api/persons/${personId}/projects`);
        const projects = result.data || [];
        
        // 分离当前参与和已退出的项目
        const activeProjects = projects.filter(p => p.data?.project_position !== '已退出');
        const exitedProjects = projects.filter(p => p.data?.project_position === '已退出');
        
        // 显示/隐藏添加项目表单
        if (addFormSection) {
            if (activeProjects.length === 0) {
                addFormSection.style.display = 'block';
                await loadProjectSelectForAdd(personId);
            } else {
                addFormSection.style.display = 'none';
            }
        }
        
        // 渲染项目历史记录
        let html = '';
        
        if (activeProjects.length > 0) {
            html += '<h6 style="margin-top: 0;">当前参与的项目</h6>';
            html += await renderProjectHistoryList(personId, activeProjects, true);
        }
        
        if (exitedProjects.length > 0) {
            html += '<h6 style="margin-top: 30px;">已退出的项目</h6>';
            html += await renderProjectHistoryList(personId, exitedProjects, false);
        }
        
        if (projects.length === 0) {
            html = '<div class="center-align grey-text" style="padding: 40px;">暂无项目参与记录</div>';
        }
        
        content.innerHTML = html;
        
        // 绑定退出项目按钮事件
        content.querySelectorAll('.exit-project-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const personId = parseInt(this.getAttribute('data-person-id'));
                const projectId = parseInt(this.getAttribute('data-project-id'));
                handleExitProject(personId, projectId);
            });
        });
        
    } catch (err) {
        content.innerHTML = `<div class="red-text center-align" style="padding: 40px;">加载失败：${err.message}</div>`;
        console.error('加载人员项目历史失败:', err);
    }
}

async function renderProjectHistoryList(personId, projects, isActive) {
    let html = '<div class="collection">';
    
    for (const project of projects) {
        const projectId = project.project_id;
        const projectData = project.data || {};
        
        // 获取项目基本信息
        const projectInfo = projectsData.find(p => p.project_id === projectId);
        const projectName = projectInfo?.data?.internal_project_name || projectInfo?.data?.contract_name || `项目 #${projectId}`;
        
        // 获取该项目的详细历史记录
        let historyHtml = '';
        try {
            const historyResult = await fetchJSON(`/api/persons/${personId}/projects/${projectId}/history`);
            const history = historyResult.data || [];
            
            if (history.length > 0) {
                historyHtml = '<div class="history-list" style="margin-top: 10px; padding-left: 20px;">';
                history.forEach((item, index) => {
                    const data = item.data || {};
                    historyHtml += `
                        <div class="history-item" style="padding: 8px 0; border-bottom: 1px solid #e0e0e0;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <strong>版本 ${item.version}</strong>
                                    <span class="grey-text" style="margin-left: 10px; font-size: 12px;">${item.ts}</span>
                                </div>
                            </div>
                            <div style="margin-top: 5px; font-size: 13px; color: #757575;">
                                ${data.project_position ? `<span>岗位: ${data.project_position}</span>` : ''}
                                ${data.assessment_level ? `<span style="margin-left: 15px;">等级: ${data.assessment_level}</span>` : ''}
                                ${data.unit_price ? `<span style="margin-left: 15px;">单价: ¥${data.unit_price}</span>` : ''}
                                ${data.process_status ? `<span style="margin-left: 15px;">状态: ${data.process_status}</span>` : ''}
                            </div>
                        </div>
                    `;
                });
                historyHtml += '</div>';
            }
        } catch (err) {
            console.error('加载项目历史失败:', err);
        }
        
        html += `
            <div class="collection-item" style="padding: 15px;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div style="flex: 1;">
                        <strong>${projectName}</strong>
                        <div style="margin-top: 5px; font-size: 13px; color: #757575;">
                            ${projectData.project_position ? `<span>岗位: ${projectData.project_position}</span>` : ''}
                            ${projectData.assessment_level ? `<span style="margin-left: 15px;">等级: ${projectData.assessment_level}</span>` : ''}
                            ${projectData.unit_price ? `<span style="margin-left: 15px;">单价: ¥${projectData.unit_price}</span>` : ''}
                        </div>
                        ${historyHtml}
                    </div>
                    ${isActive ? `
                        <div style="margin-left: 15px;">
                            <a href="#!" class="btn-small waves-effect waves-light red exit-project-btn" 
                               data-person-id="${personId}" data-project-id="${projectId}">
                                <i class="material-icons left" style="font-size: 16px;">exit_to_app</i>退出项目
                            </a>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }
    
    html += '</div>';
    return html;
}

async function handleExitProject(personId, projectId) {
    if (!confirm('确定要退出该项目吗？')) {
        return;
    }
    
    try {
        // 获取当前项目状态
        const currentResult = await fetchJSON(`/api/persons/${personId}/projects`);
        const projects = currentResult.data || [];
        const currentProject = projects.find(p => p.project_id === projectId);
        
        if (!currentProject) {
            M.toast({html: '未找到项目信息', classes: 'red'});
            return;
        }
        
        // 复制当前数据，设置 project_position 为 "已退出"
        const exitData = {
            ...currentProject.data,
            project_position: '已退出'
        };
        
        // 提交退出项目
        await fetchJSON(`/api/persons/${personId}/projects`, {
            method: 'POST',
            body: JSON.stringify({project: {project_id: projectId, ...exitData}}),
        });
        
        M.toast({html: '已退出项目', classes: 'green'});
        
        // 重新加载数据
        await loadPersonProjectHistory(personId);
        
        // 刷新关系图
        loadRelationData();
        
    } catch (err) {
        M.toast({html: `退出项目失败：${err.message}`, classes: 'red'});
        console.error('退出项目失败:', err);
    }
}

async function loadProjectSelectForAdd(personId) {
    const select = document.getElementById('addProjectSelect');
    if (!select) return;
    
    try {
        // 获取人员已参与的项目ID（包括已退出的）
        const personProjectsResult = await fetchJSON(`/api/persons/${personId}/projects`);
        const personProjects = personProjectsResult.data || [];
        const participatedProjectIds = new Set(personProjects.map(p => p.project_id));
        
        // 过滤掉已参与的项目
        const availableProjects = projectsData.filter(p => !participatedProjectIds.has(p.project_id));
        
        select.innerHTML = '<option value="" disabled selected>请选择项目</option>' +
            availableProjects.map(p => 
                `<option value="${p.project_id}">${p.data?.internal_project_name || p.data?.contract_name || `项目 #${p.project_id}`}</option>`
            ).join('');
        
        M.FormSelect.init(select);
    } catch (err) {
        M.toast({html: `加载项目列表失败：${err.message}`, classes: 'red'});
        console.error('加载项目列表失败:', err);
    }
}

async function handleAddProject() {
    const form = document.getElementById('addProjectForm');
    if (!form) return;
    
    const formData = new FormData(form);
    const projectId = formData.get('project_id');
    
    if (!projectId) {
        M.toast({html: '请选择项目', classes: 'red'});
        return;
    }
    
    if (!selectedPersonId) {
        M.toast({html: '未选择人员', classes: 'red'});
        return;
    }
    
    const data = {
        project_id: parseInt(projectId),
    };
    
    for (const [key, value] of formData.entries()) {
        if (key !== 'project_id' && value) {
            data[key] = value;
        }
    }
    
    try {
        await fetchJSON(`/api/persons/${selectedPersonId}/projects`, {
            method: 'POST',
            body: JSON.stringify({project: data}),
        });
        
        M.toast({html: '添加成功', classes: 'green'});
        
        // 重置表单
        form.reset();
        M.updateTextFields();
        const selects = document.querySelectorAll('#addProjectForm select');
        M.FormSelect.init(selects);
        
        // 重新加载数据
        await loadPersonProjectHistory(selectedPersonId);
        
        // 刷新关系图
        loadRelationData();
        
    } catch (err) {
        M.toast({html: `添加失败：${err.message}`, classes: 'red'});
        console.error('添加参与项目失败:', err);
    }
}

// 第九部分：项目人员管理相关
async function openProjectPersonsModal(projectId) {
    const modal = document.getElementById('projectPersonsModal');
    const title = document.getElementById('projectPersonsModalTitle');
    const project = projectsData.find(p => p.project_id === projectId);
    
    if (title) {
        const projectName = project?.data?.internal_project_name || project?.data?.contract_name || `项目 #${projectId}`;
        title.textContent = `${projectName} - 参与人员`;
    }
    
    // 设置当前项目ID
    currentProjectId = projectId;
    
    // 打开模态框（关闭回调已在 initMaterialize 中设置）
    let instance = M.Modal.getInstance(modal);
    if (!instance) {
        instance = M.Modal.init(modal, {
            onCloseEnd: function() {
                loadRelationData();
            }
        });
    }
    instance.open();
    
    // 加载数据
    await loadProjectPersonsTable(projectId);
    await loadPersonSelectForProject(projectId);
}

async function loadProjectPersonsTable(projectId) {
    const tbody = document.getElementById('projectPersonsTableBody');
    if (!tbody) return;
    
    try {
        // 获取项目参与的所有人员（当前参与，排除已退出）
        const result = await fetchJSON(`/api/projects/${projectId}/persons`);
        const projectPersons = result.data || [];
        
        // 获取所有人员信息用于显示姓名和公司
        const personsResult = await fetchJSON('/api/persons');
        const personsMap = {};
        personsResult.data.forEach(p => {
            personsMap[p.person_id] = p;
        });
        
        if (projectPersons.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="center-align grey-text">暂无参与人员</td></tr>';
            return;
        }
        
        // 渲染表格
        tbody.innerHTML = projectPersons.map(item => {
            const person = personsMap[item.person_id] || {};
            const data = item.data || {};
            
            return `
                <tr>
                    <td>${person.name || `ID: ${item.person_id}`}</td>
                    <td>${person.current_company || '-'}</td>
                    <td>${data.project_position || '-'}</td>
                    <td>${data.assessment_level || '-'}</td>
                    <td>${data.unit_price ? `¥${data.unit_price}` : '-'}</td>
                    <td>${data.process_status || '-'}</td>
                    <td>
                        <a href="#!" class="btn-small waves-effect waves-light red release-person-btn" 
                           data-person-id="${item.person_id}" data-project-id="${projectId}">
                            <i class="material-icons left" style="font-size: 16px;">exit_to_app</i>释放
                        </a>
                    </td>
                </tr>
            `;
        }).join('');
        
        // 绑定释放按钮事件
        tbody.querySelectorAll('.release-person-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const personId = parseInt(this.getAttribute('data-person-id'));
                const projId = parseInt(this.getAttribute('data-project-id'));
                handleReleasePerson(personId, projId);
            });
        });
        
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" class="center-align red-text">加载失败：${err.message}</td></tr>`;
        console.error('加载项目人员失败:', err);
    }
}

async function handleReleasePerson(personId, projectId) {
    if (!confirm('确定要释放该人员吗？')) {
        return;
    }
    
    try {
        // 获取当前人员在该项目中的状态
        const currentResult = await fetchJSON(`/api/persons/${personId}/projects`);
        const projects = currentResult.data || [];
        const currentProject = projects.find(p => p.project_id === projectId);
        
        if (!currentProject) {
            M.toast({html: '未找到项目信息', classes: 'red'});
            return;
        }
        
        // 复制当前数据，设置 project_position 为 "已退出"
        const exitData = {
            ...currentProject.data,
            project_position: '已退出'
        };
        
        // 提交退出项目
        await fetchJSON(`/api/persons/${personId}/projects`, {
            method: 'POST',
            body: JSON.stringify({project: {project_id: projectId, ...exitData}}),
        });
        
        M.toast({html: '已释放人员', classes: 'green'});
        
        // 重新加载数据
        await loadProjectPersonsTable(projectId);
        await loadPersonSelectForProject(projectId);
        
        // 刷新关系图
        loadRelationData();
        
    } catch (err) {
        M.toast({html: `释放人员失败：${err.message}`, classes: 'red'});
        console.error('释放人员失败:', err);
    }
}

async function loadPersonSelectForProject(projectId) {
    const select = document.getElementById('addPersonToProjectSelect');
    if (!select) return;
    
    try {
        // 获取项目已参与的所有人员ID（包括已退出的）
        // 从 relations 中获取，relations 在 loadAllRelations 中加载了所有人员的所有项目
        const participatedPersonIds = new Set(
            relations.filter(r => r.project_id === projectId).map(r => r.person_id)
        );
        
        // 过滤掉已参与的人员
        const availablePersons = personsData.filter(p => !participatedPersonIds.has(p.person_id));
        
        if (availablePersons.length === 0) {
            select.innerHTML = '<option value="" disabled>所有人员已参与该项目</option>';
        } else {
            select.innerHTML = '<option value="" disabled selected>请选择人员</option>' +
                availablePersons.map(p => 
                    `<option value="${p.person_id}">${p.name || `ID: ${p.person_id}`} ${p.current_company ? `(${p.current_company})` : ''}</option>`
                ).join('');
        }
        
        M.FormSelect.init(select);
    } catch (err) {
        M.toast({html: `加载人员列表失败：${err.message}`, classes: 'red'});
        console.error('加载人员列表失败:', err);
    }
}

async function handleAddPersonToProject() {
    const form = document.getElementById('addPersonToProjectForm');
    if (!form) return;
    
    const formData = new FormData(form);
    const personId = formData.get('person_id');
    
    if (!personId) {
        M.toast({html: '请选择人员', classes: 'red'});
        return;
    }
    
    if (!currentProjectId) {
        M.toast({html: '未选择项目', classes: 'red'});
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
        
        // 重置表单
        form.reset();
        M.updateTextFields();
        const selects = document.querySelectorAll('#addPersonToProjectForm select');
        M.FormSelect.init(selects);
        
        // 重新加载数据
        await loadProjectPersonsTable(currentProjectId);
        await loadPersonSelectForProject(currentProjectId);
        
        // 刷新关系图
        loadRelationData();
        
    } catch (err) {
        M.toast({html: `添加失败：${err.message}`, classes: 'red'});
        console.error('添加人员到项目失败:', err);
    }
}

// 打开登记人员入项模态框
async function openAddPersonToProjectModal() {
    try {
        // 加载人员和项目列表
        const [personsResult, projectsResult] = await Promise.all([
            fetchJSON('/api/persons'),
            fetchJSON('/api/projects')
        ]);
        
        const persons = personsResult.data || [];
        const projects = projectsResult.data || [];
        
        // 填充人员下拉框
        const personSelect = document.getElementById('addPersonToProjectMainSelect');
        if (personSelect) {
            let personOptions = '<option value="" disabled selected>请选择人员</option>';
            persons.forEach(person => {
                const name = person.name || `ID: ${person.person_id}`;
                personOptions += `<option value="${person.person_id}">${name}</option>`;
            });
            personSelect.innerHTML = personOptions;
        }
        
        // 填充项目下拉框
        const projectSelect = document.getElementById('addProjectToPersonMainSelect');
        if (projectSelect) {
            let projectOptions = '<option value="" disabled selected>请选择项目</option>';
            projects.forEach(project => {
                const projectName = project.data?.internal_project_name || `项目 ${project.project_id}`;
                projectOptions += `<option value="${project.project_id}">${projectName}</option>`;
            });
            projectSelect.innerHTML = projectOptions;
        }
        
        // 重置表单
        const form = document.getElementById('addPersonToProjectMainForm');
        if (form) {
            form.reset();
        }
        
        // 隐藏劳务型字段
        const laborFields = document.getElementById('addPersonToProjectLaborFields');
        if (laborFields) {
            laborFields.style.display = 'none';
        }
        
        // 打开模态框
        const modal = M.Modal.getInstance(document.getElementById('addPersonToProjectModal'));
        if (modal) {
            modal.open();
        } else {
            M.Modal.init(document.getElementById('addPersonToProjectModal')).open();
        }
        
        setTimeout(() => {
            M.updateTextFields();
            M.FormSelect.init(document.querySelectorAll('#addPersonToProjectModal select'));
        }, 100);
    } catch (err) {
        M.toast({html: `加载失败：${err.message}`, classes: 'red'});
    }
}

// 处理项目选择变化（在添加参与项目表单中）
async function handleAddProjectSelectChange() {
    const select = document.getElementById('addProjectSelect');
    const projectId = select.value;
    const laborFields = document.getElementById('addLaborFields');
    
    if (!projectId || !laborFields) return;
    
    try {
        const result = await fetchJSON(`/api/projects/${projectId}`);
        const projectType = result.data.basic.data?.project_type;
        
        if (projectType === '劳务型') {
            laborFields.style.display = 'block';
        } else {
            laborFields.style.display = 'none';
            // 清空劳务型字段
            const laborInputs = laborFields.querySelectorAll('input, select');
            laborInputs.forEach(input => {
                if (input.type === 'checkbox') {
                    input.checked = false;
                } else {
                    input.value = '';
                }
            });
        }
        
        setTimeout(() => {
            M.updateTextFields();
            M.FormSelect.init(document.querySelectorAll('#addLaborFields select'));
        }, 50);
    } catch (err) {
        console.error('获取项目信息失败:', err);
    }
}

// 处理打卡方式变化（在添加参与项目表单中）
function handleAttendanceMethodChange() {
    const select = document.getElementById('add_attendance_method');
    const method = select.value;
    const onsiteFields = document.getElementById('addOnsiteFields');
    const onlineFields = document.getElementById('addOnlineFields');
    
    if (method === '现场打卡') {
        if (onsiteFields) onsiteFields.style.display = 'block';
        if (onlineFields) onlineFields.style.display = 'none';
    } else if (method === '线上打卡') {
        if (onsiteFields) onsiteFields.style.display = 'none';
        if (onlineFields) onlineFields.style.display = 'block';
    } else {
        if (onsiteFields) onsiteFields.style.display = 'none';
        if (onlineFields) onlineFields.style.display = 'none';
    }
    
    setTimeout(() => {
        M.updateTextFields();
    }, 50);
}

// 处理项目选择变化（在登记人员入项主表单中）
async function handleAddProjectToPersonMainSelectChange() {
    const select = document.getElementById('addProjectToPersonMainSelect');
    const projectId = select.value;
    const laborFields = document.getElementById('addPersonToProjectLaborFields');
    
    if (!projectId || !laborFields) return;
    
    try {
        const result = await fetchJSON(`/api/projects/${projectId}`);
        const projectType = result.data.basic.data?.project_type;
        
        if (projectType === '劳务型') {
            laborFields.style.display = 'block';
        } else {
            laborFields.style.display = 'none';
            // 清空劳务型字段
            const laborInputs = laborFields.querySelectorAll('input, select');
            laborInputs.forEach(input => {
                if (input.type === 'checkbox') {
                    input.checked = false;
                } else {
                    input.value = '';
                }
            });
        }
        
        setTimeout(() => {
            M.updateTextFields();
            M.FormSelect.init(document.querySelectorAll('#addPersonToProjectLaborFields select'));
        }, 50);
    } catch (err) {
        console.error('获取项目信息失败:', err);
    }
}

// 处理打卡方式变化
function handleAddPersonToProjectAttendanceMethodChange() {
    const select = document.getElementById('addPersonToProject_attendance_method');
    const method = select.value;
    const onsiteFields = document.getElementById('addPersonToProjectOnsiteFields');
    const onlineFields = document.getElementById('addPersonToProjectOnlineFields');
    
    if (method === '现场打卡') {
        if (onsiteFields) onsiteFields.style.display = 'block';
        if (onlineFields) onlineFields.style.display = 'none';
    } else if (method === '线上打卡') {
        if (onsiteFields) onsiteFields.style.display = 'none';
        if (onlineFields) onlineFields.style.display = 'block';
    } else {
        if (onsiteFields) onsiteFields.style.display = 'none';
        if (onlineFields) onlineFields.style.display = 'none';
    }
    
    setTimeout(() => {
        M.updateTextFields();
    }, 50);
}

// 处理登记人员入项表单提交
async function handleAddPersonToProjectMain() {
    const form = document.getElementById('addPersonToProjectMainForm');
    if (!form) return;
    
    const formData = new FormData(form);
    const personId = formData.get('person_id');
    const projectId = formData.get('project_id');
    
    if (!personId) {
        M.toast({html: '请选择人员', classes: 'red'});
        return;
    }
    
    if (!projectId) {
        M.toast({html: '请选择项目', classes: 'red'});
        return;
    }
    
    const data = {
        project_id: parseInt(projectId),
    };
    
    // 处理通用字段
    for (const [key, value] of formData.entries()) {
        if (key !== 'person_id' && key !== 'project_id' && value) {
            if (key === 'face_recognition') {
                data[key] = formData.get('face_recognition') === 'on';
            } else {
                data[key] = value;
            }
        }
    }
    
    try {
        await fetchJSON(`/api/persons/${personId}/projects`, {
            method: 'POST',
            body: JSON.stringify({project: data}),
        });
        
        M.toast({html: '登记成功', classes: 'green'});
        
        // 关闭模态框
        const modal = M.Modal.getInstance(document.getElementById('addPersonToProjectModal'));
        if (modal) {
            modal.close();
        }
        
        // 重置表单
        form.reset();
        const laborFields = document.getElementById('addPersonToProjectLaborFields');
        if (laborFields) {
            laborFields.style.display = 'none';
        }
        
        // 刷新关系图
        loadRelationData();
    } catch (err) {
        M.toast({html: `登记失败：${err.message}`, classes: 'red'});
        console.error('登记人员入项失败:', err);
    }
}
