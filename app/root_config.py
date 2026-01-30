"""
项目根目录 config.py 的显式加载，避免与 app.config 包冲突。

供 db、daos、twin_api、payroll_api、seed 等使用 Config 或 config 时统一从此导入。
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

_root_config_path = Path(__file__).resolve().parent.parent / "config.py"
_spec = importlib.util.spec_from_file_location("_root_config", _root_config_path)
_root_config_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_root_config_module)

Config = _root_config_module.Config
config: dict[str, Any] = _root_config_module.config
