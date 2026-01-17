"""
API routes for person state management
"""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from app.services.person_service import PersonService
from app.services.attendance_service import AttendanceService
from app.services.leave_service import LeaveService
from app.services.project_service import ProjectService
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


def get_project_service() -> ProjectService:
    db_path = current_app.config["DATABASE_PATH"]
    return ProjectService(db_path)


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


@api_bp.route("/payroll/batch-confirm", methods=["POST"])
def payroll_batch_confirm():
    """确认薪酬批量发放：创建批次和明细到数据库。"""
    service = get_person_service()
    payload = request.get_json() or {}
    
    # 批次参数
    batch_params = {
        "batch_period": payload.get("batch_period"),
        "effective_date": payload.get("effective_date"),
        "target_company": payload.get("target_company"),
        "target_department": payload.get("target_department"),
        "target_employee_type": payload.get("target_employee_type"),
        "note": payload.get("note"),
    }
    
    if not batch_params["batch_period"]:
        return jsonify({"success": False, "error": "batch_period is required"}), 400
    
    # 明细数据
    items = payload.get("items") or []
    if not items:
        return jsonify({"success": False, "error": "items is required"}), 400
    
    # 创建批次和明细
    result = service.confirm_payroll_batch(batch_params, items)
    return jsonify({"success": True, "data": result})


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


# ========== 项目相关 API ==========

@api_bp.route("/projects", methods=["GET"])
def list_projects():
    service = get_project_service()
    projects = service.list_projects()
    return jsonify({"success": True, "data": projects})


@api_bp.route("/projects", methods=["POST"])
def create_project():
    service = get_project_service()
    payload = request.get_json() or {}
    project_data = payload.get("project") or payload
    try:
        project_id = service.create_project(project_data)
    except PayloadValidationError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    return jsonify({"success": True, "data": {"project_id": project_id}})


@api_bp.route("/projects/<int:project_id>", methods=["GET"])
def get_project(project_id: int):
    service = get_project_service()
    result = service.get_project(project_id)
    if not result:
        return jsonify({"success": False, "error": "project not found"}), 404
    return jsonify({"success": True, "data": result})


@api_bp.route("/projects/<int:project_id>", methods=["POST"])
def append_project_change(project_id: int):
    """追加一条项目信息变更"""
    service = get_project_service()
    payload = request.get_json() or {}
    project_data = payload.get("project") or payload
    try:
        service.append_project_change(project_id, project_data)
    except PayloadValidationError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    return jsonify({"success": True})


@api_bp.route("/projects/<int:project_id>/persons", methods=["GET"])
def get_project_persons(project_id: int):
    """获取项目参与的所有人员"""
    service = get_person_service()
    persons = service.get_project_persons(project_id)
    return jsonify({"success": True, "data": persons})


# ========== 人员参与项目相关 API ==========

@api_bp.route("/persons/<int:person_id>/projects", methods=["GET"])
def get_person_projects(person_id: int):
    """获取人员参与的所有项目"""
    service = get_person_service()
    projects = service.get_person_projects(person_id)
    return jsonify({"success": True, "data": projects})


@api_bp.route("/persons/<int:person_id>/projects", methods=["POST"])
def append_person_project_change(person_id: int):
    """追加一条人员参与项目信息变更"""
    service = get_person_service()
    payload = request.get_json() or {}
    project_data = payload.get("project") or payload
    try:
        project_id = project_data.get("project_id")
        if not project_id:
            return jsonify({"success": False, "error": "project_id is required"}), 400
        service.append_person_project_change(person_id, project_id, project_data)
    except PayloadValidationError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    return jsonify({"success": True})


@api_bp.route("/persons/<int:person_id>/projects/<int:project_id>/history", methods=["GET"])
def get_person_project_history(person_id: int, project_id: int):
    """获取人员参与项目的历史记录"""
    service = get_person_service()
    history = service.get_person_project_history(person_id, project_id)
    return jsonify({"success": True, "data": history})


# ========== 人员项目状态相关 API ==========

@api_bp.route("/persons/<int:person_id>/project-status", methods=["GET"])
def get_person_project_status(person_id: int):
    """获取人员项目状态（最新）"""
    service = get_person_service()
    status = service.get_person_project_status(person_id)
    if status is None:
        return jsonify({"success": False, "error": "person project status not found"}), 404
    return jsonify({"success": True, "data": status})


@api_bp.route("/persons/<int:person_id>/project-status", methods=["POST"])
def append_person_project_status_change(person_id: int):
    """追加一条人员项目状态变更"""
    service = get_person_service()
    payload = request.get_json() or {}
    status_data = payload.get("status") or payload
    try:
        service.append_person_project_status_change(person_id, status_data)
    except PayloadValidationError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    return jsonify({"success": True})


# ========== 薪资计算 DSL 管理 API ==========

