// 薪资计算 DSL 编辑器
let editor;
let currentRuleId = null;
let defaultDSL = `version: "1.0"
name: "默认薪资计算规则"

# 配置映射表（用户只需修改这部分配置）
configs:
  # 绩效系数映射
  performance_factors:
    A: 1.2
    B: 1.0
    C: 0.8
    D: 0.5
    E: 0.0
    default: 1.0
  
  # 基数/绩效拆分比例 [基数比例, 绩效比例]
  split_ratios:
    正式员工: [0.7, 0.3]
    试用员工: [0.8, 0.2]
    试用期员工: [0.8, 0.2]
    实习员工: [1.0, 0.0]
    实习生: [1.0, 0.0]
    部分负责人: [0.6, 0.4]
    default: [0.7, 0.3]
  
  # 试用期折扣
  probation_discount: 0.8
  
  # 默认工作天数
  default_work_days: 22`;

document.addEventListener('DOMContentLoaded', function() {
    // 初始化 CodeMirror 编辑器
    editor = CodeMirror.fromTextArea(document.getElementById('dsl-editor'), {
        mode: 'yaml',
        theme: 'material',
        lineNumbers: true,
        indentUnit: 2,
        lineWrapping: true,
    });
    
    // 初始化日期选择器
    var datepickers = document.querySelectorAll('.datepicker');
    M.Datepicker.init(datepickers, {
        format: 'yyyy-mm-dd',
        autoClose: true
    });
    
    // 加载规则列表
    loadRules();
    
    // 加载默认配置
    loadDefaultDSL();
});

function loadDefaultDSL() {
    // 如果没有选中规则，加载默认配置
    if (currentRuleId === null) {
        fetch('/api/payroll/dsl-rules/default')
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    editor.setValue(data.data.dsl_config);
                    document.getElementById('rule-name').value = data.data.name || '';
                    document.getElementById('rule-version').value = data.data.version || '1.0';
                    M.toast({html: '已加载默认配置'});
                } else {
                    // 如果加载失败，使用内置的默认配置
                    console.warn('Failed to load default DSL:', data.error);
                    editor.setValue(defaultDSL);
                }
            })
            .catch(err => {
                console.error('Error loading default DSL:', err);
                // 如果加载失败，使用内置的默认配置
                editor.setValue(defaultDSL);
            });
    }
}

function loadRules() {
    fetch('/api/payroll/dsl-rules')
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                displayRules(data.data);
            } else {
                M.toast({html: '加载规则失败: ' + (data.error || '未知错误')});
            }
        })
        .catch(err => {
            console.error('Error loading rules:', err);
            M.toast({html: '加载规则失败: ' + err.message});
        });
}

function displayRules(rules) {
    const container = document.getElementById('rules-list');
    if (rules.length === 0) {
        container.innerHTML = '<p class="grey-text">暂无规则</p>';
        return;
    }
    
    let html = '<ul class="collection">';
    rules.forEach(rule => {
        const activeClass = rule.is_active ? 'rule-active' : 'rule-inactive';
        const activeBadge = rule.is_active 
            ? '<span class="badge green white-text">已激活</span>'
            : '<span class="badge grey">未激活</span>';
        
        html += `
            <li class="collection-item ${activeClass}" onclick="loadRule(${rule.id})" style="cursor: pointer;">
                <div>
                    <strong>${rule.name}</strong> ${activeBadge}
                    <br>
                    <small class="grey-text">版本: ${rule.version} | 更新: ${new Date(rule.updated_at).toLocaleString()}</small>
                </div>
            </li>
        `;
    });
    html += '</ul>';
    container.innerHTML = html;
}

function loadRule(ruleId) {
    fetch(`/api/payroll/dsl-rules/${ruleId}`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const rule = data.data;
                currentRuleId = rule.id;
                
                document.getElementById('rule-name').value = rule.name || '';
                document.getElementById('rule-version').value = rule.version || '1.0';
                document.getElementById('rule-effective-date').value = rule.effective_date || '';
                document.getElementById('rule-description').value = rule.description || '';
                
                editor.setValue(rule.dsl_config || '');
                
                // 启用按钮
                document.getElementById('save-btn').disabled = false;
                document.getElementById('activate-btn').disabled = false;
                document.getElementById('delete-btn').disabled = false;
                
                M.toast({html: '规则加载成功'});
            } else {
                M.toast({html: '加载规则失败: ' + (data.error || '未知错误')});
            }
        })
        .catch(err => {
            console.error('Error loading rule:', err);
            M.toast({html: '加载规则失败: ' + err.message});
        });
}

