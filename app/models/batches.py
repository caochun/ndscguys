from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import sqlite3


@dataclass
class HousingFundBatch:
    id: Optional[int]
    created_at: Optional[str]
    effective_date: str
    min_base_amount: float
    max_base_amount: float
    default_company_rate: float
    default_personal_rate: float
    target_company: Optional[str]
    target_department: Optional[str]
    target_employee_type: Optional[str]
    note: Optional[str]
    status: str
    affected_count: int

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "HousingFundBatch":
        return cls(
            id=row["id"],
            created_at=row["created_at"],
            effective_date=row["effective_date"],
            min_base_amount=row["min_base_amount"],
            max_base_amount=row["max_base_amount"],
            default_company_rate=row["default_company_rate"],
            default_personal_rate=row["default_personal_rate"],
            target_company=row["target_company"],
            target_department=row["target_department"],
            target_employee_type=row["target_employee_type"],
            note=row["note"],
            status=row["status"],
            affected_count=row["affected_count"],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "effective_date": self.effective_date,
            "min_base_amount": self.min_base_amount,
            "max_base_amount": self.max_base_amount,
            "default_company_rate": self.default_company_rate,
            "default_personal_rate": self.default_personal_rate,
            "target_company": self.target_company,
            "target_department": self.target_department,
            "target_employee_type": self.target_employee_type,
            "note": self.note,
            "status": self.status,
            "affected_count": self.affected_count,
        }


@dataclass
class HousingFundBatchItem:
    id: Optional[int]
    batch_id: int
    person_id: int
    created_at: Optional[str]
    current_base_amount: Optional[float]
    current_company_rate: Optional[float]
    current_personal_rate: Optional[float]
    new_base_amount: float
    new_company_rate: float
    new_personal_rate: float
    applied: bool

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "HousingFundBatchItem":
        return cls(
            id=row["id"],
            batch_id=row["batch_id"],
            person_id=row["person_id"],
            created_at=row["created_at"],
            current_base_amount=row["current_base_amount"],
            current_company_rate=row["current_company_rate"],
            current_personal_rate=row["current_personal_rate"],
            new_base_amount=row["new_base_amount"],
            new_company_rate=row["new_company_rate"],
            new_personal_rate=row["new_personal_rate"],
            applied=bool(row["applied"]),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "batch_id": self.batch_id,
            "person_id": self.person_id,
            "created_at": self.created_at,
            "current_base_amount": self.current_base_amount,
            "current_company_rate": self.current_company_rate,
            "current_personal_rate": self.current_personal_rate,
            "new_base_amount": self.new_base_amount,
            "new_company_rate": self.new_company_rate,
            "new_personal_rate": self.new_personal_rate,
            "applied": self.applied,
        }


@dataclass
class PayrollBatch:
    """
    薪酬批量发放批次
    """

    id: Optional[int]
    created_at: Optional[str]
    batch_period: str
    effective_date: Optional[str]
    target_company: Optional[str]
    target_department: Optional[str]
    target_employee_type: Optional[str]
    note: Optional[str]
    status: str
    affected_count: int

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "PayrollBatch":
        return cls(
            id=row["id"],
            created_at=row["created_at"],
            batch_period=row["batch_period"],
            effective_date=row["effective_date"],
            target_company=row["target_company"],
            target_department=row["target_department"],
            target_employee_type=row["target_employee_type"],
            note=row["note"],
            status=row["status"],
            affected_count=row["affected_count"],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "batch_period": self.batch_period,
            "effective_date": self.effective_date,
            "target_company": self.target_company,
            "target_department": self.target_department,
            "target_employee_type": self.target_employee_type,
            "note": self.note,
            "status": self.status,
            "affected_count": self.affected_count,
        }


