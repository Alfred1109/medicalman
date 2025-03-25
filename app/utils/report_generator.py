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
    def generate_pdf_from_html(html_content, css_file=None):
        """
        从HTML生成PDF
        
        参数:
            html_content: HTML内容
            css_file: CSS文件路径（可选）
            
        返回:
            PDF二进制内容
        """
        try:
            # 尝试使用WeasyPrint
            from weasyprint import HTML, CSS
            
            # 判断css_file是否为URL
            css_obj = None
            if css_file:
                if css_file.startswith(('http://', 'https://')):
                    css_obj = CSS(url=css_file)
                else:
                    css_obj = CSS(filename=css_file) if os.path.exists(css_file) else None
            
            # 使用WeasyPrint生成PDF
            html = HTML(string=html_content)
            if css_obj:
                return html.write_pdf(stylesheets=[css_obj])
            else:
                return html.write_pdf()
        except ImportError:
            # WeasyPrint不可用，尝试使用pdfkit
            try:
                import pdfkit
                
                # 设置pdfkit选项
                options = {
                    'quiet': '',
                    'page-size': 'A4',
                    'encoding': 'UTF-8',
                    'margin-top': '1cm',
                    'margin-right': '1cm',
                    'margin-bottom': '1cm',
                    'margin-left': '1cm'
                }
                
                # 如果有css，添加到选项中
                if css_file and os.path.exists(css_file):
                    options['user-style-sheet'] = css_file
                    
                # 使用pdfkit生成PDF
                return pdfkit.from_string(html_content, False, options=options)
            except (ImportError, OSError) as e:
                # 记录警告
                current_app.logger.warning(f"PDF生成失败，将返回HTML内容: {str(e)}")
                
                # 都不可用，返回HTML内容并添加消息
                html_message = f"""
                <div style="background-color: #fff3cd; color: #856404; padding: 15px; margin: 20px 0; border: 1px solid #ffeeba; border-radius: 5px;">
                    <p><strong>注意:</strong> PDF生成组件不可用，显示的是HTML版本。要生成PDF，请安装以下依赖:</p>
                    <ol>
                        <li>WeasyPrint: <code>pip install weasyprint</code></li>
                        <li>或 pdfkit: <code>pip install pdfkit</code> 和 wkhtmltopdf (https://wkhtmltopdf.org/downloads.html)</li>
                    </ol>
                </div>
                """ + html_content
                
                # 返回HTML内容（UTF-8编码）
                return html_message.encode('utf-8')
    
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
        
        # 检查CSS文件是否存在，使用绝对路径确保能找到文件
        css_path = os.path.join(static_folder, 'css', 'bootstrap.min.css')
        if not os.path.exists(css_path):
            # 回退到默认的在线Bootstrap CSS
            css_files = ['https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css']
        else:
            css_files = [css_path]
        
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
            css_file=css_files[0] if css_files else None
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
            css_file=css_files[0]
        )
    
    @staticmethod
    def generate_custom_report(template_name: str, context: Dict[str, Any],
                              css_files: List[str] = None) -> bytes:
        """
        生成自定义PDF报告
        
        参数:
            template_name: 模板名称
            context: 模板上下文
            css_files: CSS文件路径列表
            
        返回:
            PDF报告的二进制内容
        """
        # 如果未提供CSS文件，使用默认的Bootstrap CSS
        if not css_files:
            static_folder = current_app.static_folder
            css_path = os.path.join(static_folder, 'css', 'bootstrap.min.css')
            if not os.path.exists(css_path):
                # 回退到默认的在线Bootstrap CSS
                css_files = ['https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css']
            else:
                css_files = [css_path]
                
        # 添加生成时间到上下文
        if 'generated_time' not in context:
            context['generated_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 渲染HTML模板
        html_content = render_template(template_name, **context)
        
        # 生成PDF
        return ReportGenerator.generate_pdf_from_html(
            html_content=html_content,
            css_file=css_files[0] if css_files else None
        ) 