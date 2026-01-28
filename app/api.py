"""
API 路由 - REST API 端点
统一基于 Twin 的 API 接口
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request
from typing import Optional, Dict, Any

from app.services.twin_service import TwinService
from app.schema.loader import SchemaLoader
from app.services.payroll_service import PayrollService
from config import Config

api_bp = Blueprint("api", __name__)


def get_twin_service() -> TwinService:
    """获取 TwinService 实例"""
    return TwinService(db_path=str(Config.DATABASE_PATH))


def get_schema_loader() -> SchemaLoader:
    """获取 SchemaLoader 实例"""
    return SchemaLoader()


def get_payroll_service() -> PayrollService:
    """获取 PayrollService 实例"""
    return PayrollService(db_path=str(Config.DATABASE_PATH))
def standard_response(success: bool, data=None, error: str = None, status_code: int = 200):
    """标准响应格式"""
    response = {"success": success}
    if data is not None:
        response["data"] = data
    if error:
        response["error"] = error
    if isinstance(data, list):
        response["count"] = len(data)
    return jsonify(response), status_code


# ==================== 统一的 Twin API 接口 ====================

@api_bp.route("/twins/<twin_name>", methods=["GET"])
def list_twins(twin_name: str):
    """
    列出所有指定类型的 Twin（支持过滤和 enrich）
    
    GET /api/twins/<twin_name>?field1=value1&field2=value2&enrich=true
    GET /api/twins/<twin_name>?enrich=person,project
    
    参数：
    - field1, field2, ...: 过滤条件
    - enrich: enrich 参数，支持 "true"（enrich 所有 related_entities）或实体列表（如 "person,project"），仅对 Activity Twin 有效
    """
    try:
        # 从查询参数构建过滤条件
        filters = {}
        enrich = None
        
        for key, value in request.args.items():
            if key == "enrich":
                enrich = value.strip() if value else None
            elif value and value.strip():  # 只添加非空的过滤条件
                filters[key] = value.strip()
        
        service = get_twin_service()
        twins = service.list_twins(
            twin_name, 
            filters=filters if filters else None,
            enrich=enrich
        )
        return standard_response(True, twins)
    except ValueError as e:
        return standard_response(False, error=str(e), status_code=400)
    except Exception as e:
        return standard_response(False, error=str(e), status_code=500)


@api_bp.route("/twins/<twin_name>/<int:twin_id>", methods=["GET"])
def get_twin(twin_name: str, twin_id: int):
    """
    获取指定 Twin 的详情（包含历史）
    
    GET /api/twins/<twin_name>/<twin_id>
    """
    try:
        service = get_twin_service()
        twin = service.get_twin(twin_name, twin_id)
        
        if not twin:
            return standard_response(False, error=f"{twin_name} not found", status_code=404)
        
        return standard_response(True, twin)
    except Exception as e:
        return standard_response(False, error=str(e), status_code=500)


@api_bp.route("/twins/<twin_name>", methods=["POST"])
def create_twin(twin_name: str):
    """
    创建新的 Twin
    
    POST /api/twins/<twin_name>
    Body: JSON 对象，包含字段值
    """
    try:
        data = request.get_json()
        if not data:
            return standard_response(False, error="Request body is required", status_code=400)
        
        service = get_twin_service()
        twin = service.create_twin(twin_name, data)
        
        return standard_response(True, twin, status_code=201)
    except ValueError as e:
        return standard_response(False, error=str(e), status_code=400)
    except Exception as e:
        return standard_response(False, error=str(e), status_code=500)


@api_bp.route("/twins/<twin_name>/<int:twin_id>", methods=["PUT"])
def update_twin(twin_name: str, twin_id: int):
    """
    更新 Twin 状态（追加新状态）
    
    PUT /api/twins/<twin_name>/<twin_id>
    Body: JSON 对象，包含要更新的字段值
    """
    try:
        data = request.get_json()
        if not data:
            return standard_response(False, error="Request body is required", status_code=400)
        
        service = get_twin_service()
        twin = service.update_twin(twin_name, twin_id, data)
        
        return standard_response(True, twin)
    except ValueError as e:
        return standard_response(False, error=str(e), status_code=400)
    except Exception as e:
        return standard_response(False, error=str(e), status_code=500)


# ==================== 工资计算与发放 API ====================

@api_bp.route("/payroll/calculate", methods=["POST"])
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


# ==================== 工资公式试算 & 变量列表 ====================


def _make_eval_key(var_name: str) -> str:
    """
    将原始变量名转换为安全的 eval 变量名（Python 标识符）
    例如：person_company_employment.salary -> v_person_company_employment_salary
    """
    import re

    safe = re.sub(r"[^0-9a-zA-Z_]", "_", var_name)
    if not safe or safe[0].isdigit():
        safe = f"v_{safe}"
    elif not safe.startswith("v_"):
        safe = f"v_{safe}"
    return safe


@api_bp.route("/schema/variables", methods=["GET"])
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

        return standard_response(True, result)
    except Exception as e:
        return standard_response(False, error=str(e), status_code=500)


@api_bp.route("/payroll/eval-formula", methods=["POST"])
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
    import ast
    import operator

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


@api_bp.route("/payroll/generate", methods=["POST"])
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
