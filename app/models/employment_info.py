"""
入职信息模型
"""
from typing import Optional


class EmploymentInfo:
    """入职信息模型"""
    
    def __init__(self, employee_id: int, department: str, position: str,
                 hire_date: str, company_name: str,
                 supervisor_id: Optional[int] = None,
                 version: int = 1, id: Optional[int] = None,
                 created_at: Optional[str] = None,
                 updated_at: Optional[str] = None):
        self.id = id
        self.employee_id = employee_id
        self.company_name = company_name
        self.department = department
        self.position = position
        self.supervisor_id = supervisor_id
        self.hire_date = hire_date
        self.version = version
        self.created_at = created_at
        self.updated_at = updated_at
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'company_name': self.company_name,
            'department': self.department,
            'position': self.position,
            'supervisor_id': self.supervisor_id,
            'hire_date': self.hire_date,
            'version': self.version,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_row(cls, row):
        """从数据库行创建对象"""
        return cls(
            id=row['id'],
            employee_id=row['employee_id'],
            company_name=row['company_name'],
            department=row['department'],
            position=row['position'],
            supervisor_id=row['supervisor_id'],
            hire_date=row['hire_date'],
            version=row['version'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

