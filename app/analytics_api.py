"""
经营分析 API - 聚合统计查询
"""
from __future__ import annotations

import sqlite3
from datetime import date

from flask import Blueprint, current_app, jsonify, request

analytics_api_bp = Blueprint("analytics_api", __name__)


def _get_conn() -> sqlite3.Connection:
    db_path = current_app.config["DATABASE_PATH"]
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _month_offset(base: date, offset: int) -> str:
    """返回 base 日期偏移 offset 个月后的 YYYY-MM 字符串（offset 可负）"""
    total = base.year * 12 + base.month - 1 + offset
    return f"{total // 12:04d}-{total % 12 + 1:02d}"


# ---- 公共 CTE：各实体最新状态 ----
_LATEST_PAYMENT_ITEMS = """
WITH latest_pi AS (
    SELECT pi.id,
           CAST(json_extract(h.data, '$.client_contract_id') AS INTEGER) AS client_contract_id,
           json_extract(h.data, '$.period')               AS period,
           CAST(json_extract(h.data, '$.amount') AS REAL)  AS amount,
           json_extract(h.data, '$.status')                AS status,
           json_extract(h.data, '$.planned_payment_date')  AS planned_payment_date,
           json_extract(h.data, '$.actual_payment_date')   AS actual_payment_date
    FROM payment_items pi
    JOIN payment_item_history h ON h.twin_id = pi.id
    WHERE h.version = (
        SELECT MAX(v.version) FROM payment_item_history v WHERE v.twin_id = pi.id
    )
)
"""

_LATEST_CONTRACTS = """
WITH latest_cc AS (
    SELECT cc.id,
           json_extract(h.data, '$.contract_name')                 AS contract_name,
           json_extract(h.data, '$.client_company')                AS client_company,
           CAST(json_extract(h.data, '$.contract_amount') AS REAL) AS contract_amount,
           json_extract(h.data, '$.status')                        AS status
    FROM client_contracts cc
    JOIN client_contract_history h ON h.twin_id = cc.id
    WHERE h.version = (
        SELECT MAX(v.version) FROM client_contract_history v WHERE v.twin_id = cc.id
    )
)
"""

_LATEST_PROJECTS = """
WITH latest_ip AS (
    SELECT ip.id,
           json_extract(h.data, '$.name')            AS name,
           json_extract(h.data, '$.status')          AS status,
           json_extract(h.data, '$.project_manager') AS project_manager
    FROM internal_projects ip
    JOIN internal_project_history h ON h.twin_id = ip.id
    WHERE h.version = (
        SELECT MAX(v.version) FROM internal_project_history v WHERE v.twin_id = ip.id
    )
)
"""


