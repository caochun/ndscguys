// 人员页面 JavaScript

// 全局变量
let unemployedPersons = [];
let employedPersons = [];
let selectedPersonId = null;
let isEditMode = false;
let currentTab = 'unemployed';  // 'unemployed' 或 'employed'

// Materialize 组件实例
let personModalInstance = null;
let personTabsInstance = null;

// DOM 加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initMaterializeComponents();
    initEventListeners();
    // 延迟加载数据，确保Tab组件已初始化
    setTimeout(() => {
        loadUnemployedPersons();
        loadEmployedPersons();
    }, 100);
});

// 初始化 Materialize 组件
function initMaterializeComponents() {
    // 初始化人员模态框
    const personModal = document.getElementById('personModal');
    if (personModal) {
        personModalInstance = M.Modal.init(personModal, {
            onCloseEnd: function() {
                document.getElementById('personForm').reset();
                M.updateTextFields();
            }
        });
    }
    
    // 初始化Tab组件
    const personTabs = document.getElementById('personTabs');
    if (personTabs) {
        personTabsInstance = M.Tabs.init(personTabs, {
            onShow: function(newTab) {
                // Tab切换时更新当前tab状态
                const tabId = newTab.getAttribute('href');
                if (tabId) {
                    const targetId = tabId.substring(1); // 去掉#号
                    if (targetId === 'unemployedTab') {
                        currentTab = 'unemployed';
                    } else if (targetId === 'employedTab') {
                        currentTab = 'employed';
                    }
                }
                // 清除选中状态
                selectedPersonId = null;
                document.querySelectorAll('tbody tr').forEach(r => r.classList.remove('selected'));
            }
        });
        // 确保默认显示第一个tab
        const firstTab = personTabs.querySelector('a.active');
        if (firstTab) {
            const targetId = firstTab.getAttribute('href').substring(1);
            if (targetId === 'unemployedTab') {
                currentTab = 'unemployed';
            }
        }
    }
    
    // 初始化移动端导航侧边栏
    const mobileNav = document.getElementById('mobile-nav');
    if (mobileNav) {
        M.Sidenav.init(mobileNav);
    }
}

// 初始化事件监听器
function initEventListeners() {
    // 人员页面工具栏按钮
    const addBtn = document.getElementById('addPersonBtn');
    if (addBtn) {
        addBtn.addEventListener('click', showAddPersonModal);
    }
    
    const editBtn = document.getElementById('editPersonBtn');
    if (editBtn) {
        editBtn.addEventListener('click', showEditPersonModal);
    }
    
    const refreshBtn = document.getElementById('refreshPersonsBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            loadUnemployedPersons();
            loadEmployedPersons();
        });
    }
    
    // 模态框关闭按钮
    const cancelBtn = document.getElementById('cancelPersonBtn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            if (personModalInstance) {
                personModalInstance.close();
            }
        });
    }

    // 表单提交
    const personForm = document.getElementById('personForm');
    if (personForm) {
        personForm.addEventListener('submit', savePerson);
    }

    // 人员表格行点击选择（使用事件委托）
    const unemployedTableBody = document.getElementById('unemployedPersonTableBody');
    if (unemployedTableBody) {
        unemployedTableBody.addEventListener('click', function(e) {
            const row = e.target.closest('tr');
            if (row && row.dataset.personId) {
                // 移除所有表格的选中状态
                document.querySelectorAll('tbody tr').forEach(r => r.classList.remove('selected'));
                // 添加选中状态
                row.classList.add('selected');
                selectedPersonId = parseInt(row.dataset.personId);
            }
        });
    }
    
    const employedTableBody = document.getElementById('employedPersonTableBody');
    if (employedTableBody) {
        employedTableBody.addEventListener('click', function(e) {
            const row = e.target.closest('tr');
            if (row && row.dataset.personId) {
                // 移除所有表格的选中状态
                document.querySelectorAll('tbody tr').forEach(r => r.classList.remove('selected'));
                // 添加选中状态
                row.classList.add('selected');
                selectedPersonId = parseInt(row.dataset.personId);
            }
        });
    }
}

// 加载未任职人员列表
async function loadUnemployedPersons() {
    try {
        updateStatus('加载未任职人员中...');
        const response = await fetch('/api/persons?employment_status=unemployed');
        const result = await response.json();

        if (result.success) {
            unemployedPersons = result.data;
            renderPersonTable('unemployed', unemployedPersons);
            if (currentTab === 'unemployed') {
                updateStatus(`已加载 ${unemployedPersons.length} 名未任职人员`);
            }
        } else {
            showError('加载未任职人员列表失败：' + result.error);
            if (currentTab === 'unemployed') {
                updateStatus('加载失败');
            }
        }
    } catch (error) {
        showError('加载未任职人员列表失败：' + error.message);
        if (currentTab === 'unemployed') {
            updateStatus('加载失败');
        }
    }
}

