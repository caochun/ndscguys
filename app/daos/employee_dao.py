"""
员工数据访问层
"""
import sqlite3
from typing import List, Optional
from .base_dao import BaseDAO
from app.models import Employee


class EmployeeDAO(BaseDAO):
    """员工数据访问对象"""
    
    def create(self, person_id: int, company_name: str, employee_number: str, status: str = 'active') -> int:
        """
        创建新员工记录
        
        Args:
            person_id: 人员ID
            company_name: 公司名称
            employee_number: 员工编号
            status: 员工状态，默认为 'active'
            
        Returns:
            新创建员工的ID
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO employees (person_id, company_name, employee_number, status)
                VALUES (?, ?, ?, ?)
            """, (person_id, company_name, employee_number, status))
            
            employee_id = cursor.lastrowid
            conn.commit()
            return employee_id
        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise ValueError(f"员工编号 {employee_number} 在公司 {company_name} 中已存在") from e
    
    def get_by_id(self, employee_id: int) -> Optional[Employee]:
        """根据ID获取员工信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
        row = cursor.fetchone()
        
        if row:
            return Employee.from_row(row)
        return None
    
    def get_by_number(self, company_name: str, employee_number: str) -> Optional[Employee]:
        """根据公司名称和员工编号获取员工信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM employees 
            WHERE company_name = ? AND employee_number = ?
        """, (company_name, employee_number))
        row = cursor.fetchone()
        
        if row:
            return Employee.from_row(row)
        return None
    
    def get_all(self, company_name: Optional[str] = None, status: Optional[str] = 'active') -> List[Employee]:
        """
        获取员工列表
        
        Args:
            company_name: 如果提供，只返回该公司的员工
            status: 员工状态筛选，默认只返回 'active' 员工。如果为 None，返回所有状态的员工
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if company_name:
            if status:
                cursor.execute("""
                    SELECT * FROM employees 
                    WHERE company_name = ? AND status = ?
                    ORDER BY employee_number
                """, (company_name, status))
            else:
                cursor.execute("""
                    SELECT * FROM employees 
                    WHERE company_name = ?
                    ORDER BY employee_number
                """, (company_name,))
        else:
            if status:
                cursor.execute("""
                    SELECT * FROM employees 
                    WHERE status = ?
                    ORDER BY company_name, employee_number
                """, (status,))
            else:
                cursor.execute("SELECT * FROM employees ORDER BY company_name, employee_number")
        
        rows = cursor.fetchall()
        return [Employee.from_row(row) for row in rows]
    
    def update_status(self, employee_id: int, status: str) -> bool:
        """更新员工状态（active/inactive/terminated）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE employees 
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status, employee_id))
        
        conn.commit()
        return cursor.rowcount > 0
    
    def delete(self, employee_id: int) -> bool:
        """删除员工（不会删除人员信息）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
        conn.commit()
        
        return cursor.rowcount > 0
    
    def get_by_person_id(self, person_id: int) -> List[Employee]:
        """根据人员ID获取该人员的所有员工记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM employees 
            WHERE person_id = ?
            ORDER BY created_at DESC
        """, (person_id,))
        
        rows = cursor.fetchall()
        return [Employee.from_row(row) for row in rows]
    
    def count(self) -> int:
        """获取员工总数"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM employees")
        return cursor.fetchone()[0]
    
    def clear_all(self):
        """清空所有员工数据（谨慎使用，仅用于测试）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM employees")
        conn.commit()

