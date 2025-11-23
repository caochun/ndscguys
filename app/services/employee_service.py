"""
员工信息管理服务
"""
from typing import List, Optional, Dict
from dataclasses import dataclass
from app.models import Person, Employee, Employment, EmploymentHistory
from app.daos import PersonDAO, EmployeeDAO, EmploymentDAO


@dataclass
class EmploymentHistoryItem:
    """任职历史记录项（包含 Employment/EmploymentHistory 和 Employee 信息）"""
    employment: Optional[Employment]  # 当前任职信息（如果是当前记录）
    employment_history: Optional[EmploymentHistory]  # 历史记录（如果是历史记录）
    employee: Employee  # 所属的员工记录（用于获取 company_name, employee_number）
    is_current: bool  # 是否为当前查看的 employee
    
    def to_dict(self) -> Dict:
        """转换为字典（用于 JSON 序列化）"""
        if self.employment:
            # 当前任职信息
            return {
                'id': self.employment.id,
                'version': self.employment.version,
                'department': self.employment.department,
                'position': self.employment.position,
                'hire_date': self.employment.hire_date,
                'supervisor_id': self.employment.supervisor_id,
                'employee_type': getattr(self.employment, 'employee_type', '正式员工'),
                'changed_at': self.employment.updated_at or '',  # 使用updated_at作为时间戳
                'change_reason': None,  # 当前任职没有变更原因
                'company_name': self.employee.company_name,
                'employee_number': self.employee.employee_number,
                'is_current': self.is_current
            }
        else:
            # 历史记录
            return {
                'id': self.employment_history.id,
                'version': self.employment_history.version,
                'department': self.employment_history.department,
                'position': self.employment_history.position,
                'hire_date': self.employment_history.hire_date,
                'supervisor_id': self.employment_history.supervisor_id,
                'employee_type': getattr(self.employment_history, 'employee_type', '正式员工'),
                'changed_at': self.employment_history.changed_at or '',
                'change_reason': self.employment_history.change_reason,
                'company_name': self.employee.company_name,
                'employee_number': self.employee.employee_number,
                'is_current': False  # 历史记录总是 False
            }


@dataclass
class EmployeeWithEmployment:
    """员工完整信息（包含 Person、Employee 和 Employment）"""
    person: Optional[Person]
    employee: Employee
    employment: Optional[Employment]
    has_history: bool
    
    def to_dict(self) -> Dict:
        """转换为字典（用于 JSON 序列化）"""
        return {
            'person': self.person,
            'employee': self.employee,
            'employment': self.employment,
            'has_history': self.has_history
        }


@dataclass
class SupervisorInfo:
    """上级信息"""
    id: int
    name: str
    employee_number: str
    company_name: str
    
    def to_dict(self) -> Dict:
        """转换为字典（用于 JSON 序列化）"""
        return {
            'id': self.id,
            'name': self.name,
            'employee_number': self.employee_number,
            'company_name': self.company_name
        }


@dataclass
class PersonWorkHistoryItem:
    """人员工作历史项"""
    employee_id: int
    company_name: str
    employee_number: str
    department: Optional[str]
    position: Optional[str]
    hire_date: Optional[str]
    
    def to_dict(self) -> Dict:
        """转换为字典（用于 JSON 序列化）"""
        return {
            'employee_id': self.employee_id,
            'company_name': self.company_name,
            'employee_number': self.employee_number,
            'department': self.department,
            'position': self.position,
            'hire_date': self.hire_date
        }


