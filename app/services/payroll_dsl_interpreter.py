"""
薪资计算 DSL 解释器
"""
from __future__ import annotations

import json
import re
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field


@dataclass
class CalculationContext:
    """计算上下文，包含所有可用数据"""
    # 基础数据
    person_id: int
    salary_type: str
    original_salary_amount: float
    employee_type: str
    assessment_grade: Optional[str]
    
    # 考勤数据
    expected_days: float
    actual_days: float
    
    # 社保公积金
    social_base_amount: float
    social_personal_amount: float
    housing_base_amount: float
    housing_personal_amount: float
    
    # 其他
    other_deduction: float = 0.0
    
    # 计算结果（动态添加）
    _vars: Dict[str, Any] = field(default_factory=dict)
    
    def set_var(self, name: str, value: Any):
        """设置变量值"""
        self._vars[name] = value
    
    def get_var(self, name: str, default: Any = None) -> Any:
        """获取变量值"""
        return self._vars.get(name, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，用于DSL访问"""
        result = {
            "person_id": self.person_id,
            "salary_type": self.salary_type,
            "original_salary_amount": self.original_salary_amount,
            "employee_type": self.employee_type,
            "assessment_grade": self.assessment_grade,
            "expected_days": self.expected_days,
            "actual_days": self.actual_days,
            "social_base_amount": self.social_base_amount,
            "social_personal_amount": self.social_personal_amount,
            "housing_base_amount": self.housing_base_amount,
            "housing_personal_amount": self.housing_personal_amount,
            "other_deduction": self.other_deduction,
        }
        # 合并动态变量
        result.update(self._vars)
        return result


class PayrollDSLInterpreter:
    """薪资计算 DSL 解释器"""
    
    def __init__(self, dsl_config: Dict[str, Any]):
        """
        初始化解释器
        
        Args:
            dsl_config: DSL配置字典（从YAML/JSON解析）
        """
        self.config = dsl_config
        self.configs = dsl_config.get("configs", {})
        self.rules = dsl_config.get("rules", [])
        self.calculations = dsl_config.get("calculations", {})
    
    def evaluate_expression(self, expr: Any, context: Dict[str, Any]) -> Any:
        """
        计算表达式值
        
        支持的表达式：
        - 数字、字符串、布尔值
        - 变量引用：variable_name
        - 配置访问：configs.key.subkey 或 configs.key[index]
        - 空值合并：value ?? default
        """
        if isinstance(expr, (int, float, bool)):
            return expr
        
        if isinstance(expr, str):
            # 处理字符串表达式
            if expr.startswith("configs."):
                # 配置访问：configs.performance_factors.A 或 configs.split_ratios.正式员工[0]
                return self._get_config_value(expr[8:])
            
            # 处理 null 值
            if expr.lower() == "null" or expr == "None":
                return None
            
            # 空值合并操作符
            if "??" in expr:
                parts = expr.split("??", 1)
                left = self._evaluate_simple_expr(parts[0].strip(), context)
                if left is not None and left != "":
                    return left
                return self._evaluate_simple_expr(parts[1].strip(), context)
            
            # 变量引用或数学表达式
            return self._evaluate_simple_expr(expr, context)
        
        if isinstance(expr, list):
            # 列表字面量
            return [self.evaluate_expression(item, context) for item in expr]
        
        if isinstance(expr, dict):
            # 处理字典表达式
            if "var" in expr:
                # 变量引用
                var_name = expr["var"]
                return context.get(var_name)
            
            if "if" in expr:
                # 条件表达式
                condition = self.evaluate_condition(expr["if"], context)
                if condition:
                    return self.evaluate_expression(expr.get("then"), context)
                else:
                    return self.evaluate_expression(expr.get("else"), context)
            
            if "value" in expr:
                # 值表达式
                return self.evaluate_expression(expr["value"], context)
        
        return expr
    
    def _get_config_value(self, path: str) -> Any:
        """获取配置值，支持点号和数组索引"""
        # 处理数组索引访问，如 configs.split_ratios.正式员工[0]
        import re
        match = re.match(r'^(.+)\[(\d+)\]$', path)
        if match:
            base_path = match.group(1)
            index = int(match.group(2))
            value = self._get_config_value(base_path)
            if isinstance(value, list) and 0 <= index < len(value):
                return value[index]
            return None
        
        keys = path.split(".")
        value = self.configs
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            elif isinstance(value, list):
                try:
                    value = value[int(key)]
                except (ValueError, IndexError, TypeError):
                    return None
            else:
                return None
            
            if value is None:
                return None
        
        return value
    
    def _evaluate_simple_expr(self, expr: str, context: Dict[str, Any]) -> Any:
        """计算简单表达式（变量引用或数学表达式）"""
        # 先尝试作为变量引用
        if expr in context:
            val = context[expr]
            # 如果是列表，支持索引访问
            if isinstance(val, list) and "[" in expr and "]" in expr:
                match = re.search(r'\[(\d+)\]$', expr)
                if match:
                    index = int(match.group(1))
                    if 0 <= index < len(val):
                        return val[index]
            return val
        
        # 处理数组索引访问（如 variable[0]）
        match = re.match(r'^(\w+)\[(\d+)\]$', expr)
        if match:
            var_name = match.group(1)
            index = int(match.group(2))
            if var_name in context:
                val = context[var_name]
                if isinstance(val, list) and 0 <= index < len(val):
                    return val[index]
        
        # 尝试作为数学表达式
        try:
            # 替换变量
            expr_copy = expr
            for key, val in context.items():
                if isinstance(val, (int, float)):
                    # 使用单词边界匹配，避免部分替换
                    pattern = r'\b' + re.escape(key) + r'\b'
                    expr_copy = re.sub(pattern, str(val), expr_copy)
                elif isinstance(val, list):
                    # 处理列表变量（在表达式中使用需要先提取）
                    pass
            
            # 处理数组索引访问（在表达式中）
            def replace_array_access(m):
                var_name = m.group(1)
                index = int(m.group(2))
                if var_name in context:
                    val = context[var_name]
                    if isinstance(val, list) and 0 <= index < len(val):
                        return str(val[index])
                return "0"
            
            expr_copy = re.sub(r'(\w+)\[(\d+)\]', replace_array_access, expr_copy)
            
            # 处理 max, min 函数
            expr_copy = re.sub(
                r'max\(([^)]+)\)',
                lambda m: str(max(eval(m.group(1)))),
                expr_copy
            )
            expr_copy = re.sub(
                r'min\(([^)]+)\)',
                lambda m: str(min(eval(m.group(1)))),
                expr_copy
            )
            
            # 计算表达式
            result = eval(expr_copy)
            # 如果是数字，转换为 float
            if isinstance(result, (int, float)):
                return float(result)
            return result
        except:
            # 如果计算失败，返回原始字符串
            return expr
    
    def evaluate_condition(self, condition: Any, context: Dict[str, Any]) -> bool:
        """计算条件表达式"""
        if isinstance(condition, bool):
            return condition
        
        if isinstance(condition, str):
            # 简单布尔变量
            if condition == "true":
                return True
            if condition == "false":
                return False
            return bool(context.get(condition, False))
        
        if isinstance(condition, dict):
            # 复杂条件表达式
            if "==" in condition:
                left = self.evaluate_expression(condition["=="][0], context)
                right = self.evaluate_expression(condition["=="][1], context)
                return left == right
            
            if "!=" in condition:
                left = self.evaluate_expression(condition["!="][0], context)
                right = self.evaluate_expression(condition["!="][1], context)
                return left != right
            
            if "in" in condition:
                var = self.evaluate_expression(condition["in"][0], context)
                arr = self.evaluate_expression(condition["in"][1], context)
                if isinstance(arr, list):
                    return var in arr
                return False
            
            if ">" in condition:
                left = self.evaluate_expression(condition[">"][0], context)
                right = self.evaluate_expression(condition[">"][1], context)
                return float(left) > float(right)
            
            if "<" in condition:
                left = self.evaluate_expression(condition["<"][0], context)
                right = self.evaluate_expression(condition["<"][1], context)
                return float(left) < float(right)
        
        return bool(condition)
    
    def execute_calculation(self, calc_name: str, context: CalculationContext) -> Dict[str, Any]:
        """执行指定的计算规则"""
        calc_config = self.calculations.get(calc_name)
        if not calc_config:
            raise ValueError(f"Calculation '{calc_name}' not found")
        
        steps = calc_config.get("steps", [])
        ctx_dict = context.to_dict()
        
        # 执行每个步骤
        for step in steps:
            var_name = step.get("var")
            if not var_name:
                continue
            
            # 计算变量值
            if "if" in step:
                # 条件赋值
                condition = self.evaluate_condition(step["if"], ctx_dict)
                if condition:
                    value = self.evaluate_expression(step.get("then"), ctx_dict)
                else:
                    value = self.evaluate_expression(step.get("else"), ctx_dict)
            else:
                # 直接赋值
                value = self.evaluate_expression(step.get("value"), ctx_dict)
            
            # 更新上下文
            context.set_var(var_name, value)
            ctx_dict[var_name] = value
        
        # 构建返回结果
        result = {
            "person_id": context.person_id,
            "salary_type": context.salary_type,
            "original_salary_amount": context.original_salary_amount,
            "employee_type": context.employee_type,
            "assessment_grade": context.assessment_grade,
            "expected_days": context.expected_days,
            "actual_days": context.actual_days,
            "social_base_amount": context.social_base_amount,
            "housing_base_amount": context.housing_base_amount,
        }
        
        # 添加计算出的变量
        for key, value in context._vars.items():
            result[key] = value
        
        return result
    
    def calculate(self, context: CalculationContext) -> Dict[str, Any]:
        """根据规则执行计算"""
        ctx_dict = context.to_dict()
        
        # 匹配规则
        for rule in self.rules:
            condition = rule.get("when")
            if self.evaluate_condition(condition, ctx_dict):
                calc_name = rule.get("then")
                return self.execute_calculation(calc_name, context)
        
        raise ValueError("No matching calculation rule found")
    
    @classmethod
    def from_yaml(cls, yaml_content: str) -> "PayrollDSLInterpreter":
        """从 YAML 字符串创建解释器"""
        try:
            import yaml
            config = yaml.safe_load(yaml_content)
        except ImportError:
            raise ImportError("PyYAML is required. Install it with: pip install pyyaml")
        except Exception as e:
            raise ValueError(f"Invalid YAML format: {e}")
        
        return cls(config)
    
    @classmethod
    def from_json(cls, json_content: str) -> "PayrollDSLInterpreter":
        """从 JSON 字符串创建解释器"""
        try:
            config = json.loads(json_content)
        except Exception as e:
            raise ValueError(f"Invalid JSON format: {e}")
        
        return cls(config)

