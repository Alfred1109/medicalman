"""
多维度分析路由模块 - 处理分析相关路由
"""
from flask import Blueprint, render_template, request, jsonify, current_app
from app.routes.auth_routes import login_required, api_login_required

# 创建蓝图
analysis_bp = Blueprint('analysis', __name__, url_prefix='/analysis')

@analysis_bp.route('/department')
@login_required
def department_analysis():
    """科室分析页面"""
    return render_template('analysis/department-analysis.html')

@analysis_bp.route('/doctor')
@login_required
def doctor_performance():
    """医生绩效页面"""
    return render_template('analysis/doctor-performance.html')

@analysis_bp.route('/patient')
@login_required
def patient_analysis():
    """患者分析页面"""
    return render_template('analysis/patient-analysis.html')

@analysis_bp.route('/financial')
@login_required
def financial_analysis():
    """财务分析页面"""
    return render_template('analysis/financial-analysis.html')

@analysis_bp.route('/drg')
@login_required
def drg_analysis():
    """DRG分析页面"""
    return render_template('analysis/drg-analysis.html')

@analysis_bp.route('/')
@login_required
def index():
    """分析总览页面"""
    return render_template('analysis/analysis.html') 