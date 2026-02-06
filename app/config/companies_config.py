"""
可选公司配置：从 companies.yaml 读取列表，并在需要时同步到数据库。
供聘用/考勤/缴费等页面的公司下拉使用。
"""
from __future__ import annotations

import logging
import yaml
from pathlib import Path
from typing import List, Dict, Any

_CONFIG_DIR = Path(__file__).parent
_COMPANIES_PATH = _CONFIG_DIR / "companies.yaml"
_log = logging.getLogger(__name__)


def load_companies_from_yaml() -> List[Dict[str, Any]]:
    """从 companies.yaml 读取可选公司列表。返回 [{"name": "xxx"}, ...]。"""
    try:
        with open(_COMPANIES_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        _log.warning("可选公司配置文件不存在: %s", _COMPANIES_PATH)
        return []
    except yaml.YAMLError as e:
        _log.warning("companies.yaml 解析失败: %s", e)
        return []
    items = data.get("companies") or []
    result = []
    for item in items:
        if isinstance(item, str):
            result.append({"name": item})
        elif isinstance(item, dict) and item.get("name"):
            result.append({"name": item["name"]})
    return result


def ensure_companies_in_db(twin_service) -> None:
    """
    根据 config/companies.yaml 同步公司状态到数据库：
    - 配置中有、库中没有：创建公司 twin，状态=有效
    - 配置中有、库中也有：追加新版本，状态=有效
    - 库中有、配置中没有：追加新版本，状态=无效
    twin_service: TwinService 实例。
    """
    yaml_companies = load_companies_from_yaml()
    yaml_names = {(entry.get("name") or "").strip() for entry in yaml_companies if (entry.get("name") or "").strip()}
    existing = twin_service.list_twins("company")
    existing_by_name = {c["name"]: c for c in existing if c.get("name")}

    # 配置中有、库中没有 → 创建，状态=有效
    for name in yaml_names:
        if name not in existing_by_name:
            try:
                twin_service.create_twin("company", {"name": name, "status": "有效"})
                existing_by_name[name] = {"id": None}  # 占位，避免后面重复处理
            except Exception as e:
                _log.warning("创建公司 %s 失败: %s", name, e)

    # 配置中有、库中也有 → 追加新版本，状态=有效
    for name in yaml_names:
        c = existing_by_name.get(name)
        if not c or not c.get("id"):
            continue
        try:
            detail = twin_service.get_twin("company", c["id"])
            if not detail or not detail.get("current"):
                continue
            current = dict(detail["current"])
            if current.get("status") == "有效":
                continue
            current["status"] = "有效"
            twin_service.update_twin("company", c["id"], current)
        except Exception as e:
            _log.warning("更新公司 %s 为有效失败: %s", name, e)

    # 库中有、配置中没有 → 追加新版本，状态=无效
    for c in existing:
        name = c.get("name")
        if not name or name in yaml_names:
            continue
        try:
            detail = twin_service.get_twin("company", c["id"])
            if not detail or not detail.get("current"):
                continue
            current = dict(detail["current"])
            if current.get("status") == "无效":
                continue
            current["status"] = "无效"
            twin_service.update_twin("company", c["id"], current)
        except Exception as e:
            _log.warning("更新公司 %s 为无效失败: %s", name, e)
