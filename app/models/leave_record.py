"""
请假记录模型
"""
from typing import Optional, List, Dict
import json
from datetime import datetime


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
                 updated_at: Optional[str] = None,
                 paid_hours_history: Optional[str] = None):
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
        self.paid_hours_history = paid_hours_history  # JSON字符串
    
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
            'updated_at': self.updated_at,
            'paid_hours_history': self.get_paid_hours_history()  # 返回解析后的历史记录
        }
    
    def get_paid_hours_history(self) -> List[Dict]:
        """
        获取paid_hours的修改历史记录
        
        Returns:
            历史记录列表，按时间倒序排列
        """
        if not self.paid_hours_history:
            return []
        try:
            history = json.loads(self.paid_hours_history)
            # 确保按时间倒序排列（最新的在前）
            if isinstance(history, list):
                return sorted(history, key=lambda x: x.get('changed_at', ''), reverse=True)
            return []
        except (json.JSONDecodeError, TypeError):
            return []
    
    def add_paid_hours_history(self, old_value: Optional[float], new_value: float, 
                               change_reason: str, changed_by: str = 'system'):
        """
        添加paid_hours的修改历史记录
        
        Args:
            old_value: 修改前的值（None表示初始值）
            new_value: 修改后的值
            change_reason: 修改原因
            changed_by: 修改人（用户名或ID），默认为'system'
        """
        history = self.get_paid_hours_history()
        
        # 添加新记录
        history.append({
            'old_value': old_value,
            'new_value': new_value,
            'change_reason': change_reason,
            'changed_by': changed_by,
            'changed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # 保存为JSON字符串
        self.paid_hours_history = json.dumps(history, ensure_ascii=False)
    
    @classmethod
    def from_row(cls, row):
        """从数据库行创建对象"""
        # 处理 paid_hours_history 字段（可能不存在于旧数据中）
        paid_hours_history = None
        try:
            if 'paid_hours_history' in row.keys():
                paid_hours_history = row['paid_hours_history']
        except (KeyError, IndexError):
            pass
        
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
            updated_at=row['updated_at'],
            paid_hours_history=paid_hours_history
        )

