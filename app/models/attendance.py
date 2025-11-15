"""
考勤记录模型
"""
from typing import Optional


class Attendance:
    """考勤记录模型"""
    
    def __init__(self, 
                 person_id: int,
                 company_name: str,
                 attendance_date: str,
                 check_in_time: Optional[str] = None,
                 check_out_time: Optional[str] = None,
                 status: Optional[str] = None,
                 work_hours: Optional[float] = None,
                 standard_hours: float = 8.0,
                 overtime_hours: float = 0.0,
                 leave_hours: float = 0.0,
                 remark: Optional[str] = None,
                 employee_id: Optional[int] = None,
                 id: Optional[int] = None,
                 created_at: Optional[str] = None,
                 updated_at: Optional[str] = None):
        self.id = id
        self.person_id = person_id
        self.employee_id = employee_id
        self.company_name = company_name
        self.attendance_date = attendance_date
        self.check_in_time = check_in_time
        self.check_out_time = check_out_time
        self.status = status
        self.work_hours = work_hours
        self.standard_hours = standard_hours
        self.overtime_hours = overtime_hours
        self.leave_hours = leave_hours
        self.remark = remark
        self.created_at = created_at
        self.updated_at = updated_at
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'person_id': self.person_id,
            'employee_id': self.employee_id,
            'company_name': self.company_name,
            'attendance_date': self.attendance_date,
            'check_in_time': self.check_in_time,
            'check_out_time': self.check_out_time,
            'status': self.status,
            'work_hours': self.work_hours,
            'standard_hours': self.standard_hours,
            'overtime_hours': self.overtime_hours,
            'leave_hours': self.leave_hours,
            'remark': self.remark,
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
            attendance_date=row['attendance_date'],
            check_in_time=row['check_in_time'],
            check_out_time=row['check_out_time'],
            status=row['status'],
            work_hours=row['work_hours'],
            standard_hours=row['standard_hours'],
            overtime_hours=row['overtime_hours'],
            leave_hours=row['leave_hours'],
            remark=row['remark'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

