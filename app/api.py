"""
API routes for person state management
"""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from app.services.person_service import PersonService
from app.services.attendance_service import AttendanceService
from app.services.leave_service import LeaveService
from app.models.person_payloads import PayloadValidationError

api_bp = Blueprint("api", __name__)


def get_person_service() -> PersonService:
    db_path = current_app.config["DATABASE_PATH"]
    return PersonService(db_path)


def get_attendance_service() -> AttendanceService:
    db_path = current_app.config["DATABASE_PATH"]
    return AttendanceService(db_path)


def get_leave_service() -> LeaveService:
    db_path = current_app.config["DATABASE_PATH"]
    return LeaveService(db_path)


@api_bp.route("/persons", methods=["GET"])
def list_persons():
    service = get_person_service()
    persons = service.list_persons()
    return jsonify({"success": True, "data": persons})


@api_bp.route("/persons", methods=["POST"])
def create_person():
    service = get_person_service()
    payload = request.get_json() or {}

    basic_data = payload.get("basic")
    if not basic_data or not basic_data.get("name"):
        return jsonify({"success": False, "error": "basic.name is required"}), 400

    position_data = payload.get("position")
    salary_data = payload.get("salary")
    social_security_data = payload.get("social_security")
    housing_fund_data = payload.get("housing_fund")
    assessment_data = payload.get("assessment")
    try:
        person_id = service.create_person(
            basic_data,
            position_data,
            salary_data,
            social_security_data,
            housing_fund_data,
            assessment_data,
        )
    except PayloadValidationError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    return jsonify({"success": True, "data": {"person_id": person_id}})


@api_bp.route("/persons/<int:person_id>", methods=["GET"])
def get_person(person_id: int):
    service = get_person_service()
    result = service.get_person(person_id)
    if not result:
        return jsonify({"success": False, "error": "person not found"}), 404
    return jsonify({"success": True, "data": result})


@api_bp.route("/persons/<int:person_id>/position", methods=["POST"])
def append_position_change(person_id: int):
    """追加一条岗位变动事件"""
    service = get_person_service()
    payload = request.get_json() or {}
    # 允许直接传 position 字段或扁平字段
    position_data = payload.get("position") or payload
    try:
        service.append_position_change(person_id, position_data)
    except PayloadValidationError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    return jsonify({"success": True})


@api_bp.route("/persons/<int:person_id>/salary", methods=["POST"])
def append_salary_change(person_id: int):
    """追加一条薪资变动事件"""
    service = get_person_service()
    payload = request.get_json() or {}
    salary_data = payload.get("salary") or payload
    try:
        service.append_salary_change(person_id, salary_data)
    except PayloadValidationError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    return jsonify({"success": True})


@api_bp.route("/persons/<int:person_id>/social-security", methods=["POST"])
def append_social_security_change(person_id: int):
    """追加一条社保变动事件"""
    service = get_person_service()
    payload = request.get_json() or {}
    social_data = payload.get("social_security") or payload
    try:
        service.append_social_security_change(person_id, social_data)
    except PayloadValidationError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    return jsonify({"success": True})


@api_bp.route("/persons/<int:person_id>/assessment", methods=["POST"])
def append_assessment_change(person_id: int):
    """追加一条考核状态（grade A-E）。"""
    service = get_person_service()
    payload = request.get_json() or {}
    assessment_data = payload.get("assessment") or payload
    try:
        service.append_assessment_change(person_id, assessment_data)
    except PayloadValidationError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    return jsonify({"success": True})


@api_bp.route("/persons/<int:person_id>/housing-fund", methods=["POST"])
def append_housing_fund_change(person_id: int):
    """追加一条公积金变动事件"""
    service = get_person_service()
    payload = request.get_json() or {}
    housing_data = payload.get("housing_fund") or payload
    try:
        service.append_housing_fund_change(person_id, housing_data)
    except PayloadValidationError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    return jsonify({"success": True})


