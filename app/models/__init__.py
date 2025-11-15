"""
数据模型包
"""
from .person import Person
from .employee import Employee
from .employment_info import EmploymentInfo
from .employment_info_history import EmploymentInfoHistory

__all__ = ['Person', 'Employee', 'EmploymentInfo', 'EmploymentInfoHistory']