// 加载已任职人员列表
async function loadEmployedPersons() {
    try {
        updateStatus('加载已任职人员中...');
        const response = await fetch('/api/persons?employment_status=employed');
        const result = await response.json();

        if (result.success) {
            employedPersons = result.data;
            renderPersonTable('employed', employedPersons);
            if (currentTab === 'employed') {
                updateStatus(`已加载 ${employedPersons.length} 名已任职人员`);
            }
        } else {
            showError('加载已任职人员列表失败：' + result.error);
            if (currentTab === 'employed') {
                updateStatus('加载失败');
            }
        }
    } catch (error) {
        showError('加载已任职人员列表失败：' + error.message);
        if (currentTab === 'employed') {
            updateStatus('加载失败');
        }
    }
}

// 渲染人员表格
function renderPersonTable(type, persons) {
    const tbodyId = type === 'unemployed' ? 'unemployedPersonTableBody' : 'employedPersonTableBody';
    const tbody = document.getElementById(tbodyId);
    if (!tbody) return;
    
    if (persons.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="center-align">暂无人员数据</td></tr>';
        return;
    }

    tbody.innerHTML = persons.map(person => {
        return `
        <tr data-person-id="${person.id}">
            <td>${person.id}</td>
            <td>${person.name || '-'}</td>
            <td>${person.birth_date || '-'}</td>
            <td>${person.gender || '-'}</td>
            <td>${person.phone || '-'}</td>
            <td>${person.email || '-'}</td>
            <td>${person.address || '-'}</td>
            <td>${person.created_at || '-'}</td>
            <td>${person.updated_at || '-'}</td>
        </tr>
        `;
    }).join('');
}

// 显示新增人员模态框
function showAddPersonModal() {
    isEditMode = false;
    selectedPersonId = null;
    document.getElementById('personModalTitle').textContent = '新增人员';
    document.getElementById('personForm').reset();
    document.getElementById('personId').value = '';
    M.updateTextFields();
    if (personModalInstance) {
        personModalInstance.open();
    }
}

// 显示编辑人员模态框
function showEditPersonModal() {
    if (!selectedPersonId) {
        M.toast({html: '请先选择要编辑的人员', classes: 'orange'});
        return;
    }
    
    isEditMode = true;
    // 从当前tab的数据中查找人员
    const currentPersons = currentTab === 'unemployed' ? unemployedPersons : employedPersons;
    const person = currentPersons.find(p => p.id === selectedPersonId);
    if (!person) {
        M.toast({html: '人员不存在', classes: 'red'});
        return;
    }
    
    document.getElementById('personModalTitle').textContent = '编辑人员';
    document.getElementById('personId').value = person.id;
    document.getElementById('personName').value = person.name || '';
    document.getElementById('personBirthDate').value = person.birth_date || '';
    document.getElementById('personGender').value = person.gender || '';
    document.getElementById('personPhone').value = person.phone || '';
    document.getElementById('personEmail').value = person.email || '';
    document.getElementById('personAddress').value = person.address || '';
    
    M.updateTextFields();
    M.FormSelect.init(document.getElementById('personGender'));
    if (personModalInstance) {
        personModalInstance.open();
    }
}

// 关闭人员模态框
function closePersonModal() {
    if (personModalInstance) {
        personModalInstance.close();
    }
    isEditMode = false;
    selectedPersonId = null;
}

// 保存人员
async function savePerson(e) {
    e.preventDefault();
    
    const personId = document.getElementById('personId').value;
    const name = document.getElementById('personName').value.trim();
    
    if (!name) {
        M.toast({html: '姓名不能为空', classes: 'orange'});
        return;
    }
    
    const personData = {
        name: name,
        birth_date: document.getElementById('personBirthDate').value || null,
        gender: document.getElementById('personGender').value || null,
        phone: document.getElementById('personPhone').value || null,
        email: document.getElementById('personEmail').value || null,
        address: document.getElementById('personAddress').value || null
    };
    
    try {
        updateStatus('保存中...');
        let response;
        
        if (personId) {
            // 更新
            response = await fetch(`/api/persons/${personId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(personData)
            });
        } else {
            // 创建
            response = await fetch('/api/persons', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(personData)
            });
        }
        
        const result = await response.json();
        
        if (result.success) {
            M.toast({html: result.message || '保存成功', classes: 'green'});
            updateStatus(result.message || '保存成功');
            closePersonModal();
            loadUnemployedPersons();
            loadEmployedPersons();
        } else {
            M.toast({html: '保存失败：' + result.error, classes: 'red'});
            updateStatus('保存失败');
        }
    } catch (error) {
        M.toast({html: '保存失败：' + error.message, classes: 'red'});
        updateStatus('保存失败');
    }
}

// 更新状态栏
function updateStatus(message) {
    const statusText = document.getElementById('statusText');
    if (statusText) {
        statusText.textContent = message;
    }
}

// 显示错误消息
function showError(message) {
    console.error(message);
    M.toast({html: message, classes: 'red'});
    updateStatus('错误：' + message);
}

