"""
API routes for person state management
"""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from app.services.person_service import PersonService

api_bp = Blueprint("api", __name__)


def get_person_service() -> PersonService:
    db_path = current_app.config["DATABASE_PATH"]
    return PersonService(db_path)


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
    person_id = service.create_person(basic_data, position_data)
    return jsonify({"success": True, "data": {"person_id": person_id}})


@api_bp.route("/persons/<int:person_id>", methods=["GET"])
def get_person(person_id: int):
    service = get_person_service()
    result = service.get_person(person_id)
    if not result:
        return jsonify({"success": False, "error": "person not found"}), 404
    return jsonify({"success": True, "data": result})