function createNewRule() {
    currentRuleId = null;
    document.getElementById('rule-name').value = '';
    document.getElementById('rule-version').value = '1.0';
    document.getElementById('rule-effective-date').value = '';
    document.getElementById('rule-description').value = '';
    
    // 加载默认配置
    loadDefaultDSL();
    
    document.getElementById('save-btn').disabled = false;
    document.getElementById('activate-btn').disabled = true;
    document.getElementById('delete-btn').disabled = true;
    
    M.toast({html: '已创建新规则模板'});
}

function validateDSL() {
    const dslContent = editor.getValue();
    const resultDiv = document.getElementById('validation-result');
    
    resultDiv.innerHTML = '<p class="grey-text">验证中...</p>';
    
    fetch('/api/payroll/dsl-rules/validate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            dsl_config: dslContent
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success && data.data.valid) {
            resultDiv.innerHTML = `
                <div class="card-panel green lighten-4">
                    <i class="material-icons left green-text">check_circle</i>
                    <strong>验证通过</strong><br>
                    规则名称: ${data.data.name || '未设置'}<br>
                    版本: ${data.data.version || '未设置'}
                </div>
            `;
        } else {
            resultDiv.innerHTML = `
                <div class="card-panel red lighten-4">
                    <i class="material-icons left red-text">error</i>
                    <strong>验证失败</strong><br>
                    ${data.error || '未知错误'}
                </div>
            `;
        }
    })
    .catch(err => {
        console.error('Error validating DSL:', err);
        resultDiv.innerHTML = `
            <div class="card-panel red lighten-4">
                <i class="material-icons left red-text">error</i>
                <strong>验证失败</strong><br>
                ${err.message}
            </div>
        `;
    });
}

function saveRule() {
    const name = document.getElementById('rule-name').value.trim();
    const version = document.getElementById('rule-version').value.trim();
    const effectiveDate = document.getElementById('rule-effective-date').value.trim();
    const description = document.getElementById('rule-description').value.trim();
    const dslConfig = editor.getValue();
    
    if (!name) {
        M.toast({html: '请输入规则名称'});
        return;
    }
    
    const payload = {
        name: name,
        version: version || '1.0',
        dsl_config: dslConfig,
        description: description,
        effective_date: effectiveDate || null,
    };
    
    const url = currentRuleId 
        ? `/api/payroll/dsl-rules/${currentRuleId}`
        : '/api/payroll/dsl-rules';
    const method = currentRuleId ? 'PUT' : 'POST';
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            M.toast({html: '规则保存成功'});
            if (!currentRuleId && data.data.rule_id) {
                currentRuleId = data.data.rule_id;
                document.getElementById('activate-btn').disabled = false;
                document.getElementById('delete-btn').disabled = false;
            }
            loadRules();
        } else {
            M.toast({html: '保存失败: ' + (data.error || '未知错误')});
        }
    })
    .catch(err => {
        console.error('Error saving rule:', err);
        M.toast({html: '保存失败: ' + err.message});
    });
}

function activateRule() {
    if (!currentRuleId) {
        M.toast({html: '请先保存规则'});
        return;
    }
    
    fetch(`/api/payroll/dsl-rules/${currentRuleId}/activate`, {
        method: 'POST'
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            M.toast({html: '规则已激活，将在下次计算时生效'});
            loadRules();
        } else {
            M.toast({html: '激活失败: ' + (data.error || '未知错误')});
        }
    })
    .catch(err => {
        console.error('Error activating rule:', err);
        M.toast({html: '激活失败: ' + err.message});
    });
}

function deleteRule() {
    if (!currentRuleId) {
        M.toast({html: '没有选中的规则'});
        return;
    }
    
    if (!confirm('确定要删除这个规则吗？此操作不可恢复。')) {
        return;
    }
    
    fetch(`/api/payroll/dsl-rules/${currentRuleId}`, {
        method: 'DELETE'
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            M.toast({html: '规则已删除'});
            createNewRule();
            loadRules();
        } else {
            M.toast({html: '删除失败: ' + (data.error || '未知错误')});
        }
    })
    .catch(err => {
        console.error('Error deleting rule:', err);
        M.toast({html: '删除失败: ' + err.message});
    });
}

