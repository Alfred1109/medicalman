"""
JSON辅助工具 - 提供健壮的JSON解析和修复功能
"""
import json
import re
import math
from typing import Dict, Any, Optional, List, Union, Tuple

def robust_json_parser(json_str: str) -> Optional[Dict[str, Any]]:
    """
    健壮的JSON解析器，能够处理和修复常见的JSON格式错误
    
    参数:
        json_str: 要解析的JSON字符串
        
    返回:
        解析后的Python对象，如果解析失败则返回None
    """
    if not json_str:
        return None
    
    # 首先尝试直接解析
    try:
        result = json.loads(json_str)
        print("成功直接解析JSON")
        return result
    except json.JSONDecodeError as je:
        print(f"JSON解析错误: {str(je)}")
        
        # 记录详细的错误上下文
        error_pos = je.pos
        error_context = json_str[max(0, error_pos-30):min(len(json_str), error_pos+30)]
        print(f"错误位置: {error_pos}, 上下文: '{error_context}'")
        
        # 尝试修复一些常见的JSON格式问题
        fixed_json = json_str
        
        # 1. 修复属性后缺少逗号的问题
        fixed_json = re.sub(r'}\s*{', '},{', fixed_json)
        fixed_json = re.sub(r']\s*{', '],{', fixed_json)
        fixed_json = re.sub(r'}\s*"', '},"', fixed_json)
        fixed_json = re.sub(r']\s*"', '],"', fixed_json)
        
        # 2. 修复单引号问题
        fixed_json = re.sub(r"'([^']*)':", r'"\1":', fixed_json)
        fixed_json = re.sub(r":\s*'([^']*)'", r': "\1"', fixed_json)
        
        # 3. 修复属性名没有引号的问题
        fixed_json = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', fixed_json)
        
        # 4. 修复多余的逗号问题
        fixed_json = re.sub(r',\s*}', '}', fixed_json)
        fixed_json = re.sub(r',\s*]', ']', fixed_json)
        
        # 5. 处理可能的JavaScript undefined值
        try:
            result = json.loads(fixed_json)
            print("成功修复并解析JSON")
            return result
        except json.JSONDecodeError:
            print("基本修复失败，尝试更激进的修复方法")
        return None

        return None

def aggressive_json_fix(json_str: str) -> Optional[str]:
    """
    使用激进的方法修复JSON字符串中的格式问题
    
    参数:
        json_str: 包含潜在错误的JSON字符串
        
    返回:
        修复后的JSON字符串，如果无法修复则返回None
    """
    if not json_str:
        return None
    
    # 应用一系列更激进的修复规则
    fixed = json_str
    
    # 1. 确保对象和数组有正确的开始和结束
    if not fixed.strip().startswith('{') and not fixed.strip().startswith('['):
        # 尝试找到第一个大括号或中括号
        first_brace = fixed.find('{')
        first_bracket = fixed.find('[')
        
        if first_brace >= 0 and (first_bracket < 0 or first_brace < first_bracket):
            fixed = fixed[first_brace:]
        elif first_bracket >= 0:
            fixed = fixed[first_bracket:]
        else:
            # 没有找到有效的开始标记
            return None
    
    # 确保结束与开始匹配
    if fixed.strip().startswith('{'):
        if not fixed.strip().endswith('}'):
            last_brace = fixed.rfind('}')
            if last_brace >= 0:
                fixed = fixed[:last_brace+1]
            else:
                # 添加结束大括号
                fixed = fixed + '}'
    
    elif fixed.strip().startswith('['):
        if not fixed.strip().endswith(']'):
            last_bracket = fixed.rfind(']')
            if last_bracket >= 0:
                fixed = fixed[:last_bracket+1]
            else:
                # 添加结束中括号
                fixed = fixed + ']'
    
    # 2. 整理修复后的字符串
    fixed = fixed.strip()
    
    # 3. 修复引号问题
    # 将所有单引号替换为双引号（考虑转义情况）
    fixed = re.sub(r"(?<!\\)'", '"', fixed)
    
    # 4. 修复缺少的逗号
    comma_fixes = [
        (r'}\s*{', '},{'),  # 对象之间缺少逗号
        (r'}\s*"', '},\n"'),  # 对象的结束和下一个属性之间缺少逗号
        (r']\s*{', '],{'),  # 数组结束和对象开始之间缺少逗号
        (r'}\s*\[', '},\n['),  # 对象结束和数组开始之间缺少逗号
        (r']\s*"', '],\n"'),  # 数组结束和下一个属性之间缺少逗号
        (r']\s*\[', '],\n[')  # 数组之间缺少逗号
    ]
    
    for pattern, replacement in comma_fixes:
        fixed = re.sub(pattern, replacement, fixed)
    
    # 5. 修复属性名没有引号的问题
    fixed = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', fixed)
    
    # 6. 修复多余的逗号问题
    fixed = re.sub(r',\s*}', '}', fixed)
    fixed = re.sub(r',\s*]', ']', fixed)
    
    # 7. 处理特殊值
    special_values = [
        (r':\s*undefined\b', ': null'),  # undefined -> null
        (r':\s*NaN\b', ': "NaN"'),  # NaN -> "NaN"
        (r':\s*Infinity\b', ': "Infinity"'),  # Infinity -> "Infinity"
        (r':\s*-Infinity\b', ': "-Infinity"')  # -Infinity -> "-Infinity"
    ]
    
    for pattern, replacement in special_values:
        fixed = re.sub(pattern, replacement, fixed)
    
    # 8. 验证修复是否有效
    try:
        json.loads(fixed)
        print(f"成功修复JSON，长度: {len(fixed)}")
        return fixed
    except json.JSONDecodeError as e:
        print(f"激进修复后仍然失败: {str(e)}")
        return None

def extract_json_object(text: str) -> Optional[str]:
    """
    从文本中提取第一个有效的JSON对象
    
    参数:
        text: 包含潜在JSON对象的文本
        
    返回:
        提取的JSON对象字符串，如果没有找到则返回None
    """
    # 尝试找到JSON对象的开始和结束
    obj_start = text.find('{')
    if obj_start < 0:
        return None
    
    # 从开始位置向后查找匹配的右括号
    brace_count = 0
    for i in range(obj_start, len(text)):
        if text[i] == '{':
            brace_count += 1
        elif text[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                # 找到完整的JSON对象
                json_obj = text[obj_start:i+1]
                try:
                    # 验证是否有效
                    json.loads(json_obj)
                    return json_obj
                except:
                    # 继续查找下一个可能的结束位置
                    continue
    
    return None

def clean_json_values(obj: Any) -> Any:
    """
    递归清理JSON对象中的非标准值，如NaN和Infinity
    
    参数:
        obj: 要清理的对象
        
    返回:
        清理后的对象
    """
    if isinstance(obj, dict):
        return {k: clean_json_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_json_values(v) for v in obj]
    elif isinstance(obj, float):
        if math.isnan(obj):
            return "NaN"
        elif math.isinf(obj):
            return "Infinity" if obj > 0 else "-Infinity"
    return obj

def safe_json_dumps(obj: Any, **kwargs) -> str:
    """
    安全地将对象序列化为JSON字符串，处理NaN和Infinity等特殊值
    
    参数:
        obj: 要序列化的对象
        **kwargs: 传递给json.dumps的额外参数
        
    返回:
        JSON字符串
    """
    # 先清理对象中的非标准值
    cleaned_obj = clean_json_values(obj)
    # 然后序列化
    return json.dumps(cleaned_obj, ensure_ascii=False, **kwargs)