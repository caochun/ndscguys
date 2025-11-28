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
    try:
        person_id = service.create_person(
            basic_data,
            position_data,
            salary_data,
            social_security_data,
            housing_fund_data,
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

