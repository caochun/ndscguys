"""
路由蓝图
"""
from flask import Blueprint, render_template, request, jsonify
from app.services.employee_service import EmployeeService
from app.models import Person, Employee, EmploymentInfo

# 创建蓝图
main_bp = Blueprint('main', __name__)
api_bp = Blueprint('api', __name__)

# 初始化服务
employee_service = EmployeeService()


@main_bp.route('/')
def index():
    """主页面"""
    return render_template('index.html')


@api_bp.route('/employees', methods=['GET'])
def get_employees():
    """获取所有员工列表"""
    try:
        company_name = request.args.get('company_name')  # 可选的公司筛选
        employees_data = employee_service.get_all_employees_with_info(company_name)
        result = []
        for data in employees_data:
            person = data['person']
            employee = data['employee']
            employment_info = data['employment_info']
            result.append({
                'id': employee.id,
                'person_id': employee.person_id,
                'company_name': employee.company_name,
                'employee_number': employee.employee_number,
                'name': person.name if person else None,
                'birth_date': person.birth_date if person else None,
                'gender': person.gender if person else None,
                'phone': person.phone if person else None,
                'email': person.email if person else None,
                'department': employment_info.department if employment_info else None,
                'position': employment_info.position if employment_info else None,
                'hire_date': employment_info.hire_date if employment_info else None,
                'supervisor_id': employment_info.supervisor_id if employment_info else None,
                'has_history': data.get('has_history', False),  # 是否有历史记录
            })
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/employees/<int:employee_id>', methods=['GET'])
def get_employee(employee_id):
    """获取单个员工信息"""
    try:
        data = employee_service.get_employee_with_employment_info(employee_id)
        if not data:
            return jsonify({'success': False, 'error': '员工不存在'}), 404
        
        person = data['person']
        employee = data['employee']
        employment_info = data['employment_info']
        
        result = {
            'id': employee.id,
            'person_id': employee.person_id,
            'company_name': employee.company_name,
            'employee_number': employee.employee_number,
            'name': person.name if person else None,
            'birth_date': person.birth_date if person else None,
            'gender': person.gender if person else None,
            'phone': person.phone if person else None,
            'email': person.email if person else None,
            'department': employment_info.department if employment_info else None,
            'position': employment_info.position if employment_info else None,
            'hire_date': employment_info.hire_date if employment_info else None,
            'supervisor_id': employment_info.supervisor_id if employment_info else None,
        }
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/employees', methods=['POST'])
def create_employee():
    """创建新员工"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('company_name'):
            return jsonify({'success': False, 'error': '公司名称不能为空'}), 400
        if not data.get('employee_number') or not data.get('name'):
            return jsonify({'success': False, 'error': '员工编号和姓名不能为空'}), 400
        if not data.get('department') or not data.get('position'):
            return jsonify({'success': False, 'error': '部门和职位不能为空'}), 400
        
        # 创建人员
        person = Person(
            name=data['name'],
            birth_date=data.get('birth_date'),
            gender=data.get('gender'),
            phone=data.get('phone'),
            email=data.get('email')
        )
        
        # 创建员工（会自动处理人员匹配或创建）
        employee_id = employee_service.create_employee(
            person,
            data['company_name'],
            data['employee_number']
        )
        
        # 创建入职信息
        employment_info = EmploymentInfo(
            employee_id=employee_id,
            company_name=data['company_name'],
            department=data['department'],
            position=data['position'],
            hire_date=data['hire_date'],
            supervisor_id=data.get('supervisor_id')
        )
        
        employee_service.create_employment_info(employment_info)
        
        return jsonify({'success': True, 'message': '员工创建成功', 'id': employee_id})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/employees/<int:employee_id>', methods=['PUT'])
def update_employee(employee_id):
    """更新员工信息"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('name'):
            return jsonify({'success': False, 'error': '姓名不能为空'}), 400
        if not data.get('company_name'):
            return jsonify({'success': False, 'error': '公司名称不能为空'}), 400
        if not data.get('department') or not data.get('position'):
            return jsonify({'success': False, 'error': '部门和职位不能为空'}), 400
        
        # 获取员工信息
        employee = employee_service.get_employee(employee_id)
        if not employee:
            return jsonify({'success': False, 'error': '员工不存在'}), 404
        
        # 更新人员信息
        person = employee_service.get_person(employee.person_id)
        if person:
            person.name = data['name']
            person.birth_date = data.get('birth_date')
            person.gender = data.get('gender')
            person.phone = data.get('phone')
            person.email = data.get('email')
            employee_service.update_person(person)
        
        # 检查入职信息是否有变更
        current_info = employee_service.get_employment_info(employee_id)
        if current_info:
            has_changed = (
                data.get('company_name') != current_info.company_name or
                data.get('department') != current_info.department or
                data.get('position') != current_info.position or
                data.get('hire_date') != current_info.hire_date or
                data.get('supervisor_id') != current_info.supervisor_id
            )
            
            if has_changed:
                change_reason = data.get('change_reason') or '未填写变更原因'
                employee_service.update_employment_info(
                    employee_id,
                    data['company_name'],
                    data['department'],
                    data['position'],
                    data['hire_date'],
                    data.get('supervisor_id'),
                    change_reason
                )
        else:
            # 如果没有入职信息，创建新的
            employment_info = EmploymentInfo(
                employee_id=employee_id,
                company_name=data['company_name'],
                department=data['department'],
                position=data['position'],
                hire_date=data['hire_date'],
                supervisor_id=data.get('supervisor_id')
            )
            employee_service.create_employment_info(employment_info)
        
        return jsonify({'success': True, 'message': '员工信息更新成功'})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/employees/<int:employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    """删除员工"""
    try:
        employee = employee_service.get_employee(employee_id)
        if not employee:
            return jsonify({'success': False, 'error': '员工不存在'}), 404
        
        employee_service.delete_employee(employee_id)
        return jsonify({'success': True, 'message': '员工删除成功'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/supervisors', methods=['GET'])
def get_supervisors():
    """获取所有员工列表（用于选择上级）"""
    try:
        company_name = request.args.get('company_name')  # 只返回同一公司的员工
        employees = employee_service.get_all_employees(company_name)
        result = []
        for emp in employees:
            person = employee_service.get_person(emp.person_id)
            result.append({
                'id': emp.id,
                'name': person.name if person else '未知',
                'employee_number': emp.employee_number,
                'company_name': emp.company_name
            })
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/companies', methods=['GET'])
def get_companies():
    """获取所有公司列表"""
    try:
        conn = employee_service.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT company_name FROM employees ORDER BY company_name")
        rows = cursor.fetchall()
        companies = [row['company_name'] for row in rows]
        return jsonify({'success': True, 'data': companies})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/employees/<int:employee_id>/history', methods=['GET'])
def get_employee_history(employee_id):
    """获取员工的任职历史记录（包含当前任职）
    
    如果员工已换公司，会查找该人员(person_id)在所有公司的任职信息
    """
    try:
        result = []
        
        # 1. 获取当前员工记录，找到 person_id
        employee = employee_service.get_employee(employee_id)
        if not employee:
            return jsonify({'success': False, 'error': '员工不存在'}), 404
        
        person_id = employee.person_id
        
        # 2. 获取当前任职信息
        current_info = employee_service.get_employment_info(employee_id)
        if current_info:
            result.append({
                'id': current_info.id,
                'version': current_info.version,
                'department': current_info.department,
                'position': current_info.position,
                'hire_date': current_info.hire_date,
                'supervisor_id': current_info.supervisor_id,
                'changed_at': current_info.updated_at,  # 使用updated_at作为时间戳
                'change_reason': None,  # 当前任职没有变更原因
                'company_name': current_info.company_name,
                'is_current': True  # 标记为当前任职
            })
        
        # 3. 获取历史记录
        history = employee_service.get_employment_info_history(employee_id)
        for h in history:
            result.append({
                'id': h.id,
                'version': h.version,
                'department': h.department,
                'position': h.position,
                'hire_date': h.hire_date,
                'supervisor_id': h.supervisor_id,
                'changed_at': h.changed_at,
                'change_reason': h.change_reason,
                'company_name': h.company_name,
                'is_current': False  # 标记为历史记录
            })
        
        # 5. 按时间排序（changed_at降序，最新的在前）
        # 当前任职优先显示（即使时间相同）
        # 排序：先按 is_current（True在前），再按时间降序
        # 确保 changed_at 不为 None
        for item in result:
            if item.get('changed_at') is None:
                item['changed_at'] = ''
        result.sort(key=lambda x: (x.get('is_current', False), x.get('changed_at', '')), reverse=True)
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