@analytics_api_bp.route("/analytics/overview")
def overview():
    """应收账款概览 KPI"""
    today = date.today().isoformat()
    try:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute(f"""
            {_LATEST_CONTRACTS}
            SELECT COALESCE(SUM(contract_amount), 0) FROM latest_cc
        """)
        total_contract_amount = cur.fetchone()[0] or 0

        cur.execute(f"""
            {_LATEST_PAYMENT_ITEMS}
            SELECT
                COALESCE(SUM(amount), 0) AS total,
                COALESCE(SUM(CASE WHEN status = '已付款' THEN amount ELSE 0 END), 0) AS collected,
                COALESCE(SUM(CASE WHEN status = '待付款' THEN amount ELSE 0 END), 0) AS pending,
                COALESCE(SUM(CASE WHEN status = '待付款'
                                   AND planned_payment_date IS NOT NULL
                                   AND planned_payment_date < ? THEN amount ELSE 0 END), 0) AS overdue,
                COUNT(CASE WHEN status = '待付款'
                            AND planned_payment_date IS NOT NULL
                            AND planned_payment_date < ? THEN 1 END) AS overdue_count
            FROM latest_pi
        """, (today, today))
        row = cur.fetchone()
        conn.close()

        return jsonify({
            "success": True,
            "data": {
                "total_contract_amount": round(total_contract_amount, 2),
                "total_payment_amount":  round(row[0], 2),
                "collected_amount":      round(row[1], 2),
                "pending_amount":        round(row[2], 2),
                "overdue_amount":        round(row[3], 2),
                "overdue_count":         row[4],
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@analytics_api_bp.route("/analytics/collection-trend")
def collection_trend():
    """近 N 个月收款趋势（计划 vs 实收）"""
    months = int(request.args.get("months", 12))
    today = date.today()
    month_list = [_month_offset(today, -(months - 1 - i)) for i in range(months)]

    try:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute(f"""
            {_LATEST_PAYMENT_ITEMS}
            SELECT substr(actual_payment_date, 1, 7) AS month,
                   COALESCE(SUM(amount), 0)          AS total
            FROM latest_pi
            WHERE status = '已付款'
              AND actual_payment_date IS NOT NULL
              AND substr(actual_payment_date, 1, 7) >= ?
            GROUP BY month
        """, (month_list[0],))
        collected_map = {row[0]: row[1] for row in cur.fetchall()}

        cur.execute(f"""
            {_LATEST_PAYMENT_ITEMS}
            SELECT substr(planned_payment_date, 1, 7) AS month,
                   COALESCE(SUM(amount), 0)           AS total
            FROM latest_pi
            WHERE planned_payment_date IS NOT NULL
              AND substr(planned_payment_date, 1, 7) >= ?
            GROUP BY month
        """, (month_list[0],))
        planned_map = {row[0]: row[1] for row in cur.fetchall()}

        conn.close()
        return jsonify({
            "success": True,
            "data": {
                "months":    month_list,
                "collected": [round(collected_map.get(m, 0), 2) for m in month_list],
                "planned":   [round(planned_map.get(m, 0), 2)   for m in month_list],
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@analytics_api_bp.route("/analytics/cashflow-forecast")
def cashflow_forecast():
    """未来 N 个月现金流预测（待付款项按 planned_payment_date）"""
    months = int(request.args.get("months", 6))
    today = date.today()
    month_list = [_month_offset(today, i) for i in range(months)]

    try:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute(f"""
            {_LATEST_PAYMENT_ITEMS}
            SELECT substr(planned_payment_date, 1, 7) AS month,
                   COALESCE(SUM(amount), 0)           AS total
            FROM latest_pi
            WHERE status = '待付款'
              AND planned_payment_date IS NOT NULL
              AND substr(planned_payment_date, 1, 7) BETWEEN ? AND ?
            GROUP BY month
        """, (month_list[0], month_list[-1]))
        forecast_map = {row[0]: row[1] for row in cur.fetchall()}
        conn.close()

        return jsonify({
            "success": True,
            "data": {
                "months":   month_list,
                "expected": [round(forecast_map.get(m, 0), 2) for m in month_list],
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@analytics_api_bp.route("/analytics/clients")
def clients():
    """客户维度分析（按 client_company 聚合）"""
    try:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute(f"""
            {_LATEST_CONTRACTS},
            {_LATEST_PAYMENT_ITEMS.replace('WITH ', '')}
            SELECT
                cc.client_company,
                COUNT(DISTINCT cc.id)                                                    AS contract_count,
                COALESCE(SUM(cc.contract_amount), 0)                                     AS contract_amount,
                COALESCE(SUM(CASE WHEN pi.status = '已付款' THEN pi.amount ELSE 0 END), 0) AS collected,
                COALESCE(SUM(CASE WHEN pi.status = '待付款' THEN pi.amount ELSE 0 END), 0) AS pending
            FROM latest_cc cc
            LEFT JOIN latest_pi pi ON pi.client_contract_id = cc.id
            WHERE cc.client_company IS NOT NULL AND cc.client_company != ''
            GROUP BY cc.client_company
            ORDER BY contract_amount DESC
        """)
        rows = cur.fetchall()
        conn.close()

        data = []
        for r in rows:
            collected = r[3] or 0
            pending = r[4] or 0
            pi_total = collected + pending
            data.append({
                "client_company":   r[0],
                "contract_count":   r[1],
                "contract_amount":  round(r[2] or 0, 2),
                "collected_amount": round(collected, 2),
                "pending_amount":   round(pending, 2),
                "collection_rate":  round(collected / pi_total, 4) if pi_total > 0 else 0,
            })

        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@analytics_api_bp.route("/analytics/projects")
def projects():
    """项目维度收入分析"""
    try:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute(f"""
            {_LATEST_PROJECTS},
            {_LATEST_PAYMENT_ITEMS.replace('WITH ', '')}
            SELECT
                ip.id,
                ip.name,
                ip.status,
                ip.project_manager,
                COUNT(DISTINCT assoc.payment_item_id)                                    AS pi_count,
                COALESCE(SUM(pi.amount), 0)                                              AS total_revenue,
                COALESCE(SUM(CASE WHEN pi.status = '已付款' THEN pi.amount ELSE 0 END), 0) AS collected,
                COALESCE(SUM(CASE WHEN pi.status = '待付款' THEN pi.amount ELSE 0 END), 0) AS pending
            FROM latest_ip ip
            LEFT JOIN internal_project_payment_activities assoc
                   ON assoc.internal_project_id = ip.id
            LEFT JOIN latest_pi pi ON pi.id = assoc.payment_item_id
            GROUP BY ip.id
            ORDER BY total_revenue DESC
        """)
        rows = cur.fetchall()
        conn.close()

        data = [
            {
                "project_id":         r[0],
                "project_name":       r[1] or f"项目 {r[0]}",
                "status":             r[2],
                "project_manager":    r[3],
                "payment_item_count": r[4],
                "total_revenue":      round(r[5], 2),
                "collected_revenue":  round(r[6], 2),
                "pending_revenue":    round(r[7], 2),
            }
            for r in rows
        ]

        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
