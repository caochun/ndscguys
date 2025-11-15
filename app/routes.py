"""
路由蓝图
"""
from flask import Blueprint, render_template, request, jsonify
from app.services.employee_service import EmployeeService
from app.services.attendance_service import AttendanceService
from app.models import Person, Employee, Employment, Attendance, LeaveRecord

# 创建蓝图
main_bp = Blueprint('main', __name__)
api_bp = Blueprint('api', __name__)

# 初始化服务
employee_service = EmployeeService()
attendance_service = AttendanceService()


@main_bp.route('/')
def index():
    """主页面 - 重定向到员工页面"""
    return render_template('employees.html')


@main_bp.route('/employees')
def employees():
    """员工管理页面"""
    return render_template('employees.html')


@main_bp.route('/persons')
def persons():
    """人员管理页面"""
    return render_template('persons.html')


@main_bp.route('/attendance')
def attendance():
    """考勤管理页面"""
    return render_template('attendance.html')


@api_bp.route('/employees', methods=['GET'])
def get_employees():
    """获取所有员工列表"""
    try:
        company_name = request.args.get('company_name')  # 可选的公司筛选
        employees_data = employee_service.get_all_employees_with_employment(company_name)
        result = []
        for item in employees_data:
            person = item.person
            employee = item.employee
            employment = item.employment
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
                'department': employment.department if employment else None,
                'position': employment.position if employment else None,
                'hire_date': employment.hire_date if employment else None,
                'supervisor_id': employment.supervisor_id if employment else None,
                'has_history': item.has_history,  # 是否有历史记录
            })
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/employees/<int:employee_id>', methods=['GET'])
def get_employee(employee_id):
    """获取单个员工信息"""
    try:
        data = employee_service.get_employee_with_employment(employee_id)
        if not data:
            return jsonify({'success': False, 'error': '员工不存在'}), 404
        
        person = data.person
        employee = data.employee
        employment = data.employment
        
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
            'address': person.address if person else None,
            'department': employment.department if employment else None,
            'position': employment.position if employment else None,
            'hire_date': employment.hire_date if employment else None,
            'supervisor_id': employment.supervisor_id if employment else None,
        }
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/persons', methods=['GET'])
def get_persons():
    """获取所有人员列表"""
    try:
        persons = employee_service.get_all_persons()
        result = []
        for person in persons:
            result.append({
                'id': person.id,
                'name': person.name,
                'birth_date': person.birth_date,
                'gender': person.gender,
                'phone': person.phone,
                'email': person.email,
                'address': person.address,
                'created_at': person.created_at,
                'updated_at': person.updated_at
            })
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/persons', methods=['POST'])
def create_person():
    """创建新人员"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('name'):
            return jsonify({'success': False, 'error': '姓名不能为空'}), 400
        
        # 创建人员对象
        person = Person(
            name=data['name'],
            birth_date=data.get('birth_date'),
            gender=data.get('gender'),
            phone=data.get('phone'),
            email=data.get('email'),
            address=data.get('address')
        )
        
        # 查找或创建人员（根据手机号或邮箱匹配）
        person_id = employee_service.find_or_create_person(person)
        
        return jsonify({'success': True, 'message': '人员创建成功', 'id': person_id})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/persons/<int:person_id>', methods=['PUT'])
def update_person(person_id):
    """更新人员信息"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('name'):
            return jsonify({'success': False, 'error': '姓名不能为空'}), 400
        
        # 获取人员信息
        person = employee_service.get_person(person_id)
        if not person:
            return jsonify({'success': False, 'error': '人员不存在'}), 404
        
        # 更新人员信息
        person.name = data['name']
        person.birth_date = data.get('birth_date')
        person.gender = data.get('gender')
        person.phone = data.get('phone')
        person.email = data.get('email')
        person.address = data.get('address')
        
        employee_service.update_person(person)
        
        return jsonify({'success': True, 'message': '人员信息更新成功'})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/employees', methods=['POST'])
