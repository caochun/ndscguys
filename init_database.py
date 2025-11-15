"""
数据库初始化脚本 - 生成测试数据
"""
import random
from datetime import datetime, timedelta
from employee_service import EmployeeService
from model import Employee, EmploymentInfo


# 中文姓氏
SURNAMES = ['王', '李', '张', '刘', '陈', '杨', '赵', '黄', '周', '吴', 
            '徐', '孙', '胡', '朱', '高', '林', '何', '郭', '马', '罗',
            '梁', '宋', '郑', '谢', '韩', '唐', '冯', '于', '董', '萧']

# 中文名字（常用字）
GIVEN_NAMES = ['伟', '芳', '娜', '秀英', '敏', '静', '丽', '强', '磊', '军',
               '洋', '勇', '艳', '杰', '娟', '涛', '明', '超', '秀兰', '霞',
               '平', '刚', '桂英', '建华', '文', '华', '红', '建国', '建军', '志强',
               '秀华', '秀云', '秀梅', '秀芳', '秀兰', '秀珍', '秀英', '秀莲', '秀琴', '秀霞',
               '文静', '文娟', '文秀', '文英', '文华', '文丽', '文芳', '文敏', '文慧', '文雅']

# 部门列表
DEPARTMENTS = ['技术部', '产品部', '运营部', '市场部', '销售部', '人事部', '财务部', '行政部', '设计部', '客服部']

# 职位列表（按级别）
POSITIONS = {
    '技术部': ['初级工程师', '中级工程师', '高级工程师', '技术专家', '技术经理', '技术总监'],
    '产品部': ['产品助理', '产品专员', '产品经理', '高级产品经理', '产品总监'],
    '运营部': ['运营专员', '运营经理', '高级运营经理', '运营总监'],
    '市场部': ['市场专员', '市场经理', '高级市场经理', '市场总监'],
    '销售部': ['销售代表', '销售经理', '高级销售经理', '销售总监'],
    '人事部': ['人事专员', '人事经理', '高级人事经理', '人事总监'],
    '财务部': ['会计', '财务经理', '高级财务经理', '财务总监'],
    '行政部': ['行政专员', '行政经理', '高级行政经理', '行政总监'],
    '设计部': ['设计师', '高级设计师', '设计经理', '设计总监'],
    '客服部': ['客服专员', '客服经理', '高级客服经理', '客服总监']
}

# 性别
GENDERS = ['男', '女']


def generate_phone():
    """生成手机号"""
    prefixes = ['130', '131', '132', '133', '134', '135', '136', '137', '138', '139',
                '150', '151', '152', '153', '155', '156', '157', '158', '159',
                '180', '181', '182', '183', '184', '185', '186', '187', '188', '189']
    return random.choice(prefixes) + ''.join([str(random.randint(0, 9)) for _ in range(8)])


def generate_email(name, employee_number):
    """生成邮箱"""
    return f"{name.lower()}{employee_number}@company.com"


def generate_birth_date():
    """生成出生日期（25-45岁之间）"""
    start_date = datetime.now() - timedelta(days=45*365)
    end_date = datetime.now() - timedelta(days=25*365)
    random_days = random.randint(0, (end_date - start_date).days)
    birth_date = start_date + timedelta(days=random_days)
    return birth_date.strftime('%Y-%m-%d')


def generate_hire_date():
    """生成入职日期（1-5年前）"""
    start_date = datetime.now() - timedelta(days=5*365)
    end_date = datetime.now() - timedelta(days=30)  # 至少30天前
    random_days = random.randint(0, (end_date - start_date).days)
    hire_date = start_date + timedelta(days=random_days)
    return hire_date.strftime('%Y-%m-%d')


def generate_position_change_date(base_hire_date, months_ago):
    """生成职位变更日期"""
    base = datetime.strptime(base_hire_date, '%Y-%m-%d')
    change_date = base + timedelta(days=months_ago * 30)
    # 确保变更日期不晚于今天
    if change_date > datetime.now():
        change_date = datetime.now() - timedelta(days=random.randint(1, 30))
    return change_date.strftime('%Y-%m-%d')


