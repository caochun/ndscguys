"""
人员状态流包
"""
from .basic import PersonBasicState
from .position import PersonPositionState
from .salary import PersonSalaryState
from .social_security import PersonSocialSecurityState
from .housing_fund import PersonHousingFundState
from .assessment import PersonAssessmentState
from .payroll import PersonPayrollState
from .tax_deduction import PersonTaxDeductionState
from .state import PersonState

__all__ = [
    'PersonBasicState',
    'PersonPositionState',
    'PersonSalaryState',
    'PersonSocialSecurityState',
    'PersonHousingFundState',
    'PersonAssessmentState',
    'PersonPayrollState',
    'PersonTaxDeductionState',
    'PersonState',
]

