"""
人员基本信息模型
"""
from typing import Optional


class Person:
    """人员基本信息模型（不变信息）"""
    
    def __init__(self, name: str, 
                 birth_date: Optional[str] = None,
                 gender: Optional[str] = None,
                 phone: Optional[str] = None,
                 email: Optional[str] = None,
                 address: Optional[str] = None,
                 id: Optional[int] = None,
                 created_at: Optional[str] = None,
                 updated_at: Optional[str] = None):
        self.id = id
        self.name = name
        self.birth_date = birth_date
        self.gender = gender
        self.phone = phone
        self.email = email
        self.address = address
        self.created_at = created_at
        self.updated_at = updated_at
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'birth_date': self.birth_date,
            'gender': self.gender,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_row(cls, row):
        """从数据库行创建对象"""
        return cls(
            id=row['id'],
            name=row['name'],
            birth_date=row['birth_date'],
            gender=row['gender'],
            phone=row['phone'],
            email=row['email'],
            address=row['address'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

