"""
薪资批次管理服务
"""
from typing import List, Optional
from app.daos import PayrollDAO


class PayrollService:
    """薪资批次管理服务类"""
    
    def __init__(self):
        self.payroll_dao = PayrollDAO()
    
    def get_payroll_records(self) -> List[dict]:
        """获取所有薪资批次列表"""
        return self.payroll_dao.get_payroll_records()
    
    def get_payroll_detail(self, payroll_id: int) -> dict:
        """获取批次详情（包含批次信息和明细项）"""
        payroll = self.payroll_dao.get_payroll_by_id(payroll_id)
        if not payroll:
            raise ValueError(f"批次ID {payroll_id} 不存在")
        
        items = self.payroll_dao.get_payroll_items(payroll_id)
        
        return {
            'payroll': payroll.to_dict(),
            'items': items
        }
    
    def create_payroll_record(
        self,
        period: str,
        data: List[dict],
        issue_date: Optional[str] = None,
        note: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> int:
        """
        根据前端计算的薪资数据创建或更新发薪批次
        如果 period 已存在，则更新；否则创建新记录
        """
        if not period:
            raise ValueError("发薪期不能为空")
        if not data:
            raise ValueError("薪资明细不能为空")
        
        total_gross = sum(item.get('gross_pay', 0.0) for item in data)
        payroll_id = self.payroll_dao.save_or_update_payroll_record(
            period=period,
            issue_date=issue_date,
            total_gross_amount=total_gross,
            total_net_amount=total_gross,
            status='draft',
            note=note,
            created_by=created_by
        )
        
        for item in data:
            self.payroll_dao.create_payroll_item(
                payroll_id=payroll_id,
                employee_id=item['employee_id'],
                basic_salary=float(item.get('basic_salary', 0.0)),
                performance_base=float(item.get('performance_base', 0.0)),
                performance_grade=item['grade'],
                performance_pay=float(item.get('performance_pay', 0.0)),
                adjustment=float(item.get('adjustment', 0.0)),
                gross_pay=float(item.get('total_pay', 0.0)),
                social_security_employee=0.0,
                social_security_employer=0.0,
                housing_fund_employee=0.0,
                housing_fund_employer=0.0,
                taxable_income=float(item.get('total_pay', 0.0)),
                income_tax=0.0,
                net_pay=float(item.get('total_pay', 0.0))
            )
        
        return payroll_id