@dataclass
class PayrollBatchItem:
    """
    薪酬批量发放明细
    """

    id: Optional[int]
    batch_id: int
    person_id: int
    created_at: Optional[str]
    salary_base_amount: Optional[float]
    salary_performance_base: Optional[float]
    performance_factor: Optional[float]
    performance_amount: Optional[float]
    gross_amount_before_deductions: Optional[float]
    attendance_deduction: Optional[float]
    social_personal_amount: Optional[float]
    housing_personal_amount: Optional[float]
    other_deduction: Optional[float]
    net_amount_before_tax: Optional[float]
    applied: bool

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "PayrollBatchItem":
        return cls(
            id=row["id"],
            batch_id=row["batch_id"],
            person_id=row["person_id"],
            created_at=row["created_at"],
            salary_base_amount=row["salary_base_amount"],
            salary_performance_base=row["salary_performance_base"],
            performance_factor=row["performance_factor"],
            performance_amount=row["performance_amount"],
            gross_amount_before_deductions=row["gross_amount_before_deductions"],
            attendance_deduction=row["attendance_deduction"],
            social_personal_amount=row["social_personal_amount"],
            housing_personal_amount=row["housing_personal_amount"],
            other_deduction=row["other_deduction"],
            net_amount_before_tax=row["net_amount_before_tax"],
            applied=bool(row["applied"]),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "batch_id": self.batch_id,
            "person_id": self.person_id,
            "created_at": self.created_at,
            "salary_base_amount": self.salary_base_amount,
            "salary_performance_base": self.salary_performance_base,
            "performance_factor": self.performance_factor,
            "performance_amount": self.performance_amount,
            "gross_amount_before_deductions": self.gross_amount_before_deductions,
            "attendance_deduction": self.attendance_deduction,
            "social_personal_amount": self.social_personal_amount,
            "housing_personal_amount": self.housing_personal_amount,
            "other_deduction": self.other_deduction,
            "net_amount_before_tax": self.net_amount_before_tax,
            "applied": self.applied,
        }


@dataclass
class SocialSecurityBatch:
    id: Optional[int]
    created_at: Optional[str]
    effective_date: str
    min_base_amount: float
    max_base_amount: float
    default_pension_company_rate: Optional[float]
    default_pension_personal_rate: Optional[float]
    default_unemployment_company_rate: Optional[float]
    default_unemployment_personal_rate: Optional[float]
    default_medical_company_rate: Optional[float]
    default_medical_personal_rate: Optional[float]
    default_maternity_company_rate: Optional[float]
    default_maternity_personal_rate: Optional[float]
    default_critical_illness_company_amount: Optional[float]
    default_critical_illness_personal_amount: Optional[float]
    target_company: Optional[str]
    target_department: Optional[str]
    target_employee_type: Optional[str]
    note: Optional[str]
    status: str
    affected_count: int

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "SocialSecurityBatch":
        return cls(
            id=row["id"],
            created_at=row["created_at"],
            effective_date=row["effective_date"],
            min_base_amount=row["min_base_amount"],
            max_base_amount=row["max_base_amount"],
            default_pension_company_rate=row["default_pension_company_rate"],
            default_pension_personal_rate=row["default_pension_personal_rate"],
            default_unemployment_company_rate=row["default_unemployment_company_rate"],
            default_unemployment_personal_rate=row["default_unemployment_personal_rate"],
            default_medical_company_rate=row["default_medical_company_rate"],
            default_medical_personal_rate=row["default_medical_personal_rate"],
            default_maternity_company_rate=row["default_maternity_company_rate"],
            default_maternity_personal_rate=row["default_maternity_personal_rate"],
            default_critical_illness_company_amount=row[
                "default_critical_illness_company_amount"
            ],
            default_critical_illness_personal_amount=row[
                "default_critical_illness_personal_amount"
            ],
            target_company=row["target_company"],
            target_department=row["target_department"],
            target_employee_type=row["target_employee_type"],
            note=row["note"],
            status=row["status"],
            affected_count=row["affected_count"],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "effective_date": self.effective_date,
            "min_base_amount": self.min_base_amount,
            "max_base_amount": self.max_base_amount,
            "default_pension_company_rate": self.default_pension_company_rate,
            "default_pension_personal_rate": self.default_pension_personal_rate,
            "default_unemployment_company_rate": self.default_unemployment_company_rate,
            "default_unemployment_personal_rate": self.default_unemployment_personal_rate,
            "default_medical_company_rate": self.default_medical_company_rate,
            "default_medical_personal_rate": self.default_medical_personal_rate,
            "default_maternity_company_rate": self.default_maternity_company_rate,
            "default_maternity_personal_rate": self.default_maternity_personal_rate,
            "default_critical_illness_company_amount": self.default_critical_illness_company_amount,
            "default_critical_illness_personal_amount": self.default_critical_illness_personal_amount,
            "target_company": self.target_company,
            "target_department": self.target_department,
            "target_employee_type": self.target_employee_type,
            "note": self.note,
            "status": self.status,
            "affected_count": self.affected_count,
        }


