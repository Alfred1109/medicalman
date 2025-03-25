"""
数据分析和可视化工具模块
提供了数据分析、数据可视化、数据透视表等功能
"""
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import seaborn as sns
import matplotlib.pyplot as plt
import importlib.util
import sys
import io
import json
import base64
from typing import Dict, List, Any, Optional, Tuple, Union
import importlib

# 在app/__init__.py中我们已经判断了ydata_profiling的可用性，这里直接导入全局变量
from app import YDATA_PROFILING_AVAILABLE

# 尝试导入ydata_profiling
if YDATA_PROFILING_AVAILABLE:
    from ydata_profiling import ProfileReport  # 替代pandas_profiling

from app.utils.database import execute_query_to_dataframe

class DataAnalyzer:
    """
    数据分析工具类，提供数据分析和可视化功能
    """
    
    @staticmethod
    def generate_profile_report(df, title="数据分析报告", minimal=False):
        """
        生成数据分析报告
        
        参数:
            df: DataFrame数据
            title: 报告标题
            minimal: 是否生成最小化报告
            
        返回:
            报告HTML字符串
        """
        try:
            if not YDATA_PROFILING_AVAILABLE:
                return "<p>未安装ydata_profiling包，数据分析报告功能不可用</p>"
                
            # 设置中文显示
            profile = ProfileReport(df, title=title, minimal=minimal, 
                                    explorative=not minimal,
                                    html={'style':{'full_width':True}})
            
            # 返回HTML报告
            return profile.to_html()
        except Exception as e:
            print(f"生成数据分析报告出错: {str(e)}")
            return f"<p>生成报告出错: {str(e)}</p>"
    
    @staticmethod
    def generate_profile_report_for_query(query, params=None, title="数据分析报告", minimal=False):
        """
        根据SQL查询生成数据分析报告
        
        参数:
            query: SQL查询
            params: 查询参数
            title: 报告标题
            minimal: 是否生成最小化报告
            
        返回:
            报告HTML字符串
        """
        try:
            if not YDATA_PROFILING_AVAILABLE:
                return "<p>未安装ydata_profiling包，数据分析报告功能不可用</p>"
                
            # 执行查询
            df = execute_query_to_dataframe(query, params)
            
            if df.empty:
                return "<p>查询结果为空，无法生成报告</p>"
            
            # 生成报告
            return DataAnalyzer.generate_profile_report(df, title, minimal)
        except Exception as e:
            print(f"生成查询数据分析报告出错: {str(e)}")
            return f"<p>生成报告出错: {str(e)}</p>"
    
    @staticmethod
    def create_pivot_table(df, index, columns=None, values=None, aggfunc='mean'):
        """
        创建数据透视表
        
        参数:
            df: DataFrame数据
            index: 行索引
            columns: 列索引
            values: 统计值
            aggfunc: 聚合函数
            
        返回:
            透视表DataFrame
        """
        try:
            # 创建透视表
            pivot_table = pd.pivot_table(df, index=index, columns=columns, 
                                         values=values, aggfunc=aggfunc)
            return pivot_table
        except Exception as e:
            print(f"创建数据透视表出错: {str(e)}")
            return pd.DataFrame()

    @staticmethod
    def create_correlation_heatmap(df, method='pearson'):
        """
        创建相关性热图
        
        参数:
            df: DataFrame数据
            method: 相关性计算方法
            
        返回:
            Plotly图表对象
        """
        try:
            # 计算相关性
            numeric_df = df.select_dtypes(include=[np.number])
            
            if numeric_df.empty:
                raise ValueError("没有找到数值型列，无法计算相关性")
                
            corr = numeric_df.corr(method=method)
            
            # 创建热图
            fig = px.imshow(
                corr.values,
                labels=dict(x="特征", y="特征", color="相关性"),
                x=corr.columns,
                y=corr.columns,
                color_continuous_scale="RdBu_r",
                title="特征相关性热图"
            )
            
            # 添加文本标注
            for i in range(len(corr)):
                for j in range(len(corr)):
                    fig.add_annotation(
                        x=j, y=i,
                        text=str(round(corr.iloc[i, j], 2)),
                        showarrow=False,
                        font=dict(color="black" if abs(corr.iloc[i, j]) < 0.6 else "white")
                    )
            
            return fig
        except Exception as e:
            print(f"创建相关性热图出错: {str(e)}")
            return None

    @staticmethod
    def analyze_outpatient_trends(df, time_column='日期', value_column='数量', groupby_column=None):
        """
        分析门诊量趋势
        
        参数:
            df: DataFrame数据
            time_column: 时间列名
            value_column: 数值列名
            groupby_column: 分组列名
            
        返回:
            分析结果字典
        """
        try:
            if df.empty:
                return {"error": "数据为空"}
            
            # 确保时间列为日期类型
            df[time_column] = pd.to_datetime(df[time_column])
            
            # 添加年月列
            df['年月'] = df[time_column].dt.strftime('%Y-%m')
            
            # 按年月汇总
            if groupby_column:
                monthly_data = df.groupby([groupby_column, '年月'])[value_column].sum().reset_index()
                
                # 计算各分组的趋势指标
                results = {}
                for group in monthly_data[groupby_column].unique():
                    group_data = monthly_data[monthly_data[groupby_column] == group]
                    
                    # 计算总量、均值、最大值、最小值、增长率
                    total = group_data[value_column].sum()
                    avg = group_data[value_column].mean()
                    max_val = group_data[value_column].max()
                    min_val = group_data[value_column].min()
                    
                    # 计算环比增长率
                    group_data = group_data.sort_values('年月')
                    group_data['增长率'] = group_data[value_column].pct_change() * 100
                    
                    last_month_growth = None
                    if len(group_data) >= 2:
                        last_month_growth = group_data['增长率'].iloc[-1]
                    
                    results[group] = {
                        "总量": total,
                        "平均量": avg,
                        "最大量": max_val,
                        "最小量": min_val,
                        "最近环比增长率": last_month_growth
                    }
                
                return {
                    "分组分析": results,
                    "原始数据": monthly_data.to_dict('records')
                }
            else:
                monthly_data = df.groupby('年月')[value_column].sum().reset_index()
                
                # 计算总量、均值、最大值、最小值
                total = monthly_data[value_column].sum()
                avg = monthly_data[value_column].mean()
                max_val = monthly_data[value_column].max()
                min_val = monthly_data[value_column].min()
                
                # 计算环比增长率
                monthly_data = monthly_data.sort_values('年月')
                monthly_data['增长率'] = monthly_data[value_column].pct_change() * 100
                
                last_month_growth = None
                if len(monthly_data) >= 2:
                    last_month_growth = monthly_data['增长率'].iloc[-1]
                
                return {
                    "总量": total,
                    "平均量": avg,
                    "最大量": max_val,
                    "最小量": min_val,
                    "最近环比增长率": last_month_growth,
                    "月度数据": monthly_data.to_dict('records')
                }
        except Exception as e:
            print(f"分析门诊量趋势出错: {str(e)}")
            return {"error": str(e)}
            
    @staticmethod
    def analyze_completion_rate(df, actual_column='实际量', target_column='目标值', rate_column='完成率', groupby_column=None):
        """
        分析目标完成率
        
        参数:
            df: DataFrame数据
            actual_column: 实际量列名
            target_column: 目标量列名
            rate_column: 完成率列名
            groupby_column: 分组列名
            
        返回:
            分析结果字典
        """
        try:
            if df.empty:
                return {"error": "数据为空"}
            
            # 如果没有完成率列，计算完成率
            if rate_column not in df.columns:
                df[rate_column] = df[actual_column] / df[target_column] * 100
            
            # 全局统计
            overall_avg_rate = df[rate_column].mean()
            overall_min_rate = df[rate_column].min()
            overall_max_rate = df[rate_column].max()
            
            # 计算超额完成比例和未完成比例
            over_target_count = (df[rate_column] >= 100).sum()
            under_target_count = (df[rate_column] < 100).sum()
            over_target_ratio = over_target_count / len(df) * 100
            under_target_ratio = under_target_count / len(df) * 100
            
            results = {
                "平均完成率": overall_avg_rate,
                "最低完成率": overall_min_rate,
                "最高完成率": overall_max_rate,
                "超额完成数量": over_target_count,
                "未完成数量": under_target_count,
                "超额完成比例": over_target_ratio,
                "未完成比例": under_target_ratio
            }
            
            # 分组分析
            if groupby_column and groupby_column in df.columns:
                group_analysis = {}
                for group in df[groupby_column].unique():
                    group_data = df[df[groupby_column] == group]
                    
                    group_avg_rate = group_data[rate_column].mean()
                    group_min_rate = group_data[rate_column].min()
                    group_max_rate = group_data[rate_column].max()
                    
                    group_over_target = (group_data[rate_column] >= 100).sum()
                    group_under_target = (group_data[rate_column] < 100).sum()
                    
                    group_analysis[group] = {
                        "平均完成率": group_avg_rate,
                        "最低完成率": group_min_rate,
                        "最高完成率": group_max_rate,
                        "超额完成数量": group_over_target,
                        "未完成数量": group_under_target
                    }
                
                results["分组分析"] = group_analysis
            
            return results
        except Exception as e:
            print(f"分析目标完成率出错: {str(e)}")
            return {"error": str(e)}


