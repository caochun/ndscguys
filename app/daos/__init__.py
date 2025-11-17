"""
数据访问层（DAO）
"""
from .person_dao import PersonDAO
from .employee_dao import EmployeeDAO
from .employment_dao import EmploymentDAO
from .salary_dao import SalaryDAO
from .payroll_dao import PayrollDAO

__all__ = ['PersonDAO', 'EmployeeDAO', 'EmploymentDAO', 'SalaryDAO', 'PayrollDAO']