@api_bp.route("/persons/<int:person_id>/tax-deduction", methods=["POST"])
def append_tax_deduction_change(person_id: int):
    """追加一条个税专项附加扣除变动事件"""
    service = get_person_service()
    payload = request.get_json() or {}
    tax_deduction_data = payload.get("tax_deduction") or payload
    try:
        service.append_tax_deduction_change(person_id, tax_deduction_data)
    except PayloadValidationError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    return jsonify({"success": True})


@api_bp.route("/housing-fund/batch-preview", methods=["POST"])
def housing_fund_batch_preview():
    """公积金批量调整预览：创建批次和明细，但不写入状态流。"""
    service = get_person_service()
    payload = request.get_json() or {}
    required_fields = [
        "effective_date",
        "min_base_amount",
        "max_base_amount",
        "default_company_rate",
        "default_personal_rate",
    ]
    missing = [f for f in required_fields if f not in payload]
    if missing:
        return jsonify({"success": False, "error": f"missing fields: {', '.join(missing)}"}), 400

    result = service.preview_housing_fund_batch(payload)
    return jsonify({"success": True, "data": result})


@api_bp.route("/housing-fund/batch-confirm/<int:batch_id>", methods=["POST"])
def housing_fund_batch_confirm(batch_id: int):
    """确认批量调整：更新批次明细中的 new_* 值。"""
    service = get_person_service()
    payload = request.get_json() or {}
    items = payload.get("items") or []
    if not items:
        return jsonify({"success": False, "error": "items is required"}), 400
    service.update_housing_fund_batch_items(batch_id, items)
    return jsonify({"success": True})


@api_bp.route("/housing-fund/batch-execute/<int:batch_id>", methods=["POST"])
def housing_fund_batch_execute(batch_id: int):
    """执行批量调整：为每个明细追加公积金状态流记录。"""
    service = get_person_service()
    result = service.execute_housing_fund_batch(batch_id)
    return jsonify({"success": True, "data": result})


@api_bp.route("/housing-fund/batches", methods=["GET"])
def list_housing_fund_batches():
    """列出最近的公积金批量调整批次。"""
    service = get_person_service()
    batches = service.housing_batch_dao.list_batches(limit=50)
    return jsonify({"success": True, "data": batches})


@api_bp.route("/housing-fund/batch-items/<int:batch_id>", methods=["GET"])
def list_housing_fund_batch_items(batch_id: int):
    """列出某个批次的调整明细。"""
    service = get_person_service()
    items = service.housing_batch_dao.list_items(batch_id)
    return jsonify({"success": True, "data": items})


# ---- 社保批量调整 ----

@api_bp.route("/social-security/batch-preview", methods=["POST"])
def social_security_batch_preview():
    """社保批量调整预览：创建批次和明细，但不写入状态流。"""
    service = get_person_service()
    payload = request.get_json() or {}
    required_fields = [
        "effective_date",
        "min_base_amount",
        "max_base_amount",
    ]
    missing = [f for f in required_fields if f not in payload]
    if missing:
        return jsonify({"success": False, "error": f"missing fields: {', '.join(missing)}"}), 400

    result = service.preview_social_security_batch(payload)
    return jsonify({"success": True, "data": result})


@api_bp.route("/social-security/batch-confirm/<int:batch_id>", methods=["POST"])
def social_security_batch_confirm(batch_id: int):
    """确认社保批量调整：更新批次明细中的 new_* 值。"""
    service = get_person_service()
    payload = request.get_json() or {}
    items = payload.get("items") or []
    if not items:
        return jsonify({"success": False, "error": "items is required"}), 400
    service.update_social_security_batch_items(batch_id, items)
    return jsonify({"success": True})


@api_bp.route("/social-security/batch-execute/<int:batch_id>", methods=["POST"])
def social_security_batch_execute(batch_id: int):
    """执行社保批量调整：为每个明细追加社保状态流记录。"""
    service = get_person_service()
    result = service.execute_social_security_batch(batch_id)
    return jsonify({"success": True, "data": result})


