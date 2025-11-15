"""
入职信息历史模型
"""
from typing import Optional


class EmploymentHistory:
    """入职信息历史模型"""
    
    def __init__(self, employee_id: int, department: str, position: str,
                 hire_date: str, version: int,
                 supervisor_id: Optional[int] = None,
                 change_reason: Optional[str] = None,
                 changed_at: Optional[str] = None,
                 id: Optional[int] = None,
                 created_at: Optional[str] = None):
        self.id = id
        self.employee_id = employee_id
        self.department = department
        self.position = position
        self.supervisor_id = supervisor_id
        self.hire_date = hire_date
        self.version = version
        self.change_reason = change_reason
        self.changed_at = changed_at
        self.created_at = created_at
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'department': self.department,
            'position': self.position,
            'supervisor_id': self.supervisor_id,
            'hire_date': self.hire_date,
            'version': self.version,
            'change_reason': self.change_reason,
            'changed_at': self.changed_at,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_row(cls, row):
        """从数据库行创建对象"""
        return cls(
            id=row['id'],
            employee_id=row['employee_id'],
            department=row['department'],
            position=row['position'],
            supervisor_id=row['supervisor_id'],
            hire_date=row['hire_date'],
            version=row['version'],
            change_reason=row['change_reason'],
            changed_at=row['changed_at'],
            created_at=row['created_at']
        )


