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


@web_bp.route("/housing-fund/batch")
def housing_fund_batch():
    return render_template("housing_fund_batch.html", active_page="housing_batch")


@web_bp.route("/social-security/batch")
def social_security_batch():
    return render_template("social_security_batch.html", active_page="social_batch")


@web_bp.route("/payroll/batch")
def payroll_batch():
    return render_template("payroll_batch.html", active_page="payroll_batch")


@web_bp.route("/tax-deduction/batch")
def tax_deduction_batch():
    return render_template("tax_deduction_batch.html", active_page="tax_deduction_batch")


@web_bp.route("/statistics")
def statistics():
    return render_template("statistics.html", active_page="statistics")

