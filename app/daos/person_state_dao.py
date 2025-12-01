"""
人员状态流 DAO（具体实现）
"""
from app.daos.entity_state import EntityStateDAO
from app.models.person_states import (
    PersonBasicState,
    PersonPositionState,
    PersonSalaryState,
    PersonSocialSecurityState,
    PersonHousingFundState,
    PersonAssessmentState,
    PersonPayrollState,
)


class PersonBasicStateDAO(EntityStateDAO):
    table_name = "person_basic_history"
    state_cls = PersonBasicState


class PersonPositionStateDAO(EntityStateDAO):
    table_name = "person_position_history"
    state_cls = PersonPositionState


class PersonSalaryStateDAO(EntityStateDAO):
    table_name = "person_salary_history"
    state_cls = PersonSalaryState


class PersonSocialSecurityStateDAO(EntityStateDAO):
    table_name = "person_social_security_history"
    state_cls = PersonSocialSecurityState


class PersonHousingFundStateDAO(EntityStateDAO):
    table_name = "person_housing_fund_history"
    state_cls = PersonHousingFundState


class PersonAssessmentStateDAO(EntityStateDAO):
    table_name = "person_assessment_history"
    state_cls = PersonAssessmentState


class PersonPayrollStateDAO(EntityStateDAO):
    table_name = "person_payroll_history"
    state_cls = PersonPayrollState