@dataclass
class SocialSecurityBatchItem:
    id: Optional[int]
    batch_id: int
    person_id: int
    created_at: Optional[str]
    current_base_amount: Optional[float]
    current_pension_company_rate: Optional[float]
    current_pension_personal_rate: Optional[float]
    current_unemployment_company_rate: Optional[float]
    current_unemployment_personal_rate: Optional[float]
    current_medical_company_rate: Optional[float]
    current_medical_personal_rate: Optional[float]
    current_maternity_company_rate: Optional[float]
    current_maternity_personal_rate: Optional[float]
    current_critical_illness_company_amount: Optional[float]
    current_critical_illness_personal_amount: Optional[float]
    new_base_amount: float
    new_pension_company_rate: Optional[float]
    new_pension_personal_rate: Optional[float]
    new_unemployment_company_rate: Optional[float]
    new_unemployment_personal_rate: Optional[float]
    new_medical_company_rate: Optional[float]
    new_medical_personal_rate: Optional[float]
    new_maternity_company_rate: Optional[float]
    new_maternity_personal_rate: Optional[float]
    new_critical_illness_company_amount: Optional[float]
    new_critical_illness_personal_amount: Optional[float]
    applied: bool

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "SocialSecurityBatchItem":
        return cls(
            id=row["id"],
            batch_id=row["batch_id"],
            person_id=row["person_id"],
            created_at=row["created_at"],
            current_base_amount=row["current_base_amount"],
            current_pension_company_rate=row["current_pension_company_rate"],
            current_pension_personal_rate=row["current_pension_personal_rate"],
            current_unemployment_company_rate=row["current_unemployment_company_rate"],
            current_unemployment_personal_rate=row["current_unemployment_personal_rate"],
            current_medical_company_rate=row["current_medical_company_rate"],
            current_medical_personal_rate=row["current_medical_personal_rate"],
            current_maternity_company_rate=row["current_maternity_company_rate"],
            current_maternity_personal_rate=row["current_maternity_personal_rate"],
            current_critical_illness_company_amount=row[
                "current_critical_illness_company_amount"
            ],
            current_critical_illness_personal_amount=row[
                "current_critical_illness_personal_amount"
            ],
            new_base_amount=row["new_base_amount"],
            new_pension_company_rate=row["new_pension_company_rate"],
            new_pension_personal_rate=row["new_pension_personal_rate"],
            new_unemployment_company_rate=row["new_unemployment_company_rate"],
            new_unemployment_personal_rate=row["new_unemployment_personal_rate"],
            new_medical_company_rate=row["new_medical_company_rate"],
            new_medical_personal_rate=row["new_medical_personal_rate"],
            new_maternity_company_rate=row["new_maternity_company_rate"],
            new_maternity_personal_rate=row["new_maternity_personal_rate"],
            new_critical_illness_company_amount=row["new_critical_illness_company_amount"],
            new_critical_illness_personal_amount=row["new_critical_illness_personal_amount"],
            applied=bool(row["applied"]),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "batch_id": self.batch_id,
            "person_id": self.person_id,
            "created_at": self.created_at,
            "current_base_amount": self.current_base_amount,
            "current_pension_company_rate": self.current_pension_company_rate,
            "current_pension_personal_rate": self.current_pension_personal_rate,
            "current_unemployment_company_rate": self.current_unemployment_company_rate,
            "current_unemployment_personal_rate": self.current_unemployment_personal_rate,
            "current_medical_company_rate": self.current_medical_company_rate,
            "current_medical_personal_rate": self.current_medical_personal_rate,
            "current_maternity_company_rate": self.current_maternity_company_rate,
            "current_maternity_personal_rate": self.current_maternity_personal_rate,
            "current_critical_illness_company_amount": self.current_critical_illness_company_amount,
            "current_critical_illness_personal_amount": self.current_critical_illness_personal_amount,
            "new_base_amount": self.new_base_amount,
            "new_pension_company_rate": self.new_pension_company_rate,
            "new_pension_personal_rate": self.new_pension_personal_rate,
            "new_unemployment_company_rate": self.new_unemployment_company_rate,
            "new_unemployment_personal_rate": self.new_unemployment_personal_rate,
            "new_medical_company_rate": self.new_medical_company_rate,
            "new_medical_personal_rate": self.new_medical_personal_rate,
            "new_maternity_company_rate": self.new_maternity_company_rate,
            "new_maternity_personal_rate": self.new_maternity_personal_rate,
            "new_critical_illness_company_amount": self.new_critical_illness_company_amount,
            "new_critical_illness_personal_amount": self.new_critical_illness_personal_amount,
            "applied": self.applied,
        }


