"""
考勤记录数据访问层
"""
from typing import List, Optional
from .base_dao import BaseDAO
from app.models import Attendance


class AttendanceDAO(BaseDAO):
    """考勤记录数据访问对象"""
    
    def create(self, attendance: Attendance) -> int:
        """
        创建考勤记录
        
        Args:
            attendance: 考勤记录对象
            
        Returns:
            新创建的考勤记录ID
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO attendance 
                (person_id, employee_id, company_name, attendance_date, 
                 check_in_time, check_out_time, status, work_hours, 
                 standard_hours, overtime_hours, leave_hours, remark)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                attendance.person_id,
                attendance.employee_id,
                attendance.company_name,
                attendance.attendance_date,
                attendance.check_in_time,
                attendance.check_out_time,
                attendance.status,
                attendance.work_hours,
                attendance.standard_hours,
                attendance.overtime_hours,
                attendance.leave_hours,
                attendance.remark
            ))
            attendance_id = cursor.lastrowid
            conn.commit()
            return attendance_id
        except Exception as e:
            conn.rollback()
            raise ValueError(f"创建考勤记录失败：{str(e)}") from e
    
    def get_by_id(self, attendance_id: int) -> Optional[Attendance]:
        """根据ID获取考勤记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM attendance WHERE id = ?", (attendance_id,))
        row = cursor.fetchone()
        
        if row:
            return Attendance.from_row(row)
        return None
    
    def get_by_person_id(self, person_id: int, start_date: Optional[str] = None, 
                        end_date: Optional[str] = None) -> List[Attendance]:
        """
        根据人员ID获取考勤记录
        
        Args:
            person_id: 人员ID
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if start_date and end_date:
            cursor.execute("""
                SELECT * FROM attendance 
                WHERE person_id = ? AND attendance_date BETWEEN ? AND ?
                ORDER BY attendance_date DESC
            """, (person_id, start_date, end_date))
        elif start_date:
            cursor.execute("""
                SELECT * FROM attendance 
                WHERE person_id = ? AND attendance_date >= ?
                ORDER BY attendance_date DESC
            """, (person_id, start_date))
        elif end_date:
            cursor.execute("""
                SELECT * FROM attendance 
                WHERE person_id = ? AND attendance_date <= ?
                ORDER BY attendance_date DESC
            """, (person_id, end_date))
        else:
            cursor.execute("""
                SELECT * FROM attendance 
                WHERE person_id = ?
                ORDER BY attendance_date DESC
            """, (person_id,))
        
        rows = cursor.fetchall()
        return [Attendance.from_row(row) for row in rows]
    
    def get_by_person_and_company(self, person_id: int, company_name: str,
                                  start_date: Optional[str] = None,
                                  end_date: Optional[str] = None) -> List[Attendance]:
        """
        根据人员ID和公司名称获取考勤记录
        
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
                SELECT * FROM attendance 
                WHERE person_id = ? AND company_name = ? 
                AND attendance_date BETWEEN ? AND ?
                ORDER BY attendance_date DESC
            """, (person_id, company_name, start_date, end_date))
        elif start_date:
            cursor.execute("""
                SELECT * FROM attendance 
                WHERE person_id = ? AND company_name = ? 
                AND attendance_date >= ?
                ORDER BY attendance_date DESC
            """, (person_id, company_name, start_date))
        elif end_date:
            cursor.execute("""
                SELECT * FROM attendance 
                WHERE person_id = ? AND company_name = ? 
                AND attendance_date <= ?
                ORDER BY attendance_date DESC
            """, (person_id, company_name, end_date))
        else:
            cursor.execute("""
                SELECT * FROM attendance 
                WHERE person_id = ? AND company_name = ?
                ORDER BY attendance_date DESC
            """, (person_id, company_name))
        
        rows = cursor.fetchall()
        return [Attendance.from_row(row) for row in rows]
    
    def get_by_employee_id(self, employee_id: int,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> List[Attendance]:
        """
        根据员工ID获取考勤记录
        
        Args:
            employee_id: 员工ID
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if start_date and end_date:
            cursor.execute("""
                SELECT * FROM attendance 
                WHERE employee_id = ? AND attendance_date BETWEEN ? AND ?
                ORDER BY attendance_date DESC
            """, (employee_id, start_date, end_date))
        elif start_date:
            cursor.execute("""
                SELECT * FROM attendance 
                WHERE employee_id = ? AND attendance_date >= ?
                ORDER BY attendance_date DESC
            """, (employee_id, start_date))
        elif end_date:
            cursor.execute("""
                SELECT * FROM attendance 
                WHERE employee_id = ? AND attendance_date <= ?
                ORDER BY attendance_date DESC
            """, (employee_id, end_date))
        else:
            cursor.execute("""
                SELECT * FROM attendance 
                WHERE employee_id = ?
                ORDER BY attendance_date DESC
            """, (employee_id,))
        
        rows = cursor.fetchall()
        return [Attendance.from_row(row) for row in rows]
    
    def get_by_date(self, attendance_date: str, company_name: Optional[str] = None) -> List[Attendance]:
        """
        根据日期获取考勤记录
        
        Args:
            attendance_date: 考勤日期
            company_name: 公司名称（可选）
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if company_name:
            cursor.execute("""
                SELECT * FROM attendance 
                WHERE attendance_date = ? AND company_name = ?
                ORDER BY person_id
            """, (attendance_date, company_name))
        else:
            cursor.execute("""
                SELECT * FROM attendance 
                WHERE attendance_date = ?
                ORDER BY company_name, person_id
            """, (attendance_date,))
        
        rows = cursor.fetchall()
        return [Attendance.from_row(row) for row in rows]
    
    def get_by_date_range(self, start_date: Optional[str] = None,
                         end_date: Optional[str] = None,
                         company_name: Optional[str] = None) -> List[Attendance]:
        """
        根据日期范围获取考勤记录
        
        Args:
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            company_name: 公司名称（可选）
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if start_date and end_date:
            if company_name:
                cursor.execute("""
                    SELECT * FROM attendance 
                    WHERE attendance_date BETWEEN ? AND ? AND company_name = ?
                    ORDER BY attendance_date DESC, company_name, person_id
                """, (start_date, end_date, company_name))
            else:
                cursor.execute("""
                    SELECT * FROM attendance 
                    WHERE attendance_date BETWEEN ? AND ?
                    ORDER BY attendance_date DESC, company_name, person_id
                """, (start_date, end_date))
        elif start_date:
            if company_name:
                cursor.execute("""
                    SELECT * FROM attendance 
                    WHERE attendance_date >= ? AND company_name = ?
                    ORDER BY attendance_date DESC, company_name, person_id
                """, (start_date, company_name))
            else:
                cursor.execute("""
                    SELECT * FROM attendance 
                    WHERE attendance_date >= ?
                    ORDER BY attendance_date DESC, company_name, person_id
                """, (start_date,))
        elif end_date:
            if company_name:
                cursor.execute("""
                    SELECT * FROM attendance 
                    WHERE attendance_date <= ? AND company_name = ?
                    ORDER BY attendance_date DESC, company_name, person_id
                """, (end_date, company_name))
            else:
                cursor.execute("""
                    SELECT * FROM attendance 
                    WHERE attendance_date <= ?
                    ORDER BY attendance_date DESC, company_name, person_id
                """, (end_date,))
        else:
            if company_name:
                cursor.execute("""
                    SELECT * FROM attendance 
                    WHERE company_name = ?
                    ORDER BY attendance_date DESC, person_id
                """, (company_name,))
            else:
                cursor.execute("""
                    SELECT * FROM attendance 
                    ORDER BY attendance_date DESC, company_name, person_id
                """)
        
        rows = cursor.fetchall()
        return [Attendance.from_row(row) for row in rows]
    
    def update(self, attendance: Attendance) -> bool:
        """更新考勤记录"""
        if attendance.id is None:
            raise ValueError("考勤记录ID不能为空")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE attendance 
            SET check_in_time = ?, check_out_time = ?, status = ?,
                work_hours = ?, overtime_hours = ?, leave_hours = ?,
                remark = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            attendance.check_in_time,
            attendance.check_out_time,
            attendance.status,
            attendance.work_hours,
            attendance.overtime_hours,
            attendance.leave_hours,
            attendance.remark,
            attendance.id
        ))
        
        conn.commit()
        return cursor.rowcount > 0
    
    def delete(self, attendance_id: int) -> bool:
        """删除考勤记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM attendance WHERE id = ?", (attendance_id,))
        conn.commit()
        return cursor.rowcount > 0
    
    def count(self) -> int:
        """获取考勤记录总数"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM attendance")
        return cursor.fetchone()[0]
    
    def clear_all(self):
        """清空所有考勤记录（谨慎使用，仅用于测试）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM attendance")
        conn.commit()

