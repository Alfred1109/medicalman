#!/usr/bin/env python3
"""
这是一个完整的测试脚本，用于测试图表生成功能
"""
import sys
import os
import json
import traceback
from app.services.llm_service import LLMServiceFactory

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 将项目根目录添加到路径中
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

def test_chart_generation():
    """测试图表生成功能"""
    # 使用工厂方法获取图表服务
    chart_service = LLMServiceFactory.get_chart_service()
    
    # 准备测试数据
    test_data = [
        {"日期": "2023年1月", "门诊量": 150, "住院量": 45, "手术量": 30},
        {"日期": "2023年2月", "门诊量": 180, "住院量": 50, "手术量": 35},
        {"日期": "2023年3月", "门诊量": 200, "住院量": 55, "手术量": 40},
        {"日期": "2023年4月", "门诊量": 220, "住院量": 60, "手术量": 45},
        {"日期": "2023年5月", "门诊量": 250, "住院量": 65, "手术量": 50}
    ]
    
    # 用户查询
    user_query = "请根据这些数据生成一个显示门诊量趋势的折线图和一个显示各月手术量的柱状图"
    
    # 将数据转换为JSON字符串
    structured_data = json.dumps(test_data, ensure_ascii=False)
    
    try:
        print("开始测试图表生成功能...")
        print(f"用户查询: {user_query}")
        print(f"测试数据: {structured_data}")
        
        # 使用图表服务生成图表配置
        result = chart_service.generate_chart_config(user_query, structured_data)
        
        if result and "charts" in result and result["charts"]:
            print("\n图表生成成功!")
            print(f"生成的图表数量: {len(result['charts'])}")
            
            # 打印每个图表的基本信息
            for i, chart in enumerate(result["charts"]):
                print(f"\n图表 {i+1}:")
                print(f"  标题: {chart.get('title', '无标题')}")
                print(f"  类型: {chart.get('type', '未知类型')}")
                
                # 显示X轴数据
                x_axis = chart.get("xAxis", {})
                print(f"  X轴名称: {x_axis.get('name', '无名称')}")
                x_data = x_axis.get("data", [])
                print(f"  X轴数据: {x_data[:3]}{'...' if len(x_data) > 3 else ''}")
                
                # 显示系列数据
                series = chart.get("series", [])
                print(f"  数据系列数量: {len(series)}")
                for j, s in enumerate(series[:2]):
                    print(f"    系列 {j+1}: {s.get('name', '无名称')}, 类型: {s.get('type', '未知类型')}")
                    data = s.get("data", [])
                    print(f"    数据: {data[:3]}{'...' if len(data) > 3 else ''}")
                
                if len(series) > 2:
                    print(f"    ... 还有 {len(series) - 2} 个系列")
            
            # 保存生成的图表配置到文件
            with open("chart_config_result.json", "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print("\n图表配置已保存到 chart_config_result.json")
            
            return True
        else:
            print("\n图表生成失败!")
            print(f"结果: {result}")
            return False
            
    except Exception as e:
        print(f"\n测试过程中出错: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_chart_generation()
    
    if success:
        print("\n图表生成测试通过!")
        sys.exit(0)
    else:
        print("\n图表生成测试失败!")
        sys.exit(1) 