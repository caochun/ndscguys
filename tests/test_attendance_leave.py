from __future__ import annotations

from pathlib import Path

from app.db import init_db
from app.services.person_service import PersonService
from app.services.attendance_service import AttendanceService
from app.services.leave_service import LeaveService


def setup_services(tmp_path: Path):
    db_path = tmp_path / "attendance_leave.db"
    init_db(str(db_path))
    person_service = PersonService(str(db_path))
    attendance_service = AttendanceService(str(db_path))
    leave_service = LeaveService(str(db_path))
    return str(db_path), person_service, attendance_service, leave_service


def test_attendance_service_crud(tmp_path):
    db_path, person_service, attendance_service, _ = setup_services(tmp_path)
    person_id = person_service.create_person({"name": "Alice", "id_card": "ID100"})
    record_id = attendance_service.create_attendance(
        person_id=person_id,
        date="2025-01-01",
        check_in_time="09:00",
        check_out_time="18:00",
        work_hours=8,
        overtime_hours=1,
        status="正常",
        note="test",
    )
    record = attendance_service.get_attendance(record_id)
    assert record["person_id"] == person_id
    assert record["work_hours"] == 8

    records = attendance_service.list_attendance(person_id, "2025-01-01", "2025-01-31")
    assert len(records) == 1

    updated = attendance_service.update_attendance(
        record_id, work_hours=7.5, note="updated note"
    )
    assert updated

    deleted = attendance_service.delete_attendance(record_id)
    assert deleted


def test_leave_service_crud(tmp_path):
    db_path, person_service, _, leave_service = setup_services(tmp_path)
    requester_id = person_service.create_person({"name": "Bob", "id_card": "ID200"})
    approver_id = person_service.create_person({"name": "Manager", "id_card": "ID201"})

    record_id = leave_service.create_leave(
        person_id=requester_id,
        leave_date="2025-02-10",
        leave_type="事假",
        hours=8,
        reason="personal",
    )

    records = leave_service.list_leave(requester_id, "2025-02-01", "2025-02-28")
    assert len(records) == 1
    assert records[0]["leave_type"] == "事假"

    updated = leave_service.update_leave(
        record_id,
        status="已批准",
        approver_person_id=approver_id,
        reason="approved",
    )
    assert updated

    deleted = leave_service.delete_leave(record_id)
    assert deleted

