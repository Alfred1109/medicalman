from modules.query_processor import process_user_query

# 测试查询
test_message = "分析神经内科小儿专科2024年1月的门诊量目标达成情况"
knowledge_settings = {
    "tables": {
        "outpatient": True,
        "target": True
    },
    "dimensions": {
        "department": True,
        "specialty": True,
        "target_completion": True
    }
}

# 执行查询
result = process_user_query(test_message, knowledge_settings)

# 打印结果
print("\n=== 查询结果 ===")
print(f"成功状态: {result['success']}")
print("\n=== SQL查询结果 ===")
print(result['sql_results'])
print("\n=== 回复内容 ===")
print(result['reply']) 