"""
Payroll Service - 工资计算与发放服务

基于 PayrollEngine（指标注册表驱动）实现，
本类只负责：调用引擎、组织展示结构、读写工资单 Twin。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.services.payroll_engine import PayrollEngine, _deduction_tax_period


class PayrollService:
    """
    工资计算服务。

    计算逻辑委托给 PayrollEngine（由 payroll_metrics.yaml 驱动）；
    本类负责：
      - 将引擎结果按 sections 组织为展示结构
      - 构建工资单存档数据并写入 person_company_payroll Twin
      - 查询已生成的工资单记录
    """

    def __init__(self, db_path: Optional[str] = None):
        self.engine = PayrollEngine(db_path=db_path)
        self.twin_service = self.engine.twin_service
        self.state_dao = self.engine.state_dao

    # ── 配置与步骤展示 ────────────────────────────────────────────────────────

    def load_calculation_config(self) -> Dict[str, Any]:
        """返回指标注册表内容（供配置查看接口使用）"""
        return self.engine.load_metrics()

    def get_calculation_steps_for_display(self) -> Dict[str, Any]:
        """
        返回三块步骤定义（不含计算值），供前端展示计算逻辑。
        { "gross": {"label": ..., "steps": [...]}, "social": {...}, "tax": {...} }
        """
        from app.payroll_formula import formula_to_readable

        config = self.engine.load_metrics()
        metrics = config.get("metrics", {})
        sections_def = config.get("sections", {})
        variable_labels = {k: v.get("label", k) for k, v in metrics.items()}

        result: Dict[str, Any] = {}
        for section_id, section_def in sections_def.items():
            steps = []
            for i, key in enumerate(section_def.get("display_order", [])):
                metric = metrics.get(key, {})
                source = metric.get("source") or {}
                expression = source.get("expression", "")
                desc = metric.get("desc", "")
                if expression:
                    readable = formula_to_readable(expression, variable_labels)
                    if readable:
                        desc = (desc + "\n" if desc else "") + readable
                steps.append({
                    "step": i + 1,
                    "key": key,
                    "field_name": metric.get("label", key),
                    "formula": expression,
                    "desc": desc,
                })
            result[section_id] = {
                "label": section_def.get("label", ""),
                "steps": steps,
            }
        return result

    def evaluate_calculation_steps(
        self, person_id: int, company_id: int, period: str
    ) -> Dict[str, Any]:
        """
        计算并返回结构化结果（按 sections 组织），供预览接口使用。
        每块包含 steps（含公式说明）和 values（指标key → 值，以及步骤序号 → 值）。
        """
        resolved = self.engine.compute(person_id, company_id, period)
        config = self.engine.load_metrics()
        return self._structure_result(resolved, config)

    def _structure_result(
        self, resolved: Dict[str, float], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """将引擎计算结果按 sections 组织为展示结构"""
        from app.payroll_formula import formula_to_readable, formula_with_values

        metrics = config.get("metrics", {})
        sections_def = config.get("sections", {})
        variable_labels = {k: v.get("label", k) for k, v in metrics.items()}

        result: Dict[str, Any] = {}
        for section_id, section_def in sections_def.items():
            steps = []
            values: Dict[str, Any] = {}
            for i, key in enumerate(section_def.get("display_order", [])):
                metric = metrics.get(key, {})
                source = metric.get("source") or {}
                expression = source.get("expression", "")
                val = resolved.get(key, 0.0)

                desc = metric.get("desc", "")
                if expression:
                    readable = formula_to_readable(expression, variable_labels)
                    with_vals = formula_with_values(expression, resolved)
                    if readable:
                        desc = (desc + "\n" if desc else "") + readable
                    if with_vals:
                        desc = desc + "\n" + with_vals

                step_num = i + 1
                steps.append({
                    "step": step_num,
                    "key": key,
                    "field_name": metric.get("label", key),
                    "value": val,
                    "formula": expression,
                    "desc": desc,
                })
                values[str(step_num)] = val  # 步骤序号键（兼容旧前端）
                values[key] = val            # 指标名称键

            result[section_id] = {
                "label": section_def.get("label", ""),
                "steps": steps,
                "values": values,
            }

        base = resolved.get("base_amount", 0.0)
        social = resolved.get("social_deduction_total", 0.0)
        tax = resolved.get("tax_monthly", 0.0)
        result["total_amount"] = round(max(0.0, base - social - tax), 2)
        return result

    # ── 工资单生成 ────────────────────────────────────────────────────────────

    def _build_payroll_state_data(
        self, person_id: int, company_id: int, period: str
    ) -> Dict[str, Any]:
        """
        构建写入 person_company_payroll 状态表的完整 data 字典。
        所有 persist: true 的指标都会写入，保证历史可追溯。
        """
        deduction_tax = _deduction_tax_period(period)
        resolved = self.engine.compute(person_id, company_id, period)
        config = self.engine.load_metrics()
        metrics = config.get("metrics", {})

        data: Dict[str, Any] = {
            "salary_period": period,
            "deduction_tax_period": deduction_tax,
            "status": "待发放",
            "payment_date": None,
            "remarks": None,
        }

        # 写入所有 persist: true 的指标
        for key, metric in metrics.items():
            if metric.get("persist", False):
                val = resolved.get(key)
                if val is not None:
                    data[key] = round(float(val), 2) if isinstance(val, (int, float)) else val

        # 保留旧 schema 字段别名（兼容已有工资单记录）
        data["gross_coef"] = round(float(resolved.get("assessment_coefficient", 0)), 2)
        data["social_serious_illness"] = round(float(resolved.get("serious_illness_amount", 0)), 2)
        data["gross_reward_punishment"] = round(float(resolved.get("reward_punishment_amount", 0)), 2)

        # 关键汇总字段（确保覆盖）
        data["base_amount"] = round(float(resolved.get("base_amount", 0)), 2)
        data["social_deduction_total"] = round(float(resolved.get("social_deduction_total", 0)), 2)
        data["tax_monthly"] = round(float(resolved.get("tax_monthly", 0)), 2)
        data["total_amount"] = round(
            max(0.0, data["base_amount"] - data["social_deduction_total"] - data["tax_monthly"]), 2
        )
        return data

    def _get_or_create_payroll_activity(self, person_id: int, company_id: int) -> int:
        """获取或创建 person_company_payroll 的 activity，返回 activity_id"""
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
        """为单人生成工资单并写入 person_company_payroll。成功返回 None，失败返回错误信息。"""
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
        """
        company_id = int(company_id)
        if scope == "person":
            return [(int(person_id), company_id)] if person_id is not None else []

        employments = self.twin_service.list_twins(
            "person_company_employment",
            filters={"company_id": str(company_id)},
        )
        if not employments:
            return []

        if scope == "company":
            return [
                (int(e["person_id"]), company_id)
                for e in employments if e.get("person_id") is not None
            ]

        if scope == "department" and department:
            return [
                (int(e["person_id"]), company_id)
                for e in employments
                if e.get("person_id") is not None
                and (e.get("department") or "").strip() == department.strip()
            ]
        return []

    def generate_payroll(
        self,
        scope: str,
        company_id: int,
        period: str,
        person_id: Optional[int] = None,
        department: Optional[str] = None,
    ) -> Dict[str, Any]:
        """按范围批量生成工资单。返回 { "generated": int, "errors": [...] }"""
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
        """预览将生成工资单的人数（不实际写入）"""
        return len(self.resolve_targets(scope, company_id, person_id=person_id, department=department))

    # ── 工资单查询 ────────────────────────────────────────────────────────────

    def list_payroll_records(
        self, period: str, company_id: int
    ) -> List[Dict[str, Any]]:
        """列出指定周期、公司下已生成的工资单"""
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

            row: Dict[str, Any] = {
                "id": aid,
                "person_id": pid,
                "company_id": cid,
                "salary_period": period,
                **{k: v for k, v in state.data.items() if k != "salary_period"},
            }
            person_state = self.state_dao.get_latest("person", int(pid))
            row["person_name"] = (
                (person_state.data or {}).get("name") or f"人员{pid}"
                if person_state else f"人员{pid}"
            )
            records.append(row)
        return records

    def get_payroll_record_detail(
        self, activity_id: int, period: str
    ) -> Optional[Dict[str, Any]]:
        """获取单条工资单详情"""
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
            **state.data,
        }

        if person_id is not None:
            person_state = self.state_dao.get_latest("person", int(person_id))
            row["person_name"] = (
                (person_state.data or {}).get("name") or f"人员{person_id}"
                if person_state else f"人员{person_id}"
            )
        else:
            row["person_name"] = ""

        # 指标中文标签（供详情页展示）
        config = self.engine.load_metrics()
        row["labels"] = {
            k: v.get("label", k)
            for k, v in config.get("metrics", {}).items()
        }
        return row
