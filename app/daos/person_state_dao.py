"""
人员状态流 DAO（具体实现）
"""
from typing import List

from app.daos.entity_state import EntityStateDAO
from app.models.person_states import (
    PersonBasicState,
    PersonPositionState,
    PersonSalaryState,
    PersonSocialSecurityState,
    PersonHousingFundState,
    PersonAssessmentState,
    PersonPayrollState,
    PersonTaxDeductionState,
)


class PersonBasicStateDAO(EntityStateDAO):
    table_name = "person_basic_history"
    state_cls = PersonBasicState

    def list_all_latest(self) -> List[PersonBasicState]:
        """获取所有人员的最新基础信息状态"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT pb.person_id, pb.version, pb.ts, pb.data
            FROM person_basic_history pb
            JOIN (
                SELECT person_id, MAX(version) AS max_version
                FROM person_basic_history
                GROUP BY person_id
            ) latest
            ON pb.person_id = latest.person_id AND pb.version = latest.max_version
            ORDER BY pb.ts DESC
            """
        )
        rows = cursor.fetchall()
        return [self.state_cls.from_row(row) for row in rows]


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


class PersonTaxDeductionStateDAO(EntityStateDAO):
    table_name = "person_tax_deduction_history"
    state_cls = PersonTaxDeductionState

