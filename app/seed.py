"""
Seed initial person data
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta
import sqlite3
import json

from app.services.person_service import PersonService, generate_avatar


def seed_initial_data(db_path: str, target_count: int = 30):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM persons")
    count = cursor.fetchone()[0] or 0
    conn.close()

    if count >= target_count:
        return

    service = PersonService(db_path)

    names = [
        "张伟", "王芳", "李娜", "刘洋", "陈磊", "杨静", "黄强", "徐敏", "周杰", "赵霞",
        "吴涛", "孙丽", "马超", "胡燕", "郭鹏", "何倩", "罗军", "梁欣", "宋睿", "谢婷",
        "韩磊", "唐悦", "冯峰", "于洋", "董雪", "萧晨", "石磊", "蔡薇", "蒋楠", "秦亮"
    ]

    departments = ["研发部", "市场部", "财务部", "人事部", "产品部", "运营部"]
    positions = ["工程师", "高级工程师", "主管", "经理", "分析师", "专员"]
    employee_types = ["正式员工", "试用期员工", "实习生", "其他"]

    total_positions = int(target_count * 0.9)  # 90%
    company_a_count = total_positions // 2  # 45% of total persons
    company_b_count = total_positions - company_a_count

    person_ids_with_position = []
    company_counters = {"SC高科技公司": 1, "SC能源科技公司": 1}

    def next_employee_number(company: str) -> str:
        prefix = "SCG" if company == "SC高科技公司" else "SCE"
        current = company_counters.setdefault(company, 1)
        company_counters[company] = current + 1
        return f"{prefix}{current:04d}"

    for idx, name in enumerate(names[:target_count]):
        basic = {
            "name": name,
            "id_card": f"ID{name}{idx:03d}",
            "birth_date": (datetime(1990, 1, 1) + timedelta(days=idx * 150)).strftime("%Y-%m-%d"),
            "gender": "男" if idx % 2 == 0 else "女",
            "phone": f"138{idx:08d}",
            "email": f"user{idx}@example.com",
            "address": f"某城市示例路 {idx} 号",
            "avatar": generate_avatar(name),
        }

        position_data = None
        if len(person_ids_with_position) < total_positions:
            company_name = "SC高科技公司" if len(person_ids_with_position) < company_a_count else "SC能源科技公司"
            emp_no = next_employee_number(company_name)
            position_data = {
                "company_name": company_name,
                "employee_number": emp_no,
                "department": departments[idx % len(departments)],
                "position": positions[idx % len(positions)],
                "hire_date": (datetime(2022, 1, 1) + timedelta(days=idx * 30)).strftime("%Y-%m-%d"),
                "employee_type": employee_types[idx % len(employee_types)],
            }

        person_id = service.create_person(basic, position_data)
        if position_data:
            person_ids_with_position.append(person_id)

    # 50% of people with positions have job changes
    change_count = max(1, int(len(person_ids_with_position) * 0.5))
    change_ids = random.sample(person_ids_with_position, change_count)
    for pid in change_ids:
        new_company = "SC能源科技公司"
        # 尝试读取当前岗位，如果存在且为能源公司，则切换回高科技
        latest_position = service.position_dao.get_latest(pid)
        latest_data = latest_position.data if latest_position else {}
        current_company = latest_data.get("company_name")
        if current_company == "SC能源科技公司":
            new_company = "SC高科技公司"
        elif current_company == "SC高科技公司":
            new_company = "SC能源科技公司"

        if current_company == new_company:
            employee_number = latest_data.get("employee_number")
        else:
            employee_number = next_employee_number(new_company)

        position_data = {
            "company_name": new_company,
            "employee_number": employee_number,
            "department": random.choice(departments),
            "position": random.choice(positions),
            "hire_date": datetime.now().strftime("%Y-%m-%d"),
            "employee_type": random.choice(employee_types),
        }
        service.position_dao.append(entity_id=pid, data=position_data)

    # 20% of all persons have basic info changes (address/phone)
    basic_change_count = max(1, int(target_count * 0.2))
    basic_ids = random.sample(range(1, target_count + 1), basic_change_count)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    for pid in basic_ids:
        cursor.execute(
            """
            SELECT data FROM person_basic_history
            WHERE person_id = ?
            ORDER BY version DESC
            LIMIT 1
            """,
            (pid,),
        )
        row = cursor.fetchone()
        if not row:
            continue
        data = json.loads(row[0])
        data["phone"] = f"139{random.randint(10000000, 99999999)}"
        data["address"] = f"更新地址 {random.randint(1, 100)} 号"
        service.basic_dao.append(entity_id=pid, data=data)
    conn.close()

