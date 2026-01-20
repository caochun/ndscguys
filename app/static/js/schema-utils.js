/**
 * Schema 工具函数 - 用于处理 Schema 相关的通用操作
 */

/**
 * 确保字段顺序：虽然 JSON 解析后可能顺序被打乱，但我们可以通过显式排序来保证顺序
 * 按照 schema.yaml 中定义的字段顺序重新排序
 * 
 * @param {Object} schemaObj - Schema 对象，包含 name 和 fields
 */
function ensureFieldOrder(schemaObj) {
    if (!schemaObj || !schemaObj.fields) return;
    
    // 定义 schema.yaml 中字段的标准顺序（按定义顺序）
    const fieldOrderMap = {
        'person': ['name', 'id_card', 'phone', 'email', 'address', 'avatar'],
        'project': ['internal_project_name', 'project_name', 'project_type', 'budget', 'start_date', 'end_date', 'status', 'description'],
        'person_company_employment': ['person_id', 'company_id', 'employee_type', 'position', 'department', 'hire_date', 'leave_date', 'salary_type', 'base_salary', 'performance_ratio'],
        'person_project_participation': ['person_id', 'project_id', 'role', 'start_date', 'end_date', 'status', 'change_date'],
        'person_company_attendance': ['person_id', 'company_id', 'date', 'expected_hours', 'actual_hours', 'absent_hours']
    };
    
    const twinName = schemaObj.name;
    const standardOrder = fieldOrderMap[twinName];
    
    if (standardOrder) {
        // 创建一个新的有序对象，使用 Map 来确保顺序
        const orderedFields = new Map();
        const originalFields = schemaObj.fields;
        
        // 先按标准顺序添加字段
        for (const fieldName of standardOrder) {
            if (originalFields[fieldName]) {
                orderedFields.set(fieldName, originalFields[fieldName]);
            }
        }
        
        // 再添加标准顺序中没有的字段（向后兼容）
        for (const fieldName in originalFields) {
            if (!orderedFields.has(fieldName)) {
                orderedFields.set(fieldName, originalFields[fieldName]);
            }
        }
        
        // 将 Map 转换为普通对象（保持顺序）
        schemaObj.fields = Object.fromEntries(orderedFields);
    }
}

/**
 * 按照 schema 定义的顺序遍历字段
 * 
 * @param {Object} fields - Schema fields 对象
 * @param {Function} callback - 回调函数，接收 (fieldName, fieldDef) 参数
 */
function iterateFieldsInOrder(fields, callback) {
    if (!fields) return;
    
    // 使用 Object.keys() 确保按照 schema 定义的顺序遍历
    const fieldNames = Object.keys(fields);
    for (const fieldName of fieldNames) {
        const fieldDef = fields[fieldName];
        callback(fieldName, fieldDef);
    }
}

/**
 * 获取字段值，支持嵌套对象（如 person.current[fieldName]）
 * 
 * @param {Object} obj - 对象
 * @param {string} fieldName - 字段名
 * @returns {*} 字段值
 */
function getFieldValue(obj, fieldName) {
    if (obj.current && typeof obj.current === 'object') {
        return obj.current[fieldName];
    }
    return obj[fieldName];
}

/**
 * 格式化字段显示值
 * 
 * @param {*} value - 原始值
 * @param {Object} fieldDef - 字段定义
 * @param {string} fieldName - 字段名
 * @returns {string} 格式化后的显示值
 */
function formatFieldValue(value, fieldDef, fieldName) {
    if (value === undefined || value === null || value === '') {
        return '';
    }
    
    // 特殊处理：如果是头像 URL，返回 HTML img 标签
    if (fieldName === 'avatar' && value) {
        return `<img src="${value}" alt="头像" class="w-16 h-16 rounded-full object-cover">`;
    }
    
    // 特殊处理：如果是预算字段，格式化货币
    if (fieldName === 'budget' && typeof value === 'number') {
        return `¥${value.toLocaleString()}`;
    }
    
    // 特殊处理：如果是日期字段
    if (fieldDef.type === 'date' && value) {
        return new Date(value).toLocaleDateString('zh-CN');
    }
    
    return String(value);
}