@dataclass
class TaxDeductionBatch:
    """个税专项附加扣除批量调整批次"""

    id: Optional[int]
    created_at: Optional[str]
    effective_date: str
    effective_month: str
    target_company: Optional[str]
    target_department: Optional[str]
    target_employee_type: Optional[str]
    note: Optional[str]
    status: str
    affected_count: int

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "TaxDeductionBatch":
        return cls(
            id=row["id"],
            created_at=row["created_at"],
            effective_date=row["effective_date"],
            effective_month=row["effective_month"],
            target_company=row["target_company"],
            target_department=row["target_department"],
            target_employee_type=row["target_employee_type"],
            note=row["note"],
            status=row["status"],
            affected_count=row["affected_count"],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "effective_date": self.effective_date,
            "effective_month": self.effective_month,
            "target_company": self.target_company,
            "target_department": self.target_department,
            "target_employee_type": self.target_employee_type,
            "note": self.note,
            "status": self.status,
            "affected_count": self.affected_count,
        }


@dataclass
class TaxDeductionBatchItem:
    """个税专项附加扣除批量调整明细"""

    id: Optional[int]
    batch_id: int
    person_id: int
    created_at: Optional[str]
    current_continuing_education: float
    current_infant_care: float
    current_children_education: float
    current_housing_loan_interest: float
    current_housing_rent: float
    current_elderly_support: float
    new_continuing_education: float
    new_infant_care: float
    new_children_education: float
    new_housing_loan_interest: float
    new_housing_rent: float
    new_elderly_support: float
    applied: bool

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "TaxDeductionBatchItem":
        return cls(
            id=row["id"],
            batch_id=row["batch_id"],
            person_id=row["person_id"],
            created_at=row["created_at"],
            current_continuing_education=row["current_continuing_education"] or 0.0,
            current_infant_care=row["current_infant_care"] or 0.0,
            current_children_education=row["current_children_education"] or 0.0,
            current_housing_loan_interest=row["current_housing_loan_interest"] or 0.0,
            current_housing_rent=row["current_housing_rent"] or 0.0,
            current_elderly_support=row["current_elderly_support"] or 0.0,
            new_continuing_education=row["new_continuing_education"] or 0.0,
            new_infant_care=row["new_infant_care"] or 0.0,
            new_children_education=row["new_children_education"] or 0.0,
            new_housing_loan_interest=row["new_housing_loan_interest"] or 0.0,
            new_housing_rent=row["new_housing_rent"] or 0.0,
            new_elderly_support=row["new_elderly_support"] or 0.0,
            applied=bool(row["applied"]),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "batch_id": self.batch_id,
            "person_id": self.person_id,
            "created_at": self.created_at,
            "current_continuing_education": self.current_continuing_education,
            "current_infant_care": self.current_infant_care,
            "current_children_education": self.current_children_education,
            "current_housing_loan_interest": self.current_housing_loan_interest,
            "current_housing_rent": self.current_housing_rent,
            "current_elderly_support": self.current_elderly_support,
            "new_continuing_education": self.new_continuing_education,
            "new_infant_care": self.new_infant_care,
            "new_children_education": self.new_children_education,
            "new_housing_loan_interest": self.new_housing_loan_interest,
            "new_housing_rent": self.new_housing_rent,
            "new_elderly_support": self.new_elderly_support,
            "applied": self.applied,
        }


