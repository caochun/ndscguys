"""
员工模型（员工在公司中的记录）
"""
from typing import Optional


class Employee:
    """员工模型（关联到人员和公司）"""
    
    def __init__(self, person_id: int, company_name: str, employee_number: str,
                 id: Optional[int] = None,
                 created_at: Optional[str] = None,
                 updated_at: Optional[str] = None):
        self.id = id
        self.person_id = person_id
        self.company_name = company_name
        self.employee_number = employee_number
        self.created_at = created_at
        self.updated_at = updated_at
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'person_id': self.person_id,
            'company_name': self.company_name,
            'employee_number': self.employee_number,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_row(cls, row):
        """从数据库行创建对象"""
        return cls(
            id=row['id'],
            person_id=row['person_id'],
            company_name=row['company_name'],
            employee_number=row['employee_number'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