@api_bp.route("/social-security/batches", methods=["GET"])
def list_social_security_batches():
    """列出最近的社保批量调整批次。"""
    service = get_person_service()
    batches = service.social_batch_dao.list_batches(limit=50)
    return jsonify({"success": True, "data": batches})


@api_bp.route("/social-security/batch-items/<int:batch_id>", methods=["GET"])
def list_social_security_batch_items(batch_id: int):
    """列出某个社保批次的调整明细。"""
    service = get_person_service()
    items = service.social_batch_dao.list_items(batch_id)
    return jsonify({"success": True, "data": items})


# ---- 个税专项附加扣除批量调整 ----

@api_bp.route("/tax-deduction/batch-preview", methods=["POST"])
def tax_deduction_batch_preview():
    """个税专项附加扣除批量调整预览：创建批次和明细，但不写入状态流。"""
    service = get_person_service()
    payload = request.get_json() or {}
    required_fields = ["effective_date", "effective_month"]
    missing = [f for f in required_fields if f not in payload]
    if missing:
        return jsonify({"success": False, "error": f"missing fields: {', '.join(missing)}"}), 400

    result = service.preview_tax_deduction_batch(payload)
    return jsonify({"success": True, "data": result})


@api_bp.route("/tax-deduction/batch-confirm/<int:batch_id>", methods=["POST"])
def tax_deduction_batch_confirm(batch_id: int):
    """确认个税专项附加扣除批量调整：更新批次明细中的 new_* 值。"""
    service = get_person_service()
    payload = request.get_json() or {}
    items = payload.get("items") or []
    if not items:
        return jsonify({"success": False, "error": "items is required"}), 400
    service.update_tax_deduction_batch_items(batch_id, items)
    return jsonify({"success": True})


@api_bp.route("/tax-deduction/batch-execute/<int:batch_id>", methods=["POST"])
def tax_deduction_batch_execute(batch_id: int):
    """执行个税专项附加扣除批量调整：为每个明细追加状态流记录。"""
    service = get_person_service()
    result = service.execute_tax_deduction_batch(batch_id)
    return jsonify({"success": True, "data": result})


@api_bp.route("/tax-deduction/batches", methods=["GET"])
def list_tax_deduction_batches():
    """列出最近的个税专项附加扣除批量调整批次。"""
    service = get_person_service()
    batches = service.tax_deduction_batch_dao.list_batches(limit=50)
    return jsonify({"success": True, "data": batches})


@api_bp.route("/tax-deduction/batch-items/<int:batch_id>", methods=["GET"])
def list_tax_deduction_batch_items(batch_id: int):
    """列出某个个税专项附加扣除批次的调整明细。"""
    service = get_person_service()
    items = service.tax_deduction_batch_dao.list_items(batch_id)
    return jsonify({"success": True, "data": items})


# ---- 统计信息 ----

@api_bp.route("/statistics", methods=["GET"])
def get_statistics():
    """获取人员统计信息"""
    service = get_person_service()
    at_date = request.args.get("at_date")  # 可选，格式：YYYY-MM-DD
    stats = service.get_statistics(at_date=at_date)
    return jsonify({"success": True, "data": stats})


# ---- 薪酬批量发放 ----


@api_bp.route("/payroll/batch-preview", methods=["POST"])
def payroll_batch_preview():
    """薪酬批量发放预览：创建批次和明细，但不写入个人发薪状态流。"""
    service = get_person_service()
    payload = request.get_json() or {}
    required_fields = ["batch_period"]
    missing = [f for f in required_fields if f not in payload]
    if missing:
        return (
            jsonify(
                {
                    "success": False,
                    "error": f"missing fields: {', '.join(missing)}",
                }
            ),
            400,
        )

    result = service.preview_payroll_batch(payload)
    return jsonify({"success": True, "data": result})


@api_bp.route("/payroll/batches", methods=["GET"])
def list_payroll_batches():
    """列出最近的薪酬批量发放批次。"""
    service = get_person_service()
    batches = service.payroll_batch_dao.list_batches(limit=50)
    return jsonify({"success": True, "data": batches})


