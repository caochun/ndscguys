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


def validate_and_fix_project_assignments(db_path: str):
    """验证并修复项目分配数据：确保一个人正在参与的项目不超过一个"""
    person_service = PersonService(db_path)
    
    # 获取所有人员
    persons = person_service.list_persons()
    
    fixed_count = 0
    for person in persons:
        person_id = person["person_id"]
        # 获取该人员参与的所有项目
        projects = person_service.get_person_projects(person_id)
        
        # 过滤出正在参与的项目（不是"已退出"）
        active_projects = [p for p in projects if p.get("data", {}).get("project_position") != "已退出"]
        
        if len(active_projects) > 1:
            # 如果有多于一个正在参与的项目，保留最新的一个，其他标记为"已退出"
            print(f"发现人员 {person_id} ({person.get('name', 'N/A')}) 参与了 {len(active_projects)} 个项目，进行修复...")
            
            # 按时间戳排序，保留最新的
            active_projects.sort(key=lambda x: x.get("ts", ""), reverse=True)
            
            # 将除了最新的之外的所有项目标记为"已退出"
            for project in active_projects[1:]:
                project_id = project["project_id"]
                exit_data = {
                    "project_id": project_id,
                    "project_position": "已退出",
                    "process_status": "已退出项目",
                }
                # 保留原有信息
                current_data = project.get("data", {}).copy()
                for key in ["material_submit_date", "assessment_level", "unit_price"]:
                    if key in current_data:
                        exit_data[key] = current_data[key]
                
                try:
                    person_service.append_person_project_change(person_id, project_id, exit_data)
                    fixed_count += 1
                    print(f"  已将项目 {project_id} 标记为已退出")
                except Exception as e:
                    print(f"  修复项目 {project_id} 失败: {e}")
    
    if fixed_count > 0:
        print(f"\n修复完成，共修复 {fixed_count} 条记录")
    else:
        print("\n数据验证通过，无需修复")
    
    return fixed_count


