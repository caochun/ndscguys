"""
PayrollEngine - 基于指标注册表（payroll_metrics.yaml）的工资计算引擎

每个指标的 temporal_type 和 period_basis 在配置中显式声明，
引擎根据这两个属性自动决定取数方式，无需硬编码各类数据来源。
"""
from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from app.services.twin_service import TwinService

# 月计薪天数（考勤扣减公式用）
MONTHLY_WORK_DAYS = 21.75

# 在岗月数参考日（扣减个税期数当月的该日）
PAYROLL_REFERENCE_DAY = 26

_METRICS_PATH = Path(__file__).resolve().parent.parent / "config" / "payroll_metrics.yaml"


# ── 期数工具函数 ──────────────────────────────────────────────────────────────

def _parse_date(raw: Any) -> Optional[date]:
    if not raw:
        return None
    try:
        if hasattr(raw, "year"):
            return raw
        return datetime.strptime(str(raw)[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _prev_period(period: str) -> str:
    """YYYY-MM 的上一期"""
    try:
        y, m = map(int, period.split("-"))
        m -= 1
        if m < 1:
            m, y = 12, y - 1
        return f"{y:04d}-{m:02d}"
    except (ValueError, AttributeError):
        return ""


def _next_period(period: str) -> str:
    """YYYY-MM 的下一期"""
    try:
        y, m = map(int, period.split("-"))
        m += 1
        if m > 12:
            m, y = 1, y + 1
        return f"{y:04d}-{m:02d}"
    except (ValueError, AttributeError, TypeError):
        return period


def _deduction_tax_period(salary_period: str) -> str:
    """薪资期数 → 扣减个税期数（下一自然月）"""
    return _next_period(salary_period)


def _period_end_date(period: str) -> Optional[date]:
    """YYYY-MM → 该月最后一天"""
    try:
        y, m = map(int, period.split("-"))
        next_first = date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)
        return next_first - timedelta(days=1)
    except (ValueError, TypeError, IndexError, AttributeError):
        return None


def _period_range(start: str, end: str) -> List[str]:
    """[start, end] 区间内所有 YYYY-MM（含首尾）"""
    try:
        y1, m1 = map(int, start.split("-"))
        y2, m2 = map(int, end.split("-"))
    except (ValueError, AttributeError, TypeError):
        return []
    if (y1, m1) > (y2, m2):
        return []
    out, y, m = [], y1, m1
    while (y, m) <= (y2, m2):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            m, y = 1, y + 1
    return out


# ── 引擎 ──────────────────────────────────────────────────────────────────────

class PayrollEngine:
    """
    基于指标注册表的工资计算引擎。

    调用 compute(person_id, company_id, salary_period) 返回所有指标的计算结果字典。
    各指标的取数方式由 payroll_metrics.yaml 中的 temporal_type / period_basis 声明驱动，
    不在 Python 代码中硬编码。
    """

    def __init__(self, db_path: Optional[str] = None):
        self.twin_service = TwinService(db_path=db_path)
        self.state_dao = self.twin_service.state_dao
        self._metrics_cache: Optional[Dict[str, Any]] = None

    # ── 配置加载 ──────────────────────────────────────────────────────────────

    def load_metrics(self) -> Dict[str, Any]:
        if self._metrics_cache is None:
            with open(_METRICS_PATH, "r", encoding="utf-8") as f:
                self._metrics_cache = yaml.safe_load(f) or {}
        return self._metrics_cache

    # ── 拓扑排序 ──────────────────────────────────────────────────────────────

    def _topological_sort(self, metrics: Dict[str, Any]) -> List[str]:
        """
        按 depends_on 做拓扑排序，确保 formula 指标在其所有依赖之后求值。
        非 formula 指标（无 depends_on）可以任意顺序求值。
        """
        visited: set = set()
        order: List[str] = []

        def visit(key: str) -> None:
            if key in visited:
                return
            visited.add(key)
            metric = metrics.get(key, {})
            for dep in (metric.get("source") or {}).get("depends_on", []):
                if dep in metrics:
                    visit(dep)
            order.append(key)

        for key in metrics:
            visit(key)
        return order

    # ── Twin 过滤条件构建 ──────────────────────────────────────────────────────

    def _build_twin_filters(
        self, twin_name: str, person_id: int, company_id: int
    ) -> Dict[str, str]:
        """根据 twin schema 的 related_entities 自动构建 person_id / company_id 过滤条件"""
        schema = self.twin_service.schema_loader.get_twin_schema(twin_name)
        if not schema:
            return {}
        filters: Dict[str, str] = {}
        for rel in schema.get("related_entities", []):
            key = rel.get("key", "")
            if key == "person_id":
                filters["person_id"] = str(person_id)
            elif key == "company_id":
                filters["company_id"] = str(company_id)
        return filters

    # ── Transform ─────────────────────────────────────────────────────────────

    def _apply_transform(
        self, transform: str, raw_value: Any, full_state: Dict[str, Any]
    ) -> float:
        """将 point_in_time 原始字段值通过指定 transform 转为指标值"""
        from app.config.payroll_config import (
            get_assessment_grade_coefficient,
            get_employee_type_discount,
            get_position_salary_ratio,
        )

        if transform == "salary_to_monthly":
            salary = float(raw_value or 0)
            salary_type = full_state.get("salary_type") or "月薪"
            if salary_type == "年薪":
                return round(salary / 12.0, 2)
            if salary_type == "日薪":
                return round(salary * MONTHLY_WORK_DAYS, 2)
            return salary

        if transform == "position_to_base_ratio":
            ratio = get_position_salary_ratio(str(raw_value) if raw_value else None)
            return float(ratio.get("base_ratio", 0.7)) if ratio else 0.7

        if transform == "position_to_perf_ratio":
            ratio = get_position_salary_ratio(str(raw_value) if raw_value else None)
            return float(ratio.get("performance_ratio", 0.3)) if ratio else 0.3

        if transform == "employee_type_to_discount":
            return float(get_employee_type_discount(str(raw_value) if raw_value else None))

        if transform == "grade_to_coefficient":
            return float(get_assessment_grade_coefficient(str(raw_value) if raw_value else None))

        return float(raw_value or 0)

    # ── temporal_type 解析器 ──────────────────────────────────────────────────

    def _resolve_constant(self, source: Dict[str, Any]) -> float:
        return float(source.get("value", 0))

    def _resolve_point_in_time_version_history(
        self,
        source: Dict[str, Any],
        period: str,
        person_id: int,
        company_id: int,
    ) -> float:
        """
        版本历史模式：单个 activity 有多个版本（如雇佣信息调薪记录）。
        取所有版本中 effective_field ≤ period 月末 的最新一条。
        """
        twin_name = source["twin"]
        field = source["field"]
        effective_field = source.get("effective_field")
        transform = source.get("transform")
        default = float(source.get("default", 0))

        period_end = _period_end_date(period)
        if period_end is None:
            return default

        filters = self._build_twin_filters(twin_name, person_id, company_id)
        twins = self.twin_service.list_twins(twin_name, filters=filters)
        if not twins:
            return default

        detail = self.twin_service.get_twin(twin_name, int(twins[0]["id"]))
        if not detail:
            return default

        current = detail.get("current") or {}
        history = detail.get("history") or []
        all_states = [current] + [h.get("data") or {} for h in history]

        valid: List[Tuple[Dict[str, Any], date]] = []
        for state in all_states:
            eff = _parse_date(state.get(effective_field)) if effective_field else date.min
            if eff is None:
                eff = date.min
            if eff <= period_end:
                valid.append((state, eff))

        if not valid:
            return default

        best_state = max(valid, key=lambda x: x[1])[0]
        raw_value = best_state.get(field)
        if raw_value is None:
            return default
        return self._apply_transform(transform, raw_value, best_state) if transform else float(raw_value or default)

    def _resolve_point_in_time_activity_scan(
        self,
        source: Dict[str, Any],
        period: str,
        person_id: int,
        company_id: int,
    ) -> float:
        """
        活动扫描模式：多个 activity 各自代表一次事件（如每次考核为独立 activity）。
        取所有 activity 最新状态中 effective_field ≤ period 月末 的最新一条。
        """
        twin_name = source["twin"]
        field = source["field"]
        effective_field = source.get("effective_field")
        transform = source.get("transform")
        default = float(source.get("default", 0))

        period_end = _period_end_date(period)
        if period_end is None:
            return default

        filters = self._build_twin_filters(twin_name, person_id, company_id)
        twins = self.twin_service.list_twins(twin_name, filters=filters)
        if not twins:
            return default

        valid: List[Tuple[Dict[str, Any], date]] = []
        for t in twins:
            eff = _parse_date(t.get(effective_field)) if effective_field else date.min
            if eff is None:
                continue
            if eff <= period_end:
                valid.append((t, eff))

        if not valid:
            return default

        best_state = max(valid, key=lambda x: x[1])[0]
        raw_value = best_state.get(field)
        if raw_value is None:
            return default
        return self._apply_transform(transform, raw_value, best_state) if transform else float(raw_value or default)

    def _resolve_point_in_time(
        self,
        source: Dict[str, Any],
        period: str,
        person_id: int,
        company_id: int,
    ) -> float:
        scan_mode = source.get("scan_mode", "version_history")
        if scan_mode == "activity_scan":
            return self._resolve_point_in_time_activity_scan(source, period, person_id, company_id)
        return self._resolve_point_in_time_version_history(source, period, person_id, company_id)

    def _resolve_period_record(
        self,
        source: Dict[str, Any],
        period: str,
        person_id: int,
        company_id: int,
    ) -> float:
        """当期时序记录：直接按 time_key = period 查取"""
        twin_name = source["twin"]
        field = source["field"]
        default = float(source.get("default", 0))

        filters = self._build_twin_filters(twin_name, person_id, company_id)
        twins = self.twin_service.list_twins(twin_name, filters=filters)
        if not twins:
            return default

        state = self.state_dao.get_state_by_time_key(twin_name, int(twins[0]["id"]), period)
        if not state or not state.data:
            return default
        return float(state.data.get(field, default) or default)

    def _resolve_config_lookup(self, source: Dict[str, Any], period: str) -> float:
        """从配置文件按 period 查取对应行的字段值"""
        from app.config.payroll_config import get_social_security_config

        default = float(source.get("default", 0))
        config_name = source.get("config")
        field = source.get("field")

        if config_name == "social_security_config":
            cfg = get_social_security_config(period)
            return float(cfg.get(field, default)) if cfg else default
        return default

    def _resolve_ytd_sum(
        self,
        source: Dict[str, Any],
        salary_period: str,
        deduction_tax_period: str,
        person_id: int,
        company_id: int,
    ) -> float:
        """
        当年至上期的历史工资单累计 sum（deduction_tax 口径）。

        deduction_tax_period D 所在年 = 参考日（D 月 26 日）所在年。
        对每个范围内的 deduction_period d：salary_period = d - 1 个月，
        查该 salary_period 对应的工资单，累加 from_metric 字段。
        """
        from_metric = source["from_metric"]

        try:
            dt_y, dt_m = map(int, deduction_tax_period.split("-"))
        except (ValueError, TypeError):
            return 0.0

        last_day = calendar.monthrange(dt_y, dt_m)[1]
        ref_date = date(dt_y, dt_m, min(PAYROLL_REFERENCE_DAY, last_day))
        cur_year = ref_date.year
        year_start = f"{cur_year:04d}-01"

        prev_dt = _prev_period(deduction_tax_period)
        try:
            prev_year = int(prev_dt.split("-")[0])
        except (ValueError, TypeError):
            return 0.0

        # 上期不在本年 → 当年无历史记录
        if prev_year < cur_year:
            return 0.0

        payroll_twins = self.twin_service.list_twins(
            "person_company_payroll",
            filters={"person_id": str(person_id), "company_id": str(company_id)},
        )
        if not payroll_twins:
            return 0.0
        payroll_id = int(payroll_twins[0]["id"])

        total = 0.0
        for d in _period_range(year_start, prev_dt):
            s_key = _prev_period(d)  # deduction_period → salary_period（工资单存储键）
            state = self.state_dao.get_state_by_time_key("person_company_payroll", payroll_id, s_key)
            if state and state.data:
                total += float(state.data.get(from_metric, 0) or 0)
        return total

    def _resolve_prev_value(
        self,
        source: Dict[str, Any],
        deduction_tax_period: str,
        person_id: int,
        company_id: int,
    ) -> float:
        """
        上期工资单的指定字段值（同年内，跨年归零）。

        上期 deduction_tax_period = D - 1，对应 salary_period = D - 2。
        """
        from_metric = source["from_metric"]

        prev_dt = _prev_period(deduction_tax_period)
        try:
            prev_year = int(prev_dt.split("-")[0])
            cur_year = int(deduction_tax_period.split("-")[0])
        except (ValueError, TypeError):
            return 0.0

        # 上期跨年 → 累计个税归零重算
        if prev_year != cur_year:
            return 0.0

        prev_salary_period = _prev_period(prev_dt)
        payroll_twins = self.twin_service.list_twins(
            "person_company_payroll",
            filters={"person_id": str(person_id), "company_id": str(company_id)},
        )
        if not payroll_twins:
            return 0.0
        payroll_id = int(payroll_twins[0]["id"])

        state = self.state_dao.get_state_by_time_key(
            "person_company_payroll", payroll_id, prev_salary_period
        )
        if not state or not state.data:
            return 0.0
        return float(state.data.get(from_metric, 0) or 0)

    def _resolve_cross_period(
        self,
        source: Dict[str, Any],
        deduction_tax_period: str,
        person_id: int,
        company_id: int,
    ) -> float:
        """跨期推导：调用注册的 resolver 函数"""
        resolver = source.get("resolver")
        if resolver == "months_employed_in_year":
            return float(self._months_employed_in_year(person_id, company_id, deduction_tax_period))
        return 0.0

    def _resolve_formula(
        self, source: Dict[str, Any], resolved: Dict[str, float]
    ) -> float:
        """由已求值的其他指标通过表达式计算"""
        from app.payroll_formula import eval_step_expression

        expression = source.get("expression", "")
        if not expression:
            return 0.0
        try:
            return round(float(eval_step_expression(expression, resolved)), 2)
        except Exception:
            return 0.0

    # ── 单指标调度 ────────────────────────────────────────────────────────────

    def _resolve_metric(
        self,
        metric: Dict[str, Any],
        resolved: Dict[str, float],
        person_id: int,
        company_id: int,
        salary_period: str,
        deduction_tax_period: str,
    ) -> float:
        temporal_type = metric.get("temporal_type", "formula")
        period_basis = metric.get("period_basis", "none")
        source = metric.get("source") or {}

        # period_basis 决定使用哪个期数
        period = salary_period if period_basis == "salary" else deduction_tax_period

        if temporal_type == "constant":
            return self._resolve_constant(source)
        if temporal_type == "point_in_time":
            return self._resolve_point_in_time(source, period, person_id, company_id)
        if temporal_type == "period_record":
            return self._resolve_period_record(source, period, person_id, company_id)
        if temporal_type == "config_lookup":
            return self._resolve_config_lookup(source, period)
        if temporal_type == "ytd_sum":
            return self._resolve_ytd_sum(source, salary_period, deduction_tax_period, person_id, company_id)
        if temporal_type == "prev_value":
            return self._resolve_prev_value(source, deduction_tax_period, person_id, company_id)
        if temporal_type == "cross_period":
            return self._resolve_cross_period(source, deduction_tax_period, person_id, company_id)
        if temporal_type == "formula":
            return self._resolve_formula(source, resolved)
        return 0.0

    # ── 主入口 ────────────────────────────────────────────────────────────────

    def compute(
        self, person_id: int, company_id: int, salary_period: str
    ) -> Dict[str, float]:
        """
        计算所有指标，返回 {指标key: 值} 字典。

        执行顺序由拓扑排序保证：formula 指标在其 depends_on 全部求值后才执行。
        """
        deduction_tax_period = _deduction_tax_period(salary_period)
        config = self.load_metrics()
        metrics = config.get("metrics", {})
        order = self._topological_sort(metrics)

        resolved: Dict[str, float] = {}
        for key in order:
            metric = metrics.get(key)
            if not metric:
                continue
            val = self._resolve_metric(
                metric, resolved, person_id, company_id,
                salary_period, deduction_tax_period,
            )
            resolved[key] = val

        return resolved

    # ── 在岗月数（cross_period resolver）─────────────────────────────────────

    def _months_employed_in_year(
        self, person_id: int, company_id: int, deduction_tax_period: str
    ) -> int:
        """
        本年度在岗月数。
        参考日 = deduction_tax_period 当月 26 日，year = 参考日所在年。

        - 入职月：year 年内最早的「入职」记录月份，无则默认 1 月
        - 结束月：若上月（参考日前一月）在 year 年内且有「离职」→ 上月，否则 → 参考日所在月
        - 在岗月数 = 结束月 - 入职月 + 1，限制在 [0, 12]
        """
        try:
            dt_y, dt_m = map(int, deduction_tax_period.split("-"))
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

        detail = self.twin_service.get_twin("person_company_employment", int(twins[0]["id"]))
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

        # 入职月
        entry_month = 13
        for state in all_states:
            if (state.get("change_type") or "").strip() != "入职":
                continue
            y, m = _ym(state.get("change_date"))
            if y == year and 1 <= m <= 12:
                entry_month = min(entry_month, m)
        if entry_month > 12:
            entry_month = 1

        # 上个月（参考日前一月）
        if ref_date.month == 1:
            prev_y, prev_m = year - 1, 12
        else:
            prev_y, prev_m = year, ref_date.month - 1
        prev_in_year = prev_y == year

        # 上月是否有离职
        has_resignation = False
        if prev_in_year:
            for state in all_states:
                if (state.get("change_type") or "").strip() != "离职":
                    continue
                y, m = _ym(state.get("effective_date"))
                if y == prev_y and m == prev_m:
                    has_resignation = True
                    break

        # 结束月
        end_m = prev_m if (has_resignation and prev_in_year) else ref_date.month

        if end_m < entry_month:
            return 0
        return min(max(0, (end_m - entry_month) + 1), 12)
