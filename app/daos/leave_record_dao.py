"""
请假记录数据访问层
"""
from typing import List, Optional
from .base_dao import BaseDAO
from app.models import LeaveRecord


class LeaveRecordDAO(BaseDAO):
    """请假记录数据访问对象"""
    
    def create(self, leave_record: LeaveRecord) -> int:
        """
        创建请假记录
        
        Args:
            leave_record: 请假记录对象
            
        Returns:
            新创建的请假记录ID
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 处理 paid_hours_history 字段（可能不存在于旧数据中）
            paid_hours_history = getattr(leave_record, 'paid_hours_history', None)
            
            cursor.execute("""
                INSERT INTO leave_records 
                (person_id, employee_id, company_name, leave_date, leave_type,
                 start_time, end_time, leave_hours, paid_hours, reason, status, paid_hours_history)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                leave_record.person_id,
                leave_record.employee_id,
                leave_record.company_name,
                leave_record.leave_date,
                leave_record.leave_type,
                leave_record.start_time,
                leave_record.end_time,
                leave_record.leave_hours,
                leave_record.paid_hours,
                leave_record.reason,
                leave_record.status,
                paid_hours_history
            ))
            leave_id = cursor.lastrowid
            conn.commit()
            return leave_id
        except Exception as e:
            conn.rollback()
            raise ValueError(f"创建请假记录失败：{str(e)}") from e
    
    def get_by_id(self, leave_id: int) -> Optional[LeaveRecord]:
        """根据ID获取请假记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM leave_records WHERE id = ?", (leave_id,))
        row = cursor.fetchone()
        
        if row:
            return LeaveRecord.from_row(row)
        return None
    
    def get_by_person_id(self, person_id: int, start_date: Optional[str] = None,
                        end_date: Optional[str] = None) -> List[LeaveRecord]:
        """
        根据人员ID获取请假记录
        
        Args:
            person_id: 人员ID
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if start_date and end_date:
            cursor.execute("""
                SELECT * FROM leave_records 
                WHERE person_id = ? AND leave_date BETWEEN ? AND ?
                ORDER BY leave_date DESC, start_time DESC
            """, (person_id, start_date, end_date))
        elif start_date:
            cursor.execute("""
                SELECT * FROM leave_records 
                WHERE person_id = ? AND leave_date >= ?
                ORDER BY leave_date DESC, start_time DESC
            """, (person_id, start_date))
        elif end_date:
            cursor.execute("""
                SELECT * FROM leave_records 
                WHERE person_id = ? AND leave_date <= ?
                ORDER BY leave_date DESC, start_time DESC
            """, (person_id, end_date))
        else:
            cursor.execute("""
                SELECT * FROM leave_records 
                WHERE person_id = ?
                ORDER BY leave_date DESC, start_time DESC
            """, (person_id,))
        
        rows = cursor.fetchall()
        return [LeaveRecord.from_row(row) for row in rows]
    
    def get_by_person_and_date(self, person_id: int, leave_date: str) -> List[LeaveRecord]:
        """
        根据人员ID和日期获取请假记录（一天可能有多次请假）
        
        Args:
            person_id: 人员ID
            leave_date: 请假日期
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM leave_records 
            WHERE person_id = ? AND leave_date = ? AND status = 'approved'
            ORDER BY start_time
        """, (person_id, leave_date))
        
        rows = cursor.fetchall()
        return [LeaveRecord.from_row(row) for row in rows]
    
    def get_by_person_and_company(self, person_id: int, company_name: str,
                                  start_date: Optional[str] = None,
                                  end_date: Optional[str] = None) -> List[LeaveRecord]:
        """
        根据人员ID和公司名称获取请假记录
        
        Args:
            person_id: 人员ID
            company_name: 公司名称
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if start_date and end_date:
            cursor.execute("""
                SELECT * FROM leave_records 
                WHERE person_id = ? AND company_name = ? 
                AND leave_date BETWEEN ? AND ?
                ORDER BY leave_date DESC, start_time DESC
            """, (person_id, company_name, start_date, end_date))
        elif start_date:
            cursor.execute("""
                SELECT * FROM leave_records 
                WHERE person_id = ? AND company_name = ? 
                AND leave_date >= ?
                ORDER BY leave_date DESC, start_time DESC
            """, (person_id, company_name, start_date))
        elif end_date:
            cursor.execute("""
                SELECT * FROM leave_records 
                WHERE person_id = ? AND company_name = ? 
                AND leave_date <= ?
                ORDER BY leave_date DESC, start_time DESC
            """, (person_id, company_name, end_date))
        else:
            cursor.execute("""
                SELECT * FROM leave_records 
                WHERE person_id = ? AND company_name = ?
                ORDER BY leave_date DESC, start_time DESC
            """, (person_id, company_name))
        
        rows = cursor.fetchall()
        return [LeaveRecord.from_row(row) for row in rows]
    
    def get_by_employee_id(self, employee_id: int,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> List[LeaveRecord]:
        """
        根据员工ID获取请假记录
        
        Args:
            employee_id: 员工ID
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if start_date and end_date:
            cursor.execute("""
                SELECT * FROM leave_records 
                WHERE employee_id = ? AND leave_date BETWEEN ? AND ?
                ORDER BY leave_date DESC, start_time DESC
            """, (employee_id, start_date, end_date))
        elif start_date:
            cursor.execute("""
                SELECT * FROM leave_records 
                WHERE employee_id = ? AND leave_date >= ?
                ORDER BY leave_date DESC, start_time DESC
            """, (employee_id, start_date))
        elif end_date:
            cursor.execute("""
                SELECT * FROM leave_records 
                WHERE employee_id = ? AND leave_date <= ?
                ORDER BY leave_date DESC, start_time DESC
            """, (employee_id, end_date))
        else:
            cursor.execute("""
                SELECT * FROM leave_records 
                WHERE employee_id = ?
                ORDER BY leave_date DESC, start_time DESC
            """, (employee_id,))
        
        rows = cursor.fetchall()
        return [LeaveRecord.from_row(row) for row in rows]
    
    def get_by_company(self, company_name: str,
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None) -> List[LeaveRecord]:
        """
        根据公司名称获取请假记录
        
        Args:
            company_name: 公司名称
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if start_date and end_date:
            cursor.execute("""
                SELECT * FROM leave_records 
                WHERE company_name = ? AND leave_date BETWEEN ? AND ?
                ORDER BY leave_date DESC, start_time DESC
            """, (company_name, start_date, end_date))
        elif start_date:
            cursor.execute("""
                SELECT * FROM leave_records 
                WHERE company_name = ? AND leave_date >= ?
                ORDER BY leave_date DESC, start_time DESC
            """, (company_name, start_date))
        elif end_date:
            cursor.execute("""
                SELECT * FROM leave_records 
                WHERE company_name = ? AND leave_date <= ?
                ORDER BY leave_date DESC, start_time DESC
            """, (company_name, end_date))
        else:
            cursor.execute("""
                SELECT * FROM leave_records 
                WHERE company_name = ?
                ORDER BY leave_date DESC, start_time DESC
            """, (company_name,))
        
        rows = cursor.fetchall()
        return [LeaveRecord.from_row(row) for row in rows]
    
    def update(self, leave_record: LeaveRecord) -> bool:
        """更新请假记录"""
        if leave_record.id is None:
            raise ValueError("请假记录ID不能为空")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 处理 paid_hours_history 字段（可能不存在于旧数据中）
        paid_hours_history = getattr(leave_record, 'paid_hours_history', None)
        
        cursor.execute("""
            UPDATE leave_records 
            SET leave_type = ?, start_time = ?, end_time = ?,
                leave_hours = ?, paid_hours = ?, reason = ?, status = ?,
                paid_hours_history = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            leave_record.leave_type,
            leave_record.start_time,
            leave_record.end_time,
            leave_record.leave_hours,
            leave_record.paid_hours,
            leave_record.reason,
            leave_record.status,
            paid_hours_history,
            leave_record.id
        ))
        
        conn.commit()
        return cursor.rowcount > 0
    
    def delete(self, leave_id: int) -> bool:
        """删除请假记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM leave_records WHERE id = ?", (leave_id,))
        conn.commit()
        return cursor.rowcount > 0
    
    def get_all(self, start_date: Optional[str] = None,
                end_date: Optional[str] = None) -> List[LeaveRecord]:
        """
        获取所有请假记录（可选日期范围）
        
        Args:
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if start_date and end_date:
            cursor.execute("""
                SELECT * FROM leave_records 
                WHERE leave_date BETWEEN ? AND ?
                ORDER BY leave_date DESC, start_time DESC
            """, (start_date, end_date))
        elif start_date:
            cursor.execute("""
                SELECT * FROM leave_records 
                WHERE leave_date >= ?
                ORDER BY leave_date DESC, start_time DESC
            """, (start_date,))
        elif end_date:
            cursor.execute("""
                SELECT * FROM leave_records 
                WHERE leave_date <= ?
                ORDER BY leave_date DESC, start_time DESC
            """, (end_date,))
        else:
            cursor.execute("""
                SELECT * FROM leave_records 
                ORDER BY leave_date DESC, start_time DESC
            """)
        
        rows = cursor.fetchall()
        return [LeaveRecord.from_row(row) for row in rows]
    
    def count(self) -> int:
        """获取请假记录总数"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM leave_records")
        return cursor.fetchone()[0]
    
    def clear_all(self):
        """清空所有请假记录（谨慎使用，仅用于测试）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM leave_records")
        conn.commit()

