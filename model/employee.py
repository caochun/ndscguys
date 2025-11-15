"""
员工个人信息模型
"""
from typing import Optional


class Employee:
    """员工个人信息模型"""
    
    def __init__(self, employee_number: str, name: str, 
                 birth_date: Optional[str] = None,
                 gender: Optional[str] = None,
                 phone: Optional[str] = None,
                 email: Optional[str] = None,
                 id: Optional[int] = None,
                 created_at: Optional[str] = None,
                 updated_at: Optional[str] = None):
        self.id = id
        self.employee_number = employee_number
        self.name = name
        self.birth_date = birth_date
        self.gender = gender
        self.phone = phone
        self.email = email
        self.created_at = created_at
        self.updated_at = updated_at
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'employee_number': self.employee_number,
            'name': self.name,
            'birth_date': self.birth_date,
            'gender': self.gender,
            'phone': self.phone,
            'email': self.email,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_row(cls, row):
        """从数据库行创建对象"""
        return cls(
            id=row['id'],
            employee_number=row['employee_number'],
            name=row['name'],
            birth_date=row['birth_date'],
            gender=row['gender'],
            phone=row['phone'],
            email=row['email'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

