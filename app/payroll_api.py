"""
工资计算与发放 API、个税计算步骤 API
"""
from __future__ import annotations

import json
import ast
import operator
import re
from pathlib import Path
from typing import Dict, Any

from flask import Blueprint, request
from config import Config

from app.services.payroll_service import PayrollService
from app.services.twin_service import TwinService
from app.schema.loader import SchemaLoader

payroll_api_bp = Blueprint("payroll_api", __name__)


def get_payroll_service() -> PayrollService:
    """获取 PayrollService 实例"""
    return PayrollService(db_path=str(Config.DATABASE_PATH))


def get_twin_service() -> TwinService:
    """获取 TwinService 实例"""
    return TwinService(db_path=str(Config.DATABASE_PATH))


def get_schema_loader() -> SchemaLoader:
    """获取 SchemaLoader 实例"""
    return SchemaLoader()


def standard_response(success: bool, data=None, error: str = None, status_code: int = 200):
    """标准响应格式"""
    from flask import jsonify
    response = {"success": success}
    if data is not None:
        response["data"] = data
    if error:
        response["error"] = error
    if isinstance(data, list):
        response["count"] = len(data)
    return jsonify(response), status_code


# ==================== 工资计算与发放 API ====================

@payroll_api_bp.route("/payroll/calculate", methods=["POST"])
def calculate_payroll():
    """
    计算单个人员在指定周期的工资（仅计算，不写库）
    
    POST /api/payroll/calculate
    Body: { "person_id": 1, "company_id": 2, "period": "2024-01" }
    """
    try:
        payload = request.get_json() or {}
        person_id = payload.get("person_id")
        company_id = payload.get("company_id")
        period = payload.get("period")
        
        if not all([person_id, company_id, period]):
            return standard_response(False, error="person_id, company_id, period 为必填字段", status_code=400)
        
        service = get_payroll_service()
        result = service.calculate_payroll(int(person_id), int(company_id), str(period))
        return standard_response(True, result)
    except ValueError as e:
        return standard_response(False, error=str(e), status_code=400)
    except Exception as e:
        return standard_response(False, error=str(e), status_code=500)


@payroll_api_bp.route("/payroll/generate", methods=["POST"])
def generate_payroll():
    """
    计算并生成工资单（person_company_payroll）
    
    POST /api/payroll/generate
    Body: { "person_id": 1, "company_id": 2, "period": "2024-01" }
    """
    try:
        payload = request.get_json() or {}
        person_id = payload.get("person_id")
        company_id = payload.get("company_id")
        period = payload.get("period")
        
        if not all([person_id, company_id, period]):
            return standard_response(False, error="person_id, company_id, period 为必填字段", status_code=400)
        
        service = get_payroll_service()
        result = service.generate_payroll(int(person_id), int(company_id), str(period))
        return standard_response(True, result, status_code=201)
    except ValueError as e:
        return standard_response(False, error=str(e), status_code=400)
    except Exception as e:
        return standard_response(False, error=str(e), status_code=500)


