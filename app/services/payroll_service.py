"""
Payroll Service - 工资计算与发放服务
"""
from __future__ import annotations

import calendar
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from app.services.twin_service import TwinService


# 月计薪天数（考勤扣减公式用）
MONTHLY_WORK_DAYS = 21.75

# 在岗月数计算中「参考日」：取工资期数所在月的下一月的该日作为参考日期，用于推导「上个月」（与系统当前时间解耦）
PAYROLL_REFERENCE_DAY = 26


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


def _deduction_tax_period(salary_period: str) -> str:
    """薪资期数 → 扣减个税期数（薪资期数下一月，即参考日 PAYROLL_REFERENCE_DAY 所在月）。如 2025-12 -> 2026-01"""
    try:
        y, m = map(int, salary_period.split("-"))
        m += 1
        if m > 12:
            m = 1
            y += 1
        return f"{y:04d}-{m:02d}"
    except (ValueError, AttributeError, TypeError):
        return salary_period


def _ytd_ref_date_and_year(period: str, use_next_month: bool) -> Tuple[Optional[date], int, str]:
    """
    供 YTD 聚合用：由期数得到参考日、当年度、当年 1 月。
    use_next_month=True（薪资口径）：参考日 = period 下一月 26 日。
    use_next_month=False（扣减个税口径）：参考日 = period 当月 26 日。
    返回 (ref_date, cur_year, year_start)，解析失败时 (None, 0, "")。
    """
    try:
        y, m = int(period.split("-")[0]), int(period.split("-")[1])
    except (ValueError, TypeError, IndexError, AttributeError):
        return None, 0, ""
    if use_next_month:
        if m == 12:
            ref_date = date(y + 1, 1, min(PAYROLL_REFERENCE_DAY, 31))
        else:
            last_day = calendar.monthrange(y, m + 1)[1]
            ref_date = date(y, m + 1, min(PAYROLL_REFERENCE_DAY, last_day))
    else:
        last_day = calendar.monthrange(y, m)[1]
        ref_date = date(y, m, min(PAYROLL_REFERENCE_DAY, last_day))
    cur_year = ref_date.year
    year_start = f"{cur_year:04d}-01"
    return ref_date, cur_year, year_start