def init_database():
    """初始化数据库，生成100个员工数据"""
    service = EmployeeService()
    
    print("开始初始化数据库...")
    print("=" * 50)
    
    # 清空现有数据（可选，谨慎使用）
    print("清空现有数据...")
    conn = service.db.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM employment_info_history")
    cursor.execute("DELETE FROM employment_info")
    cursor.execute("DELETE FROM employees")
    conn.commit()
    print("数据已清空")
    
    employees = []
    employee_ids = []
    
    # 生成100个员工
    print("\n生成员工数据...")
    for i in range(1, 101):
        # 生成员工编号
        employee_number = f"EMP{str(i).zfill(5)}"
        
        # 生成姓名
        surname = random.choice(SURNAMES)
        given_name = random.choice(GIVEN_NAMES)
        name = surname + given_name
        
        # 生成其他信息
        gender = random.choice(GENDERS)
        birth_date = generate_birth_date()
        phone = generate_phone()
        email = generate_email(name, employee_number)
        
        # 创建员工
        employee = Employee(
            employee_number=employee_number,
            name=name,
            birth_date=birth_date,
            gender=gender,
            phone=phone,
            email=email
        )
        
        try:
            employee_id = service.create_employee(employee)
            employees.append((employee_id, employee))
            employee_ids.append(employee_id)
            print(f"  [{i}/100] 创建员工: {name} ({employee_number})")
        except Exception as e:
            print(f"  [{i}/100] 创建员工失败: {name} - {str(e)}")
            continue
    
    print(f"\n成功创建 {len(employees)} 个员工")
    
    # 为每个员工创建入职信息
    print("\n生成入职信息...")
    supervisors = {}  # 存储每个部门的上级关系
    
    for idx, (employee_id, employee) in enumerate(employees):
        # 随机选择部门
        department = random.choice(DEPARTMENTS)
        
        # 根据部门选择职位（新员工通常是初级职位）
        available_positions = POSITIONS[department]
        # 70% 概率是初级职位，30% 概率是中级职位
        if random.random() < 0.7:
            position = random.choice(available_positions[:len(available_positions)//2])
        else:
            position = random.choice(available_positions[len(available_positions)//2:])
        
        # 生成入职日期
        hire_date = generate_hire_date()
        
        # 设置上级（从同部门的高级职位员工中选择）
        supervisor_id = None
        if department in supervisors and supervisors[department]:
            # 有30%的概率有上级
            if random.random() < 0.3:
                supervisor_id = random.choice(supervisors[department])
        
        # 创建入职信息
        employment_info = EmploymentInfo(
            employee_id=employee_id,
            department=department,
            position=position,
            hire_date=hire_date,
            supervisor_id=supervisor_id
        )
        
        try:
            service.create_employment_info(employment_info)
            
            # 如果是高级职位，加入上级候选列表
            if '经理' in position or '总监' in position or '专家' in position:
                if department not in supervisors:
                    supervisors[department] = []
                supervisors[department].append(employee_id)
            
            print(f"  [{idx+1}/{len(employees)}] {employee.name} - {department} {position}")
        except Exception as e:
            print(f"  [{idx+1}/{len(employees)}] 创建入职信息失败: {employee.name} - {str(e)}")
    
    # 为部分员工生成职位变更历史（30%的员工会有职位变更）
    print("\n生成职位变更历史...")
    change_count = 0
    employees_with_changes = random.sample(employees, min(30, len(employees)))
    
    for employee_id, employee in employees_with_changes:
        # 获取当前入职信息
        current_info = service.get_employment_info(employee_id)
        if not current_info:
            continue
        
        # 决定变更次数（1-3次）
        change_times = random.randint(1, 3)
        
        current_department = current_info.department
        current_position = current_info.position
        current_hire_date = current_info.hire_date
        current_version = current_info.version
        
        for change_idx in range(change_times):
            # 决定变更类型：调部门、升职、或两者都有
            change_type = random.choice(['department', 'promotion', 'both'])
            
            new_department = current_department
            new_position = current_position
            
            if change_type in ['department', 'both']:
                # 调部门（30%概率）
                if random.random() < 0.3:
                    new_department = random.choice([d for d in DEPARTMENTS if d != current_department])
                    # 调部门后，职位可能需要调整
                    new_position = random.choice(POSITIONS[new_department][:len(POSITIONS[new_department])//2])
            
            if change_type in ['promotion', 'both']:
                # 升职（70%概率）
                if random.random() < 0.7:
                    available_positions = POSITIONS[new_department]
                    current_index = -1
                    try:
                        current_index = available_positions.index(current_position)
                    except ValueError:
                        pass
                    
                    # 如果找到当前职位，选择更高级的职位
                    if current_index >= 0 and current_index < len(available_positions) - 1:
                        # 升1-2级
                        max_index = min(current_index + random.randint(1, 2), len(available_positions) - 1)
                        new_position = available_positions[max_index]
            
            # 生成变更日期（在入职日期之后，但不超过现在）
            hire_datetime = datetime.strptime(current_hire_date, '%Y-%m-%d')
            months_after_hire = random.randint(3, 24)  # 入职后3-24个月
            change_date = hire_datetime + timedelta(days=months_after_hire * 30)
            if change_date > datetime.now():
                change_date = datetime.now() - timedelta(days=random.randint(1, 30))
            
            # 生成变更原因
            reasons = [
                '工作表现优秀，晋升',
                '部门调整',
                '业务需要，调岗',
                '个人发展需要',
                '组织架构调整',
                '年度晋升',
                '项目表现突出',
                '团队重组'
            ]
            change_reason = random.choice(reasons)
            
            # 更新入职信息（会自动记录历史）
            try:
                service.update_employment_info(
                    employee_id,
                    new_department,
                    new_position,
                    current_hire_date,  # 入职日期不变
                    None,  # 上级暂时设为None，可以后续优化
                    change_reason
                )
                
                current_department = new_department
                current_position = new_position
                change_count += 1
                
                print(f"  {employee.name}: {current_department} {current_position} (变更原因: {change_reason})")
            except Exception as e:
                print(f"  更新失败: {employee.name} - {str(e)}")
    
    print(f"\n成功生成 {change_count} 条职位变更记录")
    
    # 统计信息
    print("\n" + "=" * 50)
    print("数据库初始化完成！")
    print("=" * 50)
    
    cursor.execute("SELECT COUNT(*) FROM employees")
    employee_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM employment_info")
    employment_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM employment_info_history")
    history_count = cursor.fetchone()[0]
    
    print(f"员工总数: {employee_count}")
    print(f"入职信息记录: {employment_count}")
    print(f"职位变更历史记录: {history_count}")
    print("=" * 50)


if __name__ == '__main__':
    try:
        init_database()
    except Exception as e:
        print(f"\n错误: {str(e)}")
        import traceback
        traceback.print_exc()

