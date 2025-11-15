"""
员工信息管理服务
"""
import sqlite3
from typing import List, Optional
from datetime import datetime
from database import get_db
from model import Employee, EmploymentInfo, EmploymentInfoHistory


class EmployeeService:
    """员工信息管理服务类"""
    
    def __init__(self):
        self.db = get_db()
    
    # ========== 员工个人信息管理 ==========
    
    def create_employee(self, employee: Employee) -> int:
        """
        创建新员工
        
        Args:
            employee: 员工对象
            
        Returns:
            新创建员工的ID
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO employees (employee_number, name, birth_date, gender, phone, email)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                employee.employee_number,
                employee.name,
                employee.birth_date,
                employee.gender,
                employee.phone,
                employee.email
            ))
            employee_id = cursor.lastrowid
            conn.commit()
            return employee_id
        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise ValueError(f"员工编号 {employee.employee_number} 已存在") from e
    
    def get_employee(self, employee_id: int) -> Optional[Employee]:
        """根据ID获取员工信息"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
        row = cursor.fetchone()
        
        if row:
            return Employee.from_row(row)
        return None
    
    def get_employee_by_number(self, employee_number: str) -> Optional[Employee]:
        """根据员工编号获取员工信息"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM employees WHERE employee_number = ?", (employee_number,))
        row = cursor.fetchone()
        
        if row:
            return Employee.from_row(row)
        return None
    
    def get_all_employees(self) -> List[Employee]:
        """获取所有员工列表"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM employees ORDER BY employee_number")
        rows = cursor.fetchall()
        
        return [Employee.from_row(row) for row in rows]
    
    def update_employee(self, employee: Employee) -> bool:
        """
        更新员工个人信息
        
        Args:
            employee: 员工对象（必须包含id）
            
        Returns:
            是否更新成功
        """
        if employee.id is None:
            raise ValueError("员工ID不能为空")
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE employees 
            SET name = ?, birth_date = ?, gender = ?, phone = ?, email = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            employee.name,
            employee.birth_date,
            employee.gender,
            employee.phone,
            employee.email,
            employee.id
        ))
        
        conn.commit()
        return cursor.rowcount > 0
    
    def delete_employee(self, employee_id: int) -> bool:
        """
        删除员工（会级联删除相关的入职信息）
        
        Args:
            employee_id: 员工ID
            
        Returns:
            是否删除成功
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
        conn.commit()
        
        return cursor.rowcount > 0
    
    # ========== 入职信息管理 ==========
    
    def create_employment_info(self, employment_info: EmploymentInfo) -> int:
        """
        创建入职信息（首次入职）
        
        Args:
            employment_info: 入职信息对象
            
        Returns:
            新创建的入职信息ID
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # 检查是否已存在入职信息
        cursor.execute("SELECT id FROM employment_info WHERE employee_id = ?", 
                      (employment_info.employee_id,))
        if cursor.fetchone():
            raise ValueError("该员工已存在入职信息，请使用更新方法")
        
        cursor.execute("""
            INSERT INTO employment_info 
            (employee_id, department, position, supervisor_id, hire_date, version)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (
            employment_info.employee_id,
            employment_info.department,
            employment_info.position,
            employment_info.supervisor_id,
            employment_info.hire_date
        ))
        
        employment_info_id = cursor.lastrowid
        conn.commit()
        return employment_info_id
    
    def get_employment_info(self, employee_id: int) -> Optional[EmploymentInfo]:
        """获取员工的当前入职信息"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM employment_info WHERE employee_id = ?", (employee_id,))
        row = cursor.fetchone()
        
        if row:
            return EmploymentInfo.from_row(row)
        return None
    
    def update_employment_info(self, employee_id: int, 
                              department: str, position: str,
                              hire_date: str, supervisor_id: Optional[int] = None,
                              change_reason: Optional[str] = None) -> bool:
        """
        更新入职信息（会记录历史版本）
        
        Args:
            employee_id: 员工ID
            department: 新部门
            position: 新职位
            hire_date: 入职时间
            supervisor_id: 上级ID
            change_reason: 变更原因
            
        Returns:
            是否更新成功
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. 获取当前入职信息
            cursor.execute("SELECT * FROM employment_info WHERE employee_id = ?", (employee_id,))
            current_info = cursor.fetchone()
            
            if not current_info:
                raise ValueError("该员工不存在入职信息")
            
            current_version = current_info['version']
            
            # 2. 将当前信息保存到历史表
            cursor.execute("""
                INSERT INTO employment_info_history 
                (employee_id, department, position, supervisor_id, hire_date, version, change_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                employee_id,
                current_info['department'],
                current_info['position'],
                current_info['supervisor_id'],
                current_info['hire_date'],
                current_version,
                change_reason
            ))
            
            # 3. 更新当前入职信息
            new_version = current_version + 1
            cursor.execute("""
                UPDATE employment_info 
                SET department = ?, position = ?, supervisor_id = ?, 
                    hire_date = ?, version = ?, updated_at = CURRENT_TIMESTAMP
                WHERE employee_id = ?
            """, (
                department,
                position,
                supervisor_id,
                hire_date,
                new_version,
                employee_id
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            raise
    
    def get_employment_info_history(self, employee_id: int) -> List[EmploymentInfoHistory]:
        """获取员工的入职信息历史记录"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM employment_info_history 
            WHERE employee_id = ? 
            ORDER BY version DESC
        """, (employee_id,))
        
        rows = cursor.fetchall()
        return [EmploymentInfoHistory.from_row(row) for row in rows]
    
    def get_employee_with_employment_info(self, employee_id: int) -> Optional[dict]:
        """
        获取员工完整信息（包括个人信息和当前入职信息）
        
        Returns:
            包含employee和employment_info的字典
        """
        employee = self.get_employee(employee_id)
        if not employee:
            return None
        
        employment_info = self.get_employment_info(employee_id)
        
        return {
            'employee': employee,
            'employment_info': employment_info
        }
    
    def get_all_employees_with_info(self) -> List[dict]:
        """获取所有员工的完整信息"""
        employees = self.get_all_employees()
        result = []
        
        for emp in employees:
            employment_info = self.get_employment_info(emp.id)
            result.append({
                'employee': emp,
                'employment_info': employment_info
            })
        
        return result

