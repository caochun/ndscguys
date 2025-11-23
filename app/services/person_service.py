"""
人员信息管理服务
"""
from typing import List, Optional
from app.models import Person
from app.daos import PersonDAO


class PersonService:
    """人员信息管理服务类"""
    
    def __init__(self):
        self.person_dao = PersonDAO()
    
    def create_person(self, person: Person) -> int:
        """
        创建新人员
        
        Args:
            person: 人员对象
            
        Returns:
            新创建人员的ID
        """
        return self.person_dao.create(person)
    
    def get_person(self, person_id: int) -> Optional[Person]:
        """根据ID获取人员信息"""
        return self.person_dao.get_by_id(person_id)
    
    def get_all_persons(self) -> List[Person]:
        """获取所有人员列表"""
        return self.person_dao.get_all()
    
    def get_unemployed_persons(self) -> List[Person]:
        """获取未任职人员列表（未在任何公司有active员工记录的人员）"""
        return self.person_dao.get_unemployed_persons()
    
    def get_employed_persons(self) -> List[Person]:
        """获取已任职人员列表（至少在一个公司有active员工记录的人员）"""
        return self.person_dao.get_employed_persons()
    
    def update_person(self, person: Person) -> bool:
        """更新人员信息"""
        return self.person_dao.update(person)
    
    def find_or_create_person(self, person: Person) -> int:
        """
        查找或创建人员（根据手机号或邮箱匹配）
        
        业务逻辑：
        1. 如果提供了 phone，先根据 phone 查找
        2. 如果找到，更新 person 信息，返回 person_id
        3. 如果没找到且提供了 email，根据 email 查找
        4. 如果找到，更新 person 信息，返回 person_id
        5. 如果都没找到，创建新 person，返回 person_id
        
        Args:
            person: Person 对象（包含人员信息）
        
        Returns:
            person_id: 人员ID（已存在或新创建的）
        """
        # 检查是否已存在相同的人员（根据手机、邮箱匹配）
        person_id = None
        if person.phone:
            existing_person = self.person_dao.get_by_phone(person.phone)
            if existing_person:
                person_id = existing_person.id
                # 更新人员信息
                person.id = person_id
                self.person_dao.update(person)
        
        if not person_id and person.email:
            existing_person = self.person_dao.get_by_email(person.email)
            if existing_person:
                person_id = existing_person.id
                # 更新人员信息
                person.id = person_id
                self.person_dao.update(person)
        
        # 如果没找到，创建新人员
        if not person_id:
            person_id = self.person_dao.create(person)
        
        return person_id

