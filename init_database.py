"""
数据库初始化脚本 - 生成测试数据（支持多公司）
"""
import random
from datetime import datetime, timedelta
from app.services.employee_service import EmployeeService
from app.services.attendance_service import AttendanceService
from app.models import Person, Employment, Attendance, LeaveRecord


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

# 江苏省城市列表
JIANGSU_CITIES = ['南京市', '苏州市', '无锡市', '常州市', '镇江市', '扬州市', '泰州市', 
                  '南通市', '盐城市', '淮安市', '宿迁市', '徐州市', '连云港市']

# 江苏省区县列表（部分）
JIANGSU_DISTRICTS = {
    '南京市': ['玄武区', '秦淮区', '建邺区', '鼓楼区', '浦口区', '栖霞区', '雨花台区', '江宁区', '六合区', '溧水区', '高淳区'],
    '苏州市': ['虎丘区', '吴中区', '相城区', '姑苏区', '吴江区', '常熟市', '张家港市', '昆山市', '太仓市'],
    '无锡市': ['锡山区', '惠山区', '滨湖区', '梁溪区', '新吴区', '江阴市', '宜兴市'],
    '常州市': ['天宁区', '钟楼区', '新北区', '武进区', '金坛区', '溧阳市'],
    '镇江市': ['京口区', '润州区', '丹徒区', '丹阳市', '扬中市', '句容市'],
    '扬州市': ['广陵区', '邗江区', '江都区', '宝应县', '仪征市', '高邮市'],
    '泰州市': ['海陵区', '高港区', '姜堰区', '兴化市', '靖江市', '泰兴市'],
    '南通市': ['崇川区', '港闸区', '通州区', '如东县', '启东市', '如皋市', '海门市', '海安市'],
    '盐城市': ['亭湖区', '盐都区', '大丰区', '响水县', '滨海县', '阜宁县', '射阳县', '建湖县', '东台市'],
    '淮安市': ['淮安区', '淮阴区', '清江浦区', '洪泽区', '涟水县', '盱眙县', '金湖县'],
    '宿迁市': ['宿城区', '宿豫区', '沭阳县', '泗阳县', '泗洪县'],
    '徐州市': ['鼓楼区', '云龙区', '贾汪区', '泉山区', '铜山区', '丰县', '沛县', '睢宁县', '新沂市', '邳州市'],
    '连云港市': ['连云区', '海州区', '赣榆区', '东海县', '灌云县', '灌南县']
}

# 街道/路名（部分）
STREETS = ['中山路', '解放路', '人民路', '建设路', '和平路', '胜利路', '光明路', '文化路', 
          '新华路', '青年路', '友谊路', '团结路', '民主路', '自由路', '幸福路', '和谐路',
          '科技路', '创新路', '发展路', '前进路', '希望路', '阳光路', '春风路', '秋月路']


def generate_phone():
    """生成手机号"""
    prefixes = ['130', '131', '132', '133', '134', '135', '136', '137', '138', '139',
                '150', '151', '152', '153', '155', '156', '157', '158', '159',
                '180', '181', '182', '183', '184', '185', '186', '187', '188', '189']
    return random.choice(prefixes) + ''.join([str(random.randint(0, 9)) for _ in range(8)])


def generate_email(employee_number):
    """生成邮箱（使用员工编号）"""
    return f"{employee_number.lower()}@company.com"


def generate_address():
    """生成江苏省的地址"""
    city = random.choice(JIANGSU_CITIES)
    district = random.choice(JIANGSU_DISTRICTS.get(city, ['市辖区']))
    street = random.choice(STREETS)
    number = random.randint(1, 999)
    return f"江苏省{city}{district}{street}{number}号"


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


def get_next_employee_number(service, company_name, base_number=0):
    """
    获取下一个员工编号
    
    Args:
        service: EmployeeService 实例
        company_name: 公司名称
        base_number: 基础编号（用于计算）
        
    Returns:
        下一个员工编号
    """
    max_number = service.get_max_employee_number(company_name)
    if max_number:
        try:
            num_str = max_number.replace('EMP', '').replace('emp', '')
            last_num = int(num_str)
            return f"EMP{last_num + 1:05d}"
        except (ValueError, AttributeError):
            pass
    
    # 如果没有找到或解析失败，使用基础编号
    return f"EMP{base_number:05d}"


