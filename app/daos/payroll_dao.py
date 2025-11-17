"""
Payroll DAO
"""
from typing import List
from app.daos.base_dao import BaseDAO


class PayrollDAO(BaseDAO):
    """薪资发放批次 DAO"""

    def create_payroll_record(
        self,
        period: str,
        issue_date: str = None,
        total_gross_amount: float = 0.0,
        total_net_amount: float = 0.0,
        status: str = 'draft',
        note: str = None,
        created_by: str = None
    ) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO payroll_records
            (period, issue_date, total_gross_amount, total_net_amount, status, note, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            period,
            issue_date,
            total_gross_amount,
            total_net_amount,
            status,
            note,
            created_by
        ))

        payroll_id = cursor.lastrowid
        conn.commit()
        return payroll_id

    def create_payroll_item(
        self,
        payroll_id: int,
        employee_id: int,
        basic_salary: float,
        performance_base: float,
        performance_grade: str,
        performance_pay: float,
        adjustment: float,
        gross_pay: float,
        social_security_employee: float,
        social_security_employer: float,
        housing_fund_employee: float,
        housing_fund_employer: float,
        taxable_income: float,
        income_tax: float,
        net_pay: float,
        metadata: str = None
    ) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO payroll_items (
                payroll_id, employee_id, basic_salary, performance_base, performance_grade,
                performance_pay, adjustment, gross_pay,
                social_security_employee, social_security_employer,
                housing_fund_employee, housing_fund_employer,
                taxable_income, income_tax, net_pay, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            payroll_id,
            employee_id,
            basic_salary,
            performance_base,
            performance_grade,
            performance_pay,
            adjustment,
            gross_pay,
            social_security_employee,
            social_security_employer,
            housing_fund_employee,
            housing_fund_employer,
            taxable_income,
            income_tax,
            net_pay,
            metadata
        ))

        item_id = cursor.lastrowid
        conn.commit()
        return item_id

    def get_payroll_records(self) -> List[dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM payroll_records ORDER BY period DESC, id DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