def create_employee():
    """创建新员工（需要先创建 Person，传递 person_id）"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('person_id'):
            return jsonify({'success': False, 'error': 'person_id 不能为空'}), 400
        if not data.get('company_name'):
            return jsonify({'success': False, 'error': '公司名称不能为空'}), 400
        if not data.get('employee_number'):
            return jsonify({'success': False, 'error': '员工编号不能为空'}), 400
        if not data.get('department'):
            return jsonify({'success': False, 'error': '部门不能为空'}), 400
        if not data.get('position'):
            return jsonify({'success': False, 'error': '职位不能为空'}), 400
        if not data.get('hire_date'):
            return jsonify({'success': False, 'error': '入职时间不能为空'}), 400
        
        # 调用 Service 层方法（原子操作：创建员工和入职信息）
        employee_id = employee_service.create_employee_with_employment(
            person_id=data['person_id'],
            company_name=data['company_name'],
            employee_number=data['employee_number'],
            department=data['department'],
            position=data['position'],
            hire_date=data['hire_date'],
            supervisor_id=data.get('supervisor_id')
        )
        
        return jsonify({'success': True, 'message': '员工创建成功', 'id': employee_id})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/employees/<int:employee_id>', methods=['PUT'])
def update_employee(employee_id):
    """更新员工的入职信息（只更新 Employment，不更新 Person，不处理换公司）"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('department'):
            return jsonify({'success': False, 'error': '部门不能为空'}), 400
        if not data.get('position'):
            return jsonify({'success': False, 'error': '职位不能为空'}), 400
        if not data.get('hire_date'):
            return jsonify({'success': False, 'error': '入职时间不能为空'}), 400
        
        # 调用 Service 层方法（封装了判断字段变化、更新或创建的逻辑）
        updated = employee_service.update_employment_info(
            employee_id=employee_id,
            department=data['department'],
            position=data['position'],
            hire_date=data['hire_date'],
            supervisor_id=data.get('supervisor_id'),
            change_reason=data.get('change_reason')
        )
        
        if updated:
            return jsonify({'success': True, 'message': '入职信息更新成功'})
        else:
            return jsonify({'success': True, 'message': '入职信息未发生变化'})
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
    """获取所有员工列表（用于选择上级，只返回active员工）"""
    try:
        company_name = request.args.get('company_name')  # 只返回同一公司的员工
        supervisors = employee_service.get_supervisors(company_name)
        result = [s.to_dict() for s in supervisors]
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/companies', methods=['GET'])
def get_companies():
    """获取所有公司列表（只返回有active员工的）"""
    try:
        companies = employee_service.get_companies()
        return jsonify({'success': True, 'data': companies})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/employees/<int:employee_id>/history', methods=['GET'])
def get_employee_history(employee_id):
    """获取员工的任职历史记录（包含当前任职）
    
    如果员工已换公司，会查找该人员(person_id)在所有公司的任职信息
    """
    try:
        # 调用 Service 层方法，获取对象列表
        history_items = employee_service.get_employee_full_history(employee_id)
        
        # 将对象列表转换为字典列表（用于 JSON 序列化）
        result = [item.to_dict() for item in history_items]
        
        return jsonify({'success': True, 'data': result})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== 考勤记录 API ==========

@api_bp.route('/attendance', methods=['POST'])
def create_attendance():
    """创建考勤记录"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('person_id'):
            return jsonify({'success': False, 'error': '人员ID不能为空'}), 400
        if not data.get('company_name'):
            return jsonify({'success': False, 'error': '公司名称不能为空'}), 400
        if not data.get('attendance_date'):
            return jsonify({'success': False, 'error': '考勤日期不能为空'}), 400
        
        # 创建考勤记录对象
        attendance = Attendance(
            person_id=data['person_id'],
            employee_id=data.get('employee_id'),
            company_name=data['company_name'],
            attendance_date=data['attendance_date'],
            check_in_time=data.get('check_in_time'),
            check_out_time=data.get('check_out_time'),
            status=data.get('status'),
            work_hours=data.get('work_hours'),
            standard_hours=data.get('standard_hours', 8.0),
            overtime_hours=data.get('overtime_hours', 0.0),
            leave_hours=data.get('leave_hours', 0.0),
            remark=data.get('remark')
        )
        
        attendance_id = attendance_service.create_attendance(attendance)
        
        return jsonify({'success': True, 'message': '考勤记录创建成功', 'id': attendance_id})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/attendance/<int:attendance_id>', methods=['GET'])
def get_attendance(attendance_id):
    """获取考勤记录"""
    try:
        attendance = attendance_service.get_attendance_by_id(attendance_id)
        if not attendance:
            return jsonify({'success': False, 'error': '考勤记录不存在'}), 404
        
        return jsonify({'success': True, 'data': attendance.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/attendance', methods=['GET'])
def get_attendance_list():
    """获取考勤记录列表"""
    try:
        person_id = request.args.get('person_id', type=int)
        employee_id = request.args.get('employee_id', type=int)
        company_name = request.args.get('company_name')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        attendance_date = request.args.get('attendance_date')
        
        if attendance_date:
            # 按日期查询
            attendance_list = attendance_service.get_attendance_by_date(attendance_date, company_name)
        elif employee_id:
            # 按员工ID查询
            attendance_list = attendance_service.get_attendance_by_employee(
                employee_id, start_date, end_date
            )
        elif person_id and company_name:
            # 按人员和公司查询
            attendance_list = attendance_service.get_attendance_by_person_and_company(
                person_id, company_name, start_date, end_date
            )
        elif person_id:
            # 按人员查询（跨公司）
            attendance_list = attendance_service.get_attendance_by_person(
                person_id, start_date, end_date
            )
        elif start_date or end_date or company_name:
            # 按日期范围查询所有记录
            attendance_list = attendance_service.get_attendance_by_date_range(
                start_date, end_date, company_name
            )
        else:
            return jsonify({'success': False, 'error': '请提供 person_id、employee_id、attendance_date 或日期范围'}), 400
        
        result = [attendance.to_dict() for attendance in attendance_list]
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/attendance/<int:attendance_id>', methods=['PUT'])
def update_attendance(attendance_id):
    """更新考勤记录"""
    try:
        data = request.get_json()
        
        attendance = attendance_service.get_attendance_by_id(attendance_id)
        if not attendance:
            return jsonify({'success': False, 'error': '考勤记录不存在'}), 404
        
        # 更新字段
        if 'check_in_time' in data:
            attendance.check_in_time = data['check_in_time']
        if 'check_out_time' in data:
            attendance.check_out_time = data['check_out_time']
        if 'status' in data:
            attendance.status = data['status']
        if 'work_hours' in data:
            attendance.work_hours = data['work_hours']
        if 'standard_hours' in data:
            attendance.standard_hours = data['standard_hours']
        if 'overtime_hours' in data:
            attendance.overtime_hours = data['overtime_hours']
        if 'remark' in data:
            attendance.remark = data['remark']
        
        attendance_service.update_attendance(attendance)
        
        return jsonify({'success': True, 'message': '考勤记录更新成功'})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/attendance/<int:attendance_id>', methods=['DELETE'])
def delete_attendance(attendance_id):
    """删除考勤记录"""
    try:
        result = attendance_service.delete_attendance(attendance_id)
        if not result:
            return jsonify({'success': False, 'error': '考勤记录不存在'}), 404
        
        return jsonify({'success': True, 'message': '考勤记录删除成功'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== 请假记录 API ==========

@api_bp.route('/leave-records', methods=['POST'])
def create_leave_record():
    """创建请假记录"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('person_id'):
            return jsonify({'success': False, 'error': '人员ID不能为空'}), 400
        if not data.get('company_name'):
            return jsonify({'success': False, 'error': '公司名称不能为空'}), 400
        if not data.get('leave_date'):
            return jsonify({'success': False, 'error': '请假日期不能为空'}), 400
        if not data.get('leave_type'):
            return jsonify({'success': False, 'error': '请假类型不能为空'}), 400
        if data.get('leave_hours') is None:
            return jsonify({'success': False, 'error': '请假时长不能为空'}), 400
        
        # 创建请假记录对象
        leave_record = LeaveRecord(
            person_id=data['person_id'],
            employee_id=data.get('employee_id'),
            company_name=data['company_name'],
            leave_date=data['leave_date'],
            leave_type=data['leave_type'],
            start_time=data.get('start_time'),
            end_time=data.get('end_time'),
            leave_hours=data['leave_hours'],
            reason=data.get('reason'),
            status=data.get('status', 'approved')
        )
        
        leave_id = attendance_service.create_leave_record(leave_record)
        
        return jsonify({'success': True, 'message': '请假记录创建成功', 'id': leave_id})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/leave-records/<int:leave_id>', methods=['GET'])
