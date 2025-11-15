"""
数据库初始化脚本 - 生成测试数据（支持多公司）
"""
import random
from datetime import datetime, timedelta
from app.services.employee_service import EmployeeService
from app.models import Person, Employee, EmploymentInfo


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

# 公司列表
COMPANIES = ['科技有限公司', '贸易有限公司', '实业有限公司', '集团股份有限公司']

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


def generate_email(employee_number):
    """生成邮箱（使用员工编号）"""
    return f"{employee_number.lower()}@company.com"


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


def init_database():
    """初始化数据库，生成测试数据"""
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
    cursor.execute("DELETE FROM persons")
    conn.commit()
    print("数据已清空")
    
    # 定义两家公司
    company1 = "第一" + random.choice(COMPANIES)
    company2 = "第二" + random.choice(COMPANIES)
    
    print(f"\n公司1: {company1} (30个员工)")
    print(f"公司2: {company2} (40个员工)")
    print("=" * 50)
    
    # 存储员工信息，用于后续生成变动记录
    company1_employees = []
    company2_employees = []
    
    # 存储已使用的手机和邮箱，确保不重复
    used_phones = set()
    used_emails = set()
    
    # ========== 生成公司1的员工（30个）==========
    print(f"\n生成 {company1} 的员工数据...")
    supervisors_company1 = {}  # 存储每个部门的上级关系
    
    for i in range(1, 31):
        # 生成员工编号
        employee_number = f"EMP{str(i).zfill(5)}"
        
        # 生成姓名
        surname = random.choice(SURNAMES)
        given_name = random.choice(GIVEN_NAMES)
        name = surname + given_name
        
        # 生成其他信息（确保手机和邮箱不重复）
        gender = random.choice(GENDERS)
        birth_date = generate_birth_date()
        
        # 生成唯一的手机号
        while True:
            phone = generate_phone()
            if phone not in used_phones:
                used_phones.add(phone)
                break
        
        # 生成唯一的邮箱
        email = generate_email(employee_number)
        while email in used_emails:
            employee_number_alt = f"EMP{str(i).zfill(5)}A"
            email = generate_email(employee_number_alt)
        used_emails.add(email)
        
        # 创建人员
        person = Person(
            name=name,
            birth_date=birth_date,
            gender=gender,
            phone=phone,
            email=email
        )
        
        try:
            # 直接创建新人员，不进行匹配
            person_id = service.create_person(person)
            # 创建员工记录
            conn = service.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO employees (person_id, company_name, employee_number)
                VALUES (?, ?, ?)
            """, (person_id, company1, employee_number))
            employee_id = cursor.lastrowid
            conn.commit()
            
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
            if department in supervisors_company1 and supervisors_company1[department]:
                # 有30%的概率有上级
                if random.random() < 0.3:
                    supervisor_id = random.choice(supervisors_company1[department])
            
            # 创建入职信息
            employment_info = EmploymentInfo(
                employee_id=employee_id,
                company_name=company1,
                department=department,
                position=position,
                hire_date=hire_date,
                supervisor_id=supervisor_id
            )
            
            service.create_employment_info(employment_info)
            
            # 如果是高级职位，加入上级候选列表
            if '经理' in position or '总监' in position or '专家' in position:
                if department not in supervisors_company1:
                    supervisors_company1[department] = []
                supervisors_company1[department].append(employee_id)
            
            company1_employees.append((employee_id, name, department, position, hire_date))
            print(f"  [{i}/30] {name} - {department} {position}")
        except Exception as e:
            print(f"  [{i}/30] 创建员工失败: {name} - {str(e)}")
            continue
    
    # ========== 生成公司2的员工（40个）==========
    print(f"\n生成 {company2} 的员工数据...")
    supervisors_company2 = {}  # 存储每个部门的上级关系
    
    for i in range(1, 41):
        # 生成员工编号（公司2使用不同的编号前缀）
        employee_number = f"EMP{str(i+30).zfill(5)}"
        
        # 生成姓名
        surname = random.choice(SURNAMES)
        given_name = random.choice(GIVEN_NAMES)
        name = surname + given_name
        
        # 生成其他信息（确保手机和邮箱不重复）
        gender = random.choice(GENDERS)
        birth_date = generate_birth_date()
        
        # 生成唯一的手机号
        while True:
            phone = generate_phone()
            if phone not in used_phones:
                used_phones.add(phone)
                break
        
        # 生成唯一的邮箱
        email = generate_email(employee_number)
        while email in used_emails:
            employee_number_alt = f"EMP{str(i+30).zfill(5)}B"
            email = generate_email(employee_number_alt)
        used_emails.add(email)
        
        # 创建人员
        person = Person(
            name=name,
            birth_date=birth_date,
            gender=gender,
            phone=phone,
            email=email
        )
        
        try:
            # 直接创建新人员，不进行匹配
            person_id = service.create_person(person)
            # 创建员工记录
            conn = service.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO employees (person_id, company_name, employee_number)
                VALUES (?, ?, ?)
            """, (person_id, company2, employee_number))
            employee_id = cursor.lastrowid
            conn.commit()
            
            # 随机选择部门
            department = random.choice(DEPARTMENTS)
            
            # 根据部门选择职位
            available_positions = POSITIONS[department]
            if random.random() < 0.7:
                position = random.choice(available_positions[:len(available_positions)//2])
            else:
                position = random.choice(available_positions[len(available_positions)//2:])
            
            # 生成入职日期
            hire_date = generate_hire_date()
            
            # 设置上级
            supervisor_id = None
            if department in supervisors_company2 and supervisors_company2[department]:
                if random.random() < 0.3:
                    supervisor_id = random.choice(supervisors_company2[department])
            
            # 创建入职信息
            employment_info = EmploymentInfo(
                employee_id=employee_id,
                company_name=company2,
                department=department,
                position=position,
                hire_date=hire_date,
                supervisor_id=supervisor_id
            )
            
            service.create_employment_info(employment_info)
            
            # 如果是高级职位，加入上级候选列表
            if '经理' in position or '总监' in position or '专家' in position:
                if department not in supervisors_company2:
                    supervisors_company2[department] = []
                supervisors_company2[department].append(employee_id)
            
            company2_employees.append((employee_id, name, department, position, hire_date))
            print(f"  [{i}/40] {name} - {department} {position}")
        except Exception as e:
            print(f"  [{i}/40] 创建员工失败: {name} - {str(e)}")
            continue
    
    # ========== 为公司1生成任职变动记录（10%，即3个员工）==========
    print(f"\n生成 {company1} 的任职变动记录（10%，3个员工）...")
    change_count = 0
    transfer_count = 0  # 换公司数量
    employees_with_changes = random.sample(company1_employees, min(3, len(company1_employees)))
    
    for employee_id, name, current_department, current_position, base_hire_date in employees_with_changes:
        # 获取当前入职信息
        current_info = service.get_employment_info(employee_id)
        if not current_info:
            continue
        
        # 决定变更类型：升职、降职、换部门、换公司
        # 40% 升职，20% 降职，25% 换部门，15% 换公司
        rand = random.random()
        if rand < 0.15:
            change_type = 'transfer_company'  # 换公司
        elif rand < 0.40:
            change_type = 'promotion'  # 升职
        elif rand < 0.60:
            change_type = 'demotion'  # 降职
        else:
            change_type = 'department'  # 换部门
        
        new_department = current_department
        new_position = current_position
        new_company = company1
        new_hire_date = base_hire_date
        
        # 生成变更原因
        if change_type == 'transfer_company':
            # 换公司
            new_company = company2
            # 在新公司中随机选择部门和职位
            new_department = random.choice(DEPARTMENTS)
            new_position = random.choice(POSITIONS[new_department])
            # 新公司的入职时间（比原公司晚）
            old_hire = datetime.strptime(base_hire_date, '%Y-%m-%d')
            new_hire_date = (old_hire + timedelta(days=random.randint(180, 1095))).strftime('%Y-%m-%d')
            change_reason = f'从 {company1} 转到 {company2}'
        elif change_type == 'promotion':
            # 升职（可能在同一部门或不同部门）
            if random.random() < 0.3:  # 30% 概率换部门
                new_department = random.choice([d for d in DEPARTMENTS if d != current_department])
            
            available_positions = POSITIONS[new_department]
            current_index = -1
            try:
                current_index = available_positions.index(current_position)
            except ValueError:
                # 如果当前职位不在新部门的职位列表中，随机选择一个中级职位
                current_index = len(available_positions) // 2
            
            # 升职：选择更高级的职位
            if current_index >= 0 and current_index < len(available_positions) - 1:
                max_index = min(current_index + random.randint(1, 2), len(available_positions) - 1)
                new_position = available_positions[max_index]
            
            change_reason = random.choice([
                '工作表现优秀，晋升',
                '年度晋升',
                '项目表现突出',
                '个人发展需要'
            ])
        elif change_type == 'demotion':
            # 降职（可能在同一部门或不同部门）
            if random.random() < 0.3:  # 30% 概率换部门
                new_department = random.choice([d for d in DEPARTMENTS if d != current_department])
            
            available_positions = POSITIONS[new_department]
            current_index = -1
            try:
                current_index = available_positions.index(current_position)
            except ValueError:
                current_index = len(available_positions) // 2
            
            # 降职：选择更低级的职位
            if current_index > 0:
                min_index = max(0, current_index - random.randint(1, 2))
                new_position = available_positions[min_index]
            
            change_reason = random.choice([
                '部门调整',
                '组织架构调整',
                '业务需要，调岗',
                '团队重组'
            ])
        else:  # change_type == 'department'
            # 换部门（职位可能调整）
            new_department = random.choice([d for d in DEPARTMENTS if d != current_department])
            # 在新部门中选择一个合适的职位（可能是同级或略低）
            available_positions = POSITIONS[new_department]
            # 随机选择一个职位（偏向中低级）
            position_range = available_positions[:len(available_positions) * 2 // 3]
            new_position = random.choice(position_range)
            
            change_reason = random.choice([
                '部门调整',
                '业务需要，调岗',
                '个人发展需要',
                '组织架构调整'
            ])
        
        # 执行变更
        try:
            if change_type == 'transfer_company':
                # 换公司：更新 employment_info（包括 company_name），就像更新部门一样
                # 生成新公司的员工编号（查找最大的编号）
                conn = service.db.get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT employee_number FROM employees 
                    WHERE company_name = ? 
                    ORDER BY employee_number DESC 
                    LIMIT 1
                """, (new_company,))
                result = cursor.fetchone()
                if result:
                    # 提取编号中的数字部分
                    last_num = int(result[0].replace('EMP', ''))
                    new_emp_count = last_num + 1
                else:
                    new_emp_count = 1
                new_employee_number = f"EMP{new_emp_count:05d}"
                
                # 换公司就是更新 employment_info，包括 company_name
                service.transfer_employee_to_company(
                    employee_id,
                    new_company,
                    new_employee_number,
                    new_department,
                    new_position,
                    new_hire_date,
                    None,  # 上级暂时设为None
                    change_reason
                )
                
                transfer_count += 1
                print(f"  {name}: {company1} {current_department} {current_position} → {new_company} {new_department} {new_position} (原因: {change_reason})")
            else:
                # 同一公司内的变更
                updated = service.update_employment_info(
                    employee_id,
                    company1,
                    new_department,
                    new_position,
                    base_hire_date,  # 入职日期不变
                    None,  # 上级暂时设为None
                    change_reason
                )
                
                if updated:
                    change_count += 1
                    print(f"  {name}: {current_department} {current_position} → {new_department} {new_position} (原因: {change_reason})")
                else:
                    print(f"  {name}: 字段未变化，跳过更新")
        except Exception as e:
            print(f"  更新失败: {name} - {str(e)}")
    
    # ========== 为公司2生成任职变动记录（15%，即6个员工）==========
    print(f"\n生成 {company2} 的任职变动记录（15%，6个员工）...")
    change_count2 = 0
    transfer_count2 = 0  # 换公司数量
    employees_with_changes2 = random.sample(company2_employees, min(6, len(company2_employees)))
    
    for employee_id, name, current_department, current_position, base_hire_date in employees_with_changes2:
        # 获取当前入职信息
        current_info = service.get_employment_info(employee_id)
        if not current_info:
            continue
        
        # 决定变更类型：升职、降职、换部门、换公司
        # 40% 升职，20% 降职，25% 换部门，15% 换公司
        rand = random.random()
        if rand < 0.15:
            change_type = 'transfer_company'  # 换公司
        elif rand < 0.40:
            change_type = 'promotion'  # 升职
        elif rand < 0.60:
            change_type = 'demotion'  # 降职
        else:
            change_type = 'department'  # 换部门
        
        new_department = current_department
        new_position = current_position
        new_company = company2
        new_hire_date = base_hire_date
        
        # 生成变更原因
        if change_type == 'transfer_company':
            # 换公司
            new_company = company1
            # 在新公司中随机选择部门和职位
            new_department = random.choice(DEPARTMENTS)
            new_position = random.choice(POSITIONS[new_department])
            # 新公司的入职时间（比原公司晚）
            old_hire = datetime.strptime(base_hire_date, '%Y-%m-%d')
            new_hire_date = (old_hire + timedelta(days=random.randint(180, 1095))).strftime('%Y-%m-%d')
            change_reason = f'从 {company2} 转到 {company1}'
        elif change_type == 'promotion':
            # 升职（可能在同一部门或不同部门）
            if random.random() < 0.3:  # 30% 概率换部门
                new_department = random.choice([d for d in DEPARTMENTS if d != current_department])
            
            available_positions = POSITIONS[new_department]
            current_index = -1
            try:
                current_index = available_positions.index(current_position)
            except ValueError:
                # 如果当前职位不在新部门的职位列表中，随机选择一个中级职位
                current_index = len(available_positions) // 2
            
            # 升职：选择更高级的职位
            if current_index >= 0 and current_index < len(available_positions) - 1:
                max_index = min(current_index + random.randint(1, 2), len(available_positions) - 1)
                new_position = available_positions[max_index]
            
            change_reason = random.choice([
                '工作表现优秀，晋升',
                '年度晋升',
                '项目表现突出',
                '个人发展需要'
            ])
        elif change_type == 'demotion':
            # 降职（可能在同一部门或不同部门）
            if random.random() < 0.3:  # 30% 概率换部门
                new_department = random.choice([d for d in DEPARTMENTS if d != current_department])
            
            available_positions = POSITIONS[new_department]
            current_index = -1
            try:
                current_index = available_positions.index(current_position)
            except ValueError:
                current_index = len(available_positions) // 2
            
            # 降职：选择更低级的职位
            if current_index > 0:
                min_index = max(0, current_index - random.randint(1, 2))
                new_position = available_positions[min_index]
            
            change_reason = random.choice([
                '部门调整',
                '组织架构调整',
                '业务需要，调岗',
                '团队重组'
            ])
        else:  # change_type == 'department'
            # 换部门（职位可能调整）
            new_department = random.choice([d for d in DEPARTMENTS if d != current_department])
            # 在新部门中选择一个合适的职位（可能是同级或略低）
            available_positions = POSITIONS[new_department]
            # 随机选择一个职位（偏向中低级）
            position_range = available_positions[:len(available_positions) * 2 // 3]
            new_position = random.choice(position_range)
            
            change_reason = random.choice([
                '部门调整',
                '业务需要，调岗',
                '个人发展需要',
                '组织架构调整'
            ])
        
        # 执行变更
        try:
            if change_type == 'transfer_company':
                # 换公司：更新 employment_info（包括 company_name），就像更新部门一样
                # 生成新公司的员工编号（查找最大的编号）
                conn = service.db.get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT employee_number FROM employees 
                    WHERE company_name = ? 
                    ORDER BY employee_number DESC 
                    LIMIT 1
                """, (new_company,))
                result = cursor.fetchone()
                if result:
                    # 提取编号中的数字部分
                    last_num = int(result[0].replace('EMP', ''))
                    new_emp_count = last_num + 1
                else:
                    new_emp_count = 1
                new_employee_number = f"EMP{new_emp_count:05d}"
                
                # 换公司就是更新 employment_info，包括 company_name
                service.transfer_employee_to_company(
                    employee_id,
                    new_company,
                    new_employee_number,
                    new_department,
                    new_position,
                    new_hire_date,
                    None,  # 上级暂时设为None
                    change_reason
                )
                
                transfer_count2 += 1
                print(f"  {name}: {company2} {current_department} {current_position} → {new_company} {new_department} {new_position} (原因: {change_reason})")
            else:
                # 同一公司内的变更
                updated = service.update_employment_info(
                    employee_id,
                    company2,
                    new_department,
                    new_position,
                    base_hire_date,  # 入职日期不变
                    None,  # 上级暂时设为None
                    change_reason
                )
                
                if updated:
                    change_count2 += 1
                    print(f"  {name}: {current_department} {current_position} → {new_department} {new_position} (原因: {change_reason})")
                else:
                    print(f"  {name}: 字段未变化，跳过更新")
        except Exception as e:
            print(f"  更新失败: {name} - {str(e)}")
    
    # 统计信息
    print("\n" + "=" * 50)
    print("数据库初始化完成！")
    print("=" * 50)
    
    cursor.execute("SELECT COUNT(*) FROM persons")
    person_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM employees")
    employee_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM employment_info")
    employment_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM employment_info_history")
    history_count = cursor.fetchone()[0]
    
    print(f"人员总数: {person_count}")
    print(f"员工总数: {employee_count}")
    print(f"  - {company1}: {len(company1_employees)} 人")
    print(f"  - {company2}: {len(company2_employees)} 人")
    print(f"入职信息记录: {employment_count}")
    print(f"任职变动历史记录: {history_count}")
    print(f"  - {company1}: {change_count} 条变动记录（其中 {transfer_count} 人换公司）")
    print(f"  - {company2}: {change_count2} 条变动记录（其中 {transfer_count2} 人换公司）")
    print("=" * 50)


if __name__ == '__main__':
    try:
        init_database()
    except Exception as e:
        print(f"\n错误: {str(e)}")
        import traceback
        traceback.print_exc()
