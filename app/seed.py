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

    # 8. 专项附加扣除年度累计：2025-12、2026-01、2026-02 三期，六项均为 0
    print("\n创建专项附加扣除年度累计记录...")
    tax_deduction_id = twin_dao.create_activity_twin(
        "person_tax_deduction",
        {"person_id": person_id},
    )
    for period in ("2025-12", "2026-01", "2026-02"):
        state_dao.append(
            "person_tax_deduction",
            tax_deduction_id,
            {
                "person_id": person_id,
                "period": period,
                "children_education_amount": 0.0,
                "continuing_education_amount": 0.0,
                "housing_loan_interest_amount": 0.0,
                "housing_rent_amount": 0.0,
                "elderly_support_amount": 0.0,
                "infant_childcare_amount": 0.0,
            },
            time_key=period,
        )
    print(f"  专项附加扣除: 2025-12、2026-01、2026-02 三期，六项累计均为 0")

    print("\n测试数据生成完成！")
    print(f"  人员: 戴森 (ID: {person_id})")
    print(f"  公司: 江苏尚诚能源科技有限公司 (ID: {company_id})")
    print(f"  聘用/考核/考勤/社保基数/公积金基数/专项附加扣除 已创建")


def generate_project_data(db_path: Optional[str] = None):
    """生成项目管理测试数据：客户合同、款项、内部项目及关联关系"""
    if db_path is None:
        db_path = str(Config.DATABASE_PATH)

    print(f"生成项目管理测试数据到: {db_path}")

    twin_dao = TwinDAO(db_path=db_path)
    state_dao = TwinStateDAO(db_path=db_path)

    # ── 内部项目 ──────────────────────────────────────────────
    print("\n创建内部项目...")

    def make_project(name, status, manager, dept):
        pid = twin_dao.create_entity_twin("internal_project")
        state_dao.append("internal_project", pid, {
            "name": name, "status": status,
            "project_manager": manager, "department": dept,
        })
        print(f"  项目: {name} [{status}] (ID: {pid})")
        return pid

    p_ai     = make_project("智慧能源AI平台", "进行中", "张伟", "技术部")
    p_carbon = make_project("碳排放监测系统", "进行中", "李娜", "产品部")
    p_micro  = make_project("微电网优化项目", "已完成", "王芳", "技术部")
    p_solar  = make_project("光伏运维数字化", "筹备中", "赵强", "产品部")

    # ── 客户合同 ──────────────────────────────────────────────
    print("\n创建客户合同...")

    def make_contract(cname, company, amount, ctype, status, cnum):
        cid = twin_dao.create_entity_twin("client_contract")
        state_dao.append("client_contract", cid, {
            "contract_name": cname, "client_company": company,
            "contract_amount": amount, "contract_type": ctype,
            "status": status, "contract_number": cnum,
            "sign_date": "2024-01-01",
        })
        print(f"  合同: {cname} / {company} ¥{amount:,.0f} (ID: {cid})")
        return cid

    c1 = make_contract("智慧能源平台建设合同",  "南京电网集团",    3_200_000, "专项", "执行中",  "HT-2024-001")
    c2 = make_contract("碳排放监测系统合同",    "江苏环保科技",    1_500_000, "专项", "执行中",  "HT-2024-002")
    c3 = make_contract("微电网优化服务合同",    "苏州工业园能源",  2_800_000, "专项", "已完成",  "HT-2023-008")
    c4 = make_contract("光伏运维年度服务合同",  "无锡新能源",       960_000, "劳务", "已签订",  "HT-2024-003")
    c5 = make_contract("能源咨询顾问合同",      "南京电网集团",     480_000, "专项", "已完成",  "HT-2023-012")

    # ── 款项 ──────────────────────────────────────────────────
    # 字段：client_contract_id, period, amount, status,
    #       planned_payment_date, actual_payment_date, description
    print("\n创建款项...")

    def make_pi(contract_id, period, amount, status, planned, actual=None, desc=""):
        pi_id = twin_dao.create_entity_twin("payment_item")
        data = {
            "client_contract_id": contract_id,
            "period": period, "amount": amount,
            "status": status, "planned_payment_date": planned,
            "description": desc,
        }
        if actual:
            data["actual_payment_date"] = actual
        state_dao.append("payment_item", pi_id, data)
        mark = "✓" if status == "已付款" else ("!" if planned < "2026-02-27" else "…")
        print(f"  款项 {mark} {period} ¥{amount:>12,.0f}  [{status}]  合同ID={contract_id}")
        return pi_id

    # 合同1 — 智慧能源平台（3 期，已收2期）
    pi1_1 = make_pi(c1, "首付款",   960_000, "已付款", "2024-03-01", "2024-03-05")
    pi1_2 = make_pi(c1, "中期款", 1_280_000, "已付款", "2024-09-01", "2024-09-10")
    pi1_3 = make_pi(c1, "尾款",     960_000, "待付款", "2026-06-01")

    # 合同2 — 碳排放监测（3 期，已收1期，1期逾期）
    pi2_1 = make_pi(c2, "首付款",   450_000, "已付款", "2024-04-01", "2024-04-08")
    pi2_2 = make_pi(c2, "中期款",   600_000, "待付款", "2025-10-01")   # 逾期
    pi2_3 = make_pi(c2, "尾款",     450_000, "待付款", "2026-08-01")

    # 合同3 — 微电网优化（3 期，已全收）
    pi3_1 = make_pi(c3, "首付款",   840_000, "已付款", "2023-04-01", "2023-04-15")
    pi3_2 = make_pi(c3, "中期款", 1_120_000, "已付款", "2023-10-01", "2023-10-20")
    pi3_3 = make_pi(c3, "尾款",     840_000, "已付款", "2024-03-01", "2024-03-12")

    # 合同4 — 光伏运维（4 季度，仅 Q1 付款）
    pi4_1 = make_pi(c4, "Q1服务费", 240_000, "已付款", "2024-04-01", "2024-04-03")
    pi4_2 = make_pi(c4, "Q2服务费", 240_000, "待付款", "2025-07-01")   # 逾期
    pi4_3 = make_pi(c4, "Q3服务费", 240_000, "待付款", "2026-04-01")
    pi4_4 = make_pi(c4, "Q4服务费", 240_000, "待付款", "2026-10-01")

    # 合同5 — 能源咨询（2 期，已全收）
    pi5_1 = make_pi(c5, "首付款",   192_000, "已付款", "2023-06-01", "2023-06-05")
    pi5_2 = make_pi(c5, "尾款",     288_000, "已付款", "2023-12-01", "2023-12-08")

    # ── 内部项目 ↔ 款项 关联 ──────────────────────────────────
    # activity: internal_project_payment
    # related_entities: internal_project_id, payment_item_id
    print("\n关联内部项目与款项...")

    def link(project_id, pi_id, notes=""):
        act_id = twin_dao.create_activity_twin(
            "internal_project_payment",
            {"internal_project_id": project_id, "payment_item_id": pi_id},
        )
        state_dao.append("internal_project_payment", act_id, {
            "internal_project_id": project_id,
            "payment_item_id": pi_id,
            "notes": notes,
        })
        return act_id

    # 智慧能源AI平台 ← 合同1全部款项 + 合同5尾款
    link(p_ai, pi1_1, "平台建设首款")
    link(p_ai, pi1_2, "平台建设中期")
    link(p_ai, pi1_3, "平台建设尾款")
    link(p_ai, pi5_2, "顾问服务收入")

    # 碳排放监测系统 ← 合同2全部款项
    link(p_carbon, pi2_1, "系统建设首款")
    link(p_carbon, pi2_2, "系统建设中期")
    link(p_carbon, pi2_3, "系统建设尾款")

    # 微电网优化项目 ← 合同3全部款项 + 合同5首款
    link(p_micro, pi3_1, "优化首款")
    link(p_micro, pi3_2, "优化中期")
    link(p_micro, pi3_3, "优化尾款")
    link(p_micro, pi5_1, "顾问咨询收入")

    # 光伏运维数字化 ← 合同4全部款项
    link(p_solar, pi4_1, "Q1运维服务")
    link(p_solar, pi4_2, "Q2运维服务")
    link(p_solar, pi4_3, "Q3运维服务")
    link(p_solar, pi4_4, "Q4运维服务")

    print("\n项目管理测试数据生成完成！")
    print(f"  内部项目: 4 个")
    print(f"  客户合同: 5 个（总额 ¥8,940,000）")
    print(f"  款项:    14 笔（已收 8 笔，待收 6 笔，其中 2 笔逾期）")
    print(f"  项目-款项关联: 14 条")


if __name__ == "__main__":
    import sys
    from app.db import init_db

    init_db()
    if len(sys.argv) > 1 and sys.argv[1] == "projects":
        generate_project_data()
    else:
        generate_test_data()
