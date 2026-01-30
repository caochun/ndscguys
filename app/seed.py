"""
测试数据生成 - 根据 Schema 生成测试数据
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Optional, Tuple

from app.daos.twins.twin_dao import TwinDAO
from app.daos.twins.state_dao import TwinStateDAO
from app.root_config import Config


def generate_test_data(db_path: Optional[str] = None):
    """生成测试数据"""
    if db_path is None:
        db_path = str(Config.DATABASE_PATH)
    
    print(f"生成测试数据到: {db_path}")
    
    twin_dao = TwinDAO(db_path=db_path)
    state_dao = TwinStateDAO(db_path=db_path)
    
    # 生成公司数据
    print("\n生成公司数据...")
    companies = []
    company_names = ["SC高科技公司", "SC能源科技公司"]
    
    for company_name in company_names:
        company_id = twin_dao.create_entity_twin("company")
        state_dao.append("company", company_id, {
            "name": company_name,
            "registration_number": f"91110000MA{random.randint(10000000, 99999999)}",
        })
        companies.append(company_id)
        print(f"  创建公司: {company_name} (ID: {company_id})")
    
    # 岗位薪资结构、员工类别折算、考核等级系数、社保公积金配置已移至 app/config/*.yaml，不再 seed
    
    # 生成人员数据
    print("\n生成人员数据...")
    persons = []
    first_names = ["张", "李", "王", "刘", "陈", "杨", "赵", "黄", "周", "吴"]
    last_names = ["三", "四", "五", "六", "七", "八", "九", "十", "明", "华", "强", "伟", "芳", "丽", "静"]
    
    for i in range(30):
        person_id = twin_dao.create_entity_twin("person")
        name = random.choice(first_names) + random.choice(last_names)
        phone = f"1{random.choice([3,4,5,6,7,8,9])}{random.randint(100000000, 999999999)}"
        email = f"{name.lower()}{i}@example.com"
        
        # 生成头像 URL（使用 DiceBear Micah 风格）
        avatar = f"https://api.dicebear.com/7.x/micah/svg?seed={name}{i}"
        
        state_dao.append("person", person_id, {
            "name": name,
            "phone": phone,
            "email": email,
            "address": f"北京市朝阳区第{i+1}街道",
            "avatar": avatar,
        })
        persons.append(person_id)
        print(f"  创建人员: {name} (ID: {person_id})")
        
        # 20% 的人员有基础信息变更
        if random.random() < 0.2:
            # 更新电话或地址
            new_phone = f"1{random.choice([3,4,5,6,7,8,9])}{random.randint(100000000, 999999999)}"
            new_address = f"北京市海淀区第{random.randint(1, 20)}街道"
            
            state_dao.append("person", person_id, {
                "name": name,
                "phone": new_phone,  # 电话变更
                "email": email,
                "address": new_address,  # 地址变更
                "avatar": avatar,
            })
            print(f"    基础信息变更: 电话和地址更新")
    
    # 工具函数：根据薪资类型生成随机薪资
    def generate_salary() -> Tuple[str, float]:
        """生成随机的薪资类型和薪资金额"""
        salary_type = random.choice(["年薪", "月薪", "日薪"])
        if salary_type == "年薪":
            amount = random.randint(12, 40) * 10000  # 12w - 40w
        elif salary_type == "月薪":
            amount = random.randint(8, 40) * 1000   # 8k - 40k
        else:  # 日薪
            amount = random.choice([300, 400, 500, 600, 800, 1000, 1200, 1500])
        return salary_type, float(amount)
    
    # 生成聘用管理数据
    print("\n生成聘用管理数据...")
    employments = []
    
    # 90% 的人员有聘用记录
    employed_persons = random.sample(persons, int(len(persons) * 0.9))
    
    for person_id in employed_persons:
        company_id = random.choice(companies)
        employment_id = twin_dao.create_activity_twin(
            "person_company_employment",
            {
                "person_id": person_id,
                "company_id": company_id,
            }
        )
        
        # 生成员工号（根据公司不同规则）
        company_name = "SC高科技公司" if company_id == companies[0] else "SC能源科技公司"
        employee_number_prefix = "SCG" if company_id == companies[0] else "SCE"
        employee_number = f"{employee_number_prefix}{random.randint(1000, 9999)}"
        
        positions = ["软件工程师", "高级软件工程师", "产品经理", "项目经理", "测试工程师", "UI设计师"]
        departments = ["研发部", "产品部", "测试部", "设计部"]
        employee_types = ["实习", "试用", "外聘", "正式"]
        position_categories = ["普通员工", "部门负责人", "BOSS"]
        job_levels = ["初级", "中级", "高级", "其他"]
        
        salary_type, salary = generate_salary()
        
        state_dao.append("person_company_employment", employment_id, {
            "person_id": person_id,
            "company_id": company_id,
            "position": random.choice(positions),
            "department": random.choice(departments),
            "employee_number": employee_number,
            "employee_type": random.choice(employee_types),
            "position_category": random.choice(position_categories),
            "job_level": random.choice(job_levels),
            "salary_type": salary_type,
            "salary": salary,
            "change_type": "入职",
            "change_date": (datetime.now() - timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d"),
        })
        employments.append((employment_id, person_id, company_id))
        print(f"  创建聘用记录: Person {person_id} -> Company {company_id}")

        # 50% 的聘用记录有岗位变动
        if random.random() < 0.5:
            # 追加岗位变动记录
            new_position = random.choice(positions)
            new_department = random.choice(departments)
            
            # 如果换公司，生成新员工号
            if random.random() < 0.2:  # 20% 概率换公司
                new_company_id = companies[1] if company_id == companies[0] else companies[0]
                new_employee_number_prefix = "SCG" if new_company_id == companies[0] else "SCE"
                new_employee_number = f"{new_employee_number_prefix}{random.randint(1000, 9999)}"
                
                # 创建新的聘用记录（跨公司）
                new_employment_id = twin_dao.create_activity_twin(
                    "person_company_employment",
                    {
                        "person_id": person_id,
                        "company_id": new_company_id,
                    }
                )
                
                new_salary_type, new_salary = generate_salary()
                
                state_dao.append("person_company_employment", new_employment_id, {
                    "person_id": person_id,
                    "company_id": new_company_id,
                    "position": new_position,
                    "department": new_department,
                    "employee_number": new_employee_number,
                    "employee_type": random.choice(employee_types),
                    "position_category": random.choice(position_categories),
                    "job_level": random.choice(job_levels),
                    "salary_type": new_salary_type,
                    "salary": new_salary,
                    "change_type": "转公司",
                    "change_date": (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d"),
                })
                print(f"    岗位变动: 转公司到 Company {new_company_id}")
            else:
                # 同公司内转岗
                new_salary_type, new_salary = generate_salary()
                
                state_dao.append("person_company_employment", employment_id, {
                    "person_id": person_id,
                    "company_id": company_id,
                    "position": new_position,
                    "department": new_department,
                    "employee_number": employee_number,  # 员工号不变
                    "employee_type": random.choice(employee_types),
                    "position_category": random.choice(position_categories),
                    "job_level": random.choice(job_levels),
                    "salary_type": new_salary_type,
                    "salary": new_salary,
                    "change_type": "转岗",
                    "change_date": (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d"),
                })
                print(f"    岗位变动: 转岗")
    
    # 生成打卡记录（时间序列数据）
    print("\n生成打卡记录数据...")
    attendance_count = 0
    attendance_activities = {}  # {(person_id, company_id): activity_id}
    
    # 为有聘用记录的人员生成最近7天的打卡记录
    for employment_id, person_id, company_id in employments[:10]:  # 只生成前10个人的打卡记录
        # 为每个 person-company 组合创建一个打卡活动
        if (person_id, company_id) not in attendance_activities:
            attendance_id = twin_dao.create_activity_twin(
                "person_company_attendance",
                {
                    "person_id": person_id,
                    "company_id": company_id,
                }
            )
            attendance_activities[(person_id, company_id)] = attendance_id
        
        attendance_id = attendance_activities[(person_id, company_id)]
        
        # 为最近7天生成打卡记录
        for day_offset in range(7):
            date = (datetime.now() - timedelta(days=day_offset)).strftime("%Y-%m-%d")
            
            # 生成打卡时间
            check_in_hour = random.randint(8, 10)
            check_in_minute = random.randint(0, 30)
            check_out_hour = random.randint(17, 19)
            check_out_minute = random.randint(0, 59)
            
            work_hours = (check_out_hour * 60 + check_out_minute - check_in_hour * 60 - check_in_minute) / 60
            
            status = "正常" if check_in_hour < 9 else "迟到"
            
            state_dao.append("person_company_attendance", attendance_id, {
                "person_id": person_id,
                "company_id": company_id,
                "date": date,
                "check_in_time": f"{check_in_hour:02d}:{check_in_minute:02d}:00",
                "check_out_time": f"{check_out_hour:02d}:{check_out_minute:02d}:00",
                "work_hours": round(work_hours, 2),
                "status": status,
            }, time_key=date)
            attendance_count += 1
    
    print(f"  生成打卡记录: {attendance_count} 条")
    
    # 生成社保基数数据
    print("\n生成社保基数数据...")
    social_base_count = 0
    
    # 为已有聘用记录的 person-company 组合生成社保基数历史
    for employment_id, person_id, company_id in employments:
        # 为每个 person-company 组合创建一个社保基数活动
        social_base_id = twin_dao.create_activity_twin(
            "person_company_social_security_base",
        {
                "person_id": person_id,
                "company_id": company_id,
            }
        )
        
        # 生成 1-2 条基数变更记录（版本化）
        num_changes = random.randint(1, 2)
        base = random.randint(5000, 20000)  # 基数金额区间
        
        for i in range(num_changes):
            # 生效日期：从过去一年内随机一天
            effective_date = (datetime.now() - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d")
            
            state_dao.append("person_company_social_security_base", social_base_id, {
                "person_id": person_id,
                "company_id": company_id,
                "base_amount": float(base),
                "effective_date": effective_date,
            })
            social_base_count += 1
            
            # 下一次调整基数（增加或减少一点）
            base_delta = random.randint(-1000, 2000)
            base = max(0, base + base_delta)
    
    print(f"  生成社保基数记录: {social_base_count} 条")
    
    # 生成公积金基数数据
    print("\n生成公积金基数数据...")
    housing_fund_base_count = 0
    
    # 为已有聘用记录的 person-company 组合生成公积金基数历史（80% 的人员有公积金）
    housing_fund_employments = random.sample(employments, int(len(employments) * 0.8))
    
    for employment_id, person_id, company_id in housing_fund_employments:
        # 为每个 person-company 组合创建一个公积金基数活动
        housing_fund_base_id = twin_dao.create_activity_twin(
            "person_company_housing_fund_base",
            {
                "person_id": person_id,
                "company_id": company_id,
            }
        )
        
        # 生成 1-2 条基数变更记录（版本化）
        num_changes = random.randint(1, 2)
        base = random.randint(5000, 20000)  # 基数金额区间（通常和社保基数接近）
        
        for i in range(num_changes):
            # 生效日期：从过去一年内随机一天
            effective_date = (datetime.now() - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d")
            
            state_dao.append("person_company_housing_fund_base", housing_fund_base_id, {
                "person_id": person_id,
                "company_id": company_id,
                "base_amount": float(base),
                "effective_date": effective_date,
            })
            housing_fund_base_count += 1
            
            # 下一次调整基数（增加或减少一点）
            base_delta = random.randint(-1000, 2000)
            base = max(0, base + base_delta)
    
    print(f"  生成公积金基数记录: {housing_fund_base_count} 条")
    
    # 生成考核数据
    print("\n生成考核数据...")
    assessment_count = 0
    assessment_grades = ["A", "B", "C", "D", "E"]
    assessment_periods = [
        "2024年第一季度", "2024年第二季度", "2024年第三季度", "2024年第四季度",
        "2023年年度", "2024年年度"
    ]
    
    # 为 60% 的人员生成考核记录
    assessed_persons = random.sample(persons, int(len(persons) * 0.6))
    
    for person_id in assessed_persons:
        # 每个人可能有 1-3 次考核记录
        num_assessments = random.randint(1, 3)
        
        for _ in range(num_assessments):
            assessment_id = twin_dao.create_activity_twin(
                "person_assessment",
                {
                    "person_id": person_id,
                }
            )

            # 生成考核日期（过去一年内）
            assessment_date = (datetime.now() - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d")
            assessment_period = random.choice(assessment_periods)
            grade = random.choice(assessment_grades)
            
            # 生成评语（根据等级）
            comments_map = {
                "A": "绩效等级A：工作表现突出，业绩显著，值得表扬。",
                "B": "绩效等级B：工作表现良好，能够完成工作任务。",
                "C": "绩效等级C：工作表现符合要求，基本完成任务。",
                "D": "绩效等级D：工作表现一般，有一定提升空间。",
                "E": "绩效等级E：工作表现有待改进，需要加强学习和提升。"
            }
            comments = comments_map.get(grade, "")
            
            # 30% 的概率有自定义评语
            if random.random() < 0.3:
                comments = f"{comments} 具体表现：在项目中表现积极，与团队协作良好。"
            
            state_dao.append("person_assessment", assessment_id, {
                "person_id": person_id,
                "assessment_period": assessment_period,
                "assessment_date": assessment_date,
                "grade": grade,
                "comments": comments if random.random() < 0.8 else None,  # 80% 有评语
            })
            assessment_count += 1
    
    print(f"  生成考核记录: {assessment_count} 条")
    
    # 生成专项附加扣除数据
    print("\n生成专项附加扣除数据...")
    tax_deduction_count = 0
    # 为 70% 的人员生成专项附加扣除记录
    # 现在每个人只有一个 person_tax_deduction 记录，包含所有 7 种扣除类型的金额
    persons_with_deductions = random.sample(persons, int(len(persons) * 0.7))
    
    for person_id in persons_with_deductions:
        deduction_id = twin_dao.create_activity_twin(
            "person_tax_deduction",
            {
                "person_id": person_id,
            }
        )
        
        # 随机生成各种扣除类型的金额（可能为0，表示没有该项扣除）
        children_education_amount = random.choice([0, 1000, 2000]) if random.random() < 0.6 else 0
        continuing_education_amount = random.choice([0, 400]) if random.random() < 0.3 else 0
        medical_expense_amount = random.choice([0, random.randint(1000, 8000)]) if random.random() < 0.2 else 0
        housing_loan_interest_amount = random.choice([0, 1000]) if random.random() < 0.4 else 0
        housing_rent_amount = random.choice([0, 800, 1100, 1500]) if random.random() < 0.5 else 0
        elderly_support_amount = random.choice([0, 1000, 2000]) if random.random() < 0.5 else 0
        infant_childcare_amount = random.choice([0, 1000, 2000]) if random.random() < 0.3 else 0
        
        # 生效日期：从过去一年内随机一天
        effective_date = (datetime.now() - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d")
        
        # 30% 的概率已失效
        status = "已失效" if random.random() < 0.3 else "生效中"
        expiry_date = None
        if status == "已失效":
            # 失效日期在生效日期之后
            expiry_days = random.randint(30, 365)
            expiry_date = (datetime.now() - timedelta(days=random.randint(0, expiry_days))).strftime("%Y-%m-%d")
        
        # 生成备注（汇总各种扣除的说明）
        remarks_parts = []
        if children_education_amount > 0:
            remarks_parts.append(f"子女教育：{random.choice(['张三', '李四', '王五', '赵六'])}，{random.choice(['XX小学', 'XX中学', 'XX大学'])}")
        if continuing_education_amount > 0:
            remarks_parts.append(random.choice(["继续教育：XX大学学历教育", "继续教育：XX证书职业资格"]))
        if medical_expense_amount > 0:
            remarks_parts.append(f"大病医疗：医疗费用{random.randint(5000, 50000)}元")
        if housing_loan_interest_amount > 0:
            remarks_parts.append(f"住房贷款利息：贷款合同号{random.randint(100000, 999999)}")
        if housing_rent_amount > 0:
            remarks_parts.append(f"住房租金：{random.choice(['XX市XX区XX路', 'XX市XX区XX街道'])}")
        if elderly_support_amount > 0:
            remarks_parts.append(f"赡养老人：{random.choice(['父亲', '母亲', '父母'])}")
        if infant_childcare_amount > 0:
            remarks_parts.append(f"3岁以下婴幼儿照护：{random.choice(['子女甲', '子女乙'])}")
        
        remarks = "；".join(remarks_parts) if remarks_parts else None
        
        # 生成 1-2 条变更记录（版本化）
        num_changes = random.randint(1, 2)
        
        for i in range(num_changes):
            # 第一次记录初始状态
            if i == 0:
                state_dao.append("person_tax_deduction", deduction_id, {
                    "person_id": person_id,
                    "children_education_amount": float(children_education_amount),
                    "continuing_education_amount": float(continuing_education_amount),
                    "medical_expense_amount": float(medical_expense_amount),
                    "housing_loan_interest_amount": float(housing_loan_interest_amount),
                    "housing_rent_amount": float(housing_rent_amount),
                    "elderly_support_amount": float(elderly_support_amount),
                    "infant_childcare_amount": float(infant_childcare_amount),
                    "effective_date": effective_date,
                    "expiry_date": expiry_date,
                    "status": status,
                    "remarks": remarks,
                })
            else:
                # 后续变更：调整金额或状态
                new_children_education = max(0, children_education_amount + random.choice([-1000, 0, 1000]))
                new_continuing_education = max(0, continuing_education_amount + random.choice([-400, 0, 400]))
                new_medical_expense = max(0, medical_expense_amount + random.randint(-1000, 2000))
                new_housing_loan = max(0, housing_loan_interest_amount + random.choice([-1000, 0, 1000]))
                new_housing_rent = max(0, housing_rent_amount + random.choice([-300, 0, 300]))
                new_elderly_support = max(0, elderly_support_amount + random.choice([-1000, 0, 1000]))
                new_infant_childcare = max(0, infant_childcare_amount + random.choice([-1000, 0, 1000]))
                
                new_status = status
                new_expiry_date = expiry_date
                if random.random() < 0.3:  # 30% 概率状态变更
                    new_status = "已失效" if status == "生效中" else "生效中"
                    if new_status == "已失效":
                        expiry_days = random.randint(30, 365)
                        new_expiry_date = (datetime.now() - timedelta(days=random.randint(0, expiry_days))).strftime("%Y-%m-%d")
                
                state_dao.append("person_tax_deduction", deduction_id, {
                    "person_id": person_id,
                    "children_education_amount": float(new_children_education),
                    "continuing_education_amount": float(new_continuing_education),
                    "medical_expense_amount": float(new_medical_expense),
                    "housing_loan_interest_amount": float(new_housing_loan),
                    "housing_rent_amount": float(new_housing_rent),
                    "elderly_support_amount": float(new_elderly_support),
                    "infant_childcare_amount": float(new_infant_childcare),
                    "effective_date": effective_date,
                    "expiry_date": new_expiry_date,
                    "status": new_status,
                    "remarks": remarks,
                })
            
            tax_deduction_count += 1
    
    print(f"  生成专项附加扣除记录: {tax_deduction_count} 条")
    
    # 生成客户合同数据
    print("\n生成客户合同数据...")
    client_contracts = []
    contract_names = [
        "智慧城市平台开发合同", "企业数字化转型合同", "AI智能客服系统合同", "大数据分析平台合同",
        "移动应用开发合同", "云服务迁移合同", "区块链应用合同", "物联网平台合同",
        "电商平台升级合同", "金融风控系统合同", "物流管理系统合同", "医疗信息化合同"
    ]
    client_companies = ["阿里巴巴", "腾讯", "百度", "京东", "字节跳动", "美团", "滴滴", "小米", "华为", "中兴", "联想", "网易"]
    contract_statuses = ["草稿", "已签订", "执行中", "已完成", "已终止", "已取消"]
    contract_types = ["劳务", "专项"]
    
    # 存储合同类型映射，供后续订单使用
    contract_type_map = {}
    
    for i in range(12):
        contract_id = twin_dao.create_entity_twin("client_contract")
        contract_status = random.choice(contract_statuses)
        contract_type = random.choice(contract_types)
        contract_date = (datetime.now() - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d")
        contract_amount = random.randint(500000, 10000000)
        
        state_dao.append("client_contract", contract_id, {
            "contract_number": f"HT{random.randint(100000, 999999)}",
            "contract_name": contract_names[i],
            "contract_type": contract_type,
            "client_company": client_companies[i],
            "client_department": random.choice(["技术部", "产品部", "运营部", "市场部", "研发部"]),
            "client_manager": random.choice(["张", "李", "王", "刘", "陈"]) + random.choice(["总", "经理", "主管"]),
            "contract_date": contract_date,
            "contract_amount": float(contract_amount),
            "status": contract_status,
            "description": f"{contract_names[i]}的详细描述",
        })
        client_contracts.append(contract_id)
        contract_type_map[contract_id] = contract_type
        print(f"  创建客户合同: {contract_names[i]} (ID: {contract_id}, 类型: {contract_type})")
    
    # 生成订单数据
    print("\n生成订单数据...")
    orders = []
    order_statuses = ["待确认", "已确认", "执行中", "已完成", "已取消"]
    
    # 为每个客户合同生成 2-4 个订单
    for contract_id in client_contracts:
        # 获取合同的类型，订单类型与合同类型保持一致
        contract_type = contract_type_map.get(contract_id, random.choice(["劳务", "专项"]))
        
        num_orders = random.randint(2, 4)
        for j in range(num_orders):
            order_id = twin_dao.create_entity_twin("order")
            order_status = random.choice(order_statuses)
            
            # 生成订单金额（合同金额的一部分）
            contract_state = state_dao.query_latest_states("client_contract", {"twin_id": contract_id})
            contract_amount = contract_state[0].data.get("contract_amount", 1000000) if contract_state else 1000000
            order_amount = float(contract_amount / num_orders * random.uniform(0.8, 1.2))
            
            execution_start_date = None
            expected_delivery_date = None
            actual_delivery_date = None
            
            if order_status in ["执行中", "已完成"]:
                execution_start_date = (datetime.now() - timedelta(days=random.randint(0, 180))).strftime("%Y-%m-%d")
                expected_delivery_date = (datetime.now() + timedelta(days=random.randint(30, 180))).strftime("%Y-%m-%d")
                if order_status == "已完成":
                    actual_delivery_date = (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d")
            
            state_dao.append("order", order_id, {
                "order_number": f"DD{random.randint(100000, 999999)}",
                "order_type": contract_type,  # 订单类型与合同类型保持一致
                "amount": order_amount,
                "status": order_status,
                "execution_start_date": execution_start_date,
                "description": f"订单 {j+1} 的详细描述",
                "expected_delivery_date": expected_delivery_date,
                "actual_delivery_date": actual_delivery_date,
            })
            orders.append((order_id, contract_id))
            print(f"  创建订单: DD{order_id} (ID: {order_id}, 合同: {contract_id}, 类型: {contract_type})")
    
    # 生成客户合同-订单关联数据
    print("\n生成客户合同-订单关联数据...")
    contract_order_count = 0
    
    for order_id, contract_id in orders:
        # 创建关联活动
        association_id = twin_dao.create_activity_twin(
            "client_contract_order",
            {
                "client_contract_id": contract_id,
                "order_id": order_id,
            }
        )
        
        # 获取订单的执行开始日期作为拆分日期
        order_state = state_dao.query_latest_states("order", {"twin_id": order_id})
        execution_start_date = order_state[0].data.get("execution_start_date") if order_state else None
        split_date = execution_start_date or (datetime.now() - timedelta(days=random.randint(0, 180))).strftime("%Y-%m-%d")
        
        state_dao.append("client_contract_order", association_id, {
            "client_contract_id": contract_id,
            "order_id": order_id,
            "split_date": split_date,
            "split_reason": random.choice([
                "按阶段拆分", "按模块拆分", "按交付物拆分", "按时间节点拆分", "按功能拆分"
            ]),
            "split_by": random.choice(["张经理", "李经理", "王经理", "刘经理", "陈经理"]),
        })
        contract_order_count += 1
    
    print(f"  生成客户合同-订单关联: {contract_order_count} 条")
    
    # 生成内部项目数据
    print("\n生成内部项目数据...")
    internal_projects = []
    internal_project_names = [
        "智慧城市平台", "企业数字化转型", "AI智能客服", "大数据分析",
        "移动应用开发", "云服务迁移", "区块链应用", "物联网平台",
        "电商平台升级", "金融风控", "物流管理", "医疗信息化"
    ]
    project_statuses = ["筹备中", "进行中", "已暂停", "已完成", "已取消"]
    departments = ["研发部", "产品部", "技术部", "创新部", "战略部"]
    
    for i in range(10):
        project_id = twin_dao.create_entity_twin("internal_project")
        project_status = random.choice(project_statuses)
        
        start_date = (datetime.now() - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d")
        end_date = None
        if project_status in ["已完成", "已取消"]:
            end_date = (datetime.now() - timedelta(days=random.randint(0, 180))).strftime("%Y-%m-%d")
        
        state_dao.append("internal_project", project_id, {
            "name": internal_project_names[i],
            "department": random.choice(departments),
            "project_manager": random.choice(["张", "李", "王", "刘", "陈"]) + random.choice(["总", "经理", "主管"]),
            "description": f"{internal_project_names[i]}项目的详细描述",
            "status": project_status,
            "start_date": start_date,
            "end_date": end_date,
        })
        internal_projects.append(project_id)
        print(f"  创建内部项目: {internal_project_names[i]} (ID: {project_id})")
    
    # 生成内部项目-订单关联数据
    print("\n生成内部项目-订单关联数据...")
    project_order_count = 0
    
    # 每个内部项目关联 2-5 个订单
    for project_id in internal_projects:
        num_associations = random.randint(2, 5)
        selected_orders = random.sample([oid for oid, _ in orders], min(num_associations, len(orders)))
        
        for order_id in selected_orders:
            # 创建关联活动
            association_id = twin_dao.create_activity_twin(
                "internal_project_order",
                {
                    "internal_project_id": project_id,
                    "order_id": order_id,
                }
            )
            
            association_date = (datetime.now() - timedelta(days=random.randint(0, 180))).strftime("%Y-%m-%d")
            
            state_dao.append("internal_project_order", association_id, {
                "internal_project_id": project_id,
                "order_id": order_id,
                "association_date": association_date,
                "association_reason": random.choice([
                    "项目需要", "资源分配", "业务需求", "战略规划", "客户要求"
                ]),
            })
            project_order_count += 1
    
    print(f"  生成内部项目-订单关联: {project_order_count} 条")
    
    # 生成人员参与订单数据
    print("\n生成人员参与订单数据...")
    participation_count = 0
    
    # 获取所有订单的最新状态，构建订单类型映射
    all_order_states = state_dao.query_latest_states("order")
    order_type_map = {}
    for state in all_order_states:
        order_type_map[state.twin_id] = state.data.get("order_type", "专项")
    
    # 为每个订单分配一些参与人员
    for order_id, contract_id in orders:
        order_type = order_type_map.get(order_id, "专项")
        
        # 每个订单随机分配 1-3 个人员
        num_participants = random.randint(1, 3)
        selected_persons = random.sample(persons, min(num_participants, len(persons)))
        
        for person_id in selected_persons:
            # 创建参与活动
            participation_id = twin_dao.create_activity_twin(
                "person_order_participation",
                {
                    "person_id": person_id,
                    "order_id": order_id,
                }
            )
            
            participation_type = random.choice(["实际参加", "名义参加"])
            
            # 构建参与数据
            participation_data = {
                "person_id": person_id,
                "order_id": order_id,
                "participation_type": participation_type,
            }
            
            # 如果是劳务订单且是实际参加，添加劳务相关字段
            if order_type == "劳务" and participation_type == "实际参加":
                start_date = (datetime.now() - timedelta(days=random.randint(0, 90))).strftime("%Y-%m-%d")
                end_date = None
                if random.random() < 0.7:  # 70% 的概率有结束时间
                    end_date = (datetime.now() + timedelta(days=random.randint(30, 180))).strftime("%Y-%m-%d")
                
                participation_data["start_date"] = start_date
                participation_data["end_date"] = end_date
                participation_data["attendance_method"] = random.choice(["现场打卡", "线上打卡"])
                participation_data["entry_progress"] = random.choice(["材料准备中", "已提交", "面试中"])
            
            state_dao.append("person_order_participation", participation_id, participation_data)
            participation_count += 1
    
    print(f"  生成人员参与订单记录: {participation_count} 条")
    
    # 生成考勤记录数据
    print("\n生成考勤记录数据...")
    attendance_record_count = 0
    
    # 为有聘用记录的人员生成最近3个月的考勤记录
    for employment_id, person_id, company_id in employments:
        # 为每个 person-company 组合创建一个考勤记录活动
        attendance_record_id = twin_dao.create_activity_twin(
            "person_company_attendance_record",
            {
                "person_id": person_id,
                "company_id": company_id,
            }
        )
        
        # 生成最近3个月的考勤记录
        for month_offset in range(3):
            period_date = datetime.now() - timedelta(days=30 * month_offset)
            period = period_date.strftime("%Y-%m")
            
            # 随机生成考勤数据
            sick_leave = random.choice([0, 0, 0, 0, 0.5, 1, 1.5, 2])  # 大部分为0，少数有请假
            personal_leave = random.choice([0, 0, 0, 0, 0.5, 1, 2])  # 大部分为0，少数有病假
            
            other = None
            if random.random() < 0.3:  # 30% 概率有其他情况
                other_options = [
                    "调休半天",
                    "外出培训",
                    "出差3天",
                    "加班补休",
                    "年假2天",
                    "婚假3天"
                ]
                other = random.choice(other_options)
            
            # 奖惩金额（大部分为0，少数有奖惩）
            reward_punishment = 0
            if random.random() < 0.2:  # 20% 概率有奖惩
                reward_punishment = random.choice([-200, -100, 0, 100, 200, 300, 500])
            
            state_dao.append("person_company_attendance_record", attendance_record_id, {
                "person_id": person_id,
                "company_id": company_id,
                "period": period,
                "sick_leave_days": float(sick_leave),
                "personal_leave_days": float(personal_leave),
                "other": other,
                "reward_punishment_amount": float(reward_punishment),
            }, time_key=period)
            attendance_record_count += 1
    
    print(f"  生成考勤记录: {attendance_record_count} 条")
    
    print("\n测试数据生成完成！")
    print(f"  公司: {len(companies)} 个")
    print(f"  人员: {len(persons)} 个")
    print(f"  聘用记录: {len(employments)} 个")
    print(f"  打卡记录: {attendance_count} 条")
    print(f"  社保基数记录: {social_base_count} 条")
    print(f"  公积金基数记录: {housing_fund_base_count} 条")
    print(f"  专项附加扣除记录: {tax_deduction_count} 条")
    print(f"  考核记录: {assessment_count} 条")
    print(f"  客户合同: {len(client_contracts)} 个")
    print(f"  订单: {len(orders)} 个")
    print(f"  客户合同-订单关联: {contract_order_count} 条")
    print(f"  内部项目: {len(internal_projects)} 个")
    print(f"  内部项目-订单关联: {project_order_count} 条")
    print(f"  人员参与订单记录: {participation_count} 条")
    print(f"  考勤记录: {attendance_record_count} 条")


if __name__ == "__main__":
    from app.db import init_db
    
    # 初始化数据库
    init_db()
    
    # 生成测试数据
    generate_test_data()
