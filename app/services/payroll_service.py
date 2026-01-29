"""
Payroll Service - 工资计算与发放服务
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.services.twin_service import TwinService


@dataclass
class PayrollContext:
    """工资计算上下文（方便调试和前端展示明细）"""
    employment: Optional[Dict[str, Any]]
    assessment: Optional[Dict[str, Any]]
    social_base: Optional[Dict[str, Any]]
    housing_base: Optional[Dict[str, Any]]
    tax_deductions: List[Dict[str, Any]]


class PayrollService:
    """
    工资计算服务
    
    负责从各类 Twin 获取数据，按规则计算一个工资单的所有字段，并可选择写入 person_company_payroll Twin。
    """

    def __init__(self, db_path: Optional[str] = None):
        self.twin_service = TwinService(db_path=db_path)
        # 直接复用 TwinService 持有的 DAO 实例
        self.twin_dao = self.twin_service.twin_dao
        self.state_dao = self.twin_service.state_dao
        self.schema_loader = self.twin_service.schema_loader

    # ======== 对外接口 ========

    def calculate_payroll(
        self,
        person_id: int,
        company_id: int,
        period: str,
    ) -> Dict[str, Any]:
        """
        计算指定人员在指定周期的工资（仅计算，不写库）
        """
        # 获取上下文数据
        ctx = self._build_context(person_id, company_id, period)

        # 1. 基本薪资
        employment = ctx.employment or {}
        base_salary = float(employment.get("salary") or 0.0)
        salary_type = employment.get("salary_type") or "月薪"

        # 2. 最近一次考核
        assessment_grade = ctx.assessment.get("grade") if ctx.assessment else None

        # 3. 各类基数与扣除
        social_security_base = float(
            (ctx.social_base or {}).get("base_amount") or 0.0
        )
        housing_fund_base = float(
            (ctx.housing_base or {}).get("base_amount") or 0.0
        )
        # 专项附加扣除：每人可有多个生效中记录，每月项（元/月）求和，大病医疗为年度/12
        _monthly_deduction_keys = (
            "children_education_amount",
            "continuing_education_amount",
            "housing_loan_interest_amount",
            "housing_rent_amount",
            "elderly_support_amount",
            "infant_childcare_amount",
        )
        tax_deduction_total = 0.0
        for d in ctx.tax_deductions:
            tax_deduction_total += sum(
                float(d.get(k) or 0.0) for k in _monthly_deduction_keys
            )
            # 大病医疗为年度扣除，按月均摊（简化：/12）
            tax_deduction_total += float(d.get("medical_expense_amount") or 0.0) / 12.0

        # 4. 绩效奖金
        performance_bonus = self._calculate_performance_bonus(
            base_salary, assessment_grade
        )

        # 5. 应发金额
        base_amount = base_salary + performance_bonus

        # 6. 各项扣除（这里只用简单比例，真实项目可以改为规则/配置驱动）
        social_security_deduction = social_security_base * 0.105  # 个人约 10.5%
        housing_fund_deduction = housing_fund_base * 0.12        # 个人 12%

        # 7. 应纳税所得额
        tax_threshold = 5000.0
        taxable_income = max(
            0.0,
            base_amount
            - social_security_deduction
            - housing_fund_deduction
            - tax_deduction_total
            - tax_threshold,
        )

        # 8. 个税
        tax_deduction = self._calculate_tax(taxable_income)

        # 9. 实发金额
        total_amount = (
            base_amount
            - social_security_deduction
            - housing_fund_deduction
            - tax_deduction
        )

        return {
            "person_id": person_id,
            "company_id": company_id,
            "period": period,
            "base_salary": round(base_salary, 2),
            "salary_type": salary_type,
            "assessment_grade": assessment_grade,
            "social_security_base": round(social_security_base, 2),
            "housing_fund_base": round(housing_fund_base, 2),
            "tax_deduction_total": round(tax_deduction_total, 2),
            "base_amount": round(base_amount, 2),
            "performance_bonus": round(performance_bonus, 2),
            "social_security_deduction": round(social_security_deduction, 2),
            "housing_fund_deduction": round(housing_fund_deduction, 2),
            "taxable_income": round(taxable_income, 2),
            "tax_deduction": round(tax_deduction, 2),
            "total_amount": round(total_amount, 2),
            "status": "待发放",
        }

    def generate_payroll(
        self,
        person_id: int,
        company_id: int,
        period: str,
    ) -> Dict[str, Any]:
        """
        计算并生成工资单 Twin（person_company_payroll）
        
        返回创建后的 Twin 详情（包含 current/history）。
        """
        # 先计算
        data = self.calculate_payroll(person_id, company_id, period)

        # 创建 Activity Twin 注册记录
        payroll_id = self.twin_dao.create_activity_twin(
            "person_company_payroll",
            {
                "person_id": person_id,
                "company_id": company_id,
            },
        )

        # 从状态数据中移除外键（根据 TwinService 的约定）
        state_data = data.copy()
        state_data.pop("person_id", None)
        state_data.pop("company_id", None)

        # 追加状态（time_series，需要 time_key=period）
        self.state_dao.append(
            "person_company_payroll",
            payroll_id,
            state_data,
            time_key=period,
        )

        # 返回完整 Twin 信息
        return self.twin_service.get_twin("person_company_payroll", payroll_id)

    # ======== 内部辅助方法 ========

    def _build_context(
        self, person_id: int, company_id: int, period: str
    ) -> PayrollContext:
        """聚合工资计算所需的上下文信息"""
        employment = self._get_latest_employment(person_id, company_id)
        assessment = self._get_latest_assessment(person_id)
        social_base = self._get_latest_social_base(person_id, company_id)
        housing_base = self._get_latest_housing_base(person_id, company_id)
        tax_deductions = self._get_active_tax_deductions(person_id, period)

        return PayrollContext(
            employment=employment,
            assessment=assessment,
            social_base=social_base,
            housing_base=housing_base,
            tax_deductions=tax_deductions,
        )

    def _get_latest_employment(
        self, person_id: int, company_id: int
    ) -> Optional[Dict[str, Any]]:
        """获取最近一次聘用状态（按 change_date 排序）"""
        twins = self.twin_service.list_twins(
            "person_company_employment",
            filters={
                "person_id": str(person_id),
                "company_id": str(company_id),
            },
        )
        if not twins:
            return None
        # change_date 降序
        return sorted(
            twins,
            key=lambda x: x.get("change_date") or "",
            reverse=True,
        )[0]

    def _get_latest_assessment(self, person_id: int) -> Optional[Dict[str, Any]]:
        """获取最近一次考核"""
        twins = self.twin_service.list_twins(
            "person_assessment",
            filters={"person_id": str(person_id)},
        )
        if not twins:
            return None
        # assessment_date 降序
        return sorted(
            twins,
            key=lambda x: x.get("assessment_date") or "",
            reverse=True,
        )[0]

    def _get_latest_social_base(
        self, person_id: int, company_id: int
    ) -> Optional[Dict[str, Any]]:
        """获取最近一次社保基数"""
        twins = self.twin_service.list_twins(
            "person_company_social_security_base",
            filters={
                "person_id": str(person_id),
                "company_id": str(company_id),
            },
            enrich="person,company",
        )
        if not twins:
            return None
        return sorted(
            twins,
            key=lambda x: x.get("effective_date") or "",
            reverse=True,
        )[0]

    def _get_latest_housing_base(
        self, person_id: int, company_id: int
    ) -> Optional[Dict[str, Any]]:
        """获取最近一次公积金基数"""
        twins = self.twin_service.list_twins(
            "person_company_housing_fund_base",
            filters={
                "person_id": str(person_id),
                "company_id": str(company_id),
            },
            enrich="person,company",
        )
        if not twins:
            return None
        return sorted(
            twins,
            key=lambda x: x.get("effective_date") or "",
            reverse=True,
        )[0]

    def _get_active_tax_deductions(
        self, person_id: int, period: str
    ) -> List[Dict[str, Any]]:
        """
        获取在指定发放周期内“生效中”的专项附加扣除
        
        简化处理：只看 effective_date <= 本月最后一天，且
        - expiry_date 为空，或
        - expiry_date >= 本月第一天
        """
        twins = self.twin_service.list_twins(
            "person_tax_deduction",
            filters={"person_id": str(person_id), "status": "生效中"},
        )
        if not twins:
            return []

        # 计算本月起止日期
        period_start = datetime.strptime(period + "-01", "%Y-%m-%d").date()
        if period_start.month == 12:
            next_month = datetime(period_start.year + 1, 1, 1).date()
        else:
            next_month = datetime(period_start.year, period_start.month + 1, 1).date()
        period_end = next_month.replace(day=1)

        def parse_date(value: Optional[str]) -> Optional[datetime.date]:
            if not value:
                return None
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                return None

        active: List[Dict[str, Any]] = []
        for d in twins:
            eff = parse_date(d.get("effective_date"))
            exp = parse_date(d.get("expiry_date"))
            if not eff:
                continue
            # 生效日期不晚于本月末
            if eff > period_end:
                continue
            # 失效日期为空或不早于本月初
            if exp and exp < period_start:
                continue
            active.append(d)
        return active

    # ======== 计算公式 ========

    def _calculate_performance_bonus(
        self, base_salary: float, grade: Optional[str]
    ) -> float:
        """根据考核等级计算绩效奖金（Demo 版，可替换为配置驱动）"""
        if base_salary <= 0 or not grade:
            return 0.0
        # 兼容旧数据（优秀/良好/合格/不合格）和新数据（A/B/C/D/E）
        bonus_rates = {
            # 新等级（推荐）：A-E
            "A": 0.3,
            "B": 0.2,
            "C": 0.1,
            "D": 0.0,
            "E": -0.1,
            # 旧等级（向后兼容）
            "优秀": 0.3,
            "良好": 0.2,
            "合格": 0.1,
            "不合格": -0.1,
        }
        rate = bonus_rates.get(str(grade), 0.0)
        return base_salary * rate

    def _calculate_tax(self, taxable_income: float) -> float:
        """
        计算个人所得税（简化版累进税率，只用于 Demo）
        
        实际项目中应该从税率表/配置加载规则。
        """
        if taxable_income <= 0:
            return 0.0
        # 按现行工资薪金所得税率表的简化实现
        if taxable_income <= 3000:
            return taxable_income * 0.03
        if taxable_income <= 12000:
            return taxable_income * 0.10 - 210
        if taxable_income <= 25000:
            return taxable_income * 0.20 - 1410
        if taxable_income <= 35000:
            return taxable_income * 0.25 - 2660
        if taxable_income <= 55000:
            return taxable_income * 0.30 - 4410
        if taxable_income <= 80000:
            return taxable_income * 0.35 - 7160
        return taxable_income * 0.45 - 15160