def seed_initial_data(db_path: str, target_count: int = 30):
    # 先初始化数据库（创建表结构）
    from app.db import init_db
    init_db(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM persons")
    count = cursor.fetchone()[0] or 0
    conn.close()

    if count >= target_count:
        print(f"数据库中已有 {count} 条人员记录，跳过初始化")
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
                employee_type = "部门负责人"
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
            # 只有实习生是日薪制，其他所有员工类型都是月薪制
            if emp_type == "实习生":
                salary_type = "日薪制"
                amount = round(random.uniform(100, 200), 2)  # 日薪：100-200元/天
            else:
                # 所有非实习生（正式员工、试用期员工、部门负责人、其他）都是月薪制
                salary_type = "月薪制"
                amount = round(random.uniform(9000, 12000), 2)  # 月薪：9000-12000元/月
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
    seed_projects(project_service, service, person_ids_with_position, db_path)


def seed_projects(project_service: ProjectService, person_service: PersonService, person_ids: list, db_path: str = None):
    """创建项目种子数据"""
    projects_data = [
        # 专项型项目
        {
            "project_type": "专项型",
            "internal_project_name": "智慧城市管理系统",
            "internal_department": "研发部",
            "internal_project_manager": "张伟",
            "external_project_name": "智慧城市管理系统开发",
            "external_company": "某市政府信息中心",
            "external_department": "信息化建设部",
            "external_manager": "王主任",
            "external_order_number": "ORD-2024-001",
            "execution_start_date": "2024-01-15",
            "execution_end_date": "2024-12-31",
        },
        {
            "project_type": "专项型",
            "internal_project_name": "企业ERP系统升级",
            "internal_department": "研发部",
            "internal_project_manager": "王芳",
            "external_project_name": "企业ERP系统升级改造",
            "external_company": "某大型制造企业",
            "external_department": "IT部门",
            "external_manager": "李经理",
            "external_order_number": "ORD-2024-002",
            "execution_start_date": "2024-03-01",
            "execution_end_date": "2024-09-30",
        },
        {
            "project_type": "专项型",
            "internal_project_name": "移动办公平台",
            "internal_department": "产品部",
            "internal_project_manager": "李娜",
            "external_project_name": "移动办公平台建设",
            "external_company": "某科技公司",
            "external_department": "产品研发部",
            "external_manager": "陈总监",
            "external_order_number": "ORD-2024-003",
            "execution_start_date": "2024-02-10",
            "execution_end_date": "2024-08-31",
        },
        {
            "project_type": "专项型",
            "internal_project_name": "数据中台架构",
            "internal_department": "研发部",
            "internal_project_manager": "刘洋",
            "external_project_name": "数据中台架构设计",
            "external_company": "某金融机构",
            "external_department": "科技部",
            "external_manager": "赵总",
            "external_order_number": "ORD-2024-004",
            "execution_start_date": "2024-04-01",
            "execution_end_date": "2024-10-31",
        },
        # 劳务型项目
        {
            "project_type": "劳务型",
            "internal_project_name": "AI智能客服系统",
            "internal_department": "研发部",
            "internal_project_manager": "陈磊",
            "external_project_name": "AI智能客服系统开发",
            "external_company": "某电商平台",
            "external_department": "技术中心",
            "external_manager": "周经理",
            "external_order_number": "ORD-2024-005",
            "execution_start_date": "2024-05-15",
            "execution_end_date": "2024-11-30",
        },
        {
            "project_type": "劳务型",
            "internal_project_name": "云原生微服务",
            "internal_department": "研发部",
            "internal_project_manager": "杨静",
            "external_project_name": "云原生微服务改造",
            "external_company": "某互联网公司",
            "external_department": "架构组",
            "external_manager": "吴总监",
            "external_order_number": "ORD-2024-006",
            "execution_start_date": "2024-06-01",
            "execution_end_date": "2024-12-31",
        },
        {
            "project_type": "劳务型",
            "internal_project_name": "前端开发外包",
            "internal_department": "研发部",
            "internal_project_manager": "黄强",
            "external_project_name": "前端开发服务",
            "external_company": "某软件公司",
            "external_department": "产品部",
            "external_manager": "孙经理",
            "external_order_number": "ORD-2024-007",
            "execution_start_date": "2024-07-01",
            "execution_end_date": "2025-01-31",
        },
        {
            "project_type": "劳务型",
            "internal_project_name": "测试服务外包",
            "internal_department": "研发部",
            "internal_project_manager": "徐敏",
            "external_project_name": "软件测试服务",
            "external_company": "某互联网企业",
            "external_department": "质量保障部",
            "external_manager": "钱经理",
            "external_order_number": "ORD-2024-008",
            "execution_start_date": "2024-08-01",
            "execution_end_date": "2025-02-28",
        },
    ]

    project_ids = []
    for project_data in projects_data:
        project_id = project_service.create_project(project_data)
        project_ids.append(project_id)

    # 为每个项目分配参与人员（每个项目 3-8 人）
    # 确保每个项目至少有一个项目经理
    # 要求：一个人正在参与的项目不超过一个
    project_positions = ["项目经理", "技术负责人", "前端开发", "后端开发", "测试工程师", "UI设计师", "产品经理", "运维工程师"]
    assessment_levels = ["高级", "中级", "初级"]
    process_statuses = ["进行中", "待启动", "已完成", "暂停"]
    
    # 记录每个人员参与的项目（包括已退出的），用于历史记录
    person_project_map = {}  # {person_id: [project_ids]}
    # 记录每个人员当前正在参与的项目（不是"已退出"状态）
    person_active_project_map = {}  # {person_id: project_id}

    # 预先过滤掉已离职的人员
    active_person_ids = []
    for pid in person_ids:
        latest_position = person_service.position_dao.get_latest(pid)
        if latest_position:
            change_type = latest_position.data.get("change_type")
            # 排除已离职或停薪留职的人员
            if change_type in {"离职", "停薪留职"}:
                continue
        active_person_ids.append(pid)
    
    for idx, project_id in enumerate(project_ids):
        # 随机选择 3-8 个人员参与项目
        # 只选择没有正在参与项目且未离职的人员（确保一个人正在参与的项目不超过一个）
        available_persons = [pid for pid in active_person_ids if pid not in person_active_project_map]
        
        # 如果可用人员不足，则无法满足要求，记录警告但继续
        if len(available_persons) < 3:
            print(f"警告：项目 {project_id} 可用人员不足（需要至少3人，可用{len(available_persons)}人）")
            if len(available_persons) == 0:
                continue  # 跳过该项目，因为没有可用人员
            # 如果可用人员少于3人，使用所有可用人员
            num_persons = len(available_persons)
        else:
            num_persons = random.randint(3, min(8, len(available_persons)))
        selected_person_ids = random.sample(available_persons, num_persons)
        
        # 再次过滤，确保没有重复选择（虽然 random.sample 不会重复，但为了安全）
        selected_person_ids = [pid for pid in selected_person_ids if pid not in person_active_project_map]
        
        if len(selected_person_ids) == 0:
            continue  # 如果筛选后没有可用人员，跳过该项目
        
        # 第一个人员设置为项目经理
        manager_person_id = selected_person_ids[0]
        
        for i, person_id in enumerate(selected_person_ids):
            # 再次检查该人员是否已经有正在参与的项目（三重检查，确保安全）
            if person_id in person_active_project_map:
                print(f"警告：人员 {person_id} 已在 person_active_project_map 中，跳过")
                continue  # 跳过，该人员已有正在参与的项目
            
            # 从数据库验证：检查该人员是否已经有正在参与的项目
            person_projects = person_service.get_person_projects(person_id)
            active_projects = [p for p in person_projects if p.get("data", {}).get("project_position") != "已退出"]
            if len(active_projects) > 0:
                print(f"警告：人员 {person_id} 在数据库中已有 {len(active_projects)} 个正在参与的项目，跳过分配")
                continue  # 跳过，该人员在数据库中已有正在参与的项目
            
            # 随机生成参与项目的时间（项目开始时间前后 30 天内）
            project_data = project_service.get_project(project_id)
            if project_data and project_data.get("basic", {}).get("data", {}).get("execution_start_date"):
                start_date = project_data["basic"]["data"]["execution_start_date"]
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
            
            # 如果是劳务型项目，添加劳务型专用字段
            if project_data and project_data.get("basic", {}).get("data", {}).get("project_type") == "劳务型":
                person_project_data["client_requirement_number"] = f"REQ-{project_id}-{person_id:03d}"
                person_project_data["position_level"] = random.choice(["P5", "P6", "P7", "P8"])
                person_project_data["labor_unit_price"] = round(random.uniform(800, 1500), 2)
                
                # 随机选择打卡方式
                attendance_method = random.choice(["现场打卡", "线上打卡"])
                person_project_data["attendance_method"] = attendance_method
                
                if attendance_method == "现场打卡":
                    person_project_data["attendance_location"] = random.choice([
                        "客户现场A座", "客户现场B座", "客户现场C座", "客户现场D座"
                    ])
                    person_project_data["work_time_range"] = random.choice([
                        "09:00-18:00", "08:30-17:30", "09:30-18:30"
                    ])
                else:  # 线上打卡
                    person_project_data["online_location"] = random.choice([
                        "远程办公", "居家办公", "混合办公"
                    ])
                    person_project_data["online_work_time"] = random.choice([
                        "弹性工作制", "标准工作时间", "项目制"
                    ])
                    person_project_data["face_recognition"] = random.choice([True, False])
                    person_project_data["attendance_person"] = random.choice([
                        "本人", "代打卡", "系统自动"
                    ])
            
            try:
                person_service.append_person_project_change(person_id, project_id, person_project_data)
                # 记录人员参与的项目（所有项目，包括历史）
                if person_id not in person_project_map:
                    person_project_map[person_id] = []
                person_project_map[person_id].append(project_id)
                # 记录人员当前正在参与的项目（确保不会重复）
                if person_id in person_active_project_map:
                    print(f"错误：人员 {person_id} 在添加到 person_active_project_map 时已经存在！")
                    raise ValueError(f"人员 {person_id} 已经在 person_active_project_map 中")
                person_active_project_map[person_id] = project_id
            except Exception as e:
                # 如果添加失败（可能因为重复），跳过
                print(f"警告：为人员 {person_id} 添加项目 {project_id} 失败: {e}")
                # 确保即使失败，也不会在 person_active_project_map 中留下错误记录
                if person_id in person_active_project_map and person_active_project_map[person_id] == project_id:
                    del person_active_project_map[person_id]
                pass
    
    # 为部分人员添加项目信息变更（模拟岗位调整、等级提升等）
    # 只更新当前正在参与的项目（不是"已退出"状态）
    if person_active_project_map:
        update_person_count = max(1, int(len(person_active_project_map) * 0.2))
        update_person_ids = random.sample(list(person_active_project_map.keys()), min(update_person_count, len(person_active_project_map)))
        
        for person_id in update_person_ids:
            # 获取该人员当前正在参与的项目
            project_id = person_active_project_map.get(person_id)
            if not project_id:
                continue
            
            # 获取当前项目参与信息
            person_projects = person_service.get_person_projects(person_id)
            current_project_data = next((p for p in person_projects if p["project_id"] == project_id), None)
            
            if current_project_data:
                current_data = current_project_data.get("data", {}).copy()
                
                # 只更新正在参与的项目（不是"已退出"状态）
                if current_data.get("project_position") == "已退出":
                    continue
                
                # 随机更新部分信息
                updates = {}
                if random.random() < 0.5:
                    # 50% 概率更新等级
                    updates["assessment_level"] = random.choice(assessment_levels)
                if random.random() < 0.3:
                    # 30% 概率更新单价
                    updates["unit_price"] = round(random.uniform(500, 2000), 2)
                if random.random() < 0.3:
                    # 30% 概率更新状态
                    updates["process_status"] = random.choice(process_statuses)
                
                if updates:
                    updates["project_id"] = project_id
                    # 保留原有信息
                    for key in ["project_position", "material_submit_date"]:
                        if key in current_data:
                            updates[key] = current_data[key]
                    
                    try:
                        person_service.append_person_project_change(person_id, project_id, updates)
                    except Exception as e:
                        print(f"警告：更新人员 {person_id} 的项目 {project_id} 信息失败: {e}")
                        pass
    
    # 为部分人员添加退出项目的情况（模拟项目结束或人员调离）
    # 注意：退出后，该人员就没有正在参与的项目了，可以从 person_active_project_map 中移除
    if person_active_project_map:
        exit_count = max(1, int(len(person_active_project_map) * 0.1))
        exit_person_ids = random.sample(list(person_active_project_map.keys()), min(exit_count, len(person_active_project_map)))
        
        for person_id in exit_person_ids:
            # 获取该人员当前正在参与的项目
            exit_project_id = person_active_project_map.get(person_id)
            if not exit_project_id:
                continue
            
            exit_data = {
                "project_id": exit_project_id,
                "project_position": "已退出",
                "process_status": "已退出项目",
            }
            
            try:
                # 获取当前项目参与信息，保留其他字段
                person_projects = person_service.get_person_projects(person_id)
                current_project_data = next((p for p in person_projects if p["project_id"] == exit_project_id), None)
                if current_project_data:
                    current_data = current_project_data.get("data", {}).copy()
                    # 保留原有信息（除了 project_position 和 process_status）
                    for key in ["material_submit_date", "assessment_level", "unit_price"]:
                        if key in current_data:
                            exit_data[key] = current_data[key]
                
                person_service.append_person_project_change(person_id, exit_project_id, exit_data)
                # 从正在参与的项目映射中移除
                del person_active_project_map[person_id]
            except Exception as e:
                print(f"警告：人员 {person_id} 退出项目 {exit_project_id} 失败: {e}")
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
                if current_data.get("execution_end_date"):
                    end_dt = datetime.strptime(current_data["execution_end_date"], "%Y-%m-%d")
                current_data["execution_end_date"] = (end_dt + timedelta(days=random.randint(30, 90))).strftime("%Y-%m-%d")
                
                project_service.append_project_change(project_id, current_data)
    
    # 为部分人员添加项目状态（在项/待入项/不可用）
    if person_ids:
        # 获取所有有项目参与的人员
        persons_with_projects = set()
        for person_id in person_ids:
            projects = person_service.get_person_projects(person_id)
            active_projects = [p for p in projects if p.get("data", {}).get("project_position") != "已退出"]
            if active_projects:
                persons_with_projects.add(person_id)
        
        # 60%的人员设置为"在项"状态
        in_project_count = max(1, int(len(persons_with_projects) * 0.6))
        in_project_ids = random.sample(list(persons_with_projects), min(in_project_count, len(persons_with_projects)))
        
        for person_id in in_project_ids:
            projects = person_service.get_person_projects(person_id)
            active_projects = [p for p in projects if p.get("data", {}).get("project_position") != "已退出"]
            if active_projects:
                project_id = active_projects[0]["project_id"]  # 使用第一个活跃项目
                status_data = {
                    "status": "在项",
                    "project_id": project_id,
                    "note": "自动生成测试数据",
                }
                try:
                    person_service.append_person_project_status_change(person_id, status_data)
                except Exception as e:
                    print(f"警告：为人员 {person_id} 设置项目状态失败: {e}")
        
        # 20%的人员设置为"待入项"状态
        pending_count = max(1, int(len(person_ids) * 0.2))
        pending_ids = random.sample(person_ids, min(pending_count, len(person_ids)))
        pending_ids = [pid for pid in pending_ids if pid not in in_project_ids]  # 排除已在项的人员
        
        for person_id in pending_ids:
            # 随机选择项目或占位符
            if random.random() < 0.5 and project_ids:
                project_id = random.choice(project_ids)
            else:
                project_id = 0  # 占位符项目
            
            status_data = {
                "status": "待入项",
                "project_id": project_id,
                "note": "等待入项安排",
            }
            try:
                person_service.append_person_project_status_change(person_id, status_data)
            except Exception as e:
                print(f"警告：为人员 {person_id} 设置待入项状态失败: {e}")
        
        # 10%的人员设置为"不可用"状态
        unavailable_count = max(1, int(len(person_ids) * 0.1))
        unavailable_ids = random.sample(person_ids, min(unavailable_count, len(person_ids)))
        unavailable_ids = [pid for pid in unavailable_ids if pid not in in_project_ids and pid not in pending_ids]
        
        for person_id in unavailable_ids:
            status_data = {
                "status": "不可用",
                "note": "暂时不可用",
            }
            try:
                person_service.append_person_project_status_change(person_id, status_data)
            except Exception as e:
                print(f"警告：为人员 {person_id} 设置不可用状态失败: {e}")
    
    # 验证并修复项目分配数据（确保一个人正在参与的项目不超过一个）
    if db_path:
        print("\n验证项目分配数据...")
        validate_and_fix_project_assignments(db_path)

