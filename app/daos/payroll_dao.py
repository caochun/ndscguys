"""
Payroll DAO
"""
from typing import List, Optional
from app.daos.base_dao import BaseDAO
from app.models.payroll_record import PayrollRecord


class PayrollDAO(BaseDAO):
    """薪资发放批次 DAO"""

    def get_by_period(self, period: str) -> Optional[PayrollRecord]:
        """根据 period 查找 PayrollRecord"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM payroll_records WHERE period = ?", (period,))
        row = cursor.fetchone()
        if row:
            return PayrollRecord.from_row(row)
        return None

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

    def update_payroll_record(
        self,
        payroll_id: int,
        issue_date: Optional[str] = None,
        total_gross_amount: float = 0.0,
        total_net_amount: float = 0.0,
        status: Optional[str] = None,
        note: Optional[str] = None
    ) -> bool:
        """更新 PayrollRecord"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 构建更新语句，只更新提供的字段
        updates = []
        params = []
        
        if issue_date is not None:
            updates.append("issue_date = ?")
            params.append(issue_date)
        if total_gross_amount is not None:
            updates.append("total_gross_amount = ?")
            params.append(total_gross_amount)
        if total_net_amount is not None:
            updates.append("total_net_amount = ?")
            params.append(total_net_amount)
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        if note is not None:
            updates.append("note = ?")
            params.append(note)
        
        if not updates:
            return False
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(payroll_id)
        
        cursor.execute(f"""
            UPDATE payroll_records
            SET {', '.join(updates)}
            WHERE id = ?
        """, params)
        
        conn.commit()
        return cursor.rowcount > 0

    def delete_payroll_items(self, payroll_id: int) -> bool:
        """删除指定 payroll_id 的所有 payroll_items"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM payroll_items WHERE payroll_id = ?", (payroll_id,))
        conn.commit()
        return cursor.rowcount >= 0  # 即使没有删除任何记录也返回 True

    def save_or_update_payroll_record(
        self,
        period: str,
        issue_date: Optional[str] = None,
        total_gross_amount: float = 0.0,
        total_net_amount: float = 0.0,
        status: str = 'draft',
        note: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> int:
        """
        根据 period 创建或更新 PayrollRecord
        如果 period 已存在，则更新；否则创建新记录
        
        Returns:
            payroll_id
        """
        existing = self.get_by_period(period)
        
        if existing:
            # 更新现有记录
            self.update_payroll_record(
                payroll_id=existing.id,
                issue_date=issue_date,
                total_gross_amount=total_gross_amount,
                total_net_amount=total_net_amount,
                status=status,
                note=note
            )
            # 删除旧的 payroll_items，后续会重新创建
            self.delete_payroll_items(existing.id)
            return existing.id
        else:
            # 创建新记录
            return self.create_payroll_record(
                period=period,
                issue_date=issue_date,
                total_gross_amount=total_gross_amount,
                total_net_amount=total_net_amount,
                status=status,
                note=note,
                created_by=created_by
            )

    def get_payroll_records(self) -> List[dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM payroll_records ORDER BY period DESC, id DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_payroll_items(self, payroll_id: int) -> List[dict]:
        """获取指定批次的明细项"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                pi.*,
                e.employee_number,
                e.company_name,
                p.name,
                emp.department,
                emp.position,
                emp.employee_type
            FROM payroll_items pi
            LEFT JOIN employees e ON pi.employee_id = e.id
            LEFT JOIN persons p ON e.person_id = p.id
            LEFT JOIN employment emp ON e.id = emp.employee_id
            WHERE pi.payroll_id = ?
            ORDER BY pi.id
        """, (payroll_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_payroll_by_id(self, payroll_id: int) -> Optional[PayrollRecord]:
        """根据ID获取PayrollRecord"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM payroll_records WHERE id = ?", (payroll_id,))
        row = cursor.fetchone()
        if row:
            return PayrollRecord.from_row(row)
        return None
    
    def clear_all(self):
        """清空所有薪资批次数据（谨慎使用，仅用于测试）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM payroll_items")
        cursor.execute("DELETE FROM payroll_records")
        conn.commit()

