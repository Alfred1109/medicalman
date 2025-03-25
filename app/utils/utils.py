"""
通用工具函数模块 - 提供项目中的通用工具函数
"""
import os
import re
import uuid
import datetime
import hashlib
import json
from typing import Dict, List, Any, Optional, Union, Tuple
import string
import random
from werkzeug.utils import secure_filename
from flask import current_app
from app.config import config

# 文件处理相关函数
def allowed_file(filename: str, file_type: str = None) -> bool:
    """
    检查文件扩展名是否允许
    
    参数:
        filename: 文件名
        file_type: 文件类型 ('document', 'image', 'spreadsheet')
        
    返回:
        是否允许
    """
    if not filename or '.' not in filename:
        return False
        
    ext = filename.rsplit('.', 1)[1].lower()
    
    # 从应用配置中获取允许的扩展名
    allowed_extensions = config.ALLOWED_EXTENSIONS
    
    if file_type in allowed_extensions:
        return ext in allowed_extensions[file_type]
    return False

def get_secure_filename(filename: str) -> str:
    """
    获取安全的文件名
    
    参数:
        filename: 原始文件名
        
    返回:
        安全的文件名
    """
    # 首先使用werkzeug的secure_filename
    secure_name = secure_filename(filename)
    
    # 如果文件名被完全过滤掉了，生成一个随机文件名
    if not secure_name:
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else config.UTILS['file']['default_extension']
        secure_name = f"file_{generate_uuid()}"
        if ext:
            secure_name = f"{secure_name}.{ext}"
            
    return secure_name

def get_file_path(filename: str, file_type: str = None) -> str:
    """
    获取文件的保存路径
    
    参数:
        filename: 文件名
        file_type: 文件类型
        
    返回:
        文件保存路径
    """
    secure_name = get_secure_filename(filename)
    timestamp = datetime.datetime.now().strftime(config.UTILS['file']['timestamp_format'])
    filename_with_timestamp = f"{timestamp}_{secure_name}"
    
    # 从应用配置中获取上传目录
    if file_type == 'image':
        upload_dir = config.IMAGE_UPLOAD_DIR
    else:
        upload_dir = config.DOCUMENT_UPLOAD_DIR
    
    return os.path.join(upload_dir, filename_with_timestamp)

def get_file_extension(filename: str) -> str:
    """
    获取文件扩展名
    
    参数:
        filename: 文件名
        
    返回:
        文件扩展名
    """
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else config.UTILS['file']['default_extension']

def get_mime_type(file_extension: str) -> str:
    """
    根据文件扩展名获取MIME类型
    
    参数:
        file_extension: 文件扩展名
        
    返回:
        MIME类型
    """
    return config.UTILS['mime_types'].get(file_extension.lower(), config.UTILS['file']['default_mime_type'])

# 字符串处理函数
def remove_html_tags(text: str) -> str:
    """
    移除HTML标签
    
    参数:
        text: 输入文本
        
    返回:
        清理后的文本
    """
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def truncate_text(text: str, max_length: int = None, suffix: str = None) -> str:
    """
    截断文本到指定长度
    
    参数:
        text: 输入文本
        max_length: 最大长度
        suffix: 后缀
        
    返回:
        截断后的文本
    """
    max_length = max_length or config.UTILS['text']['max_length']
    suffix = suffix or config.UTILS['text']['suffix']
    
    if len(text) <= max_length:
        return text
        
    return text[:max_length].rsplit(' ', 1)[0] + suffix

def slugify(text: str) -> str:
    """
    将文本转换为URL友好的格式
    
    参数:
        text: 输入文本
        
    返回:
        转换后的文本
    """
    text = re.sub(r'[^\w\s-]', '', text.lower())
    text = re.sub(r'[\s-]+', '-', text).strip('-_')
    return text

# ID生成函数
def generate_uuid() -> str:
    """
    生成UUID
    
    返回:
        UUID字符串
    """
    return str(uuid.uuid4())

def generate_random_id(length: int = 8) -> str:
    """
    生成指定长度的随机ID
    
    参数:
        length: ID长度
        
    返回:
        随机ID
    """
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# 数据处理函数
def flatten_dict(nested_dict: Dict, parent_key: str = '', separator: str = '.') -> Dict:
    """
    扁平化嵌套字典
    
    参数:
        nested_dict: 嵌套字典
        parent_key: 父键
        separator: 分隔符
        
    返回:
        扁平化后的字典
    """
    items = []
    for key, value in nested_dict.items():
        new_key = f"{parent_key}{separator}{key}" if parent_key else key
        
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, separator).items())
        else:
            items.append((new_key, value))
            
    return dict(items)

def deep_merge(dict1: Dict, dict2: Dict) -> Dict:
    """
    深度合并两个字典
    
    参数:
        dict1: 第一个字典
        dict2: 第二个字典
        
    返回:
        合并后的字典
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
            
    return result

def safe_get(obj: Any, path: str, default: Any = None, separator: str = '.') -> Any:
    """
    安全获取嵌套对象的值
    
    参数:
        obj: 对象
        path: 路径
        default: 默认值
        separator: 分隔符
        
    返回:
        获取的值或默认值
    """
    keys = path.split(separator)
    
    for key in keys:
        if isinstance(obj, dict):
            obj = obj.get(key, default)
            if obj is default:
                return default
        elif isinstance(obj, (list, tuple)) and key.isdigit():
            index = int(key)
            if 0 <= index < len(obj):
                obj = obj[index]
            else:
                return default
        else:
            return default
            
    return obj

# 日期时间处理函数
def format_datetime(dt: datetime.datetime, format_str: str = None) -> str:
    """
    格式化日期时间
    
    参数:
        dt: 日期时间对象
        format_str: 格式字符串
        
    返回:
        格式化后的字符串
    """
    format_str = format_str or config.UTILS['datetime']['default_format']
    return dt.strftime(format_str)

def parse_datetime(datetime_str: str, format_str: str = None) -> Optional[datetime.datetime]:
    """
    解析日期时间字符串
    
    参数:
        datetime_str: 日期时间字符串
        format_str: 格式字符串
        
    返回:
        日期时间对象或None
    """
    format_str = format_str or config.UTILS['datetime']['default_format']
    try:
        return datetime.datetime.strptime(datetime_str, format_str)
    except ValueError:
        return None

def get_current_timestamp() -> int:
    """
    获取当前时间戳
    
    返回:
        时间戳
    """
    return int(datetime.datetime.now().timestamp())

# 加密和哈希函数
def md5_hash(text: str) -> str:
    """
    计算MD5哈希
    
    参数:
        text: 输入文本
        
    返回:
        MD5哈希值
    """
    return hashlib.md5(text.encode()).hexdigest()

def sha256_hash(text: str) -> str:
    """
    计算SHA256哈希
    
    参数:
        text: 输入文本
        
    返回:
        SHA256哈希值
    """
    return hashlib.sha256(text.encode()).hexdigest()

# 格式化和验证函数
def is_valid_email(email: str) -> bool:
    """
    验证电子邮件地址
    
    参数:
        email: 电子邮件地址
        
    返回:
        是否有效
    """
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))

def is_valid_phone(phone: str) -> bool:
    """
    验证电话号码
    
    参数:
        phone: 电话号码
        
    返回:
        是否有效
    """
    # 移除空格和连字符等
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    # 检查是否为纯数字且长度合理
    return cleaned.isdigit() and 8 <= len(cleaned) <= 15

def format_number(number: Union[int, float], decimal_places: int = None) -> str:
    """
    格式化数字
    
    参数:
        number: 数字
        decimal_places: 小数位数
        
    返回:
        格式化后的字符串
    """
    decimal_places = decimal_places or config.UTILS['number']['decimal_places']
    return f"{number:.{decimal_places}f}"

def format_currency(amount: Union[int, float], currency: str = None, decimal_places: int = None) -> str:
    """
    格式化货币金额
    
    参数:
        amount: 金额
        currency: 货币符号
        decimal_places: 小数位数
        
    返回:
        格式化后的字符串
    """
    currency = currency or config.UTILS['number']['currency_symbol']
    decimal_places = decimal_places or config.UTILS['number']['decimal_places']
    return f"{currency}{amount:.{decimal_places}f}"

def format_percentage(value: float, decimal_places: int = None) -> str:
    """
    格式化百分比
    
    参数:
        value: 值
        decimal_places: 小数位数
        
    返回:
        格式化后的字符串
    """
    decimal_places = decimal_places or config.UTILS['number']['decimal_places']
    return config.UTILS['number']['percentage_format'].format(value)

# JSON处理函数
def to_json(obj: Any, ensure_ascii: bool = False) -> str:
    """
    将对象转换为JSON字符串
    
    参数:
        obj: 对象
        ensure_ascii: 是否确保ASCII
        
    返回:
        JSON字符串
    """
    return json.dumps(obj, ensure_ascii=ensure_ascii)

def from_json(json_str: str) -> Any:
    """
    将JSON字符串转换为对象
    
    参数:
        json_str: JSON字符串
        
    返回:
        对象
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None

# 列表处理函数
def chunks(lst: List, n: int) -> List[List]:
    """
    将列表分割为指定大小的块
    
    参数:
        lst: 列表
        n: 块大小
        
    返回:
        分割后的列表
    """
    return [lst[i:i + n] for i in range(0, len(lst), n)]

def unique(lst: List) -> List:
    """
    获取列表中的唯一元素，保持原顺序
    
    参数:
        lst: 列表
        
    返回:
        唯一元素列表
    """
    seen = set()
    result = []
    
    for item in lst:
        if item not in seen:
            seen.add(item)
            result.append(item)
            
    return result

# 整合自helpers.py的功能
def get_current_date() -> str:
    """
    获取当前日期
    
    返回:
        当前日期字符串，格式为YYYY-MM-DD
    """
    return datetime.datetime.now().strftime('%Y-%m-%d')

def dataframe_to_dict_list(df) -> List[Dict[str, Any]]:
    """
    将DataFrame转换为字典列表
    
    参数:
        df: DataFrame对象
            
    返回:
        字典列表
    """
    return df.to_dict(orient='records')

def dict_list_to_dataframe(dict_list: List[Dict[str, Any]]):
    """
    将字典列表转换为DataFrame
    
    参数:
        dict_list: 字典列表
            
    返回:
        DataFrame对象
    """
    import pandas as pd
    return pd.DataFrame(dict_list)

# 整合自json_helper.py的功能
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
        return result
    except json.JSONDecodeError as je:
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
            return result
        except json.JSONDecodeError:
            return None

def clean_json_values(obj: Any) -> Any:
    """
    递归清理JSON对象中的非标准值，如NaN和Infinity
    
    参数:
        obj: 要清理的对象
        
    返回:
        清理后的对象
    """
    import math
    
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

def safe_json_dumps(obj, ensure_ascii=False):
    """
    安全地将Python对象转换为JSON字符串，处理错误情况
    
    参数:
        obj: 要转换的Python对象
        ensure_ascii: 是否强制ASCII编码
        
    返回:
        JSON字符串
    """
    try:
        if isinstance(obj, (list, dict, str, int, float, bool, type(None))):
            return json.dumps(obj, ensure_ascii=ensure_ascii)
        else:
            # 尝试将对象转换为可序列化的字典
            if hasattr(obj, '__dict__'):
                return json.dumps(obj.__dict__, ensure_ascii=ensure_ascii)
            else:
                # 最后尝试直接转换为字符串
                return json.dumps(str(obj), ensure_ascii=ensure_ascii)
    except Exception as e:
        print(f"JSON序列化失败: {str(e)}")
        return json.dumps({"error": "无法序列化对象"}, ensure_ascii=ensure_ascii)

def safe_json_loads(json_str):
    """
    安全地解析JSON字符串为Python对象，处理错误情况
    
    参数:
        json_str: 要解析的JSON字符串
        
    返回:
        解析后的Python对象，失败时返回None或原字符串
    """
    if not json_str:
        return None
        
    try:
        if isinstance(json_str, str):
            return json.loads(json_str)
        elif isinstance(json_str, (dict, list)):
            # 已经是Python对象，直接返回
            return json_str
        else:
            # 尝试转换为字符串后解析
            return json.loads(str(json_str))
    except Exception as e:
        print(f"JSON解析失败: {str(e)}")
        return json_str  # 失败时返回原始字符串

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

# 整合自data_helpers.py的函数

def date_range_to_dates(date_range):
    """
    根据日期范围字符串生成开始日期和结束日期
    
    参数:
        date_range: 日期范围字符串 (today, yesterday, week, month, quarter, year)
        
    返回:
        包含开始日期和结束日期的元组 (start_date, end_date)，格式为'YYYY-MM-DD'
    """
    today = datetime.datetime.now().date()
    
    if date_range == 'today':
        start_date = today.strftime('%Y-%m-%d')
        end_date = start_date
    elif date_range == 'yesterday':
        yesterday = today - datetime.timedelta(days=1)
        start_date = yesterday.strftime('%Y-%m-%d')
        end_date = start_date
    elif date_range == 'week':
        # 本周一到今天
        start_date = (today - datetime.timedelta(days=today.weekday())).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
    elif date_range == 'month':
        # 本月1日到今天
        start_date = f"{today.year}-{today.month:02d}-01"
        end_date = today.strftime('%Y-%m-%d')
    elif date_range == 'quarter':
        # 本季度第一个月1日到今天
        quarter_start_month = ((today.month - 1) // 3) * 3 + 1
        start_date = f"{today.year}-{quarter_start_month:02d}-01"
        end_date = today.strftime('%Y-%m-%d')
    elif date_range == 'year':
        # 本年1月1日到今天
        start_date = f"{today.year}-01-01"
        end_date = today.strftime('%Y-%m-%d')
    else:
        # 默认返回最近7天
        start_date = (today - datetime.timedelta(days=6)).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
    
    return (start_date, end_date)

def ensure_date_continuity(df, date_col, start_date, end_date, value_col=None, fill_value=0):
    """
    确保数据框中的日期连续，如果有缺失的日期则填充
    
    参数:
        df: 包含日期的数据框
        date_col: 日期列的名称
        start_date: 开始日期（字符串格式'YYYY-MM-DD'）
        end_date: 结束日期（字符串格式'YYYY-MM-DD'）
        value_col: 需要填充的值列名称（如果提供）
        fill_value: 用于填充缺失值的默认值
        
    返回:
        处理后的数据框，包含连续的日期
    """
    import pandas as pd
    
    # 创建日期范围
    all_dates = pd.date_range(start=start_date, end=end_date)
    date_df = pd.DataFrame({date_col: all_dates})
    date_df[date_col] = date_df[date_col].dt.strftime('%Y-%m-%d')
    
    # 确保df中的日期列是字符串类型
    if df is not None and not df.empty:
        df[date_col] = df[date_col].astype(str)
        
        # 合并数据
        if value_col:
            merged_df = pd.merge(date_df, df, on=date_col, how='left')
            merged_df[value_col] = merged_df[value_col].fillna(fill_value)
            return merged_df
        else:
            return pd.merge(date_df, df, on=date_col, how='left')
    else:
        # 如果原始数据框为空，则返回只有日期的数据框
        return date_df

def aggregate_by_period(df, date_col, value_col, period='day'):
    """
    按指定时间周期聚合数据
    
    参数:
        df: 包含日期的数据框
        date_col: 日期列的名称
        value_col: 值列的名称
        period: 聚合周期 ('day', 'week', 'month', 'quarter', 'year')
        
    返回:
        聚合后的数据框
    """
    import pandas as pd
    
    # 确保日期列是datetime类型
    df[date_col] = pd.to_datetime(df[date_col])
    
    # 根据不同周期设置分组键
    if period == 'day':
        # 按天分组，不需要额外处理
        grouped = df.groupby(df[date_col].dt.strftime('%Y-%m-%d'))
    elif period == 'week':
        # 按周分组
        grouped = df.groupby(df[date_col].dt.strftime('%Y-%W'))
    elif period == 'month':
        # 按月分组
        grouped = df.groupby(df[date_col].dt.strftime('%Y-%m'))
    elif period == 'quarter':
        # 按季度分组
        grouped = df.groupby([df[date_col].dt.year, df[date_col].dt.quarter])
    elif period == 'year':
        # 按年分组
        grouped = df.groupby(df[date_col].dt.year)
    else:
        # 默认按天分组
        grouped = df.groupby(df[date_col].dt.strftime('%Y-%m-%d'))
    
    # 聚合并重置索引
    result = grouped[value_col].sum().reset_index()
    
    # 格式化日期标签
    if period == 'day':
        result.columns = [date_col, value_col]
    elif period == 'week':
        result.columns = ['period', value_col]
        result['period'] = result['period'].apply(lambda x: f"第{x.split('-')[1]}周")
    elif period == 'month':
        result.columns = ['period', value_col]
        result['period'] = result['period'].apply(lambda x: f"{x}月")
    elif period == 'quarter':
        result.columns = ['year', 'quarter', value_col]
        result['period'] = result.apply(lambda x: f"{int(x['year'])}年Q{int(x['quarter'])}", axis=1)
        result = result[['period', value_col]]
    elif period == 'year':
        result.columns = ['year', value_col]
        result['period'] = result['year'].apply(lambda x: f"{int(x)}年")
        result = result[['period', value_col]]
    
    return result 