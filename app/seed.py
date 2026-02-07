"""
测试数据生成 - 初始化戴森及江苏尚诚能源科技有限公司的指定数据
"""
from __future__ import annotations

from typing import Optional

from app.daos.twins.twin_dao import TwinDAO
from app.daos.twins.state_dao import TwinStateDAO
from app.root_config import Config


def generate_test_data(db_path: Optional[str] = None):
    """生成测试数据：戴森一人，江苏尚诚能源科技有限公司，聘用/考核/考勤/社保/公积金"""
    if db_path is None:
        db_path = str(Config.DATABASE_PATH)

    print(f"生成测试数据到: {db_path}")

    twin_dao = TwinDAO(db_path=db_path)
    state_dao = TwinStateDAO(db_path=db_path)

    # 1. 公司：江苏尚诚能源科技有限公司
    print("\n创建公司...")
    company_id = twin_dao.create_entity_twin("company")
    state_dao.append("company", company_id, {
        "name": "江苏尚诚能源科技有限公司",
        "registration_number": "91320000MA12345678",
    })
    print(f"  公司: 江苏尚诚能源科技有限公司 (ID: {company_id})")

    # 2. 人员：戴森
    print("\n创建人员...")
    person_id = twin_dao.create_entity_twin("person")
    state_dao.append("person", person_id, {
        "name": "戴森",
        "phone": "13800138000",
        "email": "daisen@example.com",
        "address": "江苏省南京市",
    })
    print(f"  人员: 戴森 (ID: {person_id})")

    # 3. 聘用：2022年8月1日在江苏尚诚入职，薪资10000（月薪）
    print("\n创建聘用记录...")
    employment_id = twin_dao.create_activity_twin(
        "person_company_employment",
        {"person_id": person_id, "company_id": company_id},
    )
    state_dao.append("person_company_employment", employment_id, {
        "person_id": person_id,
        "company_id": company_id,
        "position": "员工",
        "department": "技术部",
        "employee_number": "SC001",
        "employee_type": "正式",
        "position_category": "普通员工",
        "job_level": "中级",
        "salary_type": "月薪",
        "salary": 10000.0,
        "change_type": "入职",
        "change_date": "2022-08-01",
        "effective_date": "2022-08-01",
    })
    print(f"  聘用: 戴森 2022-08-01 入职 江苏尚诚能源科技有限公司，月薪 10000 元")

    # 4. 考核：2025年12月评定为 C
    print("\n创建考核记录...")
    assessment_id = twin_dao.create_activity_twin("person_assessment", {"person_id": person_id})
    state_dao.append("person_assessment", assessment_id, {
        "person_id": person_id,
        "assessment_period": "2025年12月",
        "assessment_date": "2025-12-31",
        "grade": "C",
        "comments": "工作表现符合要求，基本完成任务。",
    })
    print(f"  考核: 2025年12月 等级 C")

    # 5. 考勤：2025年12月，出勤21.75天（满勤），事假0、病假0、奖惩0
    print("\n创建考勤记录...")
    attendance_id = twin_dao.create_activity_twin(
        "person_company_attendance",
        {"person_id": person_id, "company_id": company_id},
    )
    state_dao.append(
        "person_company_attendance",
        attendance_id,
        {
            "person_id": person_id,
            "company_id": company_id,
            "period": "2025-12",
            "sick_leave_days": 0.0,
            "personal_leave_days": 0.0,
            "reward_punishment_amount": 0.0,
        },
        time_key="2025-12",
    )
    print(f"  考勤: 2025-12 事假0 病假0 奖惩0（满勤）")

    # 6. 社保基数：10000，生效期 2025-01-01
    print("\n创建社保基数记录...")
    social_base_id = twin_dao.create_activity_twin(
        "person_company_social_security_base",
        {"person_id": person_id, "company_id": company_id},
    )
    state_dao.append("person_company_social_security_base", social_base_id, {
        "person_id": person_id,
        "company_id": company_id,
        "base_amount": 10000.0,
        "effective_date": "2025-01-01",
    })
    print(f"  社保基数: 10000 元，生效 2025-01-01")

    # 7. 公积金基数：10000，生效期 2025-01-01
    print("\n创建公积金基数记录...")
    housing_base_id = twin_dao.create_activity_twin(
        "person_company_housing_fund_base",
        {"person_id": person_id, "company_id": company_id},
    )
    state_dao.append("person_company_housing_fund_base", housing_base_id, {
        "person_id": person_id,
        "company_id": company_id,
        "base_amount": 10000.0,
        "effective_date": "2025-01-01",
    })
    print(f"  公积金基数: 10000 元，生效 2025-01-01")

    print("\n测试数据生成完成！")
    print(f"  人员: 戴森 (ID: {person_id})")
    print(f"  公司: 江苏尚诚能源科技有限公司 (ID: {company_id})")
    print(f"  聘用/考核/考勤/社保基数/公积金基数 已创建")


if __name__ == "__main__":
    from app.db import init_db

    init_db()
    generate_test_data()
