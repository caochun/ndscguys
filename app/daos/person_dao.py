"""
人员数据访问层
"""
import sqlite3
from typing import List, Optional
from .base_dao import BaseDAO
from app.models import Person


class PersonDAO(BaseDAO):
    """人员数据访问对象"""
    
    def create(self, person: Person) -> int:
        """
        创建新人员
        
        Args:
            person: 人员对象
            
        Returns:
            新创建人员的ID
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO persons (name, birth_date, gender, phone, email, address)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                person.name,
                person.birth_date,
                person.gender,
                person.phone,
                person.email,
                person.address
            ))
            person_id = cursor.lastrowid
            conn.commit()
            return person_id
        except Exception as e:
            conn.rollback()
            raise ValueError(f"创建人员失败：{str(e)}") from e
    
    def get_by_id(self, person_id: int) -> Optional[Person]:
        """根据ID获取人员信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM persons WHERE id = ?", (person_id,))
        row = cursor.fetchone()
        
        if row:
            return Person.from_row(row)
        return None
    
    def get_by_phone(self, phone: str) -> Optional[Person]:
        """根据手机号获取人员信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM persons WHERE phone = ?", (phone,))
        row = cursor.fetchone()
        
        if row:
            return Person.from_row(row)
        return None
    
    def get_by_email(self, email: str) -> Optional[Person]:
        """根据邮箱获取人员信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM persons WHERE email = ?", (email,))
        row = cursor.fetchone()
        
        if row:
            return Person.from_row(row)
        return None
    
    def get_all(self) -> List[Person]:
        """获取所有人员列表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM persons ORDER BY name")
        rows = cursor.fetchall()
        return [Person.from_row(row) for row in rows]
    
    def update(self, person: Person) -> bool:
        """更新人员信息"""
        if person.id is None:
            raise ValueError("人员ID不能为空")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE persons 
            SET name = ?, birth_date = ?, gender = ?, phone = ?, email = ?, address = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            person.name,
            person.birth_date,
            person.gender,
            person.phone,
            person.email,
            person.address,
            person.id
        ))
        
        conn.commit()
        return cursor.rowcount > 0
    
    def count(self) -> int:
        """获取人员总数"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM persons")
        return cursor.fetchone()[0]
    
    def get_unemployed_persons(self) -> List[Person]:
        """
        获取未任职人员列表（未在任何公司有active员工记录的人员）
        
        Returns:
            未任职人员列表
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT p.*
            FROM persons p
            LEFT JOIN employees e ON p.id = e.person_id AND e.status = 'active'
            WHERE e.id IS NULL
            ORDER BY p.name
        """)
        
        rows = cursor.fetchall()
        return [Person.from_row(row) for row in rows]
    
    def get_employed_persons(self) -> List[Person]:
        """
        获取已任职人员列表（至少在一个公司有active员工记录的人员）
        
        Returns:
            已任职人员列表
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT p.*
            FROM persons p
            INNER JOIN employees e ON p.id = e.person_id
            WHERE e.status = 'active'
            ORDER BY p.name
        """)
        
        rows = cursor.fetchall()
        return [Person.from_row(row) for row in rows]
    
    def clear_all(self):
        """清空所有人员数据（谨慎使用，仅用于测试）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM persons")
        conn.commit()

