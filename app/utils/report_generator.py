"""
报告生成工具模块 - 提供PDF报告生成功能
"""
import os
import tempfile
from datetime import datetime
import json
from typing import Dict, Any, List, Optional, Union, Tuple

from flask import url_for, render_template, current_app
import matplotlib.pyplot as plt
import pandas as pd
import plotly.io as pio

class ReportGenerator:
    """报告生成器类，提供各种报告生成功能"""
    
    @staticmethod
    def generate_pdf_from_html(html_content: str, css_files: List[str] = None, 
                              base_url: str = None) -> bytes:
        """
        将HTML内容转换为PDF
        
        参数:
            html_content: HTML内容
            css_files: CSS文件列表
            base_url: 用于解析相对URL的基础URL
            
        返回:
            PDF文件的二进制内容
        """
        try:
            # 检查是否安装了WeasyPrint
            try:
                from weasyprint import HTML, CSS
                print("使用WeasyPrint生成PDF")
            except ImportError:
                # 如果未安装WeasyPrint，尝试使用pdfkit
                import pdfkit
                print("使用pdfkit生成PDF")
                
                options = {
                    'page-size': 'A4',
                    'margin-top': '0.75in',
                    'margin-right': '0.75in',
                    'margin-bottom': '0.75in',
                    'margin-left': '0.75in',
                    'encoding': 'UTF-8',
                    'no-outline': None
                }
                
                # 写入临时HTML文件
                with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp_html:
                    temp_html.write(html_content.encode('utf-8'))
                    temp_html_path = temp_html.name
                
                try:
                    # 转换HTML到PDF
                    pdf_content = pdfkit.from_file(temp_html_path, False, options=options)
                    return pdf_content
                finally:
                    # 删除临时文件
                    if os.path.exists(temp_html_path):
                        os.remove(temp_html_path)
            
            # 使用WeasyPrint
            css_data = []
            if css_files:
                for css_file in css_files:
                    if os.path.isfile(css_file):
                        with open(css_file, 'r') as f:
                            css_data.append(CSS(string=f.read()))
                    else:
                        css_data.append(CSS(filename=css_file))
            
            html = HTML(string=html_content, base_url=base_url)
            return html.write_pdf(stylesheets=css_data)
            
        except Exception as e:
            print(f"生成PDF报告出错: {str(e)}")
            raise
    
    @staticmethod
    def generate_dashboard_report(data: Dict[str, Any], title: str = "仪表盘报告",
                                 start_date: str = None, end_date: str = None,
                                 template_name: str = "reports/dashboard_report.html") -> bytes:
        """
        生成仪表盘PDF报告
        
        参数:
            data: 仪表盘数据
            title: 报告标题
            start_date: 起始日期
            end_date: 结束日期
            template_name: 模板名称
            
        返回:
            PDF报告的二进制内容
        """
        # 获取应用的静态文件夹路径
        static_folder = current_app.static_folder
        css_files = [
            os.path.join(static_folder, 'css', 'bootstrap.min.css'),
            os.path.join(static_folder, 'css', 'style.css')
        ]
        
        # 获取当前日期时间
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 将图表转换为Base64图片
        chart_images = {}
        for chart_name, chart_data in data.get('charts', {}).items():
            if 'figure' in chart_data:
                try:
                    # 尝试将Plotly图表转换为Base64
                    chart_images[chart_name] = pio.to_image(chart_data['figure'], format='png').decode('utf-8')
                except:
                    chart_images[chart_name] = None
        
        # 渲染HTML模板
        html_content = render_template(
            template_name,
            title=title,
            data=data,
            chart_images=chart_images,
            start_date=start_date,
            end_date=end_date,
            generated_time=now
        )
        
        # 生成PDF
        return ReportGenerator.generate_pdf_from_html(
            html_content=html_content,
            css_files=css_files,
            base_url=current_app.config['SERVER_NAME']
        )
    
    @staticmethod
    def generate_analysis_report(df: pd.DataFrame, analysis_results: Dict[str, Any], 
                              title: str = "分析报告", template_name: str = "reports/analysis_report.html") -> bytes:
        """
        生成数据分析PDF报告
        
        参数:
            df: 数据DataFrame
            analysis_results: 分析结果
            title: 报告标题
            template_name: 模板名称
            
        返回:
            PDF报告的二进制内容
        """
        # 获取应用的静态文件夹路径
        static_folder = current_app.static_folder
        css_files = [
            os.path.join(static_folder, 'css', 'bootstrap.min.css'),
            os.path.join(static_folder, 'css', 'style.css')
        ]
        
        # 基本数据统计
        stats = {
            'row_count': len(df),
            'column_count': len(df.columns),
            'missing_values': df.isna().sum().to_dict(),
            'data_types': df.dtypes.astype(str).to_dict()
        }
        
        # 描述性统计
        try:
            describe_stats = df.describe(include='all').fillna('').to_html(classes='table table-striped')
        except:
            describe_stats = "<p>无法生成描述性统计</p>"
        
        # 获取样本数据
        try:
            sample_data = df.head(10).to_html(classes='table table-striped')
        except:
            sample_data = "<p>无法获取样本数据</p>"
        
        # 生成图表图片
        chart_images = {}
        for chart_name, chart_fig in analysis_results.get('charts', {}).items():
            if chart_fig:
                # 将matplotlib图表保存为临时文件并读取
                if isinstance(chart_fig, plt.Figure):
                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                        chart_fig.savefig(temp_file.name, bbox_inches='tight')
                        temp_file_path = temp_file.name
                    
                    try:
                        with open(temp_file_path, 'rb') as f:
                            import base64
                            chart_images[chart_name] = base64.b64encode(f.read()).decode('utf-8')
                    finally:
                        if os.path.exists(temp_file_path):
                            os.remove(temp_file_path)
                
                # 处理Plotly图表
                elif hasattr(chart_fig, 'to_image'):
                    try:
                        chart_images[chart_name] = pio.to_image(chart_fig, format='png').decode('utf-8')
                    except:
                        chart_images[chart_name] = None
        
        # 渲染HTML模板
        html_content = render_template(
            template_name,
            title=title,
            stats=stats,
            describe_stats=describe_stats,
            sample_data=sample_data,
            analysis_results=analysis_results,
            chart_images=chart_images,
            generated_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        # 生成PDF
        return ReportGenerator.generate_pdf_from_html(
            html_content=html_content,
            css_files=css_files,
            base_url=current_app.config['SERVER_NAME']
        )
    
    @staticmethod
    def generate_custom_report(template_name: str, context: Dict[str, Any],
                              css_files: List[str] = None) -> bytes:
        """
        生成自定义PDF报告
        
        参数:
            template_name: 模板名称
            context: 模板上下文
            css_files: CSS文件列表
            
        返回:
            PDF报告的二进制内容
        """
        if css_files is None:
            # 获取应用的静态文件夹路径
            static_folder = current_app.static_folder
            css_files = [
                os.path.join(static_folder, 'css', 'bootstrap.min.css'),
                os.path.join(static_folder, 'css', 'style.css')
            ]
        
        # 添加生成时间到上下文
        if 'generated_time' not in context:
            context['generated_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 渲染HTML模板
        html_content = render_template(template_name, **context)
        
        # 生成PDF
        return ReportGenerator.generate_pdf_from_html(
            html_content=html_content,
            css_files=css_files,
            base_url=current_app.config['SERVER_NAME']
        ) 