@payroll_api_bp.route("/payroll/formula", methods=["GET", "POST"])
def payroll_formula():
    """
    保存或加载工资计算公式（应发薪资 + 社保公积金扣除 + 个税扣除）
    
    GET /api/payroll/formula - 加载保存的公式
    POST /api/payroll/formula - 保存公式
    Body: {"gross_formula": "...", "deduction_formula": "...", "tax_formula": "..."}
    兼容旧版: formula 视为 gross_formula
    """
    try:
        formula_file = Config.BASE_DIR / "data" / "payroll_formula.json"
        formula_file.parent.mkdir(parents=True, exist_ok=True)
        
        if request.method == "GET":
            if formula_file.exists():
                with open(formula_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "gross_formula" not in data and "formula" in data:
                        data["gross_formula"] = data.pop("formula", "")
                    if "deduction_formula" not in data:
                        data["deduction_formula"] = ""
                    if "tax_formula" not in data:
                        data["tax_formula"] = ""
                    return standard_response(True, data)
            return standard_response(True, {"gross_formula": "", "deduction_formula": "", "tax_formula": ""})
        
        elif request.method == "POST":
            payload = request.get_json() or {}
            gross = payload.get("gross_formula", payload.get("formula", ""))
            deduction = payload.get("deduction_formula", "")
            tax = payload.get("tax_formula", "")
            with open(formula_file, "w", encoding="utf-8") as f:
                json.dump({"gross_formula": gross, "deduction_formula": deduction, "tax_formula": tax}, f, ensure_ascii=False, indent=2)
            return standard_response(True, {"message": "公式已保存"})
    
    except Exception as e:
        return standard_response(False, error=str(e), status_code=500)


# ==================== 工资公式试算 & 变量列表 ====================


def _make_eval_key(var_name: str) -> str:
    """
    将原始变量名转换为安全的 eval 变量名（Python 标识符）
    例如：person_company_employment.salary -> v_person_company_employment_salary
    """
    safe = re.sub(r"[^0-9a-zA-Z_]", "_", var_name)
    if not safe or safe[0].isdigit():
        safe = f"v_{safe}"
    elif not safe.startswith("v_"):
        safe = f"v_{safe}"
    return safe


@payroll_api_bp.route("/schema/variables", methods=["GET"])
def list_schema_variables():
    """
    列出可用于工资公式的变量清单（基于 Twin Schema）
    
    返回示例：
    [
      {
        "twin": "person_company_employment",
        "twin_label": "人员-公司聘用活动",
        "fields": [
          {
            "key": "person_company_employment.salary",
            "label": "薪资",
            "full_label": "人员-公司聘用活动.薪资"
          },
          ...
        ]
      },
      ...
    ]
    """
    try:
        loader = get_schema_loader()
        all_twins = loader.get_all_twins()

        result = []
        # 不需要在公式变量中出现的 Twin 名称
        excluded_twins = {
            "internal_project",
            "client_contract",
            "order",
            "person_order_participation",
            "person_company_payroll",
        }

        for twin_name, twin_def in all_twins.items():
            if twin_name in excluded_twins:
                continue
            twin_label = twin_def.get("label", twin_name)
            fields_def: Dict[str, Any] = twin_def.get("fields", {}) or {}

            fields = []
            for field_name, field_def in fields_def.items():
                field_type = field_def.get("type")
                # 只暴露数值型和枚举型字段，且跳过 reference 字段（如 person_id、company_id）
                if field_type == "reference":
                    continue
                if field_type not in ("decimal", "number", "integer", "int", "float", "enum"):
                    continue

                field_label = field_def.get("label", field_name)
                raw_key = f"{twin_name}.{field_name}"
                eval_key = _make_eval_key(raw_key)

                fields.append(
                    {
                        "key": raw_key,
                        "eval_key": eval_key,
                        "label": field_label,
                        "full_label": f"{twin_label}.{field_label}",
                    }
                )

            if fields:
                result.append(
                    {
                        "twin": twin_name,
                        "twin_label": twin_label,
                        "fields": fields,
                    }
                )

        # 确保考勤记录（事假、病假、奖惩）在可选变量中
        if not any(g.get("twin") == "person_company_attendance_record" for g in result):
            att_schema = loader.get_twin_schema("person_company_attendance_record")
            if att_schema:
                att_label = att_schema.get("label", "人员-公司考勤记录")
                att_fields_def = att_schema.get("fields", {})
                att_fields = []
                for fn in ("sick_leave_days", "personal_leave_days", "reward_punishment_amount"):
                    if fn not in att_fields_def:
                        continue
                    fd = att_fields_def[fn]
                    if fd.get("type") not in ("decimal", "number", "integer", "int", "float", "enum"):
                        continue
                    raw_key = f"person_company_attendance_record.{fn}"
                    eval_key = _make_eval_key(raw_key)
                    att_fields.append({
                        "key": raw_key,
                        "eval_key": eval_key,
                        "label": fd.get("label", fn),
                        "full_label": f"{att_label}.{fd.get('label', fn)}",
                    })
                if att_fields:
                    result.append({
                        "twin": "person_company_attendance_record",
                        "twin_label": att_label,
                        "fields": att_fields,
                    })

        return standard_response(True, result)
    except Exception as e:
        return standard_response(False, error=str(e), status_code=500)


@payroll_api_bp.route("/payroll/eval-formula", methods=["POST"])
def eval_payroll_formula():
    """
    按用户提供的公式对单个人员当期工资进行试算（不写库）
    
    POST /api/payroll/eval-formula
    Body:
    {
      "person_id": 1,
      "company_id": 2,
      "period": "2024-01",
      "expression": "base_salary + performance_bonus - tax_deduction"
    }
    """
    try:
        payload = request.get_json() or {}
        person_id = payload.get("person_id")
        company_id = payload.get("company_id")
        period = payload.get("period")
        expression = payload.get("expression")

        if not all([person_id, company_id, period, expression]):
            return standard_response(
                False,
                error="person_id, company_id, period, expression 为必填字段",
                status_code=400,
            )

        service = get_payroll_service()

        # 先用现有逻辑计算一次工资，得到所有中间结果
        base_result = service.calculate_payroll(
            int(person_id), int(company_id), str(period)
        )

        # 构造变量字典：以现有返回字段为主
        variables: Dict[str, Any] = {}
        for k, v in base_result.items():
            variables[k] = v

        # 一些常用别名映射到 Twin 风格的 key，并生成 eval_key，供公式使用
        alias_map = {
            "person_company_employment.salary": "base_salary",
            "person_company_employment.salary_type": "salary_type",
            "person_assessment.grade": "assessment_grade",
            "person_company_social_security_base.base_amount": "social_security_base",
            "person_company_housing_fund_base.base_amount": "housing_fund_base",
        }
        for alias, real_key in alias_map.items():
            if real_key in base_result:
                eval_key = _make_eval_key(alias)
                variables[eval_key] = base_result[real_key]

        # 考勤记录变量：按 person_id, company_id, period 取当期的病假、事假、奖惩
        twin_service = get_twin_service()
        att_twins = twin_service.list_twins(
            "person_company_attendance_record",
            filters={"person_id": str(person_id), "company_id": str(company_id)},
        )
        if att_twins:
            activity_id = att_twins[0].get("id")
            if activity_id is not None:
                att_state = twin_service.state_dao.get_state_by_time_key(
                    "person_company_attendance_record", int(activity_id), str(period)
                )
                if att_state and att_state.data:
                    for fn in ("sick_leave_days", "personal_leave_days", "reward_punishment_amount"):
                        raw_key = f"person_company_attendance_record.{fn}"
                        eval_key = _make_eval_key(raw_key)
                        val = att_state.data.get(fn)
                        variables[eval_key] = float(val) if val is not None else 0.0

        # 评估表达式
        try:
            value = _safe_eval_expression(str(expression), variables)
        except ValueError as e:
            return standard_response(False, error=str(e), status_code=400)

        return standard_response(
            True,
            {
                "value": value,
                "variables": variables,
            },
        )
    except Exception as e:
        return standard_response(False, error=str(e), status_code=500)


def _safe_eval_expression(expression: str, variables: Dict[str, Any]) -> float:
    """
    安全地评估一个算术表达式。
    
    支持：
    - 变量：a-zA-Z0-9_ 和 点号（如 person_company_employment.salary）
    - 运算符：+ - * / 和括号
    - 函数：max, min, abs, round
    """
    grade_coef_map = {
        "A": 1.2,
        "B": 1.0,
        "C": 0.8,
        "D": 0.6,
        "E": 0.4,
    }

    def grade_coef(value: Any) -> float:
        """绩效等级系数映射函数（A-E -> 系数）"""
        key = str(value).strip().upper()
        return float(grade_coef_map.get(key, 1.0))

    allowed_funcs = {
        "max": max,
        "min": min,
        "abs": abs,
        "round": round,
        "grade_coef": grade_coef,
    }

    allowed_operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    class SafeEvaluator(ast.NodeVisitor):
        def visit(self, node):
            if isinstance(node, ast.Expression):
                return self.visit(node.body)
            if isinstance(node, ast.BinOp):
                if type(node.op) not in allowed_operators:
                    raise ValueError("不支持的运算符")
                left = self.visit(node.left)
                right = self.visit(node.right)
                return allowed_operators[type(node.op)](left, right)
            if isinstance(node, ast.UnaryOp):
                if type(node.op) not in allowed_operators:
                    raise ValueError("不支持的运算符")
                operand = self.visit(node.operand)
                return allowed_operators[type(node.op)](operand)
            if isinstance(node, ast.Num):  # 兼容 Python <3.8
                return node.n
            if isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)):
                    return node.value
                raise ValueError("仅支持数字常量")
            if isinstance(node, ast.Name):
                # 简单变量名
                return float(variables.get(node.id, 0.0) or 0.0)
            if isinstance(node, ast.Call):
                if not isinstance(node.func, ast.Name):
                    raise ValueError("仅支持简单函数调用")
                func_name = node.func.id
                if func_name not in allowed_funcs:
                    raise ValueError(f"不支持的函数: {func_name}")
                args = [self.visit(arg) for arg in node.args]
                return allowed_funcs[func_name](*args)
            if isinstance(node, ast.Attribute):
                # 不允许直接使用 Attribute 语法（如 obj.x），用户应使用变量名
                raise ValueError("不支持的表达式语法")
            if isinstance(node, ast.Subscript):
                raise ValueError("不支持的表达式语法")
            raise ValueError("表达式中包含不支持的语法")

    # 允许点号的变量名，通过在 Name 节点里直接查 variables
    # 这里依赖于前端插入的变量名整体作为一个 Name（不拆分点号），
    # 因此 expression 中变量名应是合法的 Python 标识符或用下划线代替点。
    tree = ast.parse(expression, mode="eval")
    evaluator = SafeEvaluator()
    result = evaluator.visit(tree)
    return float(result)


