"""
Payroll Service - 工资计算与发放服务
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from app.services.twin_service import TwinService


# 月计薪天数（考勤扣减公式用）
MONTHLY_WORK_DAYS = 21.75


def _prev_period(period: str) -> str:
    """上一期 YYYY-MM，如 2024-01 -> 2023-12"""
    try:
        y, m = map(int, period.split("-"))
        m -= 1
        if m < 1:
            m += 12
            y -= 1
        return f"{y:04d}-{m:02d}"
    except (ValueError, AttributeError):
        return ""


@dataclass
class PayrollContext:
    """工资计算上下文（方便调试和前端展示明细）"""
    employment: Optional[Dict[str, Any]]
    assessment: Optional[Dict[str, Any]]
    social_base: Optional[Dict[str, Any]]
    housing_base: Optional[Dict[str, Any]]
    tax_deduction: Optional[Dict[str, Any]]  # 当前人员在 period 内生效的那一条专项附加扣除记录（每人每期一条）
    attendance_record: Optional[Dict[str, Any]] = None
    prev_payroll: Optional[Dict[str, Any]] = None  # 上一期 person_company_payroll 状态（用于个税累计）


class PayrollService:
    """
    工资计算服务
    
    负责从各类 Twin 获取数据，按规则计算一个工资单的所有字段，并可选择写入 person_company_payroll Twin。
    """

    def __init__(self, db_path: Optional[str] = None):
        self.twin_service = TwinService(db_path=db_path)
        self.state_dao = self.twin_service.state_dao

    # ======== 内部辅助方法 ========

    def _get_twin_state_for_person_company(
        self, twin_name: str, person_id: int, company_id: int, time_key: str
    ) -> Optional[Dict[str, Any]]:
        """按 person_id+company_id 取 time_series twin 的某条状态，返回 state.data。"""
        twins = self.twin_service.list_twins(
            twin_name,
            filters={"person_id": str(person_id), "company_id": str(company_id)},
        )
        if not twins:
            return None
        twin_id = twins[0].get("id")
        if twin_id is None:
            return None
        state = self.state_dao.get_state_by_time_key(twin_name, twin_id, time_key)
        return state.data if state and state.data else None

    def _get_prev_payroll_state(
        self, person_id: int, company_id: int, period: str
    ) -> Optional[Dict[str, Any]]:
        """获取此人上一期的 person_company_payroll 状态（用于个税 tax_4/tax_7/tax_13）。"""
        prev = _prev_period(period)
        if not prev:
            return None
        return self._get_twin_state_for_person_company(
            "person_company_payroll", person_id, company_id, prev
        )

    def _build_context(
        self, person_id: int, company_id: int, period: str
    ) -> PayrollContext:
        """聚合工资计算所需的上下文信息（含上一期 payroll，供个税累计用）"""
        employment = self._get_latest_employment(person_id, company_id)
        assessment = self._get_latest_assessment(person_id)
        social_base = self._get_latest_social_base(person_id, company_id)
        housing_base = self._get_latest_housing_base(person_id, company_id)
        tax_deduction = self._get_active_tax_deduction(person_id, period)
        attendance_record = self._get_attendance_record(person_id, company_id, period)
        prev_payroll = self._get_prev_payroll_state(person_id, company_id, period)

        return PayrollContext(
            employment=employment,
            assessment=assessment,
            social_base=social_base,
            housing_base=housing_base,
            tax_deduction=tax_deduction,
            attendance_record=attendance_record,
            prev_payroll=prev_payroll,
        )

    @staticmethod
    def _get_context_data(ctx: PayrollContext, from_key: str) -> Dict[str, Any]:
        """从 PayrollContext 按 key 取数据块，无则返回空 dict。"""
        data = getattr(ctx, from_key, None) if hasattr(ctx, from_key) else None
        return data if isinstance(data, dict) else ({} if data is None else {})

    def _resolve_variable_from_spec(
        self,
        variable_key: str,
        spec: Dict[str, Any],
        ctx: PayrollContext,
        period: str,
    ) -> Optional[float]:
        """按 variable_sources 中的一条配置解析单个变量值；无法解析时返回 None。"""
        source = spec.get("source")
        if source == "constant":
            return float(spec.get("value", 0))
        if source == "field":
            data = self._get_context_data(ctx, spec.get("from") or "")
            default = float(spec.get("default", 0))
            raw = float(data.get(spec.get("field"), default))
            divisor = spec.get("divisor")
            if divisor is not None:
                return default if not divisor else round(raw / float(divisor), 2)
            return raw
        if source == "transform":
            data = self._get_context_data(ctx, spec.get("from") or "")
            if spec.get("transform") == "salary_to_monthly":
                return round(float(self._employment_salary_monthly(data)), 2)
            return 0.0
        if source == "lookup":
            data = self._get_context_data(ctx, spec.get("from") or "")
            field_val = data.get(spec.get("field"))
            lookup_name = spec.get("lookup")
            default = float(spec.get("default", 0))
            if lookup_name == "position_salary_ratio":
                ratio = self._get_position_salary_ratio(field_val)
                return float(ratio.get(spec.get("output"), default)) if ratio else default
            if lookup_name == "employee_type_discount":
                return float(self._get_employee_type_discount(field_val))
            if lookup_name == "assessment_grade_coefficient":
                return float(self._get_assessment_grade_coefficient(field_val))
            return default
        if source == "config":
            default = float(spec.get("default", 0))
            if spec.get("config") == "social_security_config":
                cfg = self._get_social_security_config(period)
                return float(cfg.get(spec.get("field"), default)) if cfg else default
            return default
        return None

    def get_calculation_context_variables(
        self, person_id: int, company_id: int, period: str
    ) -> Dict[str, Any]:
        """
        为工资计算步骤公式求值提供「原始变量」字典。
        完全按 config 中 variable_sources 解析。
        """
        ctx = self._build_context(person_id, company_id, period)
        config = self.load_calculation_config()
        variable_sources = config.get("variable_sources") or {}
        out: Dict[str, Any] = {}
        for variable_key, spec in variable_sources.items():
            if not isinstance(spec, dict):
                continue
            val = self._resolve_variable_from_spec(variable_key, spec, ctx, period)
            if val is not None:
                out[variable_key] = round(val, 2) if isinstance(val, (int, float)) else val
        return out

    # ======== 基于 config JSON 的工资计算步骤（公式仅来自 config） ========

    _CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "payroll_calculation_config.json"

    def load_calculation_config(self) -> Dict[str, Any]:
        """加载工资计算步骤配置（应发/社保公积金/个税三块步骤定义与公式）。"""
        path = self._CONFIG_PATH
        if not path.exists():
            return {"sections": {"gross": {"label": "应发薪资计算", "steps": []}, "social": {"label": "社保公积金扣除计算", "steps": []}, "tax": {"label": "个税计算", "step_order": [], "steps": []}}}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _build_steps_from_config(self, definitions: list) -> list:
        """根据 config 步骤定义生成 steps 列表（含 step, field_name, source, formula=default_formula, desc）。"""
        result = []
        for s in definitions:
            step_num = s.get("step", len(result) + 1)
            formula = (s.get("default_formula") or "").strip()
            item = {"step": step_num, "field_name": s["field_name"], "source": s["source"], "formula": formula}
            if "desc" in s:
                item["desc"] = s["desc"]
            if "output_key" in s:
                item["output_key"] = s["output_key"]
            if "variable_key" in s:
                item["variable_key"] = s["variable_key"]
            result.append(item)
        return result

    def _enrich_step_descs(
        self,
        steps: list,
        steps_config: list,
        variable_labels: Dict[str, str],
        variables: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        在每一步的 desc 后追加两行：公式字面解读（变量→中文）、公式代入值（变量→数值）。
        原地修改 steps 中的 desc。
        """
        from app.payroll_formula import formula_to_readable, formula_with_values
        def_by_step = {s["step"]: s for s in steps_config}
        for item in steps:
            step_num = item.get("step")
            defn = def_by_step.get(step_num)
            formula = (defn.get("default_formula") or item.get("formula") or "").strip()
            base_desc = item.get("desc") or ""
            if not formula:
                continue
            readable = formula_to_readable(formula, variable_labels)
            if readable:
                base_desc = base_desc + "\n" + readable
            if variables is not None:
                with_vals = formula_with_values(formula, variables)
                if with_vals:
                    base_desc = base_desc + "\n" + with_vals
            item["desc"] = base_desc

    def get_calculation_steps_for_display(self) -> Dict[str, list]:
        """获取三块步骤定义（公式仅来自 config），供前端展示。{ gross: [...], social: [...], tax: [...] }"""
        config = self.load_calculation_config()
        sections = config.get("sections") or {}
        variable_labels = config.get("variable_labels") or {}
        out = {}
        for section_id in ("gross", "social", "tax"):
            sec = sections.get(section_id) or {}
            steps_def = sec.get("steps") or []
            steps = self._build_steps_from_config(steps_def)
            self._enrich_step_descs(steps, steps_def, variable_labels, variables=None)
            out[section_id] = steps
        return out

    def _evaluate_section_from_config(
        self,
        variables: Dict[str, Any],
        steps_config: list,
        step_order: Optional[List[int]] = None,
    ) -> tuple:
        """
        按 config 求值一个 section（gross/social/tax 共用同一逻辑）。
        按 step_order 顺序处理每步，source 仅：variable / formula（公式可调用 cumulative_tax 等）。
        返回 (values, variables)，values 的 key 为 str(step_num)。
        """
        from app.payroll_formula import eval_step_expression

        order = step_order or [s["step"] for s in steps_config]
        step_def_by_num = {s["step"]: s for s in steps_config}
        values: Dict[str, float] = {}

        for k in order:
            s = step_def_by_num.get(k)
            if not s:
                continue
            step_num = s["step"]
            source = s.get("source", "formula")
            output_key = s.get("output_key")
            formula = (s.get("default_formula") or "").strip()

            if source == "variable":
                val = float(variables.get(s.get("variable_key", "")) or 0.0)
            elif formula:
                try:
                    val = float(eval_step_expression(formula, variables))
                except Exception:
                    val = 0.0
            else:
                val = 0.0

            val = round(val, 2)
            values[str(step_num)] = val
            if output_key:
                variables[output_key] = val

        return values, variables

    def evaluate_calculation_steps(
        self, person_id: int, company_id: int, period: str
    ) -> Dict[str, Any]:
        """
        完全基于 config JSON 计算三块步骤，返回 steps + values。公式仅来自 config。
        供工资计算页预览使用。
        """
        config = self.load_calculation_config()
        sections = config.get("sections") or {}
        variable_labels = config.get("variable_labels") or {}
        variables = self.get_calculation_context_variables(person_id, company_id, period)
        variables = {k: float(v) if isinstance(v, (int, float)) else v for k, v in variables.items()}

        result: Dict[str, Any] = {}
        for section_id in ("gross", "social", "tax"):
            sec = sections.get(section_id) or {}
            steps_def = sec.get("steps") or []
            step_order = sec.get("step_order") or [s["step"] for s in steps_def]
            values, variables = self._evaluate_section_from_config(
                variables, steps_def, step_order
            )
            steps = self._build_steps_from_config(steps_def)
            self._enrich_step_descs(steps, steps_def, variable_labels, variables)
            # values 统一按 output_key 输出，便于按变量名（如 tax_14、base_amount）取用
            display_values = {
                s["output_key"]: values.get(str(s["step"]), 0.0)
                for s in steps_def
                if s.get("output_key")
            }
            result[section_id] = {"steps": steps, "values": display_values}
        return result

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

    def _get_active_tax_deduction(
        self, person_id: int, period: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取当前人员在指定 period 内生效的那一条专项附加扣除记录（每人每期一条）。
        该条记录包含 7 个金额字段，专项附加扣除合计 = 这 7 个字段的加总。
        条件：effective_date <= 本月最后一天，且 expiry_date 为空或 >= 本月第一天。
        """
        twins = self.twin_service.list_twins(
            "person_tax_deduction",
            filters={"person_id": str(person_id), "status": "生效中"},
        )
        if not twins:
            return None

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

        for d in twins:
            eff = parse_date(d.get("effective_date"))
            exp = parse_date(d.get("expiry_date"))
            if not eff:
                continue
            if eff > period_end:
                continue
            if exp and exp < period_start:
                continue
            return d
        return None

    def _get_attendance_record(
        self, person_id: int, company_id: int, period: str
    ) -> Optional[Dict[str, Any]]:
        """获取指定人员、公司、周期的考勤记录（time_series，time_key=period）"""
        return self._get_twin_state_for_person_company(
            "person_company_attendance_record", person_id, company_id, period
        )

    def _get_position_salary_ratio(
        self, position_category: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """按岗位类别查基础/绩效划分比例（从 app/config/position_salary_ratio.yaml）"""
        from app.config.payroll_config import get_position_salary_ratio
        return get_position_salary_ratio(position_category)

    def _get_employee_type_discount(self, employee_type: Optional[str]) -> float:
        """按员工类别查折算系数（从 app/config/employee_type_discount.yaml），默认 1.0"""
        from app.config.payroll_config import get_employee_type_discount
        return get_employee_type_discount(employee_type)

    def _get_assessment_grade_coefficient(self, grade: Optional[str]) -> float:
        """按考核等级查绩效系数（从 app/config/assessment_grade_coefficient.yaml），默认 1.0"""
        from app.config.payroll_config import get_assessment_grade_coefficient
        return get_assessment_grade_coefficient(grade)

    def _get_social_security_config(
        self, period: str
    ) -> Optional[Dict[str, Any]]:
        """获取发放周期适用的社保公积金配置（从 app/config/social_security_config.yaml）"""
        from app.config.payroll_config import get_social_security_config
        return get_social_security_config(period)

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