@api_bp.route("/payroll/dsl-rules", methods=["GET"])
def list_payroll_dsl_rules():
    """列出所有薪资计算规则"""
    import sqlite3
    from flask import current_app
    
    db_path = current_app.config["DATABASE_PATH"]
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT id, name, version, is_active, effective_date, description, 
               created_at, updated_at
        FROM payroll_calculation_rules
        ORDER BY updated_at DESC
        """
    )
    rows = cursor.fetchall()
    rules = [dict(row) for row in rows]
    conn.close()
    
    return jsonify({"success": True, "data": rules})


@api_bp.route("/payroll/dsl-rules/<int:rule_id>", methods=["GET"])
def get_payroll_dsl_rule(rule_id: int):
    """获取指定规则详情"""
    import sqlite3
    from flask import current_app
    
    db_path = current_app.config["DATABASE_PATH"]
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT id, name, version, dsl_config, is_active, effective_date, 
               description, created_at, updated_at
        FROM payroll_calculation_rules
        WHERE id = ?
        """,
        (rule_id,)
    )
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return jsonify({"success": False, "error": "Rule not found"}), 404
    
    rule = dict(row)
    return jsonify({"success": True, "data": rule})


@api_bp.route("/payroll/dsl-rules", methods=["POST"])
def create_payroll_dsl_rule():
    """创建新的薪资计算规则"""
    import sqlite3
    from flask import current_app
    
    payload = request.get_json() or {}
    name = payload.get("name")
    version = payload.get("version", "1.0")
    dsl_config = payload.get("dsl_config")
    description = payload.get("description", "")
    effective_date = payload.get("effective_date")
    is_active = payload.get("is_active", 0)
    
    if not name or not dsl_config:
        return jsonify({"success": False, "error": "name and dsl_config are required"}), 400
    
    # 验证 DSL 配置（只需要验证 configs 部分）
    try:
        import yaml
        if isinstance(dsl_config, str):
            config_dict = yaml.safe_load(dsl_config)
        else:
            config_dict = dsl_config
        
        # 验证配置结构
        if "configs" not in config_dict:
            return jsonify({"success": False, "error": "Missing 'configs' section"}), 400
        
        configs = config_dict.get("configs", {})
        required_keys = ["performance_factors", "split_ratios", "probation_discount", "default_work_days"]
        missing_keys = [key for key in required_keys if key not in configs]
        if missing_keys:
            return jsonify({"success": False, "error": f"Missing required config keys: {', '.join(missing_keys)}"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Invalid DSL config: {str(e)}"}), 400
    
    db_path = current_app.config["DATABASE_PATH"]
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 如果设置为激活，先取消其他规则的激活状态
    if is_active:
        cursor.execute(
            "UPDATE payroll_calculation_rules SET is_active = 0 WHERE is_active = 1"
        )
    
    # 如果 dsl_config 是字典，转换为 YAML 字符串
    if isinstance(dsl_config, dict):
        import yaml
        dsl_config = yaml.dump(dsl_config, allow_unicode=True)
    
    cursor.execute(
        """
        INSERT INTO payroll_calculation_rules 
        (name, version, dsl_config, is_active, effective_date, description)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (name, version, dsl_config, is_active, effective_date, description)
    )
    rule_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "data": {"rule_id": rule_id}})


@api_bp.route("/payroll/dsl-rules/<int:rule_id>", methods=["PUT"])
def update_payroll_dsl_rule(rule_id: int):
    """更新薪资计算规则"""
    import sqlite3
    from flask import current_app
    
    payload = request.get_json() or {}
    
    db_path = current_app.config["DATABASE_PATH"]
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查规则是否存在
    cursor.execute("SELECT id FROM payroll_calculation_rules WHERE id = ?", (rule_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"success": False, "error": "Rule not found"}), 404
    
    # 构建更新语句
    updates = []
    values = []
    
    if "name" in payload:
        updates.append("name = ?")
        values.append(payload["name"])
    
    if "version" in payload:
        updates.append("version = ?")
        values.append(payload["version"])
    
    if "dsl_config" in payload:
        dsl_config = payload["dsl_config"]
        # 验证 DSL 配置（只需要验证 configs 部分）
        try:
            import yaml
            if isinstance(dsl_config, str):
                config_dict = yaml.safe_load(dsl_config)
            else:
                config_dict = dsl_config
            
            # 验证配置结构
            if "configs" not in config_dict:
                conn.close()
                return jsonify({"success": False, "error": "Missing 'configs' section"}), 400
            
            configs = config_dict.get("configs", {})
            required_keys = ["performance_factors", "split_ratios", "probation_discount", "default_work_days"]
            missing_keys = [key for key in required_keys if key not in configs]
            if missing_keys:
                conn.close()
                return jsonify({"success": False, "error": f"Missing required config keys: {', '.join(missing_keys)}"}), 400
        except Exception as e:
            conn.close()
            return jsonify({"success": False, "error": f"Invalid DSL config: {str(e)}"}), 400
        
        # 转换为 YAML 字符串
        if isinstance(dsl_config, dict):
            import yaml
            dsl_config = yaml.dump(dsl_config, allow_unicode=True)
        
        updates.append("dsl_config = ?")
        values.append(dsl_config)
    
    if "description" in payload:
        updates.append("description = ?")
        values.append(payload.get("description", ""))
    
    if "effective_date" in payload:
        updates.append("effective_date = ?")
        values.append(payload.get("effective_date"))
    
    if "is_active" in payload:
        is_active = payload["is_active"]
        updates.append("is_active = ?")
        values.append(is_active)
        
        # 如果设置为激活，取消其他规则的激活状态
        if is_active:
            cursor.execute(
                "UPDATE payroll_calculation_rules SET is_active = 0 WHERE is_active = 1 AND id != ?",
                (rule_id,)
            )
    
    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(rule_id)
        
        cursor.execute(
            f"UPDATE payroll_calculation_rules SET {', '.join(updates)} WHERE id = ?",
            values
        )
        conn.commit()
    
    conn.close()
    return jsonify({"success": True})


@api_bp.route("/payroll/dsl-rules/<int:rule_id>/activate", methods=["POST"])
def activate_payroll_dsl_rule(rule_id: int):
    """激活指定的薪资计算规则"""
    import sqlite3
    from flask import current_app
    
    db_path = current_app.config["DATABASE_PATH"]
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查规则是否存在
    cursor.execute("SELECT id FROM payroll_calculation_rules WHERE id = ?", (rule_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"success": False, "error": "Rule not found"}), 404
    
    # 取消其他规则的激活状态
    cursor.execute(
        "UPDATE payroll_calculation_rules SET is_active = 0 WHERE is_active = 1"
    )
    
    # 激活指定规则
    cursor.execute(
        "UPDATE payroll_calculation_rules SET is_active = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (rule_id,)
    )
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})


@api_bp.route("/payroll/dsl-rules/<int:rule_id>", methods=["DELETE"])
def delete_payroll_dsl_rule(rule_id: int):
    """删除薪资计算规则"""
    import sqlite3
    from flask import current_app
    
    db_path = current_app.config["DATABASE_PATH"]
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM payroll_calculation_rules WHERE id = ?", (rule_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    if not deleted:
        return jsonify({"success": False, "error": "Rule not found"}), 404
    
    return jsonify({"success": True})


@api_bp.route("/payroll/dsl-rules/validate", methods=["POST"])
def validate_payroll_dsl_rule():
    """验证 DSL 配置语法"""
    payload = request.get_json() or {}
    dsl_config = payload.get("dsl_config")
    
    if not dsl_config:
        return jsonify({"success": False, "error": "dsl_config is required"}), 400
    
    try:
        import yaml
        
        if isinstance(dsl_config, str):
            config_dict = yaml.safe_load(dsl_config)
        else:
            config_dict = dsl_config
        
        # 验证配置结构（只需要有 configs 部分）
        if "configs" not in config_dict:
            return jsonify({
                "success": False,
                "error": "Missing 'configs' section",
                "data": {"valid": False}
            }), 400
        
        # 验证必要的配置项
        configs = config_dict.get("configs", {})
        required_keys = ["performance_factors", "split_ratios", "probation_discount", "default_work_days"]
        missing_keys = [key for key in required_keys if key not in configs]
        if missing_keys:
            return jsonify({
                "success": False,
                "error": f"Missing required config keys: {', '.join(missing_keys)}",
                "data": {"valid": False}
            }), 400
        
        return jsonify({
            "success": True,
            "data": {
                "valid": True,
                "name": config_dict.get("name", ""),
                "version": config_dict.get("version", ""),
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "data": {"valid": False}
        }), 400


@api_bp.route("/payroll/config/performance-factors", methods=["GET"])
def get_performance_factors():
    """获取绩效系数配置（从激活的DSL规则或默认配置）"""
    service = get_person_service()
    
    # 从 DSL 配置获取
    if service.dsl_interpreter:
        perf_factors = service.dsl_interpreter.get("performance_factors", {})
    else:
        # 默认值
        perf_factors = {
            "A": 1.2,
            "B": 1.0,
            "C": 0.8,
            "D": 0.5,
            "E": 0.0,
            "default": 1.0,
        }
    
    # 只返回 key-value 映射，排除 default
    factors = {k: v for k, v in perf_factors.items() if k != "default"}
    
    return jsonify({"success": True, "data": factors})


@api_bp.route("/payroll/dsl-rules/default", methods=["GET"])
def get_default_payroll_dsl_rule():
    """获取默认的 DSL 配置（从 config/payroll_rules.yaml）"""
    from pathlib import Path
    import yaml
    
    try:
        config_path = Path(__file__).parent.parent / "config" / "payroll_rules.yaml"
        
        if not config_path.exists():
            return jsonify({
                "success": False,
                "error": "Default config file not found"
            }), 404
        
        with open(config_path, 'r', encoding='utf-8') as f:
            dsl_content = f.read()
        
        # 解析 YAML 以获取元数据
        config_dict = yaml.safe_load(dsl_content)
        
        return jsonify({
            "success": True,
            "data": {
                "dsl_config": dsl_content,
                "name": config_dict.get("name", "默认薪资计算规则"),
                "version": config_dict.get("version", "1.0"),
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to load default config: {str(e)}"
        }), 500