def get_leave_record(leave_id):
    """获取请假记录"""
    try:
        leave_record = attendance_service.get_leave_record_by_id(leave_id)
        if not leave_record:
            return jsonify({'success': False, 'error': '请假记录不存在'}), 404
        
        return jsonify({'success': True, 'data': leave_record.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/leave-records', methods=['GET'])
def get_leave_record_list():
    """获取请假记录列表"""
    try:
        person_id = request.args.get('person_id', type=int)
        employee_id = request.args.get('employee_id', type=int)
        company_name = request.args.get('company_name')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if employee_id:
            # 按员工ID查询
            leave_records = attendance_service.get_leave_records_by_employee(
                employee_id, start_date, end_date
            )
        elif person_id and company_name:
            # 按人员和公司查询
            leave_records = attendance_service.get_leave_records_by_person_and_company(
                person_id, company_name, start_date, end_date
            )
        elif person_id:
            # 按人员查询（跨公司）
            leave_records = attendance_service.get_leave_records_by_person(
                person_id, start_date, end_date
            )
        else:
            return jsonify({'success': False, 'error': '请提供 person_id 或 employee_id'}), 400
        
        result = [leave_record.to_dict() for leave_record in leave_records]
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/leave-records/<int:leave_id>', methods=['PUT'])
def update_leave_record(leave_id):
    """更新请假记录"""
    try:
        data = request.get_json()
        
        leave_record = attendance_service.get_leave_record_by_id(leave_id)
        if not leave_record:
            return jsonify({'success': False, 'error': '请假记录不存在'}), 404
        
        # 更新字段
        if 'leave_type' in data:
            leave_record.leave_type = data['leave_type']
        if 'start_time' in data:
            leave_record.start_time = data['start_time']
        if 'end_time' in data:
            leave_record.end_time = data['end_time']
        if 'leave_hours' in data:
            leave_record.leave_hours = data['leave_hours']
        if 'reason' in data:
            leave_record.reason = data['reason']
        if 'status' in data:
            leave_record.status = data['status']
        
        attendance_service.update_leave_record(leave_record)
        
        return jsonify({'success': True, 'message': '请假记录更新成功'})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/leave-records/<int:leave_id>', methods=['DELETE'])
def delete_leave_record(leave_id):
    """删除请假记录"""
    try:
        result = attendance_service.delete_leave_record(leave_id)
        if not result:
            return jsonify({'success': False, 'error': '请假记录不存在'}), 404
        
        return jsonify({'success': True, 'message': '请假记录删除成功'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
