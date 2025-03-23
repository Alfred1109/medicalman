#!/usr/bin/env python3
"""
专门测试中文属性值后缺少逗号的JSON修复
"""
import sys
import os
import json
import traceback

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 将项目根目录添加到路径中
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

def test_chinese_property_fix():
    """测试中文属性值后缺少逗号的修复功能"""
    from app.utils.json_helper import robust_json_parser, fix_chinese_property_commas
    
    # 测试用例1：中文属性值后缺少逗号（直接紧跟另一个属性）
    test_json1 = """
    {
      "charts": [
        {
          "title": "医院门诊量统计",
          "type": "bar",
          "xAxis": {
            "type": "category",
            "data": ["1月", "2月", "3月"],
            "name": "月份"
          },
          "yAxis": {
            "type": "value",
            "name": "指标"
          "series": [
            {
              "name": "门诊量",
              "data": [150, 200, 250],
              "type": "bar"
            }
          ]
        }
      ]
    }
    """
    
    # 测试用例2：中文属性值后缺少逗号（紧跟对象结束）
    test_json2 = """
    {
      "charts": [
        {
          "title": "医院门诊量统计",
          "type": "bar",
          "xAxis": {
            "type": "category",
            "data": ["1月", "2月", "3月"],
            "name": "月份"
          },
          "yAxis": {
            "type": "value",
            "name": "指标"
          }
          "series": [
            {
              "name": "门诊量",
              "data": [150, 200, 250],
              "type": "bar"
            }
          ]
        }
      ]
    }
    """
    
    # 测试用例3：多处中文属性值后缺少逗号
    test_json3 = """
    {
      "charts": [
        {
          "title": "医院统计分析"
          "type": "line",
          "xAxis": {
            "type": "category"
            "data": ["1月", "2月", "3月"]
            "name": "月份"
          },
          "yAxis": {
            "type": "value"
            "name": "指标"
          },
          "series": [
            {
              "name": "门诊量"
              "data": [150, 200, 250]
              "type": "line"
            }
          ]
        }
      ]
    }
    """
    
    # 测试用例4：原始错误提示中的案例
    test_json4 = """
    {
      "charts": [
        {
          "title": "医院月度门诊量分析",
          "type": "line",
          "xAxis": {
            "type": "category",
            "data": ["1月", "2月", "3月", "4月", "5月"],
            "name": "月份" 
          },
          "yAxis": {
            "type": "value",
            "name": "指标"
          }
          "series": [
            {
              "name": "门诊量",
              "data": [150, 180, 200, 220, 250],
              "type": "line"
            }
          ]
        }
      ]
    }
    """
    
    tests = [
        ("测试用例1: 中文属性值后缺少逗号（直接紧跟另一个属性）", test_json1),
        ("测试用例2: 中文属性值后缺少逗号（紧跟对象结束）", test_json2),
        ("测试用例3: 多处中文属性值后缺少逗号", test_json3),
        ("测试用例4: 原始错误提示中的案例", test_json4)
    ]
    
    success_count = 0
    
    for name, test_json in tests:
        print(f"\n===== {name} =====")
        print(f"原始JSON (部分):\n{test_json[:200]}...")
        
        try:
            # 尝试直接解析
            try:
                json.loads(test_json)
                print("原JSON能直接解析，不需要修复")
                success_count += 1
                continue
            except json.JSONDecodeError as je:
                print(f"JSON解析错误: {str(je)}")
            
            # 使用中文属性修复函数
            print("\n1. 尝试使用专门的中文属性修复函数:")
            fixed_json = fix_chinese_property_commas(test_json)
            if fixed_json == test_json:
                print("  - 中文属性修复函数未进行任何修改")
            else:
                print("  - 修复函数进行了修改")
                try:
                    json.loads(fixed_json)
                    print("  - 修复后的JSON可以成功解析!")
                    success_count += 1
                    continue
                except json.JSONDecodeError as je2:
                    print(f"  - 修复后仍有错误: {str(je2)}")
            
            # 使用健壮解析器
            print("\n2. 尝试使用健壮JSON解析器:")
            result = robust_json_parser(test_json)
            if result:
                print("  - 健壮JSON解析器成功解析!")
                print(f"  - 图表数量: {len(result.get('charts', []))}")
                success_count += 1
            else:
                print("  - 健壮JSON解析器也无法解析")
                
        except Exception as e:
            print(f"测试过程中出错: {str(e)}")
            traceback.print_exc()
    
    # 汇总结果
    print(f"\n===== 测试结果汇总 =====")
    print(f"成功修复: {success_count}/{len(tests)}")
    
    return success_count == len(tests)

if __name__ == "__main__":
    if test_chinese_property_fix():
        print("\n所有测试通过!")
        sys.exit(0)
    else:
        print("\n部分测试失败!")
        sys.exit(1) 