@api_bp.route("/payroll/batch-items/<int:batch_id>", methods=["GET"])
def list_payroll_batch_items(batch_id: int):
    """列出某个薪酬批次的发放明细。"""
    service = get_person_service()
    items = service.payroll_batch_dao.list_items(batch_id)
    # 补充计算相关的元数据
    batch = service.payroll_batch_dao.get_batch(batch_id)
    if batch:
        batch_period = batch.get("batch_period")
        enriched_items = []
        for item in items:
            person_id = item.get("person_id")
            # 获取员工姓名
            basic_state = service.basic_dao.get_latest(person_id)
            person_name = (basic_state.data or {}).get("name") if basic_state else None
            item["person_name"] = person_name
            # 重新计算以获取所有计算相关的属性（如果批次还未执行，这些信息应该已经在预览时存在）
            # 但如果是从数据库读取的，需要重新计算
            if batch_period:
                calc = service._calculate_payroll_for_person(person_id, batch_period)
                if calc:
                    # 补充计算相关的属性
                    item.update({
                        "salary_type": calc.get("salary_type"),
                        "original_salary_amount": calc.get("original_salary_amount"),
                        "adjusted_salary_amount": calc.get("adjusted_salary_amount"),
                        "employee_type": calc.get("employee_type"),
                        "assessment_grade": calc.get("assessment_grade"),
                        "base_ratio": calc.get("base_ratio"),
                        "perf_ratio": calc.get("perf_ratio"),
                        "expected_days": calc.get("expected_days"),
                        "actual_days": calc.get("actual_days"),
                        "absent_days": calc.get("absent_days"),
                        "day_salary": calc.get("day_salary"),
                        "social_base_amount": calc.get("social_base_amount"),
                        "housing_base_amount": calc.get("housing_base_amount"),
                    })
            enriched_items.append(item)
        items = enriched_items
    return jsonify({"success": True, "data": items})


@api_bp.route("/payroll/batch-confirm/<int:batch_id>", methods=["POST"])
def payroll_batch_confirm(batch_id: int):
    """确认薪酬批量发放：更新明细中的 other_deduction 等字段。"""
    service = get_person_service()
    payload = request.get_json() or {}
    items = payload.get("items") or []
    if not items:
        return jsonify({"success": False, "error": "items is required"}), 400
    service.update_payroll_batch_items(batch_id, items)
    return jsonify({"success": True})


@api_bp.route("/payroll/batch-execute/<int:batch_id>", methods=["POST"])
def payroll_batch_execute(batch_id: int):
    """执行薪酬批量发放：当前仅将批次与明细标记为已执行。"""
    service = get_person_service()
    result = service.execute_payroll_batch(batch_id)
    return jsonify({"success": True, "data": result})


@api_bp.route("/attendance", methods=["GET"])
def list_attendance():
    person_id = request.args.get("person_id", type=int)
    if not person_id:
        return jsonify({"success": False, "error": "person_id is required"}), 400
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    service = get_attendance_service()
    records = service.list_attendance(person_id, start_date, end_date)
    return jsonify({"success": True, "data": records})


@api_bp.route("/attendance", methods=["POST"])
def create_attendance():
    payload = request.get_json() or {}
    person_id = payload.get("person_id")
    date = payload.get("date")
    if not person_id or not date:
        return jsonify({"success": False, "error": "person_id and date are required"}), 400
    try:
        person_id = int(person_id)
        work_hours = float(payload.get("work_hours", 0))
        overtime_hours = float(payload.get("overtime_hours", 0))
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "work_hours and overtime_hours must be numbers"}), 400
    service = get_attendance_service()
    record_id = service.create_attendance(
        person_id=person_id,
        date=date,
        check_in_time=payload.get("check_in_time"),
        check_out_time=payload.get("check_out_time"),
        work_hours=work_hours,
        overtime_hours=overtime_hours,
        status=payload.get("status", "正常"),
        note=payload.get("note"),
    )
    return jsonify({"success": True, "data": {"record_id": record_id}})


