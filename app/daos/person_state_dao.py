"""
人员状态流 DAO（具体实现）
"""
from app.daos.entity_state import EntityStateDAO
from app.models.person_states import PersonBasicState, PersonPositionState


class PersonBasicStateDAO(EntityStateDAO):
    table_name = "person_basic_history"
    state_cls = PersonBasicState


class PersonPositionStateDAO(EntityStateDAO):
    table_name = "person_position_history"
    state_cls = PersonPositionState

