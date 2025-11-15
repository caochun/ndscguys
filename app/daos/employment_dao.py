"""
雇佣信息数据访问层
"""
from typing import List, Optional, Dict
from .base_dao import BaseDAO
from app.models import Employment, EmploymentHistory


class EmploymentDAO(BaseDAO):
    """雇佣信息数据访问对象"""
    
    def create(self, employment: Employment) -> int:
        """
        创建入职信息（首次入职）
        
        Args:
            employment: 入职信息对象
            
        Returns:
            新创建的入职信息ID
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 检查是否已存在入职信息
        cursor.execute("SELECT id FROM employment WHERE employee_id = ?", 
                      (employment.employee_id,))
        if cursor.fetchone():
            raise ValueError("该员工已存在入职信息，请使用更新方法")
        
        cursor.execute("""
            INSERT INTO employment 
            (employee_id, department, position, supervisor_id, hire_date, version)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (
            employment.employee_id,
            employment.department,
            employment.position,
            employment.supervisor_id,
            employment.hire_date
        ))
        
        employment_id = cursor.lastrowid
        conn.commit()
        return employment_id
    
    def get_by_employee_id(self, employee_id: int) -> Optional[Employment]:
        """获取员工的当前入职信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM employment WHERE employee_id = ?", (employee_id,))
        row = cursor.fetchone()
        
        if row:
            return Employment.from_row(row)
        return None
    
    def get_current_info(self, employee_id: int) -> Optional[Dict]:
        """
        获取当前入职信息的原始数据（用于更新前的检查）
        
        Returns:
            字典格式的当前入职信息，如果不存在返回 None
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM employment WHERE employee_id = ?", (employee_id,))
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        return None
    
    def update(self, employee_id: int, 
               department: str, position: str,
               hire_date: str, supervisor_id: Optional[int] = None,
               change_reason: Optional[str] = None) -> bool:
        """
        更新入职信息（会记录历史版本）
        
        只处理公司内的岗位变更（部门、职位、上级等），不处理公司变更
        
        Args:
            employee_id: 员工ID
            department: 新部门
            position: 新职位
            hire_date: 入职时间（通常不变，但允许修改）
            supervisor_id: 上级ID
            change_reason: 变更原因
            
        Returns:
            是否更新成功（如果字段没有变化，返回 False）
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. 获取当前入职信息
            current_info = self.get_current_info(employee_id)
            
            if not current_info:
                raise ValueError("该员工不存在入职信息")
            
            # 2. 检查字段是否有变化
            fields_changed = (
                current_info['department'] != department or
                current_info['position'] != position or
                current_info['hire_date'] != hire_date or
                (current_info['supervisor_id'] or 0) != (supervisor_id or 0)
            )
            
            if not fields_changed:
                # 字段没有变化，不更新
                return False
            
            current_version = current_info['version']
            
            # 3. 将当前任职信息保存到历史表
            cursor.execute("""
                INSERT INTO employment_history 
                (employee_id, department, position, supervisor_id, hire_date, version, change_reason, changed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                employee_id,
                current_info['department'],
                current_info['position'],
                current_info['supervisor_id'],
                current_info['hire_date'],
                current_version,
                change_reason
            ))
            
            # 4. 更新当前任职信息
            new_version = current_version + 1
            cursor.execute("""
                UPDATE employment 
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
    
    def get_history(self, employee_id: int) -> List[EmploymentHistory]:
        """获取员工的入职信息历史记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM employment_history 
            WHERE employee_id = ? 
            ORDER BY version DESC
        """, (employee_id,))
        
        rows = cursor.fetchall()
        return [EmploymentHistory.from_row(row) for row in rows]
    
    def get_all_with_join(self, company_name: Optional[str] = None) -> List[Dict]:
        """
        获取所有员工的完整信息（使用JOIN优化查询）
        
        Args:
            company_name: 如果提供，只返回该公司的员工
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 使用JOIN一次性查询所有数据
        if company_name:
            cursor.execute("""
                SELECT 
                    e.id as employee_id,
                    e.person_id,
                    e.company_name,
                    e.employee_number,
                    e.status,
                    e.created_at as employee_created_at,
                    e.updated_at as employee_updated_at,
                    p.name,
                    p.birth_date,
                    p.gender,
                    p.phone,
                    p.email,
                    p.address,
                    p.created_at as person_created_at,
                    p.updated_at as person_updated_at,
                    ei.id as employment_id,
                    ei.department,
                    ei.position,
                    ei.hire_date,
                    ei.supervisor_id,
                    ei.version,
                    ei.created_at as employment_created_at,
                    ei.updated_at as employment_updated_at,
                    CASE WHEN eih.id IS NOT NULL THEN 1 ELSE 0 END as has_history
                FROM employees e
                LEFT JOIN persons p ON e.person_id = p.id
                LEFT JOIN employment ei ON e.id = ei.employee_id
                LEFT JOIN (
                    SELECT DISTINCT employee_id, 1 as id
                    FROM employment_history
                ) eih ON e.id = eih.employee_id
                WHERE e.company_name = ? AND e.status = 'active'
                ORDER BY e.employee_number
            """, (company_name,))
        else:
            cursor.execute("""
                SELECT 
                    e.id as employee_id,
                    e.person_id,
                    e.company_name,
                    e.employee_number,
                    e.status,
                    e.created_at as employee_created_at,
                    e.updated_at as employee_updated_at,
                    p.name,
                    p.birth_date,
                    p.gender,
                    p.phone,
                    p.email,
                    p.address,
                    p.created_at as person_created_at,
                    p.updated_at as person_updated_at,
                    ei.id as employment_id,
                    ei.department,
                    ei.position,
                    ei.hire_date,
                    ei.supervisor_id,
                    ei.version,
                    ei.created_at as employment_created_at,
                    ei.updated_at as employment_updated_at,
                    CASE WHEN eih.id IS NOT NULL THEN 1 ELSE 0 END as has_history
                FROM employees e
                LEFT JOIN persons p ON e.person_id = p.id
                LEFT JOIN employment ei ON e.id = ei.employee_id
                LEFT JOIN (
                    SELECT DISTINCT employee_id, 1 as id
                    FROM employment_history
                ) eih ON e.id = eih.employee_id
                WHERE e.status = 'active'
                ORDER BY e.company_name, e.employee_number
            """)
        
        return cursor.fetchall()
    
    def count_employment(self) -> int:
        """获取入职信息总数"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM employment")
        return cursor.fetchone()[0]
    
    def count_history(self) -> int:
        """获取历史记录总数"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM employment_history")
        return cursor.fetchone()[0]
    
    def clear_all(self):
        """清空所有入职信息和历史数据（谨慎使用，仅用于测试）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM employment_history")
        cursor.execute("DELETE FROM employment")
        conn.commit()