class DataVisualizer:
    """
    数据可视化工具类，提供各种数据可视化方法
    """
    
    @staticmethod
    def create_line_chart(df, x, y, title=None, color=None, labels=None):
        """
        创建折线图
        
        参数:
            df: DataFrame数据
            x: x轴字段
            y: y轴字段
            title: 图表标题
            color: 颜色分组字段
            labels: 标签字典
            
        返回:
            Plotly图表对象
        """
        try:
            fig = px.line(df, x=x, y=y, color=color, title=title, labels=labels)
            fig.update_layout(
                template="plotly_white",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            return fig
        except Exception as e:
            print(f"创建折线图出错: {str(e)}")
            return None
    
    @staticmethod
    def create_bar_chart(df, x, y, title=None, color=None, labels=None, barmode="group"):
        """
        创建柱状图
        
        参数:
            df: DataFrame数据
            x: x轴字段
            y: y轴字段
            title: 图表标题
            color: 颜色分组字段
            labels: 标签字典
            barmode: 柱状图模式
            
        返回:
            Plotly图表对象
        """
        try:
            fig = px.bar(df, x=x, y=y, color=color, title=title, 
                         labels=labels, barmode=barmode)
            fig.update_layout(
                template="plotly_white",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            return fig
        except Exception as e:
            print(f"创建柱状图出错: {str(e)}")
            return None
    
    @staticmethod
    def create_scatter_chart(df, x, y, title=None, color=None, size=None, labels=None):
        """
        创建散点图
        
        参数:
            df: DataFrame数据
            x: x轴字段
            y: y轴字段
            title: 图表标题
            color: 颜色分组字段
            size: 点大小字段
            labels: 标签字典
            
        返回:
            Plotly图表对象
        """
        try:
            fig = px.scatter(df, x=x, y=y, color=color, size=size, 
                            title=title, labels=labels)
            fig.update_layout(
                template="plotly_white",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            return fig
        except Exception as e:
            print(f"创建散点图出错: {str(e)}")
            return None
    
    @staticmethod
    def create_pie_chart(df, names, values, title=None, labels=None):
        """
        创建饼图
        
        参数:
            df: DataFrame数据
            names: 分类名称字段
            values: 值字段
            title: 图表标题
            labels: 标签字典
            
        返回:
            Plotly图表对象
        """
        try:
            fig = px.pie(df, names=names, values=values, title=title, labels=labels)
            fig.update_layout(
                template="plotly_white"
            )
            return fig
        except Exception as e:
            print(f"创建饼图出错: {str(e)}")
            return None
    
    @staticmethod
    def create_histogram(df, x, title=None, nbins=None, color=None, labels=None):
        """
        创建直方图
        
        参数:
            df: DataFrame数据
            x: 数据字段
            title: 图表标题
            nbins: 分箱数量
            color: 颜色分组字段
            labels: 标签字典
            
        返回:
            Plotly图表对象
        """
        try:
            fig = px.histogram(df, x=x, nbins=nbins, color=color, 
                              title=title, labels=labels)
            fig.update_layout(
                template="plotly_white",
                bargap=0.1
            )
            return fig
        except Exception as e:
            print(f"创建直方图出错: {str(e)}")
            return None
    
    @staticmethod
    def create_dashboard(df, title="数据分析仪表板"):
        """
        创建综合仪表板
        
        参数:
            df: DataFrame数据
            title: 仪表板标题
            
        返回:
            Plotly图表对象
        """
        try:
            # 获取数据特征信息
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            
            if not numeric_cols:
                return None
            
            # 创建子图布局
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=(
                    "数值分布", 
                    "箱线图", 
                    "热图", 
                    "类别分布"
                )
            )
            
            # 第一个子图：数值分布直方图
            for i, col in enumerate(numeric_cols[:3]):  # 最多展示前3个数值列
                fig.add_trace(
                    go.Histogram(x=df[col], name=col),
                    row=1, col=1
                )
            
            # 第二个子图：箱线图
            for i, col in enumerate(numeric_cols[:3]):  # 最多展示前3个数值列
                fig.add_trace(
                    go.Box(y=df[col], name=col),
                    row=1, col=2
                )
            
            # 第三个子图：热图
            if len(numeric_cols) >= 2:
                corr = df[numeric_cols].corr()
                fig.add_trace(
                    go.Heatmap(
                        z=corr.values,
                        x=corr.columns,
                        y=corr.columns,
                        colorscale='RdBu_r'
                    ),
                    row=2, col=1
                )
            
            # 第四个子图：类别分布
            if categorical_cols:
                cat_col = categorical_cols[0]  # 使用第一个类别列
                value_counts = df[cat_col].value_counts()
                fig.add_trace(
                    go.Bar(
                        x=value_counts.index,
                        y=value_counts.values,
                        name=cat_col
                    ),
                    row=2, col=2
                )
            
            # 更新布局
            fig.update_layout(
                title_text=title,
                height=800,
                showlegend=False,
                template="plotly_white"
            )
            
            return fig
        except Exception as e:
            print(f"创建仪表板出错: {str(e)}")
            return None

    @staticmethod
    def create_outpatient_trend_chart(df, x='日期', y='数量', color=None, title="门诊量趋势分析"):
        """
        创建门诊量趋势图
        
        参数:
            df: DataFrame数据
            x: x轴字段（时间字段）
            y: y轴字段（数量字段）
            color: 颜色分组字段
            title: 图表标题
            
        返回:
            Plotly图表对象
        """
        try:
            # 确保日期格式正确
            if pd.api.types.is_datetime64_any_dtype(df[x]):
                # 日期已经是datetime类型
                pass
            else:
                # 尝试转换为日期类型
                df[x] = pd.to_datetime(df[x])
            
            # 创建趋势图
            fig = px.line(df, x=x, y=y, color=color, title=title,
                          labels={x: "日期", y: "门诊量"})
            
            # 添加移动平均线（7天移动平均）
            if color is None and len(df) >= 7:
                df_copy = df.copy()
                df_copy = df_copy.sort_values(by=x)
                df_copy['移动平均'] = df_copy[y].rolling(window=7).mean()
                
                fig.add_scatter(x=df_copy[x], y=df_copy['移动平均'], 
                                mode='lines', name='7日移动平均',
                                line=dict(color='red', dash='dash'))
            
            # 更新布局
            fig.update_layout(
                template="plotly_white",
                xaxis_title="日期",
                yaxis_title="门诊量",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            return fig
        except Exception as e:
            print(f"创建门诊量趋势图出错: {str(e)}")
            return None
    
    @staticmethod
    def create_completion_rate_chart(df, x='科室', y='完成率', target_column='目标值', actual_column='实际量', title="目标完成率分析"):
        """
        创建目标完成率图表
        
        参数:
            df: DataFrame数据
            x: x轴字段（分类字段）
            y: y轴字段（完成率字段）
            target_column: 目标值字段
            actual_column: 实际值字段
            title: 图表标题
            
        返回:
            Plotly图表对象
        """
        try:
            # 如果没有完成率列，计算完成率
            if y not in df.columns and target_column in df.columns and actual_column in df.columns:
                df[y] = df[actual_column] / df[target_column] * 100
            
            # 创建条形图
            fig = px.bar(df, x=x, y=y, title=title,
                        labels={x: x, y: "完成率(%)"},
                        color=y,
                        color_continuous_scale=["red", "yellow", "green"],
                        range_color=[0, 150])
            
            # 添加目标线
            fig.add_shape(
                type="line",
                x0=-0.5,
                y0=100,
                x1=len(df) - 0.5,
                y1=100,
                line=dict(color="black", width=2, dash="dash"),
            )
            
            # 添加标注
            fig.add_annotation(
                x=len(df) / 2,
                y=100,
                text="目标值 (100%)",
                showarrow=False,
                yshift=10
            )
            
            # 更新布局
            fig.update_layout(
                template="plotly_white",
                xaxis_title=x,
                yaxis_title="完成率(%)",
                coloraxis_showscale=True
            )
            
            return fig
        except Exception as e:
            print(f"创建目标完成率图表出错: {str(e)}")
            return None
            
    @staticmethod
    def create_department_comparison_chart(df, department_column='科室', value_column='数量', title="科室门诊量对比"):
        """
        创建科室对比图表
        
        参数:
            df: DataFrame数据
            department_column: 科室列名
            value_column: 数值列名
            title: 图表标题
            
        返回:
            Plotly图表对象
        """
        try:
            # 按科室汇总
            dept_summary = df.groupby(department_column)[value_column].sum().reset_index()
            
            # 排序
            dept_summary = dept_summary.sort_values(by=value_column, ascending=False)
            
            # 创建条形图
            fig = px.bar(dept_summary, x=department_column, y=value_column, 
                        title=title,
                        labels={department_column: "科室", value_column: "门诊量"},
                        color=value_column,
                        color_continuous_scale="Viridis")
            
            # 添加数据标签
            fig.update_traces(texttemplate='%{y:.0f}', textposition='outside')
            
            # 更新布局
            fig.update_layout(
                template="plotly_white",
                xaxis_title="科室",
                yaxis_title="门诊量"
            )
            
            return fig
        except Exception as e:
            print(f"创建科室对比图表出错: {str(e)}")
            return None


def generate_plotly_chart_for_sql(query, params=None, chart_type='line', 
                                 x=None, y=None, title=None, **kwargs):
    """
    根据SQL查询生成Plotly图表
    
    参数:
        query: SQL查询
        params: 查询参数
        chart_type: 图表类型
        x: x轴字段
        y: y轴字段
        title: 图表标题
        **kwargs: 其他参数
        
    返回:
        Plotly图表JSON
    """
    try:
        # 执行查询
        df = execute_query_to_dataframe(query, params)
        
        if df.empty:
            return None
        
        # 确保x和y有值
        if not x:
            x = df.columns[0]
        if not y:
            if len(df.columns) > 1:
                y = df.columns[1]
            else:
                y = df.columns[0]
        
        # 根据图表类型生成图表
        if chart_type == 'line':
            fig = DataVisualizer.create_line_chart(df, x, y, title, **kwargs)
        elif chart_type == 'bar':
            fig = DataVisualizer.create_bar_chart(df, x, y, title, **kwargs)
        elif chart_type == 'scatter':
            fig = DataVisualizer.create_scatter_chart(df, x, y, title, **kwargs)
        elif chart_type == 'pie':
            fig = DataVisualizer.create_pie_chart(df, x, y, title, **kwargs)
        elif chart_type == 'histogram':
            fig = DataVisualizer.create_histogram(df, x, title, **kwargs)
        elif chart_type == 'dashboard':
            fig = DataVisualizer.create_dashboard(df, title)
        else:
            raise ValueError(f"不支持的图表类型: {chart_type}")
        
        if fig is None:
            return None
        
        # 转换为JSON
        return fig.to_json()
    except Exception as e:
        print(f"生成Plotly图表出错: {str(e)}")
        return None

# 添加替代方案的基本数据分析功能
def generate_basic_profile(df):
    """
    生成基本数据概览，作为ydata_profiling的替代方案
    
    参数:
        df: 数据框
    
    返回:
        HTML格式的基本数据概览
    """
    if df is None or df.empty:
        return "<p>数据为空，无法生成分析报告</p>"
    
    # 基本描述统计
    desc_stats = df.describe(include='all').fillna('').to_html(classes='table table-striped table-sm')
    
    # 缺失值统计
    missing_stats = pd.DataFrame({
        '缺失值数量': df.isna().sum(),
        '缺失比例(%)': (df.isna().sum() / len(df) * 100).round(2)
    }).to_html(classes='table table-striped table-sm')
    
    # 列类型统计
    dtype_counts = df.dtypes.value_counts().reset_index()
    dtype_counts.columns = ['数据类型', '列数量']
    dtype_stats = dtype_counts.to_html(index=False, classes='table table-striped table-sm')
    
    # 样本数据
    sample_data = df.head(10).to_html(classes='table table-striped table-sm')
    
    # 生成HTML报告
    html = f"""
    <div class="basic-profile-report">
        <h2>数据基本概览</h2>
        <div class="alert alert-info">
            注意: 这是基本数据概览。安装 ydata_profiling 包可获得更详细的分析报告。
        </div>
        
        <div class="card mb-4">
            <div class="card-header">
                <h3>数据概览</h3>
            </div>
            <div class="card-body">
                <p><strong>行数:</strong> {len(df)}</p>
                <p><strong>列数:</strong> {len(df.columns)}</p>
            </div>
        </div>
        
        <div class="card mb-4">
            <div class="card-header">
                <h3>列类型统计</h3>
            </div>
            <div class="card-body">
                {dtype_stats}
            </div>
        </div>
        
        <div class="card mb-4">
            <div class="card-header">
                <h3>缺失值统计</h3>
            </div>
            <div class="card-body">
                {missing_stats}
            </div>
        </div>
        
        <div class="card mb-4">
            <div class="card-header">
                <h3>描述统计</h3>
            </div>
            <div class="card-body">
                {desc_stats}
            </div>
        </div>
        
        <div class="card mb-4">
            <div class="card-header">
                <h3>数据样本 (前10行)</h3>
            </div>
            <div class="card-body">
                {sample_data}
            </div>
        </div>
    </div>
    """
    
    return html

def generate_profile_report(df, title="数据分析报告", mode="html", **kwargs):
    """
    生成数据概要报告
    
    参数:
        df: 数据框
        title: 报告标题
        mode: 输出模式，'html'或'json'
        
    返回:
        HTML格式的报告或JSON数据
    """
    if df is None or df.empty:
        return "<p>数据为空，无法生成分析报告</p>"
    
    if YDATA_PROFILING_AVAILABLE:
        try:
            # 生成报告
            profile = ProfileReport(df, title=title, **kwargs)
            
            if mode == "html":
                return profile.to_html()
            else:
                return profile.to_json()
        except Exception as e:
            print(f"生成报告时出错: {str(e)}")
            return f"<p>生成报告时出错: {str(e)}</p>"
    else:
        # 使用替代方案
        return generate_basic_profile(df)

def generate_minimal_report(df, title="数据概览"):
    """
    生成简化版数据概要报告
    
    参数:
        df: 数据框
        title: 报告标题
        
    返回:
        HTML格式的简化报告
    """
    if df is None or df.empty:
        return "<p>数据为空，无法生成分析报告</p>"
    
    if YDATA_PROFILING_AVAILABLE:
        try:
            # 生成简化报告
            profile = ProfileReport(df, 
                                  title=title,
                                  minimal=True,  # 最小配置
                                  explorative=False,  # 不包含探索性分析
                                  dark_mode=False)
            return profile.to_html()
        except Exception as e:
            print(f"生成简化报告时出错: {str(e)}")
            return f"<p>生成简化报告时出错: {str(e)}</p>"
    else:
        # 使用替代方案
        return generate_basic_profile(df) 