def _period_end_date(period: str) -> Optional[date]:
    """period 'YYYY-MM' → 该月最后一天，用于 effective_date 比较。"""
    try:
        y, m = map(int, period.split("-"))
        if m == 12:
            next_first = date(y + 1, 1, 1)
        else:
            next_first = date(y, m + 1, 1)
        return next_first - timedelta(days=1)
    except (ValueError, TypeError, IndexError, AttributeError):
        return None


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
        salary_period: str,
        deduction_tax_period: str,
        ctx: PayrollContext,
        spec_list: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        """
        从已保存工资单中按配置做聚合，供公式使用。
        每条 spec 可指定 period_type：salary（按薪资期数）或 deduction_tax（按扣减个税期数，默认）。
        - period_type="salary"：当年度/上一期/汇总区间按 salary_period，查询 time_key=p（工资单即按薪资期数存）。
        - period_type="deduction_tax"：当年度/上一期/汇总区间按 deduction_tax_period，查询 time_key=_prev_period(d)。
        """
        if not spec_list:
            return {}
        result: Dict[str, float] = {}
        for spec in spec_list:
            if not isinstance(spec, dict):
                continue
            var_key = spec.get("variable_key")
            field = spec.get("field")
            agg = (spec.get("aggregation") or "sum").strip().lower()
            period_type = (spec.get("period_type") or "deduction_tax").strip().lower()
            if not var_key or not field:
                continue
            use_next_month = period_type == "salary"
            base_period = salary_period if use_next_month else deduction_tax_period
            ref_date, cur_year, year_start = _ytd_ref_date_and_year(base_period, use_next_month)
            if ref_date is None or not year_start:
                result[var_key] = 0.0
                continue
            prev = _prev_period(base_period)
            # 逻辑期数 → 工资单 time_key：薪资口径用自身，扣减个税口径用上一月
            def payroll_time_key(logical_period: str) -> str:
                return logical_period if use_next_month else _prev_period(logical_period)

            if agg == "last":
                time_key = payroll_time_key(prev)
                prev_state = self._get_twin_state_for_person_company(
                    "person_company_payroll", person_id, company_id, time_key
                )
                if not prev_state:
                    result[var_key] = 0.0
                else:
                    try:
                        prev_year = int(str(prev).split("-")[0]) if prev else 0
                    except (ValueError, TypeError):
                        prev_year = 0
                    result[var_key] = float(prev_state.get(field, 0) or 0) if cur_year == prev_year else 0.0
                continue
            try:
                prev_year = int(prev.split("-")[0]) if prev else 0
            except (ValueError, TypeError):
                prev_year = 0
            sum_end = prev if prev_year >= cur_year else year_start
            periods = _period_range(year_start, sum_end)
            total = 0.0
            for p in periods:
                time_key = payroll_time_key(p)
                state = self._get_twin_state_for_person_company(
                    "person_company_payroll", person_id, company_id, time_key
                )
                if state:
                    total += float(state.get(field, 0) or 0)
            result[var_key] = total
        return result

    def _get_months_employed_in_year(
        self, person_id: int, company_id: int, deduction_tax_period: str
    ) -> int:
        """
        本年度在岗月数（按实际在公司的月数），用于减除费用 = 在岗月数 × 5000。
        入职月、上个月、结束月均限定在「参考日所在年份」的自然年内。
        参考日按扣减个税期数：参考日 = deduction_tax_period 当月 PAYROLL_REFERENCE_DAY 日（与 YTD 口径一致）。
        - 年度 year：参考日所在年份（ref_date.year）。
        - 入职月：year 年内若有 change_type=入职 且 change_date 在 year 年，取最早月份；否则默认 1 月。
        - 上个月：参考日所在月的前一月；若参考日为 1 月则上个月为去年 12 月（不在 year 内，不参与同年内逻辑）。
        - 是否在上月离职：仅当上个月在 year 年内时，检查是否存在 离职 且 effective_date 年月 = 上个月。
        - 结束月（均在 year 年内）：若上月有离职且上个月在 year 内则=上个月，否则=参考日所在月。
        - 在岗月数 = 入职月～结束月（含）的月数，限制在 0～12。
        返回 0～12 的整数。
        """
        try:
            dt_y, dt_m = int((deduction_tax_period or "").split("-")[0]), int((deduction_tax_period or "").split("-")[1])
        except (ValueError, TypeError, IndexError):
            return 0
        last_day = calendar.monthrange(dt_y, dt_m)[1]
        ref_date = date(dt_y, dt_m, min(PAYROLL_REFERENCE_DAY, last_day))
        year = ref_date.year

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

        # 入职月：在参考日所在年 year 内
        entry_month = 13
        for state in all_states:
            if (state.get("change_type") or "").strip() != "入职":
                continue
            y, m = _ym(state.get("change_date"))
            if y == year and 1 <= m <= 12:
                entry_month = min(entry_month, m)
        if entry_month > 12:
            entry_month = 1

        # 上个月：参考日所在月的前一月（仅在 year 年内时参与「上月离职」判断）
        if ref_date.month == 1:
            prev_y, prev_m = year - 1, 12
        else:
            prev_y, prev_m = year, ref_date.month - 1
        prev_in_year = prev_y == year

        has_resignation_in_prev = False
        if prev_in_year:
            for state in all_states:
                if (state.get("change_type") or "").strip() != "离职":
                    continue
                y, m = _ym(state.get("effective_date"))
                if y == prev_y and m == prev_m:
                    has_resignation_in_prev = True
                    break

        # 结束月：限定在 year 年内
        if has_resignation_in_prev and prev_in_year:
            end_y, end_m = prev_y, prev_m
        else:
            # 上月未离职或上个月不在 year 内：结束月 = 参考日所在月（若参考日为 1 月则已是 year 年 1 月）
            end_y, end_m = year, ref_date.month

        if end_m < entry_month:
            return 0
        months = (end_m - entry_month) + 1
        return min(max(0, months), 12)

    def _build_context(
        self,
        person_id: int,
        company_id: int,
        salary_period: str,
        deduction_tax_period: str,
    ) -> PayrollContext:
        """
        聚合工资计算所需的上下文信息。
        salary_period（薪资期数）：用于聘用、考核、考勤、上一期工资单。
        deduction_tax_period（扣减个税期数）：用于社保基数、公积金基数、专项附加扣除。
        """
        employment = self._get_employment_for_period(person_id, company_id, salary_period)
        assessment = self._get_assessment_for_period(person_id, salary_period)
        attendance_record = self._get_attendance_record(person_id, company_id, salary_period)
        prev_payroll = self._get_prev_payroll_state(person_id, company_id, salary_period)
        social_base = self._get_social_base_for_period(person_id, company_id, deduction_tax_period)
        housing_base = self._get_housing_base_for_period(person_id, company_id, deduction_tax_period)
        tax_deduction = self._get_active_tax_deduction(person_id, deduction_tax_period)

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
        self,
        person_id: int,
        company_id: int,
        salary_period: str,
        deduction_tax_period: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        为工资计算步骤公式求值提供「原始变量」字典。
        salary_period：薪资期数。deduction_tax_period：扣减个税期数，不传则按薪资期数下一月推导。
        """
        if deduction_tax_period is None:
            deduction_tax_period = _deduction_tax_period(salary_period)
        ctx = self._build_context(
            person_id, company_id, salary_period, deduction_tax_period
        )
        config = self.load_calculation_config()
        variable_sources = config.get("variable_sources") or {}
        out: Dict[str, Any] = {}
        for variable_key, spec in variable_sources.items():
            if not isinstance(spec, dict):
                continue
            val = self._resolve_variable_from_spec(
                variable_key, spec, ctx, deduction_tax_period
            )
            if val is not None:
                out[variable_key] = val
        # 通用：当年第一期至上一期 payroll 的聚合变量（当年度、上一期、汇总区间均按 deduction_tax_period）
        ytd_specs = config.get("payroll_ytd_variables") or []
        for k, v in self._get_payroll_ytd_aggregates(
            person_id, company_id, salary_period, deduction_tax_period, ctx, ytd_specs
        ).items():
            out[k] = v
        # 本年度在岗月数（参考日=薪资期数下一月26日所在年），按薪资期数
        out["months_employed_in_year"] = self._get_months_employed_in_year(
            person_id, company_id, deduction_tax_period
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
        social_total = float(result.get("social", {}).get("values", {}).get("social_deduction_total", 0) or 0)
        tax_month = float(result.get("tax", {}).get("values", {}).get("tax_monthly", 0) or 0)
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
            "salary_period": period,
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
        data["social_deduction_total"] = round(float(result.get("social", {}).get("values", {}).get("social_deduction_total", 0) or 0), 2)
        data["tax_monthly"] = round(float(result.get("tax", {}).get("values", {}).get("tax_monthly", 0) or 0), 2)
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
        返回列表项含 activity id、person_id、company_id、period、base_amount、social_deduction_total、tax_monthly、total_amount、status 及 person_name（enrich）。
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
                "salary_period": period,
                **{k: v for k, v in state.data.items() if k not in ("salary_period",)},
            }
            row["salary_period"] = period
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
        返回含 id、person_id、company_id、salary_period、person_name、labels（variable_labels）
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
            "salary_period": period,
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

    def _get_employment_for_period(
        self, person_id: int, company_id: int, period: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取指定 period 时点已生效的最新聘用状态。
        只考虑 effective_date ≤ 该 period 月末 的版本，在其中取 effective_date 最大的一条。
        """
        period_end = _period_end_date(period)
        if period_end is None:
            return None
        twins = self.twin_service.list_twins(
            "person_company_employment",
            filters={
                "person_id": str(person_id),
                "company_id": str(company_id),
            },
        )
        if not twins:
            return None
        activity_id = twins[0].get("id")
        if activity_id is None:
            return None
        detail = self.twin_service.get_twin("person_company_employment", activity_id)
        if not detail:
            return None
        current = detail.get("current") or {}
        history = detail.get("history") or []
        all_states = [current] + [h.get("data") or {} for h in history]
        valid: List[Tuple[Dict[str, Any], date]] = []
        for state in all_states:
            eff = _parse_date_to_compare(state.get("effective_date"))
            if eff is None:
                eff = date.min
            if eff <= period_end:
                valid.append((state, eff))
        if not valid:
            return None
        valid.sort(key=lambda x: x[1], reverse=True)
        return valid[0][0]

    def _get_assessment_for_period(
        self, person_id: int, period: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取指定 period 时点已发生的最新考核。
        只考虑 assessment_date ≤ 该 period 月末 的记录，在其中取 assessment_date 最大的一条。
        """
        period_end = _period_end_date(period)
        if period_end is None:
            return None
        twins = self.twin_service.list_twins(
            "person_assessment",
            filters={"person_id": str(person_id)},
        )
        if not twins:
            return None
        valid: List[Tuple[Dict[str, Any], date]] = []
        for t in twins:
            ad = _parse_date_to_compare(t.get("assessment_date"))
            if ad is None:
                continue
            if ad <= period_end:
                valid.append((t, ad))
        if not valid:
            return None
        valid.sort(key=lambda x: x[1], reverse=True)
        return valid[0][0]

    def _get_social_base_for_period(
        self, person_id: int, company_id: int, period: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取指定 period 时点已生效的最新社保基数。
        只考虑 effective_date ≤ 该 period 月末 的记录，在其中取 effective_date 最大的一条。
        """
        period_end = _period_end_date(period)
        if period_end is None:
            return None
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
        in_effect: List[Tuple[Dict[str, Any], date]] = []
        for t in twins:
            eff_date = _parse_date_to_compare(t.get("effective_date"))
            if eff_date is None:
                eff_date = date.min
            if eff_date <= period_end:
                in_effect.append((t, eff_date))
        if not in_effect:
            return None
        in_effect.sort(key=lambda x: x[1], reverse=True)
        return in_effect[0][0]

    def _get_housing_base_for_period(
        self, person_id: int, company_id: int, period: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取指定 period 时点已生效的最新公积金基数。
        只考虑 effective_date ≤ 该 period 月末 的记录，在其中取 effective_date 最大的一条。
        """
        period_end = _period_end_date(period)
        if period_end is None:
            return None
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
        in_effect: List[Tuple[Dict[str, Any], date]] = []
        for t in twins:
            eff_date = _parse_date_to_compare(t.get("effective_date"))
            if eff_date is None:
                eff_date = date.min
            if eff_date <= period_end:
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