# ==================== 个税计算步骤（14 步） ====================

# 14 步定义：步骤号、字段名、数据来源、默认公式（仅“本月公式”有）
TAX_STEP_DEFINITIONS = [
    {"step": 1, "field_name": "专项累计扣除", "source": "formula", "default_formula": "social_security_deduction + housing_fund_deduction"},
    {"step": 2, "field_name": "专项附加扣除合计", "source": "formula", "default_formula": "tax_deduction_total"},
    {"step": 3, "field_name": "税前扣除项目合计", "source": "formula", "default_formula": "step_1 + step_2"},
    {"step": 4, "field_name": "上月累计专项扣除合计", "source": "prev_month", "default_formula": ""},
    {"step": 5, "field_name": "上月薪资的累计专项合计(不含附加)", "source": "formula", "default_formula": "step_6 - step_2"},
    {"step": 6, "field_name": "累计扣除项目合计", "source": "formula", "default_formula": "step_3 + step_4"},
    {"step": 7, "field_name": "上月累计收入", "source": "prev_month", "default_formula": ""},
    {"step": 8, "field_name": "累计收入", "source": "formula", "default_formula": "step_7 + base_amount"},
    {"step": 9, "field_name": "减除费用", "source": "formula", "default_formula": "5000"},
    {"step": 10, "field_name": "税前工资", "source": "formula", "default_formula": "base_amount - step_1"},
    {"step": 11, "field_name": "累计计税部分", "source": "formula", "default_formula": "max(0, step_8 - step_6 - step_9)"},
    {"step": 12, "field_name": "累计个税", "source": "tax_bracket", "default_formula": ""},
    {"step": 13, "field_name": "上月累计个税", "source": "prev_month", "default_formula": ""},
    {"step": 14, "field_name": "本月个税", "source": "formula", "default_formula": "max(0, step_12 - step_13)"},
]

