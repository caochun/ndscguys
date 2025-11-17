"""
请假记录模型
"""
from typing import Optional


class LeaveRecord:
    """请假记录模型"""
    
    def __init__(self,
                 person_id: int,
                 company_name: str,
                 leave_date: str,
                 leave_type: str,
                 leave_hours: float,
                 start_time: Optional[str] = None,
                 end_time: Optional[str] = None,
                 reason: Optional[str] = None,
                 paid_hours: float = 0.0,
                 status: str = 'approved',
                 employee_id: Optional[int] = None,
                 id: Optional[int] = None,
                 created_at: Optional[str] = None,
                 updated_at: Optional[str] = None):
        self.id = id
        self.person_id = person_id
        self.employee_id = employee_id
        self.company_name = company_name
        self.leave_date = leave_date
        self.leave_type = leave_type
        self.start_time = start_time
        self.end_time = end_time
        self.leave_hours = leave_hours
        self.paid_hours = paid_hours
        self.reason = reason
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'person_id': self.person_id,
            'employee_id': self.employee_id,
            'company_name': self.company_name,
            'leave_date': self.leave_date,
            'leave_type': self.leave_type,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'leave_hours': self.leave_hours,
            'paid_hours': self.paid_hours,
            'reason': self.reason,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_row(cls, row):
        """从数据库行创建对象"""
        return cls(
            id=row['id'],
            person_id=row['person_id'],
            employee_id=row['employee_id'],
            company_name=row['company_name'],
            leave_date=row['leave_date'],
            leave_type=row['leave_type'],
            start_time=row['start_time'],
            end_time=row['end_time'],
            leave_hours=row['leave_hours'],
            paid_hours=row['paid_hours'] if 'paid_hours' in row.keys() else 0.0,
            reason=row['reason'],
            status=row['status'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