def init_database():
    """初始化数据库，生成测试数据"""
    service = EmployeeService()
    
    print("开始初始化数据库...")
    print("=" * 50)
    
    # 清空现有数据（可选，谨慎使用）
    print("清空现有数据...")
    service.clear_all_data()
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
        
        # 创建人员对象
        person = Person(
            name=name,
            birth_date=birth_date,
            gender=gender,
            phone=phone,
            email=email,
            address=generate_address()
        )
        
        try:
            # 使用 Service 层创建员工（会自动处理人员匹配或创建）
            employee_id = service.create_employee(person, company1, employee_number)
            
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
            employment = Employment(
                employee_id=employee_id,
                department=department,
                position=position,
                hire_date=hire_date,
                supervisor_id=supervisor_id
            )
            
            service.create_employment(employment)
            
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
        
        # 创建人员对象
        person = Person(
            name=name,
            birth_date=birth_date,
            gender=gender,
            phone=phone,
            email=email,
            address=generate_address()
        )
        
        try:
            # 使用 Service 层创建员工
            employee_id = service.create_employee(person, company2, employee_number)
            
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
            employment = Employment(
                employee_id=employee_id,
                department=department,
                position=position,
                hire_date=hire_date,
                supervisor_id=supervisor_id
            )
            
            service.create_employment(employment)
            
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
    
    # 确保至少有一个换公司的案例（如果员工数量足够）
    ensure_transfer = len(employees_with_changes) > 0 and len(company2_employees) > 0
    
    for idx, (employee_id, name, current_department, current_position, base_hire_date) in enumerate(employees_with_changes):
        # 获取当前入职信息
        current_employment = service.get_employment(employee_id)
        if not current_employment:
            continue
        
        # 从当前employment获取部门和职位
        current_department = current_employment.department
        current_position = current_employment.position
        
        # 决定变更类型：升职、降职、换部门、换公司
        # 如果还没有换公司的案例，且这是第一个员工，强制换公司
        if ensure_transfer and transfer_count == 0 and idx == 0:
            change_type = 'transfer_company'  # 换公司
        else:
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
                # 换公司：使用 Service 层获取下一个员工编号
                max_number = service.get_max_employee_number(new_company)
                if max_number:
                    try:
                        num_str = max_number.replace('EMP', '').replace('emp', '')
                        last_num = int(num_str)
                        new_emp_count = last_num + 1
                    except (ValueError, AttributeError):
                        new_emp_count = 1
                else:
                    new_emp_count = 1
                new_employee_number = f"EMP{new_emp_count:05d}"
                
                # 换公司：创建新employee记录
                new_employee_id = service.transfer_employee_to_company(
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
                updated = service.update_employment(
                    employee_id,
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
    
    # 确保至少有一个换公司的案例（如果员工数量足够）
    ensure_transfer2 = len(employees_with_changes2) > 0 and len(company1_employees) > 0
    
    for idx, (employee_id, name, current_department, current_position, base_hire_date) in enumerate(employees_with_changes2):
        # 获取当前入职信息
        current_employment = service.get_employment(employee_id)
        if not current_employment:
            continue
        
        # 从当前employment获取部门和职位
        current_department = current_employment.department
        current_position = current_employment.position
        
        # 决定变更类型：升职、降职、换部门、换公司
        # 如果还没有换公司的案例，且这是第一个员工，强制换公司
        if ensure_transfer2 and transfer_count2 == 0 and idx == 0:
            change_type = 'transfer_company'  # 换公司
        else:
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
                # 换公司：使用 Service 层获取下一个员工编号
                max_number = service.get_max_employee_number(new_company)
                if max_number:
                    try:
                        num_str = max_number.replace('EMP', '').replace('emp', '')
                        last_num = int(num_str)
                        new_emp_count = last_num + 1
                    except (ValueError, AttributeError):
                        new_emp_count = 1
                else:
                    new_emp_count = 1
                new_employee_number = f"EMP{new_emp_count:05d}"
                
                # 换公司：创建新employee记录
                new_employee_id = service.transfer_employee_to_company(
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
                updated = service.update_employment(
                    employee_id,
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
    
    stats = service.get_statistics()
    
    print(f"人员总数: {stats['person_count']}")
    print(f"员工总数: {stats['employee_count']}")
    print(f"  - {company1}: {len(company1_employees)} 人")
    print(f"  - {company2}: {len(company2_employees)} 人")
    print(f"入职信息记录: {stats['employment_count']}")
    print(f"任职变动历史记录: {stats['history_count']}")
    print(f"  - {company1}: {change_count} 条变动记录（其中 {transfer_count} 人换公司）")
    print(f"  - {company2}: {change_count2} 条变动记录（其中 {transfer_count2} 人换公司）")
    print("=" * 50)
    
    # ========== 生成考勤和请假数据 ==========
    print("\n生成考勤和请假数据...")
    print("=" * 50)
    
    attendance_service = AttendanceService()
    
    # 获取所有活跃员工
    all_employees = service.get_employees(status='active')
    
    # 生成最近30天的考勤数据
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    attendance_count = 0
    leave_count = 0
    
    # 请假类型
    LEAVE_TYPES = ['病假', '事假', '年假', '调休', '产假', '婚假']
    
    for employee in all_employees:
        person_id = employee.person_id
        company_name = employee.company_name
        employee_id = employee.id
        
        # 获取该员工在公司的工作日期（从入职日期开始）
        employment = service.get_employment(employee_id)
        if not employment:
            continue
        
        hire_date = datetime.strptime(employment.hire_date, '%Y-%m-%d').date()
        work_start_date = max(hire_date, start_date)
        
        # 为每个工作日生成考勤记录
        current_date = work_start_date
        while current_date <= end_date:
            # 跳过周末（简化处理，实际应该考虑节假日）
            if current_date.weekday() >= 5:  # 周六、周日
                current_date += timedelta(days=1)
                continue
            
            # 30% 概率请假
            if random.random() < 0.3:
                # 生成请假记录
                leave_type = random.choice(LEAVE_TYPES)
                # 请假时长：50% 全天（8小时），30% 半天（4小时），20% 其他时长
                rand = random.random()
                if rand < 0.5:
                    leave_hours = 8.0
                elif rand < 0.8:
                    leave_hours = 4.0
                else:
                    leave_hours = random.choice([2.0, 3.0, 6.0])
                
                leave_record = LeaveRecord(
                    person_id=person_id,
                    employee_id=employee_id,
                    company_name=company_name,
                    leave_date=current_date.strftime('%Y-%m-%d'),
                    leave_type=leave_type,
                    leave_hours=leave_hours,
                    reason=f"{leave_type}原因",
                    status='approved'
                )
                
                try:
                    attendance_service.create_leave_record(leave_record)
                    leave_count += 1
                except Exception as e:
                    print(f"  创建请假记录失败: {str(e)}")
            
            # 生成考勤记录（如果请假时长 < 8小时，仍然有考勤记录）
            # 标准上班时间 9:00，下班时间 18:00
            standard_start = datetime.combine(current_date, datetime.strptime('09:00', '%H:%M').time())
            standard_end = datetime.combine(current_date, datetime.strptime('18:00', '%H:%M').time())
            
            # 签到时间：90% 正常（9:00-9:30），10% 迟到（9:30-10:00）
            if random.random() < 0.9:
                # 正常签到
                check_in_delta = timedelta(minutes=random.randint(0, 30))
            else:
                # 迟到
                check_in_delta = timedelta(minutes=random.randint(30, 90))
            
            check_in_time = standard_start + check_in_delta
            
            # 签退时间：90% 正常（17:30-18:30），10% 早退（17:00-17:30）
            if random.random() < 0.9:
                # 正常签退
                check_out_delta = timedelta(minutes=random.randint(-30, 30))
            else:
                # 早退
                check_out_delta = timedelta(minutes=random.randint(-60, -30))
            
            check_out_time = standard_end + check_out_delta
            
            # 创建考勤记录
            attendance = Attendance(
                person_id=person_id,
                employee_id=employee_id,
                company_name=company_name,
                attendance_date=current_date.strftime('%Y-%m-%d'),
                check_in_time=check_in_time.strftime('%Y-%m-%d %H:%M:%S'),
                check_out_time=check_out_time.strftime('%Y-%m-%d %H:%M:%S'),
                standard_hours=8.0
            )
            
            try:
                attendance_service.create_attendance(attendance)
                attendance_count += 1
            except Exception as e:
                # 如果记录已存在（可能是唯一约束），尝试更新
                try:
                    existing = attendance_service.get_attendance_by_person_and_company(
                        person_id, company_name, 
                        current_date.strftime('%Y-%m-%d'),
                        current_date.strftime('%Y-%m-%d')
                    )
                    if existing:
                        existing[0].check_in_time = check_in_time.strftime('%Y-%m-%d %H:%M:%S')
                        existing[0].check_out_time = check_out_time.strftime('%Y-%m-%d %H:%M:%S')
                        attendance_service.update_attendance(existing[0])
                        attendance_count += 1
                except:
                    pass
            
            current_date += timedelta(days=1)
    
    print(f"生成考勤记录: {attendance_count} 条")
    print(f"生成请假记录: {leave_count} 条")
    print("=" * 50)


if __name__ == '__main__':
    try:
        init_database()
    except Exception as e:
        print(f"\n错误: {str(e)}")
        import traceback
        traceback.print_exc()
