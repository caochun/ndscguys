"""
Seed initial person data
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta
import sqlite3
import json
from typing import Optional

from app.services.person_service import PersonService, generate_avatar
from app.services.attendance_service import AttendanceService
from app.services.leave_service import LeaveService
from app.services.project_service import ProjectService


def seed_initial_data(db_path: str, target_count: int = 30):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM persons")
    count = cursor.fetchone()[0] or 0
    conn.close()

    if count >= target_count:
        return

    service = PersonService(db_path)
    attendance_service = AttendanceService(db_path)
    leave_service = LeaveService(db_path)
    project_service = ProjectService(db_path)

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

    def seed_attendance_for_person(person_id: int):
        today = datetime.now().date()
        for delta in range(1, 32):  # 至少覆盖近 30 天
            date = (today - timedelta(days=delta)).strftime("%Y-%m-%d")
            # 周末按较高概率标记为休息（缺勤），但仍记录
            weekday = (today - timedelta(days=delta)).weekday()
            if weekday >= 5:  # 周六周日
                status = random.choice(["缺勤", "外勤"])
                work_hours = 0 if status == "缺勤" else 6
                overtime_hours = 0
                check_in = None
                check_out = None
            else:
                status = random.choices(
                    population=["正常", "迟到", "早退", "外勤"],
                    weights=[0.75, 0.1, 0.1, 0.05],
                )[0]
                check_in = "09:00" if status != "迟到" else "09:30"
                check_out = "18:00" if status != "早退" else "17:00"
                work_hours = 8 if status in {"正常", "外勤"} else 7.5
                overtime_hours = random.choice([0, 0, 0, 1, 2])
            attendance_service.create_attendance(
                person_id=person_id,
                date=date,
                check_in_time=check_in,
                check_out_time=check_out,
                work_hours=work_hours,
                overtime_hours=overtime_hours,
                status=status,
                note="自动生成",
            )

    def seed_leave_for_person(person_id: int):
        leave_types = ["事假", "病假", "年假", "调休"]
        today = datetime.now().date()
        for delta in range(1, 32):
            if random.random() < 0.1:  # 请假概率较低
                date = (today - timedelta(days=delta)).strftime("%Y-%m-%d")
                leave_service.create_leave(
                    person_id=person_id,
                    leave_date=date,
                    leave_type=random.choice(leave_types),
                    hours=random.choice([4, 8]),
                    reason="示例请假记录",
                )

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
        employee_type = None
        if len(person_ids_with_position) < total_positions:
            company_name = "SC高科技公司" if len(person_ids_with_position) < company_a_count else "SC能源科技公司"
            emp_no = next_employee_number(company_name)
            employee_type = employee_types[idx % len(employee_types)]
            is_department_head = random.random() < 0.1
            position_title = positions[idx % len(positions)]
            if is_department_head:
                employee_type = "部分负责人"
                position_title = f"{position_title}-负责人"

            position_data = {
                "company_name": company_name,
                "employee_number": emp_no,
                "department": departments[idx % len(departments)],
                "position": position_title,
                "change_type": "入职",
                "change_date": (datetime(2022, 1, 1) + timedelta(days=idx * 30)).strftime("%Y-%m-%d"),
                "employee_type": employee_type,
            }

        def generate_salary_payload(emp_type: Optional[str]) -> dict:
            if emp_type == "实习生":
                salary_type = "日薪制度"
                amount = round(random.uniform(100, 200), 2)
            else:
                salary_type = "月薪制"
                amount = round(random.uniform(9000, 12000), 2)
            return {
                "salary_type": salary_type,
                "amount": amount,
                "effective_date": (datetime(2021, 1, 1) + timedelta(days=idx * 60)).strftime("%Y-%m-%d"),
            }

        salary_data = generate_salary_payload(employee_type)

        social_security_data = {
            "base_amount": round(random.uniform(5000, 15000), 2),
            "pension_company_rate": 0.16,
            "pension_personal_rate": 0.08,
            "unemployment_company_rate": 0.005,
            "unemployment_personal_rate": 0.005,
            "medical_company_rate": 0.1,
            "medical_personal_rate": 0.02,
            "maternity_company_rate": 0.008,
            "maternity_personal_rate": 0.0,
            "critical_illness_company_amount": round(random.uniform(30, 60), 2),
            "critical_illness_personal_amount": round(random.uniform(5, 20), 2),
        }

        housing_fund_data = {
            "base_amount": round(random.uniform(5000, 15000), 2),
            "company_rate": 0.07,
            "personal_rate": 0.07,
        }

        person_id = service.create_person(
            basic,
            position_data,
            salary_data,
            social_security_data,
            housing_fund_data,
        )
        seed_attendance_for_person(person_id)
        seed_leave_for_person(person_id)
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

        # 若公司变更，则视为“转公司”；否则视为“转岗/调部门”
        if current_company and current_company != new_company:
            change_type = "转公司"
        else:
            change_type = "转岗"

        position_data = {
            "company_name": new_company,
            "employee_number": employee_number,
            "department": random.choice(departments),
            "position": random.choice(positions),
            "change_type": change_type,
            "change_date": datetime.now().strftime("%Y-%m-%d"),
            "employee_type": random.choice(employee_types),
        }
        service.position_dao.append(entity_id=pid, data=position_data)

    # 20% of people with positions have termination events (离职)
    if person_ids_with_position:
        terminate_count = max(1, int(len(person_ids_with_position) * 0.2))
        terminate_ids = random.sample(person_ids_with_position, terminate_count)
        today_str = datetime.now().strftime("%Y-%m-%d")
        for pid in terminate_ids:
            latest_position = service.position_dao.get_latest(pid)
            latest_data = latest_position.data if latest_position else {}
            terminate_position = {
                "company_name": latest_data.get("company_name", "SC高科技公司"),
                "employee_number": latest_data.get("employee_number"),
                "department": latest_data.get("department"),
                "position": latest_data.get("position"),
                "employee_type": latest_data.get("employee_type"),
                "change_type": "离职",
                "change_date": today_str,
                "change_reason": "示例数据：自动生成离职事件",
            }
            service.position_dao.append(entity_id=pid, data=terminate_position)

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

    # 创建项目数据
    seed_projects(project_service, service, person_ids_with_position)


def seed_projects(project_service: ProjectService, person_service: PersonService, person_ids: list):
    """创建项目种子数据"""
    projects_data = [
        {
            "contract_name": "智慧城市管理系统开发",
            "start_date": "2024-01-15",
            "end_date": "2024-12-31",
            "client_company": "某市政府信息中心",
            "client_department": "信息化建设部",
            "client_project_manager": "王主任",
        },
        {
            "contract_name": "企业ERP系统升级改造",
            "start_date": "2024-03-01",
            "end_date": "2024-09-30",
            "client_company": "某大型制造企业",
            "client_department": "IT部门",
            "client_project_manager": "李经理",
        },
        {
            "contract_name": "移动办公平台建设",
            "start_date": "2024-02-10",
            "end_date": "2024-08-31",
            "client_company": "某科技公司",
            "client_department": "产品研发部",
            "client_project_manager": "陈总监",
        },
        {
            "contract_name": "数据中台架构设计",
            "start_date": "2024-04-01",
            "end_date": "2024-10-31",
            "client_company": "某金融机构",
            "client_department": "科技部",
            "client_project_manager": "赵总",
        },
        {
            "contract_name": "AI智能客服系统",
            "start_date": "2024-05-15",
            "end_date": "2024-11-30",
            "client_company": "某电商平台",
            "client_department": "技术中心",
            "client_project_manager": "周经理",
        },
        {
            "contract_name": "云原生微服务改造",
            "start_date": "2024-06-01",
            "end_date": "2024-12-31",
            "client_company": "某互联网公司",
            "client_department": "架构组",
            "client_project_manager": "吴总监",
        },
    ]

    project_ids = []
    for project_data in projects_data:
        project_id = project_service.create_project(project_data)
        project_ids.append(project_id)

    # 为每个项目分配参与人员（每个项目 3-8 人）
    # 确保每个项目至少有一个项目经理
    project_positions = ["项目经理", "技术负责人", "前端开发", "后端开发", "测试工程师", "UI设计师", "产品经理", "运维工程师"]
    manager_names = ["张伟", "刘洋", "杨静", "黄强", "徐敏", "周杰"]
    assessment_levels = ["高级", "中级", "初级"]
    process_statuses = ["进行中", "待启动", "已完成", "暂停"]

    for idx, project_id in enumerate(project_ids):
        # 随机选择 3-8 个人员参与项目
        num_persons = random.randint(3, min(8, len(person_ids)))
        selected_person_ids = random.sample(person_ids, num_persons)
        
        # 第一个人员设置为项目经理
        manager_person_id = selected_person_ids[0]
        manager_name = manager_names[idx % len(manager_names)]
        
        for i, person_id in enumerate(selected_person_ids):
            # 随机生成参与项目的时间（项目开始时间前后 30 天内）
            project_data = project_service.get_project(project_id)
            if project_data and project_data.get("basic", {}).get("data", {}).get("start_date"):
                start_date = project_data["basic"]["data"]["start_date"]
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                material_date = (start_dt + timedelta(days=random.randint(-30, 30))).strftime("%Y-%m-%d")
            else:
                material_date = datetime.now().strftime("%Y-%m-%d")
            
            # 第一个人员设置为项目经理，其他随机分配
            if i == 0:
                position = "项目经理"
            else:
                position = random.choice([p for p in project_positions if p != "项目经理"])
            
            person_project_data = {
                "project_id": project_id,
                "project_position": position,
                "material_submit_date": material_date,
                "assessment_level": random.choice(assessment_levels),
                "unit_price": round(random.uniform(500, 2000), 2),
                "process_status": random.choice(process_statuses),
            }
            
            try:
                person_service.append_person_project_change(person_id, project_id, person_project_data)
            except Exception as e:
                # 如果添加失败（可能因为重复），跳过
                pass

    # 为部分项目添加信息变更历史（模拟项目信息更新）
    if project_ids:
        update_count = max(1, int(len(project_ids) * 0.3))
        update_project_ids = random.sample(project_ids, update_count)
        
        for project_id in update_project_ids:
            project_data = project_service.get_project(project_id)
            if project_data and project_data.get("basic", {}).get("data"):
                current_data = project_data["basic"]["data"].copy()
                # 延长项目结束日期
                if current_data.get("end_date"):
                    end_dt = datetime.strptime(current_data["end_date"], "%Y-%m-%d")
                    current_data["end_date"] = (end_dt + timedelta(days=random.randint(30, 90))).strftime("%Y-%m-%d")
                
                project_service.append_project_change(project_id, current_data)

