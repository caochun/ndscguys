"""
员工信息管理服务
"""
import sqlite3
from typing import List, Optional, Dict
from datetime import datetime
from app.database import get_db
from app.models import Person, Employee, EmploymentInfo, EmploymentInfoHistory


class EmployeeService:
    """员工信息管理服务类"""
    
    def __init__(self):
        self.db = get_db()
    
    # ========== 人员基本信息管理 ==========
    
    def create_person(self, person: Person) -> int:
        """
        创建新人员
        
        Args:
            person: 人员对象
            
        Returns:
            新创建人员的ID
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO persons (name, birth_date, gender, phone, email)
                VALUES (?, ?, ?, ?, ?)
            """, (
                person.name,
                person.birth_date,
                person.gender,
                person.phone,
                person.email
            ))
            person_id = cursor.lastrowid
            conn.commit()
            return person_id
        except Exception as e:
            conn.rollback()
            raise ValueError(f"创建人员失败：{str(e)}") from e
    
    def get_person(self, person_id: int) -> Optional[Person]:
        """根据ID获取人员信息"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM persons WHERE id = ?", (person_id,))
        row = cursor.fetchone()
        
        if row:
            return Person.from_row(row)
        return None
    
    def update_person(self, person: Person) -> bool:
        """更新人员信息"""
        if person.id is None:
            raise ValueError("人员ID不能为空")
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE persons 
            SET name = ?, birth_date = ?, gender = ?, phone = ?, email = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            person.name,
            person.birth_date,
            person.gender,
            person.phone,
            person.email,
            person.id
        ))
        
        conn.commit()
        return cursor.rowcount > 0
    
    # ========== 员工管理 ==========
    
    def create_employee(self, person: Person, company_name: str, employee_number: str) -> int:
        """
        创建新员工（先创建或查找人员，再创建员工记录）
        
        Args:
            person: 人员对象
            company_name: 公司名称
            employee_number: 员工编号
            
        Returns:
            新创建员工的ID
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # 检查是否已存在相同的人员（根据姓名、手机、邮箱匹配）
            person_id = None
            if person.phone or person.email:
                if person.phone:
                    cursor.execute("SELECT id FROM persons WHERE phone = ?", (person.phone,))
                    row = cursor.fetchone()
                    if row:
                        person_id = row['id']
                        # 更新人员信息
                        person.id = person_id
                        self.update_person(person)
                
                if not person_id and person.email:
                    cursor.execute("SELECT id FROM persons WHERE email = ?", (person.email,))
                    row = cursor.fetchone()
                    if row:
                        person_id = row['id']
                        # 更新人员信息
                        person.id = person_id
                        self.update_person(person)
            
            # 如果没找到，创建新人员
            if not person_id:
                person_id = self.create_person(person)
            
            # 创建员工记录
            cursor.execute("""
                INSERT INTO employees (person_id, company_name, employee_number)
                VALUES (?, ?, ?)
            """, (person_id, company_name, employee_number))
            
            employee_id = cursor.lastrowid
            conn.commit()
            return employee_id
        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise ValueError(f"员工编号 {employee_number} 在公司 {company_name} 中已存在") from e
    
    def get_employee(self, employee_id: int) -> Optional[Employee]:
        """根据ID获取员工信息"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
        row = cursor.fetchone()
        
        if row:
            return Employee.from_row(row)
        return None
    
    def get_employee_by_number(self, company_name: str, employee_number: str) -> Optional[Employee]:
        """根据公司名称和员工编号获取员工信息"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM employees 
            WHERE company_name = ? AND employee_number = ?
        """, (company_name, employee_number))
        row = cursor.fetchone()
        
        if row:
            return Employee.from_row(row)
        return None
    
    def get_all_employees(self, company_name: Optional[str] = None) -> List[Employee]:
        """
        获取所有员工列表
        
        Args:
            company_name: 如果提供，只返回该公司的员工
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        if company_name:
            cursor.execute("""
                SELECT * FROM employees 
                WHERE company_name = ?
                ORDER BY employee_number
            """, (company_name,))
        else:
            cursor.execute("SELECT * FROM employees ORDER BY company_name, employee_number")
        
        rows = cursor.fetchall()
        return [Employee.from_row(row) for row in rows]
    
    def delete_employee(self, employee_id: int) -> bool:
        """删除员工（不会删除人员信息）"""
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
            (employee_id, company_name, department, position, supervisor_id, hire_date, version)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (
            employment_info.employee_id,
            employment_info.company_name,
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
                              company_name: str,
                              department: str, position: str,
                              hire_date: str, supervisor_id: Optional[int] = None,
                              change_reason: Optional[str] = None) -> bool:
        """
        更新入职信息（会记录历史版本）
        
        换公司和换部门没有本质区别，都是更新 employment_info 的字段
        
        Args:
            employee_id: 员工ID
            company_name: 公司名称（如果变化，会同时更新 employees 表）
            department: 新部门
            position: 新职位
            hire_date: 入职时间
            supervisor_id: 上级ID
            change_reason: 变更原因
            
        Returns:
            是否更新成功（如果字段没有变化，返回 False）
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. 获取当前入职信息和员工信息
            cursor.execute("SELECT * FROM employment_info WHERE employee_id = ?", (employee_id,))
            current_info = cursor.fetchone()
            
            if not current_info:
                raise ValueError("该员工不存在入职信息")
            
            # 检查公司是否匹配
            cursor.execute("SELECT company_name FROM employees WHERE id = ?", (employee_id,))
            employee = cursor.fetchone()
            if not employee:
                raise ValueError("员工不存在")
            
            # 允许更新公司名称（换公司和换部门没有本质区别）
            # 如果公司名称变化，需要同时更新 employees 表
            if employee['company_name'] != company_name:
                cursor.execute("""
                    UPDATE employees 
                    SET company_name = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (company_name, employee_id))
            
            # 2. 检查字段是否有变化
            fields_changed = (
                current_info['company_name'] != company_name or
                current_info['department'] != department or
                current_info['position'] != position or
                current_info['hire_date'] != hire_date or
                (current_info['supervisor_id'] or 0) != (supervisor_id or 0)
            )
            
            if not fields_changed:
                # 字段没有变化，不更新
                return False
            
            current_version = current_info['version']
            
            # 3. 将当前任职信息保存到历史表（设置变更时间、变更原因等字段）
            cursor.execute("""
                INSERT INTO employment_info_history 
                (employee_id, company_name, department, position, supervisor_id, hire_date, version, change_reason, changed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                employee_id,
                current_info['company_name'],
                current_info['department'],
                current_info['position'],
                current_info['supervisor_id'],
                current_info['hire_date'],
                current_version,
                change_reason
            ))
            
            # 4. 将新的任职信息存到 employment_info 中
            new_version = current_version + 1
            cursor.execute("""
                UPDATE employment_info 
                SET company_name = ?, department = ?, position = ?, supervisor_id = ?, 
                    hire_date = ?, version = ?, updated_at = CURRENT_TIMESTAMP
                WHERE employee_id = ?
            """, (
                company_name,
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
    
    def transfer_employee_to_company(self, employee_id: int,
                                     new_company_name: str,
                                     new_employee_number: str,
                                     department: str, position: str,
                                     hire_date: str, supervisor_id: Optional[int] = None,
                                     change_reason: Optional[str] = None) -> int:
        """
        将员工转移到新公司（更新 employment_info，包括 company_name）
        
        换公司和换部门没有本质区别，都是更新 employment_info 的字段
        
        Args:
            employee_id: 员工ID
            new_company_name: 新公司名称
            new_employee_number: 新公司中的员工编号（如果与当前不同，需要更新 employees 表）
            department: 新部门
            position: 新职位
            hire_date: 新公司的入职时间
            supervisor_id: 上级ID（新公司中的员工ID）
            change_reason: 变更原因
            
        Returns:
            员工ID（保持不变）
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. 获取原员工信息
            cursor.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
            old_employee = cursor.fetchone()
            if not old_employee:
                raise ValueError("员工不存在")
            
            # 2. 获取原入职信息并保存到历史表
            cursor.execute("SELECT * FROM employment_info WHERE employee_id = ?", (employee_id,))
            old_info = cursor.fetchone()
            
            if not old_info:
                raise ValueError("该员工不存在入职信息")
            
            # 3. 将当前任职信息保存到历史表（设置变更时间、变更原因等字段）
            cursor.execute("""
                INSERT INTO employment_info_history 
                (employee_id, company_name, department, position, supervisor_id, hire_date, version, change_reason, changed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                employee_id,
                old_info['company_name'],
                old_info['department'],
                old_info['position'],
                old_info['supervisor_id'],
                old_info['hire_date'],
                old_info['version'],
                change_reason or f"从 {old_info['company_name']} 转到 {new_company_name}"
            ))
            
            # 4. 更新 employees 表的 company_name 和 employee_number（如果需要）
            if (old_employee['company_name'] != new_company_name or 
                old_employee['employee_number'] != new_employee_number):
                cursor.execute("""
                    UPDATE employees 
                    SET company_name = ?, employee_number = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (new_company_name, new_employee_number, employee_id))
            
            # 5. 更新 employment_info（包括 company_name，就像更新部门一样）
            new_version = old_info['version'] + 1
            cursor.execute("""
                UPDATE employment_info 
                SET company_name = ?, department = ?, position = ?, supervisor_id = ?, 
                    hire_date = ?, version = ?, updated_at = CURRENT_TIMESTAMP
                WHERE employee_id = ?
            """, (
                new_company_name,
                department,
                position,
                supervisor_id,
                hire_date,
                new_version,
                employee_id
            ))
            
            conn.commit()
            return employee_id
            
        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise ValueError(f"员工编号 {new_employee_number} 在公司 {new_company_name} 中已存在") from e
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
    
    def get_employee_with_employment_info(self, employee_id: int) -> Optional[Dict]:
        """
        获取员工完整信息（包括人员信息、员工信息和当前入职信息）
        
        Returns:
            包含person、employee和employment_info的字典
        """
        employee = self.get_employee(employee_id)
        if not employee:
            return None
        
        person = self.get_person(employee.person_id)
        employment_info = self.get_employment_info(employee_id)
        
        return {
            'person': person,
            'employee': employee,
            'employment_info': employment_info
        }
    
    def get_all_employees_with_info(self, company_name: Optional[str] = None) -> List[Dict]:
        """
        获取所有员工的完整信息（使用JOIN优化查询）
        
        Args:
            company_name: 如果提供，只返回该公司的员工
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # 使用JOIN一次性查询所有数据
        if company_name:
            cursor.execute("""
                SELECT 
                    e.id as employee_id,
                    e.person_id,
                    e.company_name,
                    e.employee_number,
                    e.created_at as employee_created_at,
                    e.updated_at as employee_updated_at,
                    p.name,
                    p.birth_date,
                    p.gender,
                    p.phone,
                    p.email,
                    p.created_at as person_created_at,
                    p.updated_at as person_updated_at,
                    ei.id as employment_info_id,
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
                LEFT JOIN employment_info ei ON e.id = ei.employee_id
                LEFT JOIN (
                    SELECT DISTINCT employee_id, 1 as id
                    FROM employment_info_history
                ) eih ON e.id = eih.employee_id
                WHERE e.company_name = ?
                ORDER BY e.employee_number
            """, (company_name,))
        else:
            cursor.execute("""
                SELECT 
                    e.id as employee_id,
                    e.person_id,
                    e.company_name,
                    e.employee_number,
                    e.created_at as employee_created_at,
                    e.updated_at as employee_updated_at,
                    p.name,
                    p.birth_date,
                    p.gender,
                    p.phone,
                    p.email,
                    p.created_at as person_created_at,
                    p.updated_at as person_updated_at,
                    ei.id as employment_info_id,
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
                LEFT JOIN employment_info ei ON e.id = ei.employee_id
                LEFT JOIN (
                    SELECT DISTINCT employee_id, 1 as id
                    FROM employment_info_history
                ) eih ON e.id = eih.employee_id
                ORDER BY e.company_name, e.employee_number
            """)
        
        rows = cursor.fetchall()
        result = []
        
        for row in rows:
            # 构建Person对象
            person = None
            if row['person_id']:
                person = Person(
                    id=row['person_id'],
                    name=row['name'],
                    birth_date=row['birth_date'],
                    gender=row['gender'],
                    phone=row['phone'],
                    email=row['email'],
                    created_at=row['person_created_at'],
                    updated_at=row['person_updated_at']
                )
            
            # 构建Employee对象
            employee = Employee(
                id=row['employee_id'],
                person_id=row['person_id'],
                company_name=row['company_name'],
                employee_number=row['employee_number'],
                created_at=row['employee_created_at'],
                updated_at=row['employee_updated_at']
            )
            
            # 构建EmploymentInfo对象
            employment_info = None
            if row['employment_info_id']:
                employment_info = EmploymentInfo(
                    id=row['employment_info_id'],
                    employee_id=row['employee_id'],
                    company_name=row['company_name'],
                    department=row['department'],
                    position=row['position'],
                    hire_date=row['hire_date'],
                    supervisor_id=row['supervisor_id'],
                    version=row['version'],
                    created_at=row['employment_created_at'],
                    updated_at=row['employment_updated_at']
                )

            result.append({
                'person': person,
                'employee': employee,
                'employment_info': employment_info,
                'has_history': bool(row['has_history'])
            })
        
        return result
    
    def get_persons_by_company(self, company_name: str) -> List[Dict]:
        """
        获取指定公司的所有人员信息（包括员工和入职信息）
        """
        return self.get_all_employees_with_info(company_name)
    
    def get_person_work_history(self, person_id: int) -> List[Dict]:
        """
        获取一个人在所有公司的工作历史
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT e.*, ei.department, ei.position, ei.hire_date
            FROM employees e
            LEFT JOIN employment_info ei ON e.id = ei.employee_id
            WHERE e.person_id = ?
            ORDER BY ei.hire_date DESC
        """, (person_id,))
        
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                'employee_id': row['id'],
                'company_name': row['company_name'],
                'employee_number': row['employee_number'],
                'department': row['department'],
                'position': row['position'],
                'hire_date': row['hire_date']
            })
        
        return result