class EmployeeService:
    """员工信息管理服务类"""
    
    def __init__(self):
        self.person_dao = PersonDAO()
        self.employee_dao = EmployeeDAO()
        self.employment_dao = EmploymentDAO()
    
    # ========== 员工管理 ==========
    
    def create_employee_with_employment(
        self,
        person_id: int,
        company_name: str,
        employee_number: str,
        department: str,
        position: str,
        hire_date: str,
        supervisor_id: Optional[int] = None,
        employee_type: str = '正式员工'
    ) -> int:
        """
        创建员工和入职信息（原子操作）
        
        Args:
            person_id: 人员ID（必填，应该先通过其他接口创建 Person）
            company_name: 公司名称（必填）
            employee_number: 员工编号（必填）
            department: 部门（必填）
            position: 职位（必填）
            hire_date: 入职时间（必填）
            supervisor_id: 上级ID（可选）
        
        Returns:
            employee_id: 新创建的员工ID
        
        Raises:
            ValueError: person_id 不存在、参数验证失败、员工编号重复等
        """
        # 1. 验证 person_id 是否存在
        person = self.person_dao.get_by_id(person_id)
        if not person:
            raise ValueError(f"人员ID {person_id} 不存在")
        
        # 2. 验证必填字段
        if not company_name:
            raise ValueError("公司名称不能为空")
        if not employee_number:
            raise ValueError("员工编号不能为空")
        if not department:
            raise ValueError("部门不能为空")
        if not position:
            raise ValueError("职位不能为空")
        if not hire_date:
            raise ValueError("入职时间不能为空")
        
        # 3. 创建员工记录
        employee_id = self.employee_dao.create(person_id, company_name, employee_number, 'active')
        
        # 4. 创建入职信息
        employment = Employment(
            employee_id=employee_id,
            department=department,
            position=position,
            hire_date=hire_date,
            supervisor_id=supervisor_id,
            employee_type=employee_type,
            version=1
        )
        self.employment_dao.create(employment)
        
        return employee_id
    
    def get_employee(self, employee_id: int) -> Optional[Employee]:
        """根据ID获取员工信息"""
        return self.employee_dao.get_by_id(employee_id)
    
    def get_employee_by_number(self, company_name: str, employee_number: str) -> Optional[Employee]:
        """根据公司名称和员工编号获取员工信息"""
        return self.employee_dao.get_by_number(company_name, employee_number)
    
    def get_employees(self, company_name: Optional[str] = None, status: Optional[str] = 'active') -> List[Employee]:
        """
        获取员工列表（仅返回Employee对象）
        
        Args:
            company_name: 如果提供，只返回该公司的员工
            status: 员工状态筛选，默认只返回 'active' 员工。如果为 None，返回所有状态的员工
        """
        return self.employee_dao.get_all(company_name, status)
    
    def delete_employee(self, employee_id: int) -> bool:
        """删除员工（不会删除人员信息）"""
        return self.employee_dao.delete(employee_id)
    
    # ========== 入职信息管理 ==========
    
    def create_employment(self, employment: Employment) -> int:
        """
        创建入职信息（首次入职）
        
        Args:
            employment: 入职信息对象
            
        Returns:
            新创建的入职信息ID
        """
        return self.employment_dao.create(employment)
    
    def get_employment(self, employee_id: int) -> Optional[Employment]:
        """获取员工的当前入职信息"""
        return self.employment_dao.get_by_employee_id(employee_id)
    
    def get_employees_by_person_id(self, person_id: int) -> List[Employee]:
        """
        获取指定 person 的所有 employee 记录
        
        Args:
            person_id: 人员ID
        
        Returns:
            该 person 的所有 employee 记录列表
        """
        return self.employee_dao.get_by_person_id(person_id)
    
    def get_employee_full_history(self, employee_id: int) -> List[EmploymentHistoryItem]:
        """
        获取员工在所有公司的完整历史记录（已排序）
        
        业务逻辑：
        1. 获取当前 employee，找到 person_id
        2. 获取该 person 的所有 employee 记录（包括换公司后的新记录）
        3. 遍历所有 employee 记录，收集所有任职信息
        4. 排序：先按 is_current（True在前），再按时间降序
        
        Args:
            employee_id: 员工ID
        
        Returns:
            已排序的历史记录项列表（EmploymentHistoryItem 对象）
        
        Raises:
            ValueError: employee_id 不存在
        """
        # 1. 获取当前员工记录，找到 person_id
        employee = self.employee_dao.get_by_id(employee_id)
        if not employee:
            raise ValueError(f"员工ID {employee_id} 不存在")
        
        person_id = employee.person_id
        
        # 2. 获取该 person 的所有 employee 记录（包括换公司后的新记录）
        all_employees = self.employee_dao.get_by_person_id(person_id)
        
        # 3. 遍历所有 employee 记录，收集所有任职信息
        result: List[EmploymentHistoryItem] = []
        for emp in all_employees:
            # 获取当前任职信息
            current_employment = self.employment_dao.get_by_employee_id(emp.id)
            if current_employment:
                # 判断是否是当前查看的 employee（用于标记 is_current）
                is_current_employee = (emp.id == employee_id)
                result.append(EmploymentHistoryItem(
                    employment=current_employment,
                    employment_history=None,
                    employee=emp,
                    is_current=is_current_employee
                ))
            
            # 获取历史记录
            history = self.employment_dao.get_history(emp.id)
            for h in history:
                result.append(EmploymentHistoryItem(
                    employment=None,
                    employment_history=h,
                    employee=emp,
                    is_current=False
                ))
        
        # 4. 按时间排序（changed_at降序，最新的在前）
        # 当前任职优先显示（即使时间相同）
        # 排序：先按 is_current（True在前），再按时间降序
        def get_sort_key(item: EmploymentHistoryItem) -> tuple:
            is_current = item.is_current
            if item.employment:
                changed_at = item.employment.updated_at or ''
            else:
                changed_at = item.employment_history.changed_at or ''
            return (is_current, changed_at)
        
        result.sort(key=get_sort_key, reverse=True)
        
        return result
    
    def update_employment(self, employee_id: int, 
                              department: str, position: str,
                              hire_date: str, supervisor_id: Optional[int] = None,
                              employee_type: Optional[str] = None,
                              change_reason: Optional[str] = None) -> bool:
        """
        更新入职信息（会记录历史版本）
        
        只处理公司内的岗位变更（部门、职位、上级等），不处理公司变更
        公司变更应使用 transfer_employee_to_company 方法
        
        Args:
            employee_id: 员工ID
            department: 新部门
            position: 新职位
            hire_date: 入职时间（通常不变，但允许修改）
            supervisor_id: 上级ID
            change_reason: 变更原因
            
        Returns:
            是否更新成功（如果字段没有变化，返回 False）
        """
        return self.employment_dao.update(
            employee_id, department, position, hire_date, supervisor_id, employee_type, change_reason
        )
    
    def update_employment_info(
        self,
        employee_id: int,
        department: str,
        position: str,
        hire_date: str,
        supervisor_id: Optional[int] = None,
        employee_type: Optional[str] = None,
        change_reason: Optional[str] = None
    ) -> bool:
        """
        更新或创建员工的入职信息
        
        业务逻辑：
        1. 如果已有 employment，判断字段是否变化
        2. 如果有变化，更新 employment（会记录历史版本）
        3. 如果没有 employment，创建新的 employment
        4. 如果没有变化，返回 False
        
        Args:
            employee_id: 员工ID
            department: 部门（必填）
            position: 职位（必填）
            hire_date: 入职时间（必填）
            supervisor_id: 上级ID（可选）
            change_reason: 变更原因（可选，如果没有提供且字段有变化，使用默认值）
        
        Returns:
            bool: 是否执行了更新或创建操作（如果字段没有变化，返回 False）
        
        Raises:
            ValueError: employee_id 不存在、参数验证失败等
        """
        # 1. 验证 employee 是否存在
        employee = self.employee_dao.get_by_id(employee_id)
        if not employee:
            raise ValueError(f"员工ID {employee_id} 不存在")
        
        # 2. 验证必填字段
        if not department:
            raise ValueError("部门不能为空")
        if not position:
            raise ValueError("职位不能为空")
        if not hire_date:
            raise ValueError("入职时间不能为空")
        
        # 3. 获取当前 employment
        current_employment = self.employment_dao.get_by_employee_id(employee_id)
        
        if current_employment:
            # 4. 判断字段是否变化
            current_employee_type = current_employment.employee_type if hasattr(current_employment, 'employee_type') else '正式员工'
            new_employee_type = employee_type if employee_type is not None else current_employee_type
            
            has_changed = (
                department != current_employment.department or
                position != current_employment.position or
                hire_date != current_employment.hire_date or
                (supervisor_id or 0) != (current_employment.supervisor_id or 0) or
                current_employee_type != new_employee_type
            )
            
            if has_changed:
                # 5. 如果有变化，更新 employment（如果没有提供 change_reason，使用默认值）
                if change_reason is None:
                    change_reason = '未填写变更原因'
                return self.employment_dao.update(
                    employee_id, department, position, hire_date, supervisor_id, new_employee_type, change_reason
                )
            else:
                # 6. 如果没有变化，返回 False
                return False
        else:
            # 7. 如果没有 employment，创建新的
            new_employee_type = employee_type if employee_type is not None else '正式员工'
            employment = Employment(
                employee_id=employee_id,
                department=department,
                position=position,
                hire_date=hire_date,
                supervisor_id=supervisor_id,
                employee_type=new_employee_type,
                version=1
            )
            self.employment_dao.create(employment)
            return True
    
    def transfer_employee_to_company(self, employee_id: int,
                                     new_company_name: str,
                                     new_employee_number: str,
                                     department: str, position: str,
                                     hire_date: str, supervisor_id: Optional[int] = None,
                                     employee_type: str = '正式员工',
                                     change_reason: Optional[str] = None) -> int:
        """
        将员工转移到新公司（创建新的employee记录）
        
        换公司时，创建新的employee记录，而不是更新现有记录
        旧employee记录保留（用于历史查询），新employee创建新的employment
        
        Args:
            employee_id: 原员工ID
            new_company_name: 新公司名称
            new_employee_number: 新公司中的员工编号
            department: 新部门
            position: 新职位
            hire_date: 新公司的入职时间
            supervisor_id: 上级ID（新公司中的员工ID）
            change_reason: 变更原因
            
        Returns:
            新创建的员工ID
        """
        # 1. 获取原员工信息
        old_employee = self.employee_dao.get_by_id(employee_id)
        if not old_employee:
            raise ValueError("员工不存在")
        
        person_id = old_employee.person_id
        
        # 2. 标记旧employee为inactive
        self.employee_dao.update_status(employee_id, 'inactive')
        
        # 3. 创建新employee记录（新公司）
        new_employee_id = self.employee_dao.create(person_id, new_company_name, new_employee_number, 'active')
        
        # 4. 创建新employment（新公司的职位信息）
        new_employment = Employment(
            employee_id=new_employee_id,
            department=department,
            position=position,
            supervisor_id=supervisor_id,
            hire_date=hire_date,
            employee_type=employee_type,
            version=1
        )
        self.employment_dao.create(new_employment)
        
        return new_employee_id
    
    def get_employment_history(self, employee_id: int) -> List[EmploymentHistory]:
        """获取员工的入职信息历史记录"""
        return self.employment_dao.get_history(employee_id)
    
    def update_employee_status(self, employee_id: int, status: str) -> bool:
        """更新员工状态（active/inactive/terminated）"""
        return self.employee_dao.update_status(employee_id, status)
    
    def get_employee_with_employment(self, employee_id: int) -> Optional[EmployeeWithEmployment]:
        """
        获取员工完整信息（包括人员信息、员工信息和当前入职信息）
        
        Returns:
            EmployeeWithEmployment 对象，如果员工不存在则返回 None
        """
        employee = self.employee_dao.get_by_id(employee_id)
        if not employee:
            return None
        
        person = self.person_dao.get_by_id(employee.person_id)
        employment = self.employment_dao.get_by_employee_id(employee_id)
        
        # 检查是否有历史记录
        has_history = False
        if person:
            employees = self.employee_dao.get_by_person_id(person.id)
            if len(employees) > 1:
                has_history = True
            else:
                history = self.employment_dao.get_history(employee_id)
                if len(history) > 0:
                    has_history = True
        
        return EmployeeWithEmployment(
            person=person,
            employee=employee,
            employment=employment,
            has_history=has_history
        )
    
    def get_all_employees_with_employment(self, company_name: Optional[str] = None, department: Optional[str] = None) -> List[EmployeeWithEmployment]:
        """
        获取所有员工的完整信息（使用JOIN优化查询）
        
        Args:
            company_name: 如果提供，只返回该公司的员工
            department: 如果提供，只返回该部门的员工
        
        Returns:
            EmployeeWithEmployment 对象列表
        """
        rows = self.employment_dao.get_all_with_join(company_name, department)
        result: List[EmployeeWithEmployment] = []
        
        # 预先收集所有 person_id，用于批量查询历史记录
        person_ids = set()
        for row in rows:
            if row['person_id']:
                person_ids.add(row['person_id'])
        
        # 批量查询每个 person 的所有 employee 是否有历史记录
        # 如果有多个 employee 记录（说明换过公司），也应该显示历史按钮
        person_has_history = {}
        for person_id in person_ids:
            # 获取该 person 的所有 employee
            employees = self.employee_dao.get_by_person_id(person_id)
            has_any_history = False
            
            # 如果有多个 employee 记录，说明换过公司，应该显示历史
            if len(employees) > 1:
                has_any_history = True
            else:
                # 检查是否有 employment_history 记录
                for emp in employees:
                    history = self.employment_dao.get_history(emp.id)
                    if len(history) > 0:
                        has_any_history = True
                        break
            
            person_has_history[person_id] = has_any_history
        
        for row in rows:
            # 构建Person对象
            person = None
            if row['person_id']:
                # 处理 address 字段（可能不存在于旧数据中）
                address = None
                try:
                    address = row['address']
                except (KeyError, IndexError):
                    pass
                
                person = Person(
                    id=row['person_id'],
                    name=row['name'],
                    birth_date=row['birth_date'],
                    gender=row['gender'],
                    phone=row['phone'],
                    email=row['email'],
                    address=address,
                    created_at=row['person_created_at'],
                    updated_at=row['person_updated_at']
                )
            
            # 构建Employee对象（包含status字段）
            employee = Employee(
                id=row['employee_id'],
                person_id=row['person_id'],
                company_name=row['company_name'],
                employee_number=row['employee_number'],
                status=row['status'],
                created_at=row['employee_created_at'],
                updated_at=row['employee_updated_at']
            )
            
            # 构建Employment对象
            employment = None
            if row['employment_id']:
                # sqlite3.Row 不支持 .get()，使用 try-except 兼容旧数据
                try:
                    employee_type = row['employee_type']
                except (KeyError, IndexError):
                    employee_type = '正式员工'  # 兼容旧数据
                
                employment = Employment(
                    id=row['employment_id'],
                    employee_id=row['employee_id'],
                    department=row['department'],
                    position=row['position'],
                    hire_date=row['hire_date'],
                    supervisor_id=row['supervisor_id'],
                    employee_type=employee_type,
                    version=row['version'],
                    created_at=row['employment_created_at'],
                    updated_at=row['employment_updated_at']
                )

            # 检查该 person 的所有 employee 是否有历史记录（包括换公司的情况）
            person_id = row['person_id'] if row['person_id'] else None
            has_history = person_has_history.get(person_id, False) or bool(row['has_history'])

            result.append(EmployeeWithEmployment(
                person=person,
                employee=employee,
                employment=employment,
                has_history=has_history
            ))
        
        return result
    
    
    def get_person_work_history(self, person_id: int) -> List[PersonWorkHistoryItem]:
        """
        获取一个人在所有公司的工作历史
        
        Returns:
            PersonWorkHistoryItem 对象列表（已按入职时间降序排序）
        """
        employees = self.employee_dao.get_by_person_id(person_id)
        result: List[PersonWorkHistoryItem] = []
        
        for employee in employees:
            employment = self.employment_dao.get_by_employee_id(employee.id)
            result.append(PersonWorkHistoryItem(
                employee_id=employee.id,
                company_name=employee.company_name,
                employee_number=employee.employee_number,
                department=employment.department if employment else None,
                position=employment.position if employment else None,
                hire_date=employment.hire_date if employment else None
            ))
        
        # 按入职时间降序排序
        result.sort(key=lambda x: x.hire_date or '', reverse=True)
        
        return result
    
    def get_supervisors(self, company_name: Optional[str] = None) -> List[SupervisorInfo]:
        """
        获取所有员工列表（用于选择上级，只返回active员工）
        
        Args:
            company_name: 如果提供，只返回该公司的员工
        
        Returns:
            SupervisorInfo 对象列表
        """
        employees = self.employee_dao.get_all(company_name, 'active')
        result: List[SupervisorInfo] = []
        
        for employee in employees:
            person = self.person_dao.get_by_id(employee.person_id)
            result.append(SupervisorInfo(
                id=employee.id,
                name=person.name if person else '未知',
                employee_number=employee.employee_number,
                company_name=employee.company_name
            ))
        
        return result
    
    def get_companies(self) -> List[str]:
        """
        获取所有公司列表（只返回有active员工的）
        """
        employees = self.employee_dao.get_all(None, 'active')
        companies = set()
        for employee in employees:
            companies.add(employee.company_name)
        return sorted(list(companies))
    
    def get_departments(self, company_name: Optional[str] = None) -> List[str]:
        """
        获取所有部门列表
        
        Args:
            company_name: 如果提供，只返回该公司的部门；否则返回所有公司的部门
        
        Returns:
            部门名称列表（已去重并排序）
        """
        rows = self.employment_dao.get_all_with_join(company_name)
        departments = set()
        for row in rows:
            if row['department']:
                departments.add(row['department'])
        return sorted(list(departments))
    
    def get_max_employee_number(self, company_name: str) -> Optional[str]:
        """
        获取指定公司的最大员工编号
        
        支持多种编号格式：
        - EMP001, EMP002, ...
        - emp001, emp002, ...
        - 001, 002, ...
        - 其他纯数字格式
        
        Args:
            company_name: 公司名称
            
        Returns:
            最大员工编号，如果公司没有员工则返回 None
        """
        import re
        
        employees = self.employee_dao.get_all(company_name, None)
        if not employees:
            return None
        
        max_number = None
        max_num = -1
        
        for employee in employees:
            # 使用正则表达式提取编号中的数字部分
            match = re.search(r'\d+', employee.employee_number)
            if match:
                try:
                    num = int(match.group())
                    if num > max_num:
                        max_num = num
                        max_number = employee.employee_number
                except ValueError:
                    continue
        
        return max_number
    
    def clear_all_data(self):
        """清空所有数据（谨慎使用，仅用于测试）"""
        from app.daos.attendance_dao import AttendanceDAO
        from app.daos.leave_record_dao import LeaveRecordDAO
        from app.daos import SalaryDAO, PayrollDAO
        
        # 注意：删除顺序很重要，因为有外键约束
        # 先删除子表数据，再删除父表数据
        attendance_dao = AttendanceDAO()
        leave_record_dao = LeaveRecordDAO()
        salary_dao = SalaryDAO()
        payroll_dao = PayrollDAO()
        
        # 清空子表
        attendance_dao.clear_all()
        leave_record_dao.clear_all()
        salary_dao.clear_all()
        payroll_dao.clear_all()
        
        # 清空父表
        self.employment_dao.clear_all()
        self.employee_dao.clear_all()
        self.person_dao.clear_all()
    
    def get_statistics(self) -> Dict:
        """获取数据库统计信息"""
        return {
            'person_count': self.person_dao.count(),
            'employee_count': self.employee_dao.count(),
            'employment_count': self.employment_dao.count_employment(),
            'history_count': self.employment_dao.count_history()
        }
    
    def create_employee(self, person: Person, company_name: str, employee_number: str) -> int:
        """
        创建员工（用于初始化脚本，会自动创建或查找 Person）
        
        Args:
            person: Person 对象
            company_name: 公司名称
            employee_number: 员工编号
            
        Returns:
            employee_id: 新创建的员工ID
        """
        from app.services.person_service import PersonService
        
        person_service = PersonService()
        # 查找或创建人员
        person_id = person_service.find_or_create_person(person)
        
        # 创建员工记录
        employee_id = self.employee_dao.create(person_id, company_name, employee_number, 'active')
        return employee_id
    
    def create_person(self, person: Person) -> int:
        """
        创建人员（用于初始化脚本）
        
        Args:
            person: Person 对象
            
        Returns:
            person_id: 新创建的人员ID
        """
        return self.person_dao.create(person)
    
    def get_unemployed_persons(self) -> List[Person]:
        """获取未任职人员列表"""
        return self.person_dao.get_unemployed_persons()
    