# 计算顺序：5 依赖 6，故先算 6 再算 5
TAX_STEP_ORDER = [1, 2, 3, 4, 6, 5, 7, 8, 9, 10, 11, 12, 13, 14]

# 个税税率表与计算：从 app/config/income_tax_brackets.yaml 加载
from app.config.tax_brackets import calculate_tax as _cumulative_tax


def _eval_step_expression(expression: str, variables: Dict[str, Any]) -> float:
    """安全求值单步公式，变量可为 step_1 等及 base_result 键"""
    if not expression or not expression.strip():
        return 0.0
    safe_vars = {}
    for k, v in variables.items():
        if v is None:
            safe_vars[k] = 0.0
        elif isinstance(v, (int, float)):
            safe_vars[k] = float(v)
        elif isinstance(v, str) and v.replace(".", "").replace("-", "").isdigit():
            safe_vars[k] = float(v)
        else:
            safe_vars[k] = v
    return _safe_eval_expression(expression.strip(), safe_vars)


def _load_tax_step_formulas() -> Dict[str, str]:
    """加载已保存的步骤公式"""
    path = Config.BASE_DIR / "data" / "payroll_tax_steps.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("formulas", {})
    except Exception:
        return {}


def _save_tax_step_formulas(formulas: Dict[str, str]) -> None:
    """保存步骤公式"""
    path = Config.BASE_DIR / "data" / "payroll_tax_steps.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"formulas": formulas}, f, ensure_ascii=False, indent=2)


