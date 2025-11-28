"""
Web routes for person management UI
"""
from __future__ import annotations

from flask import Blueprint, render_template, redirect, url_for

web_bp = Blueprint("web", __name__)


@web_bp.route("/")
def index():
    return redirect(url_for("web.persons"))


@web_bp.route("/persons")
def persons():
    return render_template("persons.html", active_page="persons")


@web_bp.route("/attendance")
def attendance():
    return render_template("attendance.html", active_page="attendance")


@web_bp.route("/leave")
def leave():
    return render_template("leave.html", active_page="leave")

