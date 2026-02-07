"""
Payroll Service - 工资计算与发放服务
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from app.services.twin_service import TwinService


# 月计薪天数（考勤扣减公式用）
MONTHLY_WORK_DAYS = 21.75


def _parse_date_to_compare(raw: Any) -> Optional[date]:
    """把 effective_date 等解析为 date，用于与当前日期比较；解析失败返回 None。"""
    if not raw:
        return None
    try:
        if hasattr(raw, "year"):
            return raw
        s = str(raw)[:10]
        return datetime.strptime(s, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


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


def _period_range(start_period: str, end_period: str) -> List[str]:
    """自然月周期区间 [start_period, end_period] 的 YYYY-MM 列表（含首尾）。"""
    try:
        y1, m1 = map(int, start_period.split("-"))
        y2, m2 = map(int, end_period.split("-"))
    except (ValueError, AttributeError, TypeError):
        return []
    if (y1, m1) > (y2, m2):
        return []
    out: List[str] = []
    y, m = y1, m1
    while (y, m) <= (y2, m2):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            m = 1
            y += 1
    return out


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

    def _get_twin_state_for_person(
        self, twin_name: str, person_id: int, time_key: str
    ) -> Optional[Dict[str, Any]]:
        """按 person_id 取 time_series twin 的某条状态，返回 state.data（用于专项附加扣除年度累计等）。"""
        twins = self.twin_service.list_twins(
            twin_name,
            filters={"person_id": str(person_id)},
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

    def _get_payroll_ytd_aggregates(
        self,
        person_id: int,
        company_id: int,
        period: str,
        ctx: PayrollContext,
        spec_list: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        """
        通用：从「当年第一期」到「上一期」的 payroll 中，按配置做聚合，供公式使用。

        spec_list 每项: variable_key, field, aggregation。
        - aggregation "last": 取上一期同一年内的该字段值（跨年返回 0）。
        - aggregation "sum": 取当年 01 至上一期该字段的合计。

        返回 { variable_key: 数值 }。
        """
        if not spec_list:
            return {}
        prev = _prev_period(period)
        try:
            cur_year = int((period or "").split("-")[0])
        except (ValueError, TypeError):
            cur_year = 0
        year_start = f"{cur_year:04d}-01" if cur_year else ""
        result: Dict[str, float] = {}
        for spec in spec_list:
            if not isinstance(spec, dict):
                continue
            var_key = spec.get("variable_key")
            field = spec.get("field")
            agg = (spec.get("aggregation") or "sum").strip().lower()
            if not var_key or not field:
                continue
            if agg == "last":
                # 上一期同一年内的单值
                prev_state = ctx.prev_payroll
                if not prev_state:
                    result[var_key] = 0.0
                    continue
                prev_period_val = prev_state.get("period")
                try:
                    prev_year = int(str(prev_period_val).split("-")[0]) if prev_period_val else 0
                except (ValueError, TypeError):
                    prev_year = 0
                if cur_year != prev_year:
                    result[var_key] = 0.0
                else:
                    result[var_key] = float(prev_state.get(field, 0) or 0)
                continue
            # aggregation "sum": 当年 01 到上一期 的 field 合计
            if not prev or not year_start:
                result[var_key] = 0.0
                continue
            periods = _period_range(year_start, prev)
            total = 0.0
            for p in periods:
                state = self._get_twin_state_for_person_company(
                    "person_company_payroll", person_id, company_id, p
                )
                if state:
                    total += float(state.get(field, 0) or 0)
            result[var_key] = total
        return result

    def _get_months_employed_in_year(
        self, person_id: int, company_id: int, period: str
    ) -> int:
        """
        本年度在岗月数（按实际在公司的月数）：
        - 入职月份：当年该人该公司聘用记录中若有 change_type=入职 且 change_date 在当年，取该月；否则取当年 1 月。
        - 上个月：当前系统日期的上个月（如今天 2024-05-15 则上个月=2024-04）。
        - 是否在上月离职：聘用状态中是否存在 change_type=离职 且 effective_date 的年份-月份 = 上个月。
        - 若上个月有离职，则在岗月数 = 入职月～上个月（含）；否则 = 入职月～当前月（含），当前月取计算周期 period 所在月。
        返回 0～12 的整数。
        """
        try:
            year = int(period.split("-")[0])
        except (ValueError, TypeError, AttributeError):
            return 0
        twins = self.twin_service.list_twins(
            "person_company_employment",
            filters={"person_id": str(person_id), "company_id": str(company_id)},
        )
        if not twins:
            return 0
        employment_id = twins[0].get("id")
        if employment_id is None:
            return 0
        detail = self.twin_service.get_twin("person_company_employment", employment_id)
        if not detail:
            return 0
        current = detail.get("current") or {}
        history = detail.get("history") or []
        all_states = [current] + [h.get("data") or {} for h in history]

        def _ym(s: Any) -> Tuple[int, int]:
            if not s:
                return 0, 0
            s = str(s)[:10]
            if len(s) >= 7 and s[4] == "-":
                try:
                    return int(s[:4]), int(s[5:7])
                except ValueError:
                    pass
            return 0, 0

        entry_month = 13
        for state in all_states:
            if (state.get("change_type") or "").strip() != "入职":
                continue
            y, m = _ym(state.get("change_date"))
            if y == year and 1 <= m <= 12:
                entry_month = min(entry_month, m)
        if entry_month > 12:
            entry_month = 1

        today = date.today()
        if today.month == 1:
            prev_y, prev_m = today.year - 1, 12
        else:
            prev_y, prev_m = today.year, today.month - 1
        try:
            cur_y, cur_m = int(period.split("-")[0]), int(period.split("-")[1])
        except (ValueError, TypeError, IndexError):
            cur_y, cur_m = year, 12

        has_resignation_in_prev = False
        for state in all_states:
            if (state.get("change_type") or "").strip() != "离职":
                continue
            y, m = _ym(state.get("effective_date"))
            if y == prev_y and m == prev_m:
                has_resignation_in_prev = True
                break

        if has_resignation_in_prev:
            end_y, end_m = prev_y, prev_m
        else:
            end_y, end_m = cur_y, cur_m

        if end_y < year or (end_y == year and end_m < entry_month):
            return 0
        if end_y > year:
            end_m = 12
            end_y = year
        months = (end_y - year) * 12 + (end_m - entry_month) + 1
        return min(max(0, months), 12)

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
                out[variable_key] = val
        # 通用：当年第一期至上一期 payroll 的聚合变量（last=上期单值，sum=期内合计）
        ytd_specs = config.get("payroll_ytd_variables") or []
        for k, v in self._get_payroll_ytd_aggregates(
            person_id, company_id, period, ctx, ytd_specs
        ).items():
            out[k] = v
        # 本年度在岗月数（用于减除费用 = 在岗月数 × 5000）
        out["months_employed_in_year"] = self._get_months_employed_in_year(
            person_id, company_id, period
        )
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
            # 前端按步骤号（"1","2",...）取数；同时保留 output_key 便于按变量名取用
            display_values: Dict[str, Any] = {}
            for s in steps_def:
                step_num = s["step"]
                val = values.get(str(step_num), 0.0)
                display_values[str(step_num)] = val
                if s.get("output_key"):
                    display_values[s["output_key"]] = val
            result[section_id] = {"steps": steps, "values": display_values}
        # 实发薪资 = 应发 - 社保公积金扣除合计 - 本月个税；写入 person_company_payroll 时使用 total_amount 字段
        base = float(result.get("gross", {}).get("values", {}).get("base_amount", 0) or 0)
        social_total = float(result.get("social", {}).get("values", {}).get("social_5", 0) or 0)
        tax_month = float(result.get("tax", {}).get("values", {}).get("tax_14", 0) or 0)
        result["total_amount"] = round(max(0.0, base - social_total - tax_month), 2)
        return result

    # ======== 工资单生成（写入 person_company_payroll Twin） ========

    def _build_payroll_state_data(
        self, person_id: int, company_id: int, period: str
    ) -> Dict[str, Any]:
        """
        构建写入 person_company_payroll 状态表的完整 data 字典。
        包含计算过程涉及的所有输入变量与三块结果，便于查历史依据。
        """
        variables = self.get_calculation_context_variables(person_id, company_id, period)
        variables = {k: float(v) if isinstance(v, (int, float)) else v for k, v in variables.items()}
        result = self.evaluate_calculation_steps(person_id, company_id, period)
        # 专项附加扣除合计（6 项之和）
        tax_deduction_total = sum(
            float(variables.get(k, 0) or 0)
            for k in (
                "tax_deduction_children",
                "tax_deduction_continuing",
                "tax_deduction_housing_loan",
                "tax_deduction_housing_rent",
                "tax_deduction_elderly",
                "tax_deduction_infant",
            )
        )
        data: Dict[str, Any] = {
            "period": period,
            "employment_salary": variables.get("employment_salary"),
            "base_ratio": variables.get("base_ratio"),
            "perf_ratio": variables.get("perf_ratio"),
            "employee_discount": variables.get("employee_discount"),
            "assessment_coefficient": variables.get("assessment_coefficient"),
            "MONTHLY_WORK_DAYS": variables.get("MONTHLY_WORK_DAYS"),
            "personal_leave_days": variables.get("personal_leave_days"),
            "sick_leave_days": variables.get("sick_leave_days"),
            "reward_punishment_amount": variables.get("reward_punishment_amount"),
            "social_security_base": variables.get("social_security_base"),
            "housing_fund_base": variables.get("housing_fund_base"),
            "pension_rate": variables.get("pension_rate"),
            "unemployment_rate": variables.get("unemployment_rate"),
            "medical_rate": variables.get("medical_rate"),
            "housing_rate": variables.get("housing_rate"),
            "serious_illness_amount": variables.get("serious_illness_amount"),
            "tax_deduction_total": round(tax_deduction_total, 2),
            "status": "待发放",
            "payment_date": None,
            "remarks": None,
        }
        for key, val in (result.get("gross", {}).get("values", {}) or {}).items():
            if key not in ("1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"):
                data[key] = round(float(val), 2) if isinstance(val, (int, float)) else val
        for key, val in (result.get("social", {}).get("values", {}) or {}).items():
            if key not in ("1", "2", "3", "4", "5"):
                data[key] = round(float(val), 2) if isinstance(val, (int, float)) else val
        for key, val in (result.get("tax", {}).get("values", {}) or {}).items():
            if key not in ("1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14"):
                data[key] = round(float(val), 2) if isinstance(val, (int, float)) else val
        data["base_amount"] = round(float(result.get("gross", {}).get("values", {}).get("base_amount", 0) or 0), 2)
        data["social_5"] = round(float(result.get("social", {}).get("values", {}).get("social_5", 0) or 0), 2)
        data["tax_14"] = round(float(result.get("tax", {}).get("values", {}).get("tax_14", 0) or 0), 2)
        data["total_amount"] = result.get("total_amount", 0)
        return data

    def resolve_targets(
        self,
        scope: str,
        company_id: int,
        person_id: Optional[int] = None,
        department: Optional[str] = None,
    ) -> List[Tuple[int, int]]:
        """
        按范围解析待生成工资单的 (person_id, company_id) 列表。
        scope: "person" | "department" | "company"
        部门来源：person_company_employment 当前状态的 department 字段。
        """
        company_id = int(company_id)
        if scope == "person":
            if person_id is None:
                return []
            return [(int(person_id), company_id)]
        employments = self.twin_service.list_twins(
            "person_company_employment",
            filters={"company_id": str(company_id)},
        )
        if not employments:
            return []
        if scope == "company":
            return [(int(e["person_id"]), company_id) for e in employments if e.get("person_id") is not None]
        if scope == "department":
            if not department:
                return []
            return [
                (int(e["person_id"]), company_id)
                for e in employments
                if e.get("person_id") is not None and (e.get("department") or "").strip() == (department or "").strip()
            ]
        return []

    def _get_or_create_payroll_activity(self, person_id: int, company_id: int) -> int:
        """获取或创建 person_company_payroll 的 activity，返回 activity_id。"""
        twins = self.twin_service.list_twins(
            "person_company_payroll",
            filters={"person_id": str(person_id), "company_id": str(company_id)},
        )
        if twins:
            return int(twins[0]["id"])
        return self.twin_service.twin_dao.create_activity_twin(
            "person_company_payroll",
            {"person_id": person_id, "company_id": company_id},
        )

    def generate_payroll_for_one(
        self, person_id: int, company_id: int, period: str
    ) -> Optional[str]:
        """
        为单人生成工资单并写入 person_company_payroll。
        成功返回 None，失败返回错误信息字符串。
        """
        try:
            data = self._build_payroll_state_data(person_id, company_id, period)
            activity_id = self._get_or_create_payroll_activity(person_id, company_id)
            self.state_dao.append(
                "person_company_payroll",
                activity_id,
                data,
                time_key=period,
            )
            return None
        except Exception as e:
            return str(e)

    def generate_payroll(
        self,
        scope: str,
        company_id: int,
        period: str,
        person_id: Optional[int] = None,
        department: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        按范围批量生成工资单。返回 { "generated": int, "errors": [ {"person_id": int, "reason": str}, ... ] }。
        """
        targets = self.resolve_targets(scope, company_id, person_id=person_id, department=department)
        generated = 0
        errors: List[Dict[str, Any]] = []
        for pid, cid in targets:
            err = self.generate_payroll_for_one(pid, cid, period)
            if err:
                errors.append({"person_id": pid, "reason": err})
            else:
                generated += 1
        return {"generated": generated, "errors": errors}

    def get_generate_preview_count(
        self,
        scope: str,
        company_id: int,
        person_id: Optional[int] = None,
        department: Optional[str] = None,
    ) -> int:
        """预览将生成工资单的人数（不实际写入）。"""
        return len(self.resolve_targets(scope, company_id, person_id=person_id, department=department))

    def list_payroll_records(
        self, period: str, company_id: int
    ) -> List[Dict[str, Any]]:
        """
        列出指定周期、公司下已创建的工资单（person_company_payroll 状态 time_key=period）。
        返回列表项含 activity id、person_id、company_id、period、base_amount、social_5、tax_14、total_amount、status 及 person_name（enrich）。
        """
        activities = self.twin_service.list_twins(
            "person_company_payroll",
            filters={"company_id": str(company_id)},
        )
        records: List[Dict[str, Any]] = []
        for act in activities:
            aid = act.get("id")
            pid = act.get("person_id")
            cid = act.get("company_id")
            if aid is None or pid is None:
                continue
            state = self.state_dao.get_state_by_time_key(
                "person_company_payroll", int(aid), period
            )
            if not state or not state.data:
                continue
            row = {
                "id": aid,
                "person_id": pid,
                "company_id": cid,
                "period": period,
                **{k: v for k, v in state.data.items() if k not in ("period",)},
            }
            row["period"] = period
            # 人员姓名：取 person 最新状态 name
            person_state = self.state_dao.get_latest("person", int(pid))
            if person_state and person_state.data:
                row["person_name"] = (person_state.data or {}).get("name") or f"人员{pid}"
            else:
                row["person_name"] = f"人员{pid}"
            records.append(row)
        return records

    def get_payroll_record_detail(
        self, activity_id: int, period: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取单条工资单详情（指定 activity_id 与 period 对应的状态）。
        返回含 id、person_id、company_id、period、person_name、labels（variable_labels）
        以及该条状态的全部 data 字段。
        """
        state = self.state_dao.get_state_by_time_key(
            "person_company_payroll", int(activity_id), period
        )
        if not state or not state.data:
            return None
        twin = self.twin_service.get_twin("person_company_payroll", int(activity_id))
        person_id = (twin or {}).get("person_id")
        company_id = (twin or {}).get("company_id")
        row: Dict[str, Any] = {
            "id": activity_id,
            "person_id": person_id,
            "company_id": company_id,
            "period": period,
            **{k: v for k, v in state.data.items()},
        }
        if person_id is not None:
            person_state = self.state_dao.get_latest("person", int(person_id))
            if person_state and person_state.data:
                row["person_name"] = (person_state.data or {}).get("name") or f"人员{person_id}"
            else:
                row["person_name"] = f"人员{person_id}"
        else:
            row["person_name"] = ""
        config = self.load_calculation_config()
        row["labels"] = config.get("variable_labels") or {}
        return row

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
        """获取生效日期不晚于当前系统日期的最近一条社保基数"""
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
        today = date.today()
        in_effect = []
        for t in twins:
            eff_date = _parse_date_to_compare(t.get("effective_date"))
            if eff_date is not None and eff_date <= today:
                in_effect.append((t, eff_date))
        if not in_effect:
            return None
        in_effect.sort(key=lambda x: x[1], reverse=True)
        return in_effect[0][0]

    def _get_latest_housing_base(
        self, person_id: int, company_id: int
    ) -> Optional[Dict[str, Any]]:
        """获取生效日期不晚于当前系统日期的最近一条公积金基数"""
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
        today = date.today()
        in_effect = []
        for t in twins:
            eff_date = _parse_date_to_compare(t.get("effective_date"))
            if eff_date is not None and eff_date <= today:
                in_effect.append((t, eff_date))
        if not in_effect:
            return None
        in_effect.sort(key=lambda x: x[1], reverse=True)
        return in_effect[0][0]

    def _get_active_tax_deduction(
        self, person_id: int, period: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取当前人员在指定 period（账期 YYYY-MM）的专项附加扣除年度累计记录（time_series，每人每期一条）。
        该条记录包含 6 个金额字段（年度累计值），专项附加扣除合计 = 这 6 个字段的加总。
        """
        return self._get_twin_state_for_person("person_tax_deduction", person_id, period)

    def _get_attendance_record(
        self, person_id: int, company_id: int, period: str
    ) -> Optional[Dict[str, Any]]:
        """获取指定人员、公司、周期的考勤记录（time_series，time_key=period）"""
        return self._get_twin_state_for_person_company(
            "person_company_attendance", person_id, company_id, period
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
