"""
Person service for managing state streams
"""
from __future__ import annotations

import json
from typing import List, Dict, Any, Optional

import sqlite3

from app.daos.person_state_dao import (
    PersonBasicStateDAO,
    PersonPositionStateDAO,
    PersonSalaryStateDAO,
    PersonSocialSecurityStateDAO,
    PersonHousingFundStateDAO,
    PersonAssessmentStateDAO,
    PersonPayrollStateDAO,
)
from app.models.person_payloads import (
    sanitize_basic_payload,
    sanitize_position_payload,
    sanitize_salary_payload,
    sanitize_social_security_payload,
    sanitize_housing_fund_payload,
    sanitize_assessment_payload,
)
from app.db import init_db
from app.daos.housing_fund_batch_dao import HousingFundBatchDAO
from app.daos.social_security_batch_dao import SocialSecurityBatchDAO
from app.daos.payroll_batch_dao import PayrollBatchDAO


def generate_avatar(name: str) -> str:
    safe_name = (name or "user").strip() or "user"
    return (
        "https://api.dicebear.com/7.x/micah/svg"
        "?backgroundColor=bde0fe"
        "&mouth=smile"
        "&pose=thumbsUp"
        f"&seed={safe_name}"
    )


class PersonService:
    def __init__(self, db_path: str):
        self.db_path = db_path
        init_db(db_path)
        self.basic_dao = PersonBasicStateDAO(db_path=db_path)
        self.position_dao = PersonPositionStateDAO(db_path=db_path)
        self.salary_dao = PersonSalaryStateDAO(db_path=db_path)
        self.social_security_dao = PersonSocialSecurityStateDAO(db_path=db_path)
        self.housing_fund_dao = PersonHousingFundStateDAO(db_path=db_path)
        self.assessment_dao = PersonAssessmentStateDAO(db_path=db_path)
        self.payroll_dao = PersonPayrollStateDAO(db_path=db_path)
        self.housing_batch_dao = HousingFundBatchDAO(db_path=db_path)
        self.social_batch_dao = SocialSecurityBatchDAO(db_path=db_path)
        self.payroll_batch_dao = PayrollBatchDAO(db_path=db_path)

    def _get_connection(self) -> sqlite3.Connection:
        return self.basic_dao.get_connection()

    def list_persons(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT pb.person_id, pb.ts, pb.data
            FROM person_basic_history pb
            JOIN (
                SELECT person_id, MAX(version) AS max_version
                FROM person_basic_history
                GROUP BY person_id
            ) latest
            ON pb.person_id = latest.person_id AND pb.version = latest.max_version
            ORDER BY pb.ts DESC
            """
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            data = json.loads(row["data"])
            # 获取当前岗位变动，用于推导当前任职公司
            position_state = self.position_dao.get_latest(row["person_id"])
            current_company: Optional[str] = None
            current_position: Optional[str] = None
            if position_state:
                p_data = position_state.data
                company_name = p_data.get("company_name")
                change_type = p_data.get("change_type")
                # 若最新事件为离职 / 停薪留职，则视为当前无任职公司
                if company_name and change_type not in {"离职", "停薪留职"}:
                    current_company = company_name
                    current_position = p_data.get("position")

            result.append(
                {
                    "person_id": row["person_id"],
                    "ts": row["ts"],
                    "name": data.get("name"),
                    "id_card": data.get("id_card"),
                    "gender": data.get("gender"),
                    "phone": data.get("phone"),
                    "email": data.get("email"),
                    "avatar": data.get("avatar"),
                    "current_company": current_company,
                    "current_position": current_position,
                }
            )
        return result

    def create_person(
        self,
        basic_data: dict,
        position_data: Optional[dict] = None,
        salary_data: Optional[dict] = None,
        social_security_data: Optional[dict] = None,
        housing_fund_data: Optional[dict] = None,
        assessment_data: Optional[dict] = None,
    ) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO persons DEFAULT VALUES")
        conn.commit()
        person_id = cursor.lastrowid

        cleaned_basic = sanitize_basic_payload(basic_data)
        if not cleaned_basic.get("avatar"):
            cleaned_basic["avatar"] = generate_avatar(cleaned_basic.get("name"))
        self.basic_dao.append(entity_id=person_id, data=cleaned_basic)

        cleaned_position = sanitize_position_payload(position_data)
        if cleaned_position:
            self.position_dao.append(entity_id=person_id, data=cleaned_position)

        cleaned_salary = sanitize_salary_payload(salary_data)
        if cleaned_salary:
            self.salary_dao.append(entity_id=person_id, data=cleaned_salary)

        cleaned_social_security = sanitize_social_security_payload(social_security_data)
        if cleaned_social_security:
            self.social_security_dao.append(entity_id=person_id, data=cleaned_social_security)

        cleaned_housing_fund = sanitize_housing_fund_payload(housing_fund_data)
        if cleaned_housing_fund:
            self.housing_fund_dao.append(entity_id=person_id, data=cleaned_housing_fund)

        cleaned_assessment = sanitize_assessment_payload(assessment_data)
        if cleaned_assessment:
            self.assessment_dao.append(entity_id=person_id, data=cleaned_assessment)

        return person_id

    def append_position_change(self, person_id: int, position_data: dict) -> None:
        """追加一条岗位变动事件"""
        cleaned_position = sanitize_position_payload(position_data)
        if not cleaned_position:
            raise ValueError("position payload is empty")
        # 确保 entity_id 存在（persons 表中有该人）
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM persons WHERE id = ?", (person_id,))
        if not cursor.fetchone():
            raise ValueError("person not found")
        self.position_dao.append(entity_id=person_id, data=cleaned_position)

    def append_salary_change(self, person_id: int, salary_data: dict) -> None:
        """追加一条薪资变动事件"""
        cleaned_salary = sanitize_salary_payload(salary_data)
        if not cleaned_salary:
            raise ValueError("salary payload is empty")
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM persons WHERE id = ?", (person_id,))
        if not cursor.fetchone():
            raise ValueError("person not found")
        self.salary_dao.append(entity_id=person_id, data=cleaned_salary)

    def append_social_security_change(self, person_id: int, social_data: dict) -> None:
        """追加一条社保变动事件"""
        cleaned_social = sanitize_social_security_payload(social_data)
        if not cleaned_social:
            raise ValueError("social security payload is empty")
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM persons WHERE id = ?", (person_id,))
        if not cursor.fetchone():
            raise ValueError("person not found")
        self.social_security_dao.append(entity_id=person_id, data=cleaned_social)

    def append_assessment_change(self, person_id: int, assessment_data: dict) -> None:
        """追加一条考核状态事件（grade A-E）。"""
        cleaned_assessment = sanitize_assessment_payload(assessment_data)
        if not cleaned_assessment:
            raise ValueError("assessment payload is empty")
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM persons WHERE id = ?", (person_id,))
        if not cursor.fetchone():
            raise ValueError("person not found")
        self.assessment_dao.append(entity_id=person_id, data=cleaned_assessment)

    # ---- 批量调整：社保 ----

    def preview_social_security_batch(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算一次社保批量调整的预览结果：
        - 创建批次记录（pending）
        - 为每个受影响员工生成一条 batch_item（当前值 + 建议新值）
        - 不写入 person_social_security_history
        """
        effective_date = params["effective_date"]
        min_base = float(params["min_base_amount"])
        max_base = float(params["max_base_amount"])

        # 创建批次记录
        batch_id = self.social_batch_dao.create_batch(
            {
                "effective_date": effective_date,
                "min_base_amount": min_base,
                "max_base_amount": max_base,
                "default_pension_company_rate": params.get("default_pension_company_rate"),
                "default_pension_personal_rate": params.get("default_pension_personal_rate"),
                "default_unemployment_company_rate": params.get("default_unemployment_company_rate"),
                "default_unemployment_personal_rate": params.get("default_unemployment_personal_rate"),
                "default_medical_company_rate": params.get("default_medical_company_rate"),
                "default_medical_personal_rate": params.get("default_medical_personal_rate"),
                "default_maternity_company_rate": params.get("default_maternity_company_rate"),
                "default_maternity_personal_rate": params.get("default_maternity_personal_rate"),
                "default_critical_illness_company_amount": params.get(
                    "default_critical_illness_company_amount"
                ),
                "default_critical_illness_personal_amount": params.get(
                    "default_critical_illness_personal_amount"
                ),
                "target_company": params.get("target_company"),
                "target_department": params.get("target_department"),
                "target_employee_type": params.get("target_employee_type"),
                "note": params.get("note"),
                "status": "pending",
                "affected_count": 0,
            }
        )

        # 找出所有已注册 person_id
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM persons")
        person_ids = [row["id"] for row in cursor.fetchall()]

        target_company = params.get("target_company")
        target_department = params.get("target_department")
        target_employee_type = params.get("target_employee_type")

        affected = 0
        skipped_no_position = 0
        skipped_no_social = 0
        items: List[Dict[str, Any]] = []

        for pid in person_ids:
            # 仅针对当前在职员工
            position_state = self.position_dao.get_latest(pid)
            if not position_state:
                skipped_no_position += 1
                continue
            if not self.is_currently_employed(pid):
                skipped_no_position += 1
                continue

            p_data = position_state.data or {}
            if target_company and p_data.get("company_name") != target_company:
                continue
            if target_department and p_data.get("department") != target_department:
                continue
            if target_employee_type and p_data.get("employee_type") != target_employee_type:
                continue

            # 当前社保状态
            social_state = self.social_security_dao.get_latest(pid)
            if not social_state:
                skipped_no_social += 1
                continue
            s = social_state.data or {}

            orig_base = s.get("base_amount")
            if orig_base is None:
                new_base = min_base
            else:
                try:
                    orig_base_val = float(orig_base)
                except (TypeError, ValueError):
                    orig_base_val = min_base
                new_base = max(min_base, min(max_base, orig_base_val))

            def pick_rate(key_company: str, key_personal: str, def_company: Any, def_personal: Any):
                current_company = s.get(key_company)
                current_personal = s.get(key_personal)
                new_company = float(current_company) if current_company is not None else def_company
                new_personal = float(current_personal) if current_personal is not None else def_personal
                return current_company, current_personal, new_company, new_personal

            (
                cur_pension_company,
                cur_pension_personal,
                new_pension_company,
                new_pension_personal,
            ) = pick_rate(
                "pension_company_rate",
                "pension_personal_rate",
                params.get("default_pension_company_rate"),
                params.get("default_pension_personal_rate"),
            )
            (
                cur_unemp_company,
                cur_unemp_personal,
                new_unemp_company,
                new_unemp_personal,
            ) = pick_rate(
                "unemployment_company_rate",
                "unemployment_personal_rate",
                params.get("default_unemployment_company_rate"),
                params.get("default_unemployment_personal_rate"),
            )
            (
                cur_med_company,
                cur_med_personal,
                new_med_company,
                new_med_personal,
            ) = pick_rate(
                "medical_company_rate",
                "medical_personal_rate",
                params.get("default_medical_company_rate"),
                params.get("default_medical_personal_rate"),
            )
            (
                cur_mat_company,
                cur_mat_personal,
                new_mat_company,
                new_mat_personal,
            ) = pick_rate(
                "maternity_company_rate",
                "maternity_personal_rate",
                params.get("default_maternity_company_rate"),
                params.get("default_maternity_personal_rate"),
            )

            cur_ci_company = s.get("critical_illness_company_amount")
            cur_ci_personal = s.get("critical_illness_personal_amount")
            new_ci_company = (
                float(cur_ci_company)
                if cur_ci_company is not None
                else params.get("default_critical_illness_company_amount")
            )
            new_ci_personal = (
                float(cur_ci_personal)
                if cur_ci_personal is not None
                else params.get("default_critical_illness_personal_amount")
            )

            item_data = {
                "batch_id": batch_id,
                "person_id": pid,
                "current_base_amount": orig_base,
                "current_pension_company_rate": cur_pension_company,
                "current_pension_personal_rate": cur_pension_personal,
                "current_unemployment_company_rate": cur_unemp_company,
                "current_unemployment_personal_rate": cur_unemp_personal,
                "current_medical_company_rate": cur_med_company,
                "current_medical_personal_rate": cur_med_personal,
                "current_maternity_company_rate": cur_mat_company,
                "current_maternity_personal_rate": cur_mat_personal,
                "current_critical_illness_company_amount": cur_ci_company,
                "current_critical_illness_personal_amount": cur_ci_personal,
                "new_base_amount": round(new_base, 2),
                "new_pension_company_rate": new_pension_company,
                "new_pension_personal_rate": new_pension_personal,
                "new_unemployment_company_rate": new_unemp_company,
                "new_unemployment_personal_rate": new_unemp_personal,
                "new_medical_company_rate": new_med_company,
                "new_medical_personal_rate": new_med_personal,
                "new_maternity_company_rate": new_mat_company,
                "new_maternity_personal_rate": new_mat_personal,
                "new_critical_illness_company_amount": new_ci_company,
                "new_critical_illness_personal_amount": new_ci_personal,
                "applied": 0,
            }
            item_id = self.social_batch_dao.create_item(item_data)
            item_data["id"] = item_id
            items.append(item_data)
            affected += 1

        self.social_batch_dao.update_affected_count(batch_id, affected)

        return {
            "batch_id": batch_id,
            "affected_count": affected,
            "skipped_no_position_or_not_active": skipped_no_position,
            "skipped_no_social": skipped_no_social,
            "total_persons": len(person_ids),
            "items": items,
        }

    def update_social_security_batch_items(self, batch_id: int, items: List[Dict[str, Any]]) -> None:
        """根据前端确认的结果更新社保批次明细中的 new_* 字段。"""
        for item in items:
            self.social_batch_dao.update_item(
                item_id=int(item["id"]),
                new_data={
                    "new_base_amount": float(item["new_base_amount"]),
                    "new_pension_company_rate": item.get("new_pension_company_rate"),
                    "new_pension_personal_rate": item.get("new_pension_personal_rate"),
                    "new_unemployment_company_rate": item.get("new_unemployment_company_rate"),
                    "new_unemployment_personal_rate": item.get("new_unemployment_personal_rate"),
                    "new_medical_company_rate": item.get("new_medical_company_rate"),
                    "new_medical_personal_rate": item.get("new_medical_personal_rate"),
                    "new_maternity_company_rate": item.get("new_maternity_company_rate"),
                    "new_maternity_personal_rate": item.get("new_maternity_personal_rate"),
                    "new_critical_illness_company_amount": item.get(
                        "new_critical_illness_company_amount"
                    ),
                    "new_critical_illness_personal_amount": item.get(
                        "new_critical_illness_personal_amount"
                    ),
                },
            )

    def execute_social_security_batch(self, batch_id: int) -> Dict[str, Any]:
        """将某个社保批次的明细真正写入 person_social_security_history。"""
        batch = self.social_batch_dao.get_batch(batch_id)
        if not batch:
            raise ValueError("batch not found")
        if batch.get("status") == "applied":
            return {"batch_id": batch_id, "affected_count": batch.get("affected_count", 0)}

        items = self.social_batch_dao.list_items(batch_id)
        affected = 0
        for item in items:
            if item["applied"]:
                continue
            person_id = item["person_id"]
            data = {
                "base_amount": item["new_base_amount"],
                "pension_company_rate": item.get("new_pension_company_rate"),
                "pension_personal_rate": item.get("new_pension_personal_rate"),
                "unemployment_company_rate": item.get("new_unemployment_company_rate"),
                "unemployment_personal_rate": item.get("new_unemployment_personal_rate"),
                "medical_company_rate": item.get("new_medical_company_rate"),
                "medical_personal_rate": item.get("new_medical_personal_rate"),
                "maternity_company_rate": item.get("new_maternity_company_rate"),
                "maternity_personal_rate": item.get("new_maternity_personal_rate"),
                "critical_illness_company_amount": item.get(
                    "new_critical_illness_company_amount"
                ),
                "critical_illness_personal_amount": item.get(
                    "new_critical_illness_personal_amount"
                ),
                "batch_id": batch_id,
                "batch_effective_date": batch["effective_date"],
            }
            self.social_security_dao.append(entity_id=person_id, data=data)
            affected += 1

        self.social_batch_dao.update_affected_count(batch_id, affected)
        self.social_batch_dao.mark_items_applied(batch_id)
        self.social_batch_dao.update_status(batch_id, "applied")

        return {"batch_id": batch_id, "affected_count": affected}

    def append_housing_fund_change(self, person_id: int, housing_data: dict) -> None:
        """追加一条公积金变动事件"""
        cleaned_housing = sanitize_housing_fund_payload(housing_data)
        if not cleaned_housing:
            raise ValueError("housing fund payload is empty")
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM persons WHERE id = ?", (person_id,))
        if not cursor.fetchone():
            raise ValueError("person not found")
        self.housing_fund_dao.append(entity_id=person_id, data=cleaned_housing)

    def is_currently_employed(self, person_id: int) -> bool:
        """根据最新岗位事件判断是否在职。"""
        position_state = self.position_dao.get_latest(person_id)
        if not position_state:
            return False
        data = position_state.data
        change_type = data.get("change_type")
        # 简单规则：非离职 / 非停薪留职即视为在职
        return change_type not in {"离职", "停薪留职"}

    # ---- 薪酬批量发放 ----

    def _get_latest_state_data(
        self, dao, person_id: int
    ) -> Optional[Dict[str, Any]]:
        """助手函数：获取最新状态并返回 data dict。"""
        state = dao.get_latest(person_id)
        if not state:
            return None
        return state.data or {}

    def _calculate_payroll_for_person(
        self,
        person_id: int,
        batch_period: str,
    ) -> Optional[Dict[str, Any]]:
        """
        根据当前各状态，计算某人的本期薪酬构成。
        - 月薪制：基数 + 绩效（按考核系数） – 补扣 – 个人社保/公积金
        - 日薪制：实际工作天数 × 日薪 – 个人社保/公积金
        """
        salary_state = self.salary_dao.get_latest(person_id)
        if not salary_state:
            return None
        salary_data = salary_state.data or {}

        salary_type = salary_data.get("salary_type")  # 月薪制 / 日薪制度 / 年薪制
        try:
            amount = float(salary_data.get("amount"))
        except (TypeError, ValueError):
            return None

        # 解析批次对应的年月
        from datetime import datetime

        try:
            year, month = batch_period.split("-")
            year_i = int(year)
            month_i = int(month)
        except Exception:
            now = datetime.now()
            year_i, month_i = now.year, now.month

        # 最新考核
        assessment_state = self.assessment_dao.get_latest(person_id)
        assessment_data = assessment_state.data if assessment_state else {}
        grade = (assessment_data or {}).get("grade")

        # 定义绩效系数
        grade_factor_map = {
            "A": 1.2,
            "B": 1.0,
            "C": 0.8,
            "D": 0.5,
            "E": 0.0,
        }
        performance_factor = grade_factor_map.get(grade, 1.0)

        # 员工类别 & 拆分基数/绩效比例
        position_state = self.position_dao.get_latest(person_id)
        position_data = position_state.data if position_state else {}
        employee_type = position_data.get("employee_type")

        # 默认拆分比例（可后续抽到配置）
        split_config = {
            "正式员工": (0.7, 0.3),
            "试用员工": (0.8, 0.2),
            "实习员工": (1.0, 0.0),
            "部分负责人": (0.6, 0.4),
        }
        base_ratio, perf_ratio = split_config.get(employee_type, (0.7, 0.3))

        # 考勤/请假补扣：复用考勤服务
        from app.services.attendance_service import AttendanceService
        from app.services.leave_service import LeaveService

        attendance_service = AttendanceService(self.db_path)
        leave_service = LeaveService(self.db_path)

        summary = attendance_service.get_monthly_summary(
            person_id, year_i, month_i
        )
        # 简化：expected_days 从 summary 中取，取不到则默认 22
        expected_days = summary.get("expected_days") or 22
        actual_days = summary.get("actual_days") or expected_days

        # 统计当月请假（目前只用于日薪实发天数；月薪部分仍用 expected_days/actual_days 推扣）
        leave_records = leave_service.list_leave_for_month(
            person_id, year_i, month_i
        )

        # 个人社保、公积金
        social_data = self._get_latest_state_data(
            self.social_security_dao, person_id
        ) or {}
        housing_data = self._get_latest_state_data(
            self.housing_fund_dao, person_id
        ) or {}

        # 统一计算个人社保、公积金金额
        social_base = float(social_data.get("base_amount") or 0.0)

        def f_or_0(v):
            try:
                return float(v)
            except (TypeError, ValueError):
                return 0.0

        pension_personal = f_or_0(social_data.get("pension_personal_rate"))
        unemp_personal = f_or_0(social_data.get("unemployment_personal_rate"))
        medical_personal = f_or_0(social_data.get("medical_personal_rate"))
        maternity_personal = f_or_0(social_data.get("maternity_personal_rate"))
        ci_personal = f_or_0(social_data.get("critical_illness_personal_amount"))

        social_personal_amount = (
            social_base
            * (
                pension_personal
                + unemp_personal
                + medical_personal
                + maternity_personal
            )
            + ci_personal
        )

        housing_base = float(housing_data.get("base_amount") or 0.0)
        housing_personal_rate = f_or_0(housing_data.get("personal_rate"))
        housing_personal_amount = housing_base * housing_personal_rate

        # 日薪制：只按实际工作天数 × 日薪
        if salary_type == "日薪制度":
            # 简化：实际工作天数 = summary.actual_days
            actual_work_days = actual_days or 0
            gross_amount = amount * actual_work_days
            attendance_deduction = 0.0  # 缺勤已经体现在 actual_work_days 里
            other_deduction = 0.0
            net_amount_before_tax = (
                gross_amount
                - social_personal_amount
                - housing_personal_amount
                - other_deduction
            )
            return {
                "person_id": person_id,
                "salary_base_amount": None,
                "salary_performance_base": None,
                "performance_factor": None,
                "performance_amount": None,
                "gross_amount_before_deductions": gross_amount,
                "attendance_deduction": attendance_deduction,
                "social_personal_amount": social_personal_amount,
                "housing_personal_amount": housing_personal_amount,
                "other_deduction": other_deduction,
                "net_amount_before_tax": net_amount_before_tax,
            }

        # 其他情况（先按月薪制处理）
        monthly_amount = amount

        salary_base_amount = monthly_amount * base_ratio
        salary_performance_base = monthly_amount * perf_ratio
        performance_amount = salary_performance_base * performance_factor

        # 简单考勤扣款：缺勤天数 × 日薪
        day_salary = monthly_amount / float(expected_days or 22)
        absent_days = max(0, (expected_days or 0) - (actual_days or 0))
        attendance_deduction = day_salary * absent_days

        other_deduction = 0.0
        gross_amount_before = salary_base_amount + performance_amount
        net_amount_before_tax = (
            gross_amount_before
            - attendance_deduction
            - social_personal_amount
            - housing_personal_amount
            - other_deduction
        )

        return {
            "person_id": person_id,
            "salary_base_amount": salary_base_amount,
            "salary_performance_base": salary_performance_base,
            "performance_factor": performance_factor,
            "performance_amount": performance_amount,
            "gross_amount_before_deductions": gross_amount_before,
            "attendance_deduction": attendance_deduction,
            "social_personal_amount": social_personal_amount,
            "housing_personal_amount": housing_personal_amount,
            "other_deduction": other_deduction,
            "net_amount_before_tax": net_amount_before_tax,
        }

    def preview_housing_fund_batch(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算一次公积金批量调整的预览结果：
        - 创建批次记录（pending）
        - 为每个受影响员工生成一条 batch_item（当前值 + 建议新值）
        - 不写入 person_housing_fund_history
        返回：批次信息 + 预览明细
        """
        effective_date = params["effective_date"]
        min_base = float(params["min_base_amount"])
        max_base = float(params["max_base_amount"])
        default_company_rate = float(params["default_company_rate"])
        default_personal_rate = float(params["default_personal_rate"])

        # 创建批次记录（先不写 affected_count，稍后回填）
        batch_id = self.housing_batch_dao.create_batch(
            {
                "effective_date": effective_date,
                "min_base_amount": min_base,
                "max_base_amount": max_base,
                "default_company_rate": default_company_rate,
                "default_personal_rate": default_personal_rate,
                "target_company": params.get("target_company"),
                "target_department": params.get("target_department"),
                "target_employee_type": params.get("target_employee_type"),
                "note": params.get("note"),
                "status": "pending",
                "affected_count": 0,
            }
        )

        # 找出所有已注册 person_id
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM persons")
        person_ids = [row["id"] for row in cursor.fetchall()]

        target_company = params.get("target_company")
        target_department = params.get("target_department")
        target_employee_type = params.get("target_employee_type")

        affected = 0
        skipped_no_position = 0
        skipped_no_housing = 0
        items: List[Dict[str, Any]] = []

        for pid in person_ids:
            # 仅针对当前在职员工
            position_state = self.position_dao.get_latest(pid)
            if not position_state:
                skipped_no_position += 1
                continue
            if not self.is_currently_employed(pid):
                skipped_no_position += 1
                continue

            p_data = position_state.data or {}
            if target_company and p_data.get("company_name") != target_company:
                continue
            if target_department and p_data.get("department") != target_department:
                continue
            if target_employee_type and p_data.get("employee_type") != target_employee_type:
                continue

            # 当前公积金状态
            housing_state = self.housing_fund_dao.get_latest(pid)
            if not housing_state:
                skipped_no_housing += 1
                continue
            h = housing_state.data or {}

            orig_base = h.get("base_amount")
            if orig_base is None:
                # 若没有原始基数，这里可以选择跳过，也可以使用下限；目前采用使用下限
                new_base = min_base
            else:
                try:
                    orig_base_val = float(orig_base)
                except (TypeError, ValueError):
                    orig_base_val = min_base
                new_base = max(min_base, min(max_base, orig_base_val))

            company_rate = h.get("company_rate")
            personal_rate = h.get("personal_rate")
            new_company_rate = (
                float(company_rate) if company_rate is not None else default_company_rate
            )
            new_personal_rate = (
                float(personal_rate) if personal_rate is not None else default_personal_rate
            )

            item_data = {
                "batch_id": batch_id,
                "person_id": pid,
                "current_base_amount": orig_base,
                "current_company_rate": company_rate,
                "current_personal_rate": personal_rate,
                "new_base_amount": round(new_base, 2),
                "new_company_rate": new_company_rate,
                "new_personal_rate": new_personal_rate,
                "applied": 0,
            }
            item_id = self.housing_batch_dao.create_item(item_data)
            item_data["id"] = item_id
            items.append(item_data)
            affected += 1

        # 回填受影响人数
        self.housing_batch_dao.update_affected_count(batch_id, affected)

        return {
            "batch_id": batch_id,
            "affected_count": affected,
            "skipped_no_position_or_not_active": skipped_no_position,
            "skipped_no_housing": skipped_no_housing,
            "total_persons": len(person_ids),
            "items": items,
        }

    def update_housing_fund_batch_items(self, batch_id: int, items: List[Dict[str, Any]]) -> None:
        """根据前端确认的结果更新批次明细中的 new_* 字段。"""
        for item in items:
            self.housing_batch_dao.update_item(
                item_id=int(item["id"]),
                new_data={
                    "new_base_amount": float(item["new_base_amount"]),
                    "new_company_rate": float(item["new_company_rate"]),
                    "new_personal_rate": float(item["new_personal_rate"]),
                },
            )

    def execute_housing_fund_batch(self, batch_id: int) -> Dict[str, Any]:
        """
        将某个批次的明细真正写入 person_housing_fund_history：
        - 仅处理未 applied 的 items
        - 为每人追加一条公积金状态记录
        - 更新批次 affected_count 与 status='applied'
        """
        batch = self.housing_batch_dao.get_batch(batch_id)
        if not batch:
            raise ValueError("batch not found")
        if batch.get("status") == "applied":
            # 已执行过，不重复执行
            return {"batch_id": batch_id, "affected_count": batch.get("affected_count", 0)}

        effective_date = batch["effective_date"]
        items = self.housing_batch_dao.list_items(batch_id)
        affected = 0
        for item in items:
            if item["applied"]:
                continue
            person_id = item["person_id"]
            new_data = {
                "base_amount": item["new_base_amount"],
                "company_rate": item["new_company_rate"],
                "personal_rate": item["new_personal_rate"],
                "batch_id": batch_id,
                "batch_effective_date": effective_date,
            }
            self.housing_fund_dao.append(entity_id=person_id, data=new_data)
            affected += 1

        self.housing_batch_dao.update_affected_count(batch_id, affected)
        self.housing_batch_dao.mark_items_applied(batch_id)
        self.housing_batch_dao.update_status(batch_id, "applied")

        return {"batch_id": batch_id, "affected_count": affected}

    def preview_payroll_batch(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        薪酬批量发放预览：
        - 根据过滤条件找到当前在职人员
        - 按 batch_period（通常为 YYYY-MM）计算本期应发金额
        - 创建 payroll_batches + payroll_batch_items
        """
        batch_period = params["batch_period"]
        effective_date = params.get("effective_date")
        target_company = params.get("target_company")
        target_department = params.get("target_department")
        target_employee_type = params.get("target_employee_type")
        note = params.get("note")

        # 创建批次
        batch_id = self.payroll_batch_dao.create_batch(
            {
                "batch_period": batch_period,
                "effective_date": effective_date,
                "target_company": target_company,
                "target_department": target_department,
                "target_employee_type": target_employee_type,
                "note": note,
                "status": "pending",
                "affected_count": 0,
            }
        )

        # 遍历所有 person，按条件筛选 + 计算薪资
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM persons")
        person_ids = [row["id"] for row in cursor.fetchall()]

        items: List[Dict[str, Any]] = []
        affected = 0
        for pid in person_ids:
            # 仅在职
            if not self.is_currently_employed(pid):
                continue
            position_state = self.position_dao.get_latest(pid)
            if not position_state:
                continue
            p_data = position_state.data or {}
            if target_company and p_data.get("company_name") != target_company:
                continue
            if target_department and p_data.get("department") != target_department:
                continue
            if target_employee_type and p_data.get("employee_type") != target_employee_type:
                continue

            calc = self._calculate_payroll_for_person(pid, batch_period=batch_period)
            if not calc:
                continue

            item_data = {
                "batch_id": batch_id,
                **calc,
                "applied": 0,
            }
            item_id = self.payroll_batch_dao.create_item(item_data)
            item_data["id"] = item_id
            items.append(item_data)
            affected += 1

        self.payroll_batch_dao.update_affected_count(batch_id, affected)

        return {
            "batch_id": batch_id,
            "batch_period": batch_period,
            "effective_date": effective_date,
            "affected_count": affected,
            "total_persons": len(person_ids),
            "items": items,
        }

    def update_payroll_batch_items(self, batch_id: int, items: List[Dict[str, Any]]) -> None:
        """
        根据前端确认结果更新薪酬批次明细，目前主要支持修改 other_deduction，
        并据此回算 net_amount_before_tax。
        """
        # 先取出当前所有明细，构建字典方便查找
        existing_items = {
            item["id"]: item for item in self.payroll_batch_dao.list_items(batch_id)
        }

        def f_or_0(v: Any) -> float:
            try:
                return float(v)
            except (TypeError, ValueError):
                return 0.0

        for payload in items:
            item_id = int(payload["id"])
            if item_id not in existing_items:
                continue
            original = existing_items[item_id]
            other_deduction = f_or_0(payload.get("other_deduction"))

            gross = f_or_0(original.get("gross_amount_before_deductions"))
            attendance = f_or_0(original.get("attendance_deduction"))
            social = f_or_0(original.get("social_personal_amount"))
            housing = f_or_0(original.get("housing_personal_amount"))

            net_amount_before_tax = gross - attendance - social - housing - other_deduction

            self.payroll_batch_dao.update_item(
                item_id=item_id,
                new_data={
                    "other_deduction": other_deduction,
                    "net_amount_before_tax": net_amount_before_tax,
                },
            )

    def execute_payroll_batch(self, batch_id: int) -> Dict[str, Any]:
        """
        执行薪酬批量发放：
        目前实现为：
        - 将该批次下所有明细标记为 applied=1
        - 批次 status 置为 'applied'
        后续若引入单独的发薪状态流，可在此处追加写入逻辑。
        """
        batch = self.payroll_batch_dao.get_batch(batch_id)
        if not batch:
            raise ValueError("batch not found")
        if batch.get("status") == "applied":
            return {"batch_id": batch_id, "affected_count": batch.get("affected_count", 0)}

        items = self.payroll_batch_dao.list_items(batch_id)
        affected = 0

        # 将每条明细写入 person_payroll_history 状态流
        for item in items:
            if item.get("applied"):
                continue
            person_id = item["person_id"]
            data = {
                "batch_id": batch_id,
                "batch_period": batch.get("batch_period"),
                "effective_date": batch.get("effective_date"),
                "salary_base_amount": item.get("salary_base_amount"),
                "salary_performance_base": item.get("salary_performance_base"),
                "performance_factor": item.get("performance_factor"),
                "performance_amount": item.get("performance_amount"),
                "gross_amount_before_deductions": item.get("gross_amount_before_deductions"),
                "attendance_deduction": item.get("attendance_deduction"),
                "social_personal_amount": item.get("social_personal_amount"),
                "housing_personal_amount": item.get("housing_personal_amount"),
                "other_deduction": item.get("other_deduction"),
                "net_amount_before_tax": item.get("net_amount_before_tax"),
            }
            self.payroll_dao.append(entity_id=person_id, data=data)
            affected += 1

        # 标记批次与明细已执行
        self.payroll_batch_dao.mark_items_applied(batch_id)
        self.payroll_batch_dao.update_status(batch_id, "applied")
        self.payroll_batch_dao.update_affected_count(batch_id, affected)

        return {"batch_id": batch_id, "affected_count": affected}

    def get_person(self, person_id: int) -> Optional[Dict[str, Any]]:
        basic = self.basic_dao.get_latest(person_id)
        if not basic:
            return None

        position = self.position_dao.get_latest(person_id)
        salary = self.salary_dao.get_latest(person_id)
        social_security = self.social_security_dao.get_latest(person_id)
        housing_fund = self.housing_fund_dao.get_latest(person_id)
        assessment = self.assessment_dao.get_latest(person_id)
        payroll = self.payroll_dao.get_latest(person_id)

        details = {
            "person_id": person_id,
            "basic": basic.to_dict(),
            "position": position.to_dict() if position else None,
            "salary": salary.to_dict() if salary else None,
            "social_security": social_security.to_dict() if social_security else None,
            "housing_fund": housing_fund.to_dict() if housing_fund else None,
            "assessment": assessment.to_dict() if assessment else None,
            "payroll": payroll.to_dict() if payroll else None,
            "basic_history": [state.to_dict() for state in self.basic_dao.list_states(person_id, limit=10)],
            "position_history": [state.to_dict() for state in self.position_dao.list_states(person_id, limit=10)],
            "salary_history": [state.to_dict() for state in self.salary_dao.list_states(person_id, limit=10)],
            "social_security_history": [state.to_dict() for state in self.social_security_dao.list_states(person_id, limit=10)],
            "housing_fund_history": [state.to_dict() for state in self.housing_fund_dao.list_states(person_id, limit=10)],
            "assessment_history": [state.to_dict() for state in self.assessment_dao.list_states(person_id, limit=10)],
            "payroll_history": [state.to_dict() for state in self.payroll_dao.list_states(person_id, limit=10)],
        }
        return details

