"""
薪资管理服务
"""
from typing import List, Optional, Dict
from app.models import SalaryRecord
from app.daos import SalaryDAO, EmployeeDAO, EmploymentDAO, PersonDAO


class SalaryService:
    """薪资管理服务类"""
    
    def __init__(self):
        self.salary_dao = SalaryDAO()
        self.employee_dao = EmployeeDAO()
        self.employment_dao = EmploymentDAO()
        self.person_dao = PersonDAO()
    
    def create_salary_record(
        self,
        employee_id: int,
        base_amount: float,
        effective_date: str,
        change_reason: Optional[str] = None
    ) -> int:
        """
        创建新的薪资记录，并自动失效上一条记录
        """
        employee = self.employee_dao.get_by_id(employee_id)
        if not employee:
            raise ValueError(f"员工ID {employee_id} 不存在")
        
        if base_amount is None:
            raise ValueError("月薪基数不能为空")
        
        try:
            base_amount_value = float(base_amount)
        except (TypeError, ValueError):
            raise ValueError("月薪基数必须为数字")
        
        if base_amount_value <= 0:
            raise ValueError("月薪基数必须大于0")
        
        if not effective_date:
            raise ValueError("生效日期不能为空")
        
        # 结束当前生效薪资
        self.salary_dao.deactivate_current(employee_id, effective_date)
        
        basic_salary = round(base_amount_value * 0.6, 2)
        performance_salary = round(base_amount_value * 0.4, 2)
        version = self.salary_dao.get_next_version(employee_id)
        
        salary_record = SalaryRecord(
            employee_id=employee_id,
            base_amount=round(base_amount_value, 2),
            basic_salary=basic_salary,
            performance_salary=performance_salary,
            effective_date=effective_date,
            change_reason=change_reason,
            version=version,
            status='active'
        )
        
        return self.salary_dao.create(salary_record)
    
    def get_current_salary(self, employee_id: int) -> Optional[SalaryRecord]:
        """获取员工当前薪资"""
        return self.salary_dao.get_current_by_employee(employee_id)
    
    def get_salary_history(self, employee_id: int) -> List[SalaryRecord]:
        """获取员工薪资历史记录"""
        return self.salary_dao.get_history_by_employee(employee_id)
    
    def get_active_employees_with_salary(self, company_name: Optional[str] = None) -> List[Dict]:
        """
        获取所有在职员工的当前薪资信息
        """
        employees = self.employee_dao.get_all(company_name, 'active')
        result: List[Dict] = []
        
        for employee in employees:
            person = self.person_dao.get_by_id(employee.person_id)
            employment = self.employment_dao.get_by_employee_id(employee.id)
            salary = self.salary_dao.get_current_by_employee(employee.id)
            
            basic_salary = float(salary.basic_salary) if salary and salary.basic_salary else 0.0
            performance_salary = float(salary.performance_salary) if salary and salary.performance_salary else 0.0
            
            result.append({
                'employee_id': employee.id,
                'person_id': employee.person_id,
                'name': person.name if person else '未知',
                'company_name': employee.company_name,
                'department': employment.department if employment else None,
                'position': employment.position if employment else None,
                'employee_type': employment.employee_type if employment and hasattr(employment, 'employee_type') else '正式员工',
                'basic_salary': basic_salary,
                'performance_salary': performance_salary,
                'has_salary': salary is not None
            })
        
        return result

