"""
工资计算步骤公式求值：安全解析并求值算术表达式。
供 PayrollService、payroll_api 等使用，不依赖 Flask。
"""
from __future__ import annotations

import ast
import operator
from typing import Dict, Any


def safe_eval_expression(expression: str, variables: Dict[str, Any]) -> float:
    """
    安全地评估一个算术表达式。
    支持变量、+ - * / 括号、函数 max/min/abs/round/grade_coef。
    """
    from app.config.payroll_config import get_assessment_grade_coefficient

    def grade_coef(value: Any) -> float:
        return get_assessment_grade_coefficient(str(value).strip() if value else None)

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
            if isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)):
                    return node.value
                raise ValueError("仅支持数字常量")
            if hasattr(ast, "Num") and isinstance(node, ast.Num):
                return node.n
            if isinstance(node, ast.Name):
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
                raise ValueError("不支持的表达式语法")
            if isinstance(node, ast.Subscript):
                raise ValueError("不支持的表达式语法")
            raise ValueError("表达式中包含不支持的语法")

    tree = ast.parse(expression, mode="eval")
    evaluator = SafeEvaluator()
    result = evaluator.visit(tree)
    return float(result)


def eval_step_expression(expression: str, variables: Dict[str, Any]) -> float:
    """安全求值单步公式，变量可为 tax_1、gross_2 等及上下文键。"""
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
    return safe_eval_expression(expression.strip(), safe_vars)


# 运算符在「字面解读」与「代入值」中的显示符号
_OP_READABLE = {
    ast.Add: "+",
    ast.Sub: "−",
    ast.Mult: "×",
    ast.Div: "÷",
}


def _format_value(v: Any) -> str:
    """将数值格式化为简短字符串（整数不显示小数）。"""
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        if v == int(v):
            return str(int(v))
        return str(round(v, 2))
    return str(v)


class _FormulaToStringVisitor(ast.NodeVisitor):
    """AST 访问器：将公式树输出为「中文解读」或「代入值」字符串。"""

    def __init__(self, variable_labels: Dict[str, str], variables: Dict[str, Any], mode: str):
        self.labels = variable_labels or {}
        self.variables = variables or {}
        self.mode = mode  # "readable" | "values"

    def visit(self, node):
        if isinstance(node, ast.Expression):
            return self.visit(node.body)
        if isinstance(node, ast.BinOp):
            left = self.visit(node.left)
            right = self.visit(node.right)
            op_char = _OP_READABLE.get(type(node.op), "?")
            return f"({left}{op_char}{right})"
        if isinstance(node, ast.UnaryOp):
            operand = self.visit(node.operand)
            if type(node.op) == ast.USub:
                return f"−({operand})"
            return f"({operand})"
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return _format_value(node.value) if self.mode == "values" else str(node.value)
        if hasattr(ast, "Num") and isinstance(node, ast.Num):
            return _format_value(node.n) if self.mode == "values" else str(node.n)
        if isinstance(node, ast.Name):
            if self.mode == "readable":
                return self.labels.get(node.id, node.id)
            return _format_value(self.variables.get(node.id, 0))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            args = [self.visit(a) for a in node.args]
            args_str = ",".join(args)
            return f"{node.func.id}({args_str})"
        return "?"


def formula_to_readable(expression: str, variable_labels: Dict[str, str]) -> str:
    """
    将公式字面解读为中文：变量名替换为中文标签，*→×，/→÷。
    例如 employment_salary * base_ratio → 聘用薪资×基础薪资比例
    """
    if not expression or not expression.strip():
        return ""
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        visitor = _FormulaToStringVisitor(variable_labels, {}, "readable")
        s = visitor.visit(tree)
        return s.strip("()") if s.startswith("(") and s.endswith(")") else s
    except Exception:
        return expression


def formula_with_values(expression: str, variables: Dict[str, Any]) -> str:
    """
    将公式中的变量代入为当前数值。
    例如 employment_salary * base_ratio 与 variables={...} → 5000×0.8
    """
    if not expression or not expression.strip():
        return ""
    safe_vars = {}
    for k, v in (variables or {}).items():
        if v is None:
            safe_vars[k] = 0
        elif isinstance(v, (int, float)):
            safe_vars[k] = float(v)
        elif isinstance(v, str) and v.replace(".", "").replace("-", "").isdigit():
            safe_vars[k] = float(v)
        else:
            safe_vars[k] = v
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        visitor = _FormulaToStringVisitor({}, safe_vars, "values")
        s = visitor.visit(tree)
        return s.strip("()") if s.startswith("(") and s.endswith(")") else s
    except Exception:
        return expression
