#!/usr/bin/env python3
"""
这是一个简单的测试脚本，用于测试修改后的图表生成功能
"""
import sys
import os
import json
import re

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 将项目根目录添加到路径中
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# 测试json解析和修复功能
def test_json_fix():
    # 导入JSON辅助函数
    from app.utils.json_helper import robust_json_parser, fix_json_format
    
    # 测试缺少逗号的JSON
    test_json = '{ "charts": [ { "title": "2023年医院门诊量统计", "type": "bar", "xAxis": { "type": "category", "data": ["1月", "2月", "3月"] "name": "门诊量类型" }, "yAxis": { "type": "value", "name": "门诊数量" }, "series": [ { "name": "普通门诊", "data": [150, 200, 250], "type": "bar" } ] } ] }'
    
    print("测试JSON修复功能:")
    print("原始JSON:", test_json)
    
    # 尝试修复和解析
    result = robust_json_parser(test_json)
    
    # 显示结果
    if result:
        print("修复成功!")
        print("解析结果:", json.dumps(result, ensure_ascii=False, indent=2))
        return True
    else:
        print("修复失败!")
        return False

# 测试指标名称后缺少逗号的情况
def test_indicator_name_fix():
    from app.utils.json_helper import robust_json_parser, fix_json_format
    
    # 测试中文指标名称后缺少逗号的JSON
    test_json = '{ "charts": [ { "title": "2023年医院门诊量统计", "type": "bar", "xAxis": { "type": "category", "data": ["1月", "2月", "3月"], "name": "月份" }, "yAxis": { "type": "value", "name": "指标" } "series": [ { "name": "门诊量", "data": [150, 200, 250], "type": "bar" } ] } ] }'
    
    print("\n测试中文指标名称修复功能:")
    print("原始JSON:", test_json)
    
    # 尝试修复和解析
    result = robust_json_parser(test_json)
    
    # 显示结果
    if result:
        print("修复成功!")
        print("解析结果:", json.dumps(result, ensure_ascii=False, indent=2))
        return True
    else:
        print("修复失败!")
        return False

if __name__ == "__main__":
    print("开始测试JSON修复功能...")
    success1 = test_json_fix()
    success2 = test_indicator_name_fix()
    
    if success1 and success2:
        print("\n所有测试通过!")
        sys.exit(0)
    else:
        print("\n测试失败!")
        sys.exit(1) 