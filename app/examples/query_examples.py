"""
Twin Query DAO 使用示例 - 演示基于属性的过滤查询
"""
from app.daos.twins.state_dao import TwinStateDAO
from app.daos.twins.twin_dao import TwinDAO
from app.daos.twins.state_dao import TwinStateDAO


def example_query_by_json_field():
    """示例：通过 JSON 字段查询"""
    print("=" * 50)
    print("通过 JSON 字段查询示例")
    print("=" * 50)
    
    # 初始化 DAO
    twin_dao = TwinDAO(db_path=":memory:")
    state_dao = TwinStateDAO(db_path=":memory:")
    query_dao = TwinStateDAO(db_path=":memory:")
    
    # 创建 Person 并添加状态
    person_id1 = twin_dao.create_entity_twin("person")
    state_dao.append("person", person_id1, {
        "name": "张三",
        "phone": "13800138000",
        "email": "zhangsan@example.com",
    })
    
    person_id2 = twin_dao.create_entity_twin("person")
    state_dao.append("person", person_id2, {
        "name": "李四",
        "phone": "13900139000",
        "email": "lisi@example.com",
    })
    
    # 查询：通过姓名查询
    results = query_dao.query_by_json_field("person", "name", "张三")
    print(f"查询 name='张三': 找到 {len(results)} 条记录")
    for state in results:
        print(f"  Twin ID: {state.twin_id}, 数据: {state.data}")
    
    # 查询：通过电话查询
    results = query_dao.query_by_json_field("person", "phone", "13900139000")
    print(f"\n查询 phone='13900139000': 找到 {len(results)} 条记录")
    for state in results:
        print(f"  Twin ID: {state.twin_id}, 数据: {state.data}")


def example_query_with_filters():
    """示例：使用多个过滤条件查询"""
    print("\n" + "=" * 50)
    print("多条件过滤查询示例")
    print("=" * 50)
    
    twin_dao = TwinDAO(db_path=":memory:")
    state_dao = TwinStateDAO(db_path=":memory:")
    query_dao = TwinStateDAO(db_path=":memory:")
    
    # 创建公司和雇佣关系
    person_id = twin_dao.create_entity_twin("person")
    company_id = twin_dao.create_entity_twin("company")
    
    # 创建雇佣活动
    employment_id1 = twin_dao.create_activity_twin(
        "person_company_employment",
        {"person_id": person_id, "company_id": company_id}
    )
    
    # 添加状态
    state_dao.append("person_company_employment", employment_id1, {
        "change_type": "入职",
        "position": "软件工程师",
        "department": "研发部",
        "employee_type": "正式员工",
    })
    
    # 查询：通过部门查询
    results = query_dao.query_states(
        "person_company_employment",
        filters={"department": "研发部"}
    )
    print(f"查询 department='研发部': 找到 {len(results)} 条记录")
    for state in results:
        print(f"  Activity ID: {state.twin_id}, 数据: {state.data}")
    
    # 查询：通过职位和部门查询
    results = query_dao.query_states(
        "person_company_employment",
        filters={
            "position": "软件工程师",
            "department": "研发部",
        }
    )
    print(f"\n查询 position='软件工程师' AND department='研发部': 找到 {len(results)} 条记录")


def example_query_latest_with_filters():
    """示例：查询最新状态（带过滤条件）"""
    print("\n" + "=" * 50)
    print("查询最新状态（带过滤）示例")
    print("=" * 50)
    
    twin_dao = TwinDAO(db_path=":memory:")
    state_dao = TwinStateDAO(db_path=":memory:")
    query_dao = TwinStateDAO(db_path=":memory:")
    
    # 创建多个 Person
    person_ids = []
    for i, name in enumerate(["张三", "李四", "王五"], 1):
        person_id = twin_dao.create_entity_twin("person")
        person_ids.append(person_id)
        state_dao.append("person", person_id, {
            "name": name,
            "phone": f"1380000{1000 + i}",
        })
    
    # 查询所有最新状态
    all_latest = query_dao.query_latest_states("person")
    print(f"所有 Person 的最新状态: {len(all_latest)} 条")
    
    # 查询特定姓名的最新状态
    latest = query_dao.query_latest_states(
        "person",
        filters={"name": "张三"}
    )
    print(f"\n查询 name='张三' 的最新状态: {len(latest)} 条")
    if latest:
        print(f"  数据: {latest[0].data}")


def example_complex_query():
    """示例：复杂查询（时间序列 + JSON 字段）"""
    print("\n" + "=" * 50)
    print("复杂查询示例（时间序列）")
    print("=" * 50)
    
    twin_dao = TwinDAO(db_path=":memory:")
    state_dao = TwinStateDAO(db_path=":memory:")
    query_dao = TwinStateDAO(db_path=":memory:")
    
    # 创建打卡活动
    person_id = twin_dao.create_entity_twin("person")
    company_id = twin_dao.create_entity_twin("company")
    attendance_id = twin_dao.create_activity_twin(
        "person_company_attendance",
        {"person_id": person_id, "company_id": company_id}
    )
    
    # 添加多天打卡记录
    for date, status in [("2024-01-01", "正常"), ("2024-01-02", "迟到"), ("2024-01-03", "正常")]:
        state_dao.append(
            "person_company_attendance",
            attendance_id,
            {
                "check_in_time": "09:00:00",
                "work_hours": 8.0,
                "status": status,
            },
            time_key=date
        )
    
    # 查询：状态为"正常"的打卡记录
    results = query_dao.query_states(
        "person_company_attendance",
        filters={"status": "正常"},
        order_by="time_key DESC"
    )
    print(f"查询 status='正常' 的打卡记录: {len(results)} 条")
    for state in results:
        print(f"  日期: {state.time_key}, 状态: {state.data.get('status')}")


if __name__ == "__main__":
    print("Twin Query DAO 使用示例")
    print("注意：这些示例需要先初始化数据库表结构")
    print("\n")
    
    # 示例 1: 通过 JSON 字段查询
    # example_query_by_json_field()
    
    # 示例 2: 多条件过滤查询
    # example_query_with_filters()
    
    # 示例 3: 查询最新状态（带过滤）
    # example_query_latest_with_filters()
    
    # 示例 4: 复杂查询
    # example_complex_query()
    
    print("请先实现数据库初始化功能，然后取消注释示例代码运行")