@api_bp.route("/attendance/<int:record_id>", methods=["PUT"])
def update_attendance(record_id: int):
    payload = request.get_json() or {}
    service = get_attendance_service()
    def to_optional_float(value):
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            raise ValueError
    try:
        updated = service.update_attendance(
            record_id=record_id,
            check_in_time=payload.get("check_in_time"),
            check_out_time=payload.get("check_out_time"),
            work_hours=to_optional_float(payload.get("work_hours")),
            overtime_hours=to_optional_float(payload.get("overtime_hours")),
            status=payload.get("status"),
            note=payload.get("note"),
        )
    except ValueError:
        return jsonify({"success": False, "error": "work_hours and overtime_hours must be numbers"}), 400
    if not updated:
        return jsonify({"success": False, "error": "attendance record not found"}), 404
    return jsonify({"success": True})


@api_bp.route("/attendance/<int:record_id>", methods=["DELETE"])
def delete_attendance(record_id: int):
    service = get_attendance_service()
    deleted = service.delete_attendance(record_id)
    if not deleted:
        return jsonify({"success": False, "error": "attendance record not found"}), 404
    return jsonify({"success": True})


@api_bp.route("/attendance/monthly-summary", methods=["GET"])
def get_monthly_attendance_summary():
    person_id = request.args.get("person_id", type=int)
    if not person_id:
        return jsonify({"success": False, "error": "person_id is required"}), 400
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)
    if not year or not month:
        from datetime import datetime
        now = datetime.now()
        year = year or now.year
        month = month or now.month
    service = get_attendance_service()
    summary = service.get_monthly_summary(person_id, year, month)
    return jsonify({"success": True, "data": summary})


@api_bp.route("/leave", methods=["GET"])
def list_leave():
    person_id = request.args.get("person_id", type=int)
    if not person_id:
        return jsonify({"success": False, "error": "person_id is required"}), 400
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    service = get_leave_service()
    records = service.list_leave(person_id, start_date, end_date)
    return jsonify({"success": True, "data": records})


@api_bp.route("/leave", methods=["POST"])
def create_leave():
    payload = request.get_json() or {}
    person_id = payload.get("person_id")
    leave_date = payload.get("leave_date")
    leave_type = payload.get("leave_type")
    hours = payload.get("hours")
    if not all([person_id, leave_date, leave_type, hours]):
        return jsonify({"success": False, "error": "person_id, leave_date, leave_type, hours are required"}), 400
    try:
        person_id = int(person_id)
        hours = float(hours)
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "person_id must be int and hours must be number"}), 400
    service = get_leave_service()
    record_id = service.create_leave(
        person_id=person_id,
        leave_date=leave_date,
        leave_type=leave_type,
        hours=hours,
        reason=payload.get("reason"),
    )
    return jsonify({"success": True, "data": {"record_id": record_id}})


@api_bp.route("/leave/<int:record_id>", methods=["PUT"])
def update_leave(record_id: int):
    payload = request.get_json() or {}
    hours = payload.get("hours")
    try:
        hours_value = float(hours) if hours is not None else None
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "hours must be a number"}), 400
    approver_id = payload.get("approver_person_id")
    if approver_id is not None:
        try:
            approver_id = int(approver_id)
        except (TypeError, ValueError):
            return jsonify({"success": False, "error": "approver_person_id must be int"}), 400
    service = get_leave_service()
    updated = service.update_leave(
        record_id=record_id,
        leave_type=payload.get("leave_type"),
        hours=hours_value,
        status=payload.get("status"),
        approver_person_id=approver_id,
        reason=payload.get("reason"),
    )
    if not updated:
        return jsonify({"success": False, "error": "leave record not found"}), 404
    return jsonify({"success": True})


@api_bp.route("/leave/<int:record_id>", methods=["DELETE"])
def delete_leave(record_id: int):
    service = get_leave_service()
    deleted = service.delete_leave(record_id)
    if not deleted:
        return jsonify({"success": False, "error": "leave record not found"}), 404
    return jsonify({"success": True})

