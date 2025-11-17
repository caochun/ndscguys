"""
PayrollRecord 模型
"""
from typing import Optional


class PayrollRecord:
    """薪资发放批次"""

    def __init__(
        self,
        period: str,
        issue_date: Optional[str] = None,
        total_gross_amount: float = 0.0,
        total_net_amount: float = 0.0,
        status: str = 'draft',
        id: Optional[int] = None,
        note: Optional[str] = None,
        created_by: Optional[str] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None
    ):
        self.id = id
        self.period = period
        self.issue_date = issue_date
        self.total_gross_amount = total_gross_amount
        self.total_net_amount = total_net_amount
        self.status = status
        self.note = note
        self.created_by = created_by
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self):
        return {
            'id': self.id,
            'period': self.period,
            'issue_date': self.issue_date,
            'total_gross_amount': self.total_gross_amount,
            'total_net_amount': self.total_net_amount,
            'status': self.status,
            'note': self.note,
            'created_by': self.created_by,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }

    @classmethod
    def from_row(cls, row):
        return cls(
            id=row['id'],
            period=row['period'],
            issue_date=row['issue_date'],
            total_gross_amount=row['total_gross_amount'],
            total_net_amount=row['total_net_amount'],
            status=row['status'],
            note=row['note'],
            created_by=row['created_by'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )


class PayrollItem:
    """发薪批次内的员工明细"""

    def __init__(
        self,
        payroll_id: int,
        employee_id: int,
        basic_salary: float,
        performance_base: float,
        performance_grade: str,
        performance_pay: float,
        adjustment: float = 0.0,
        gross_pay: float = 0.0,
        social_security_employee: float = 0.0,
        social_security_employer: float = 0.0,
        housing_fund_employee: float = 0.0,
        housing_fund_employer: float = 0.0,
        taxable_income: float = 0.0,
        income_tax: float = 0.0,
        net_pay: float = 0.0,
        metadata: Optional[str] = None,
        id: Optional[int] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None
    ):
        self.id = id
        self.payroll_id = payroll_id
        self.employee_id = employee_id
        self.basic_salary = basic_salary
        self.performance_base = performance_base
        self.performance_grade = performance_grade
        self.performance_pay = performance_pay
        self.adjustment = adjustment
        self.gross_pay = gross_pay
        self.social_security_employee = social_security_employee
        self.social_security_employer = social_security_employer
        self.housing_fund_employee = housing_fund_employee
        self.housing_fund_employer = housing_fund_employer
        self.taxable_income = taxable_income
        self.income_tax = income_tax
        self.net_pay = net_pay
        self.metadata = metadata
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self):
        return {
            'id': self.id,
            'payroll_id': self.payroll_id,
            'employee_id': self.employee_id,
            'basic_salary': self.basic_salary,
            'performance_base': self.performance_base,
            'performance_grade': self.performance_grade,
            'performance_pay': self.performance_pay,
            'adjustment': self.adjustment,
            'gross_pay': self.gross_pay,
            'social_security_employee': self.social_security_employee,
            'social_security_employer': self.social_security_employer,
            'housing_fund_employee': self.housing_fund_employee,
            'housing_fund_employer': self.housing_fund_employer,
            'taxable_income': self.taxable_income,
            'income_tax': self.income_tax,
            'net_pay': self.net_pay,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }

    @classmethod
    def from_row(cls, row):
        return cls(
            id=row['id'],
            payroll_id=row['payroll_id'],
            employee_id=row['employee_id'],
            basic_salary=row['basic_salary'],
            performance_base=row['performance_base'],
            performance_grade=row['performance_grade'],
            performance_pay=row['performance_pay'],
            adjustment=row['adjustment'],
            gross_pay=row['gross_pay'],
            social_security_employee=row['social_security_employee'],
            social_security_employer=row['social_security_employer'],
            housing_fund_employee=row['housing_fund_employee'],
            housing_fund_employer=row['housing_fund_employer'],
            taxable_income=row['taxable_income'],
            income_tax=row['income_tax'],
            net_pay=row['net_pay'],
            metadata=row['metadata'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )

