"""
自然语言处理路由模块
提供文本分析API
"""
from flask import Blueprint, request, jsonify, render_template, current_app
import json
import traceback

from app.utils.nlp_utils import TextProcessor, MedicalTermExtractor
from app.routes.auth_routes import login_required, api_login_required

# 创建蓝图
nlp_bp = Blueprint('nlp', __name__, url_prefix='/nlp')

@nlp_bp.route('/')
@login_required
def nlp_home():
    """NLP首页"""
    return render_template('nlp/index.html')

@nlp_bp.route('/segment', methods=['POST'])
@api_login_required
def segment_text():
    """中文分词"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
            
        text = data.get('text')
        cut_all = data.get('cut_all', False)
        
        if not text:
            return jsonify({'error': '文本为空'}), 400
            
        # 分词
        words = TextProcessor.segment_text(text, cut_all=cut_all)
        
        return jsonify({
            'success': True,
            'words': words,
            'word_count': len(words)
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'分词出错: {str(e)}'}), 500

@nlp_bp.route('/keywords', methods=['POST'])
@api_login_required
def extract_keywords():
    """提取关键词"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
            
        text = data.get('text')
        topk = data.get('topk', 10)
        
        if not text:
            return jsonify({'error': '文本为空'}), 400
            
        # 提取关键词
        keywords = TextProcessor.extract_keywords(text, topk=topk)
        
        # 转换为字典格式
        keyword_dict = {word: weight for word, weight in keywords}
        
        return jsonify({
            'success': True,
            'keywords': keyword_dict
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'提取关键词出错: {str(e)}'}), 500

@nlp_bp.route('/entities', methods=['POST'])
@api_login_required
def extract_entities():
    """提取医疗实体"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
            
        text = data.get('text')
        
        if not text:
            return jsonify({'error': '文本为空'}), 400
            
        # 提取医疗实体
        entities = TextProcessor.extract_medical_entities(text)
        
        return jsonify({
            'success': True,
            'entities': entities
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'提取医疗实体出错: {str(e)}'}), 500

@nlp_bp.route('/word-freq', methods=['POST'])
@api_login_required
def get_word_frequency():
    """获取词频统计"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
            
        text = data.get('text')
        stop_words = data.get('stop_words')
        
        if not text:
            return jsonify({'error': '文本为空'}), 400
            
        # 词频统计
        word_freq = TextProcessor.get_word_frequency(text, stop_words=stop_words)
        
        # 按频率排序
        sorted_word_freq = dict(sorted(word_freq.items(), key=lambda x: x[1], reverse=True))
        
        return jsonify({
            'success': True,
            'word_freq': sorted_word_freq
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'词频统计出错: {str(e)}'}), 500

@nlp_bp.route('/similarity', methods=['POST'])
@api_login_required
def calculate_similarity():
    """计算文本相似度"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
            
        text1 = data.get('text1')
        text2 = data.get('text2')
        
        if not text1 or not text2:
            return jsonify({'error': '文本为空'}), 400
            
        # 计算相似度
        similarity = TextProcessor.text_similarity(text1, text2)
        
        return jsonify({
            'success': True,
            'similarity': similarity
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'计算相似度出错: {str(e)}'}), 500

@nlp_bp.route('/classify', methods=['POST'])
@api_login_required
def classify_text():
    """文本分类"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
            
        text = data.get('text')
        
        if not text:
            return jsonify({'error': '文本为空'}), 400
            
        # 文本分类
        category = TextProcessor.classify_medical_text(text)
        
        return jsonify({
            'success': True,
            'category': category
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'文本分类出错: {str(e)}'}), 500

@nlp_bp.route('/diagnoses', methods=['POST'])
@api_login_required
def extract_diagnoses():
    """提取诊断信息"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
            
        text = data.get('text')
        
        if not text:
            return jsonify({'error': '文本为空'}), 400
            
        # 提取诊断信息
        diagnoses = MedicalTermExtractor.extract_diagnoses(text)
        
        return jsonify({
            'success': True,
            'diagnoses': diagnoses
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'提取诊断信息出错: {str(e)}'}), 500

@nlp_bp.route('/medications', methods=['POST'])
@api_login_required
def extract_medications():
    """提取用药信息"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
            
        text = data.get('text')
        
        if not text:
            return jsonify({'error': '文本为空'}), 400
            
        # 提取用药信息
        medications = MedicalTermExtractor.extract_medications(text)
        
        return jsonify({
            'success': True,
            'medications': medications
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'提取用药信息出错: {str(e)}'}), 500

@nlp_bp.route('/lab-values', methods=['POST'])
@api_login_required
def extract_lab_values():
    """提取化验值"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
            
        text = data.get('text')
        
        if not text:
            return jsonify({'error': '文本为空'}), 400
            
        # 提取化验值
        lab_values = MedicalTermExtractor.extract_lab_values(text)
        
        return jsonify({
            'success': True,
            'lab_values': lab_values
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'提取化验值出错: {str(e)}'}), 500 