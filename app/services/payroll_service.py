"""
Payroll Service - 工资计算与发放服务
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.services.twin_service import TwinService


# 月计薪天数（考勤扣减公式用）
MONTHLY_WORK_DAYS = 21.75


@dataclass
class PayrollContext:
    """工资计算上下文（方便调试和前端展示明细）"""
    employment: Optional[Dict[str, Any]]
    assessment: Optional[Dict[str, Any]]
    social_base: Optional[Dict[str, Any]]
    housing_base: Optional[Dict[str, Any]]
    tax_deductions: List[Dict[str, Any]]
    attendance_record: Optional[Dict[str, Any]] = None


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
        计算指定人员在指定周期的工资（仅计算，不写库）。
        应发 6 步：岗位划分 → 员工类别折算 → 绩效系数 → 考勤扣减 → 奖惩 → 应发；
        社保公积金 4 步：三险个人 + 公积金个人 + 大病个人 → 合计。
        """
        ctx = self._build_context(person_id, company_id, period)
        employment = ctx.employment or {}
        assessment = ctx.assessment or {}
        attendance = ctx.attendance_record or {}

        salary_type = employment.get("salary_type") or "月薪"
        assessment_grade = assessment.get("grade")

        # 聘用薪资（月薪等价），用于岗位划分与考勤公式
        employment_salary = self._employment_salary_monthly(employment)

        # ----- 应发计算 6 步 -----
        # 第 1 步：按岗位类别划分基础/绩效
        position_category = employment.get("position_category")
        ratio = self._get_position_salary_ratio(position_category)
        base_ratio = float(ratio.get("base_ratio", 0.7)) if ratio else 0.7
        perf_ratio = float(ratio.get("performance_ratio", 0.3)) if ratio else 0.3
        base_salary_part = employment_salary * base_ratio
        performance_salary_part = employment_salary * perf_ratio

        # 第 2 步：按员工类别折算
        employee_type = employment.get("employee_type")
        discount = self._get_employee_type_discount(employee_type)
        discounted_base_salary = base_salary_part * discount
        discounted_performance_salary = performance_salary_part * discount

        # 第 3 步：考核等级绩效系数
        performance_coefficient = self._get_assessment_grade_coefficient(
            assessment_grade
        )
        actual_performance_salary = discounted_performance_salary * performance_coefficient

        # 第 4 步：考勤扣减（事假 100%、病假 30%）
        personal_leave_days = float(attendance.get("personal_leave_days") or 0)
        sick_leave_days = float(attendance.get("sick_leave_days") or 0)
        personal_leave_deduction = (
            employment_salary / MONTHLY_WORK_DAYS * personal_leave_days
        )
        sick_leave_deduction = (
            employment_salary / MONTHLY_WORK_DAYS * 0.3 * sick_leave_days
        )
        attendance_deduction = personal_leave_deduction + sick_leave_deduction

        # 第 5 步：奖惩金额
        reward_punishment_amount = float(
            attendance.get("reward_punishment_amount") or 0
        )

        # 第 6 步：应发
        base_amount = (
            discounted_base_salary
            + actual_performance_salary
            - attendance_deduction
            + reward_punishment_amount
        )
        base_amount = max(0.0, base_amount)

        # ----- 社保公积金扣除 4 步 -----
        social_security_base = float(
            (ctx.social_base or {}).get("base_amount") or 0.0
        )
        housing_fund_base = float(
            (ctx.housing_base or {}).get("base_amount") or 0.0
        )
        config = self._get_social_security_config(period)
        if config:
            pension = float(config.get("pension_employee_rate") or 0)
            unemployment = float(config.get("unemployment_employee_rate") or 0)
            medical = float(config.get("medical_employee_rate") or 0)
            housing_rate = float(config.get("housing_fund_employee_rate") or 0)
            serious_illness_amount = float(
                config.get("serious_illness_employee_amount") or 0
            )
            social_insurance_deduction = social_security_base * (
                pension + unemployment + medical
            )
            housing_fund_deduction = housing_fund_base * housing_rate
            social_housing_total_deduction = (
                social_insurance_deduction
                + housing_fund_deduction
                + serious_illness_amount
            )
        else:
            social_insurance_deduction = social_security_base * 0.105
            housing_fund_deduction = housing_fund_base * 0.12
            serious_illness_amount = 0.0
            social_housing_total_deduction = (
                social_insurance_deduction + housing_fund_deduction
            )

        # 专项附加扣除
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
            tax_deduction_total += float(d.get("medical_expense_amount") or 0.0) / 12.0

        # 应纳税所得额与个税
        tax_threshold = 5000.0
        taxable_income = max(
            0.0,
            base_amount
            - social_housing_total_deduction
            - tax_deduction_total
            - tax_threshold,
        )
        tax_deduction = self._calculate_tax(taxable_income)

        # 实发
        total_amount = max(
            0.0,
            base_amount - social_housing_total_deduction - tax_deduction,
        )

        def r2(x: float) -> float:
            return round(float(x), 2)

        return {
            "person_id": person_id,
            "company_id": company_id,
            "period": period,
            "salary_type": salary_type,
            "assessment_grade": assessment_grade,
            "social_security_base": r2(social_security_base),
            "housing_fund_base": r2(housing_fund_base),
            "tax_deduction_total": r2(tax_deduction_total),
            # 应发中间结果
            "employment_salary": r2(employment_salary),
            "base_salary_part": r2(base_salary_part),
            "performance_salary_part": r2(performance_salary_part),
            "discounted_base_salary": r2(discounted_base_salary),
            "discounted_performance_salary": r2(discounted_performance_salary),
            "performance_coefficient": r2(performance_coefficient),
            "actual_performance_salary": r2(actual_performance_salary),
            "personal_leave_deduction": r2(personal_leave_deduction),
            "sick_leave_deduction": r2(sick_leave_deduction),
            "attendance_deduction": r2(attendance_deduction),
            "reward_punishment_amount": r2(reward_punishment_amount),
            "base_amount": r2(base_amount),
            # 社保公积金中间结果
            "social_insurance_deduction": r2(social_insurance_deduction),
            "housing_fund_deduction": r2(housing_fund_deduction),
            "serious_illness_amount": r2(serious_illness_amount),
            "social_housing_total_deduction": r2(social_housing_total_deduction),
            # 兼容旧字段
            "base_salary": r2(discounted_base_salary),
            "performance_bonus": r2(actual_performance_salary),
            "social_security_deduction": r2(social_insurance_deduction + serious_illness_amount),
            #
            "taxable_income": r2(taxable_income),
            "tax_deduction": r2(tax_deduction),
            "total_amount": r2(total_amount),
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
        attendance_record = self._get_attendance_record(person_id, company_id, period)

        return PayrollContext(
            employment=employment,
            assessment=assessment,
            social_base=social_base,
            housing_base=housing_base,
            tax_deductions=tax_deductions,
            attendance_record=attendance_record,
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

    def _get_attendance_record(
        self, person_id: int, company_id: int, period: str
    ) -> Optional[Dict[str, Any]]:
        """获取指定人员、公司、周期的考勤记录（time_series，time_key=period）"""
        twins = self.twin_service.list_twins(
            "person_company_attendance_record",
            filters={"person_id": str(person_id), "company_id": str(company_id)},
        )
        if not twins:
            return None
        twin_id = twins[0].get("id")
        if twin_id is None:
            return None
        state = self.state_dao.get_state_by_time_key(
            "person_company_attendance_record", twin_id, period
        )
        if not state:
            return None
        return state.data

    def _get_position_salary_ratio(
        self, position_category: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """按岗位类别查基础/绩效划分比例"""
        if not position_category:
            return None
        states = self.state_dao.query_latest_states(
            "position_salary_ratio",
            filters={"position_category": position_category},
        )
        if not states:
            return None
        return states[0].data

    def _get_employee_type_discount(self, employee_type: Optional[str]) -> float:
        """按员工类别查折算系数，默认 1.0"""
        if not employee_type:
            return 1.0
        states = self.state_dao.query_latest_states(
            "employee_type_discount",
            filters={"employee_type": employee_type},
        )
        if not states:
            return 1.0
        return float(states[0].data.get("discount_ratio") or 1.0)

    def _get_assessment_grade_coefficient(self, grade: Optional[str]) -> float:
        """按考核等级查绩效系数，默认 1.0"""
        if not grade:
            return 1.0
        states = self.state_dao.query_latest_states(
            "assessment_grade_coefficient",
            filters={"grade": grade},
        )
        if not states:
            return 1.0
        return float(states[0].data.get("coefficient") or 1.0)

    def _get_social_security_config(
        self, period: str
    ) -> Optional[Dict[str, Any]]:
        """获取发放周期适用的社保公积金配置（取生效日期不晚于周期末的最新一条）"""
        twins = self.twin_service.list_twins("social_security_config")
        if not twins:
            return None
        period_end = period + "-01"
        try:
            period_date = datetime.strptime(period_end, "%Y-%m-%d").date()
            if period_date.month == 12:
                next_month = datetime(period_date.year + 1, 1, 1).date()
            else:
                next_month = datetime(
                    period_date.year, period_date.month + 1, 1
                ).date()
            period_end_str = next_month.strftime("%Y-%m-%d")
        except ValueError:
            period_end_str = period_end
        # 只保留 effective_date <= period 末的配置，取 effective_date 最新
        valid = [
            t
            for t in twins
            if (t.get("effective_date") or "") <= period_end_str
        ]
        if not valid:
            return None
        return sorted(
            valid,
            key=lambda x: x.get("effective_date") or "",
            reverse=True,
        )[0]

    def _employment_salary_monthly(self, employment: Dict[str, Any]) -> float:
        """将聘用薪资转为月薪（元/月），用于应发与考勤扣减公式"""
        salary = float(employment.get("salary") or 0.0)
        salary_type = employment.get("salary_type") or "月薪"
        if salary_type == "月薪":
            return salary
        if salary_type == "年薪":
            return salary / 12.0
        if salary_type == "日薪":
            return salary * MONTHLY_WORK_DAYS
        return salary

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

