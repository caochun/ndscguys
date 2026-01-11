"""
项目服务层
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional

from app.db import init_db
from app.daos.project_dao import ProjectDAO
from app.daos.project_state_dao import ProjectBasicStateDAO
from app.daos.person_project_state_dao import PersonProjectStateDAO
from app.models.project_payloads import sanitize_project_payload


class ProjectService:
    def __init__(self, db_path: str):
        self.db_path = db_path
        init_db(db_path)
        self.project_dao = ProjectDAO(db_path=db_path)
        self.basic_dao = ProjectBasicStateDAO(db_path=db_path)

    def create_project(self, project_data: dict) -> int:
        """创建新项目（使用 DAO 层方法）"""
        cleaned_data = sanitize_project_payload(project_data)
        # 使用 DAO 层方法创建 project_id
        project_id = self.project_dao.create_project()
        self.basic_dao.append(project_id, cleaned_data)
        return project_id

    def get_current_project_manager(self, project_id: int) -> Optional[Dict[str, Any]]:
        """获取项目的当前项目经理（从 person_project_history 中查询）"""
        person_project_dao = PersonProjectStateDAO(self.db_path)
        
        # 获取项目参与人员（最新状态）
        states = person_project_dao.list_by_project(project_id)
        
        # 查找角色为"项目经理"的最新记录
        manager_states = [
            s for s in states 
            if s.data.get("project_position") == "项目经理"
        ]
        
        if not manager_states:
            return None
        
        # 返回最新的项目经理记录
        latest = max(manager_states, key=lambda s: s.ts)
        
        # 获取人员基本信息
        from app.services.person_service import PersonService
        person_service = PersonService(self.db_path)
        person = person_service.get_person(latest.person_id)
        
        return {
            "person_id": latest.person_id,
            "person_name": person["basic"]["data"].get("name") if person else None,
            "project_position": latest.data.get("project_position"),
            "ts": latest.ts,
        }

    def list_projects(self) -> List[Dict[str, Any]]:
        """列出所有项目（最新状态，使用 DAO 层方法）"""
        # 使用 DAO 层方法获取所有项目的最新基础信息
        basic_states = self.basic_dao.list_all_latest()
        result = []
        for state in basic_states:
            data = state.data
            project_id = state.project_id
            
            # 查询当前项目经理
            manager = self.get_current_project_manager(project_id)
            
            result.append({
                "project_id": project_id,
                "ts": state.ts,
                "data": data,
                "current_manager": manager,  # 添加当前项目经理信息
            })
        return result

    def get_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        """获取项目详情（包含历史）"""
        basic_state = self.basic_dao.get_latest(project_id)
        if not basic_state:
            return None

        basic_history = self.basic_dao.list_states(project_id, limit=100)
        
        # 查询当前项目经理
        manager = self.get_current_project_manager(project_id)

        return {
            "project_id": project_id,
            "basic": {
                "version": basic_state.version,
                "ts": basic_state.ts,
                "data": basic_state.data,
            },
            "basic_history": [
                {
                    "version": h.version,
                    "ts": h.ts,
                    "data": h.data,
                }
                for h in basic_history
            ],
            "current_manager": manager,  # 添加当前项目经理信息
        }

    def append_project_change(self, project_id: int, project_data: dict) -> int:
        """追加项目信息变更"""
        cleaned_data = sanitize_project_payload(project_data)
        return self.basic_dao.append(project_id, cleaned_data)

