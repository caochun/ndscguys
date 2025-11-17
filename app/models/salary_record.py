"""
薪资信息模型
"""
from typing import Optional


class SalaryRecord:
    """员工薪资记录"""

    def __init__(
        self,
        employee_id: int,
        base_amount: float,
        basic_salary: float,
        performance_salary: float,
        effective_date: str,
        id: Optional[int] = None,
        end_date: Optional[str] = None,
        change_reason: Optional[str] = None,
        version: int = 1,
        status: str = 'active',
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ):
        self.id = id
        self.employee_id = employee_id
        self.base_amount = base_amount
        self.basic_salary = basic_salary
        self.performance_salary = performance_salary
        self.effective_date = effective_date
        self.end_date = end_date
        self.change_reason = change_reason
        self.version = version
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'base_amount': self.base_amount,
            'basic_salary': self.basic_salary,
            'performance_salary': self.performance_salary,
            'effective_date': self.effective_date,
            'end_date': self.end_date,
            'change_reason': self.change_reason,
            'version': self.version,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }

    @classmethod
    def from_row(cls, row):
        """从数据库行创建对象"""
        return cls(
            id=row['id'],
            employee_id=row['employee_id'],
            base_amount=row['base_amount'],
            basic_salary=row['basic_salary'],
            performance_salary=row['performance_salary'],
            effective_date=row['effective_date'],
            end_date=row['end_date'],
            change_reason=row['change_reason'],
            version=row['version'],
            status=row['status'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )

