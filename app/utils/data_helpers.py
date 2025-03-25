"""
数据处理辅助函数模块 - 提供数据处理相关的辅助函数
"""

from datetime import datetime, timedelta
import pandas as pd


def date_range_to_dates(date_range):
    """
    根据日期范围字符串生成开始日期和结束日期
    
    参数:
        date_range: 日期范围字符串 (today, yesterday, week, month, quarter, year)
        
    返回:
        包含开始日期和结束日期的元组 (start_date, end_date)，格式为'YYYY-MM-DD'
    """
    today = datetime.now().date()
    
    if date_range == 'today':
        start_date = today.strftime('%Y-%m-%d')
        end_date = start_date
    elif date_range == 'yesterday':
        yesterday = today - timedelta(days=1)
        start_date = yesterday.strftime('%Y-%m-%d')
        end_date = start_date
    elif date_range == 'week':
        # 本周一到今天
        start_date = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
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
        start_date = (today - timedelta(days=6)).strftime('%Y-%m-%d')
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


def format_number(value, precision=2, with_commas=True, with_prefix=None):
    """
    格式化数字为易读的字符串
    
    参数:
        value: 要格式化的数值
        precision: 小数点后的精度
        with_commas: 是否使用逗号分隔千位
        with_prefix: 可选前缀，例如货币符号
        
    返回:
        格式化后的字符串
    """
    if value is None:
        return "N/A"
    
    try:
        # 将值转换为浮点数
        float_value = float(value)
        
        # 格式化数字
        if with_commas:
            formatted = f"{float_value:,.{precision}f}"
        else:
            formatted = f"{float_value:.{precision}f}"
        
        # 添加前缀
        if with_prefix:
            formatted = f"{with_prefix}{formatted}"
            
        return formatted
    except (ValueError, TypeError):
        return str(value) 