from __future__ import annotations

from pathlib import Path

import pytest

from app.services.person_service import PersonService


@pytest.fixture()
def tmp_service(tmp_path: Path) -> PersonService:
    db_path = tmp_path / "batches.db"
    return PersonService(str(db_path))


def _create_person_with_housing_and_social(tmp_service: PersonService, name: str, base: float) -> int:
    return tmp_service.create_person(
        basic_data={"name": name, "id_card": f"ID-{name}"},
        position_data={
            "company_name": "SC高科技公司",
            "employee_number": f"NO-{name}",
            "department": "研发部",
            "position": "工程师",
            "change_type": "入职",
            "change_date": "2025-01-01",
            "employee_type": "正式员工",
        },
        salary_data={"salary_type": "月薪制", "amount": 10000, "effective_date": "2025-01-01"},
        social_security_data={
            "base_amount": base,
            "pension_company_rate": 0.16,
            "pension_personal_rate": 0.08,
        },
        housing_fund_data={
            "base_amount": base,
            "company_rate": 0.07,
            "personal_rate": 0.07,
        },
    )


def test_housing_fund_batch_preview_confirm_execute(tmp_service: PersonService):
    # 创建两个人员，基数分别为 5000 和 20000（超出上限，用于测试 clamp）
    pid1 = _create_person_with_housing_and_social(tmp_service, "Alice", 5000)
    pid2 = _create_person_with_housing_and_social(tmp_service, "Bob", 20000)

    params = {
        "effective_date": "2025-12-01",
        "min_base_amount": 8000,
        "max_base_amount": 15000,
        "default_company_rate": 0.08,
        "default_personal_rate": 0.08,
        "target_company": "SC高科技公司",
    }
    preview = tmp_service.preview_housing_fund_batch(params)

    assert preview["batch_id"] > 0
    assert preview["affected_count"] == 2
    assert len(preview["items"]) == 2

    # 校验 clamp 逻辑：5000 -> 8000；20000 -> 15000
    base_values = sorted(item["new_base_amount"] for item in preview["items"])
    assert base_values == [8000.0, 15000.0]

    batch_id = preview["batch_id"]

    # 模拟用户在前端把第一条的基数微调为 9000
    items_to_update = []
    for item in preview["items"]:
        if item["person_id"] == pid1:
            item["new_base_amount"] = 9000
        items_to_update.append(
            {
                "id": item["id"],
                "new_base_amount": item["new_base_amount"],
                "new_company_rate": item["new_company_rate"],
                "new_personal_rate": item["new_personal_rate"],
            }
        )

    tmp_service.update_housing_fund_batch_items(batch_id, items_to_update)

    # 执行批次，写入公积金状态流
    execute_result = tmp_service.execute_housing_fund_batch(batch_id)
    assert execute_result["batch_id"] == batch_id
    assert execute_result["affected_count"] == 2

    # 再执行一次应视为幂等，不再新增记录
    execute_again = tmp_service.execute_housing_fund_batch(batch_id)
    assert execute_again["affected_count"] == 2

    # 验证每个人最新的公积金记录是否符合预期
    person1 = tmp_service.get_person(pid1)
    person2 = tmp_service.get_person(pid2)

    hf1_latest = person1["housing_fund_history"][0]["data"]
    hf2_latest = person2["housing_fund_history"][0]["data"]

    assert hf1_latest["base_amount"] == 9000
    assert hf2_latest["base_amount"] == 15000
    assert hf1_latest["batch_id"] == batch_id
    assert hf2_latest["batch_id"] == batch_id


def test_social_security_batch_preview_confirm_execute(tmp_service: PersonService):
    pid1 = _create_person_with_housing_and_social(tmp_service, "Carol", 6000)
    pid2 = _create_person_with_housing_and_social(tmp_service, "Dave", 18000)

    params = {
        "effective_date": "2025-12-01",
        "min_base_amount": 7000,
        "max_base_amount": 16000,
        "default_pension_company_rate": 0.16,
        "default_pension_personal_rate": 0.08,
        "default_unemployment_company_rate": 0.005,
        "default_unemployment_personal_rate": 0.005,
        "default_medical_company_rate": 0.10,
        "default_medical_personal_rate": 0.02,
        "default_maternity_company_rate": 0.008,
        "default_maternity_personal_rate": 0.0,
        "default_critical_illness_company_amount": 50.0,
        "default_critical_illness_personal_amount": 10.0,
        "target_company": "SC高科技公司",
    }
    preview = tmp_service.preview_social_security_batch(params)

    assert preview["batch_id"] > 0
    assert preview["affected_count"] == 2
    assert len(preview["items"]) == 2

    base_values = sorted(item["new_base_amount"] for item in preview["items"])
    # 6000 -> 7000, 18000 -> 16000
    assert base_values == [7000.0, 16000.0]

    batch_id = preview["batch_id"]

    items_to_update = []
    for item in preview["items"]:
        if item["person_id"] == pid1:
            item["new_base_amount"] = 7500
        items_to_update.append(
            {
                "id": item["id"],
                "new_base_amount": item["new_base_amount"],
                "new_pension_company_rate": item.get("new_pension_company_rate"),
                "new_pension_personal_rate": item.get("new_pension_personal_rate"),
                "new_unemployment_company_rate": item.get("new_unemployment_company_rate"),
                "new_unemployment_personal_rate": item.get("new_unemployment_personal_rate"),
                "new_medical_company_rate": item.get("new_medical_company_rate"),
                "new_medical_personal_rate": item.get("new_medical_personal_rate"),
                "new_maternity_company_rate": item.get("new_maternity_company_rate"),
                "new_maternity_personal_rate": item.get("new_maternity_personal_rate"),
                "new_critical_illness_company_amount": item.get(
                    "new_critical_illness_company_amount"
                ),
                "new_critical_illness_personal_amount": item.get(
                    "new_critical_illness_personal_amount"
                ),
            }
        )

    tmp_service.update_social_security_batch_items(batch_id, items_to_update)

    execute_result = tmp_service.execute_social_security_batch(batch_id)
    assert execute_result["batch_id"] == batch_id
    assert execute_result["affected_count"] == 2

    execute_again = tmp_service.execute_social_security_batch(batch_id)
    assert execute_again["affected_count"] == 2

    person1 = tmp_service.get_person(pid1)
    person2 = tmp_service.get_person(pid2)

    ss1_latest = person1["social_security_history"][0]["data"]
    ss2_latest = person2["social_security_history"][0]["data"]

    assert ss1_latest["base_amount"] == 7500
    assert ss2_latest["base_amount"] == 16000
    assert ss1_latest["batch_id"] == batch_id
    assert ss2_latest["batch_id"] == batch_id