@payroll_api_bp.route("/payroll/tax-steps", methods=["GET", "POST"])
def payroll_tax_steps():
    """
    GET: 返回 14 步定义 + 已保存的公式
    POST: 保存步骤公式，Body: {"formulas": {"1": "expr", "2": "expr", ...}}
    """
    try:
        if request.method == "GET":
            formulas = _load_tax_step_formulas()
            steps = []
            for s in TAX_STEP_DEFINITIONS:
                step_num = s["step"]
                formulas_key = str(step_num)
                formula = formulas.get(formulas_key) or s.get("default_formula") or ""
                steps.append({
                    "step": step_num,
                    "field_name": s["field_name"],
                    "source": s["source"],
                    "formula": formula,
                })
            return standard_response(True, {"steps": steps})

        elif request.method == "POST":
            payload = request.get_json() or {}
            formulas = payload.get("formulas", {})
            if not isinstance(formulas, dict):
                return standard_response(False, error="formulas 必须为对象", status_code=400)
            _save_tax_step_formulas(formulas)
            return standard_response(True, {"message": "步骤公式已保存"})
    except Exception as e:
        return standard_response(False, error=str(e), status_code=500)


@payroll_api_bp.route("/payroll/tax-steps/preview", methods=["POST"])
def payroll_tax_steps_preview():
    """
    按当前周期、人员、公司预览 14 步结果（上月带入暂为 0）
    Body: { "person_id": 1, "company_id": 2, "period": "2024-01" }
    """
    try:
        payload = request.get_json() or {}
        person_id = payload.get("person_id")
        company_id = payload.get("company_id")
        period = payload.get("period")
        if not all([person_id, company_id, period]):
            return standard_response(False, error="person_id, company_id, period 为必填", status_code=400)

        service = get_payroll_service()
        base_result = service.calculate_payroll(int(person_id), int(company_id), str(period))
        formulas = _load_tax_step_formulas()

        variables = {}
        for k, v in base_result.items():
            if k in ("person_id", "company_id", "period", "status"):
                continue
            if isinstance(v, (int, float)):
                variables[k] = float(v)
            elif isinstance(v, str):
                try:
                    variables[k] = float(v)
                except (ValueError, TypeError):
                    variables[k] = 0.0
            else:
                variables[k] = 0.0

        prev_step_4 = 0.0
        prev_step_7 = 0.0
        prev_step_13 = 0.0
        step_values = {}

        for k in TAX_STEP_ORDER:
            s = next((x for x in TAX_STEP_DEFINITIONS if x["step"] == k), None)
            if not s:
                continue
            source = s["source"]
            formula_key = str(k)
            formula = (formulas.get(formula_key) or s.get("default_formula") or "").strip()

            if source == "prev_month":
                if k == 4:
                    val = prev_step_4
                elif k == 7:
                    val = prev_step_7
                else:
                    val = prev_step_13
                step_values[f"step_{k}"] = val
                variables[f"step_{k}"] = val
                continue

            if source == "tax_bracket":
                step_11 = step_values.get("step_11", 0.0)
                val = _cumulative_tax(step_11)
                step_values[f"step_{k}"] = val
                variables[f"step_{k}"] = val
                continue

            if source == "formula" and formula:
                try:
                    val = _eval_step_expression(formula, variables)
                except Exception:
                    val = 0.0
                val = round(val, 2)
            else:
                val = 0.0

            step_values[f"step_{k}"] = val
            variables[f"step_{k}"] = val

            if k == 5:
                prev_step_4 = val
            elif k == 8:
                prev_step_7 = val
            elif k == 12:
                prev_step_13 = val

        return standard_response(True, {
            "base_result": base_result,
            "step_values": step_values,
        })
    except Exception as e:
        return standard_response(False, error=str(e), status_code=500)
