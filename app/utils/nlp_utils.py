"""
自然语言处理工具模块
提供中文分词、医疗实体识别、文本分类等功能
"""
import re
import jieba_fast as jieba
import os
import logging
from collections import Counter
import numpy as np
from typing import List, Dict, Tuple, Optional, Any

# 设置日志记录器
logger = logging.getLogger(__name__)

# 加载医学词典
DICT_PATHS = [
    "data/dict/medical_dict.txt",  # 项目根目录
    "app/data/medical_dict.txt",   # app目录
]

dict_loaded = False
for dict_path in DICT_PATHS:
    if os.path.exists(dict_path):
        try:
            jieba.load_userdict(dict_path)
            logger.info(f"成功加载医学词典: {dict_path}")
            dict_loaded = True
            break
        except Exception as e:
            logger.warning(f"尝试加载医学词典 {dict_path} 失败: {str(e)}")

if not dict_loaded:
    logger.warning("医学词典加载失败，使用默认词典")

# 尝试加载SpaCy中文模型
nlp = None
try:
    import spacy
    nlp = spacy.load("zh_core_web_sm")
    logger.info("成功加载SpaCy中文模型")
except ImportError:
    logger.warning("SpaCy库未安装，某些NLP功能将不可用")
except Exception as e:
    logger.warning(f"中文SpaCy模型加载失败: {str(e)}，某些NLP功能将不可用")


class TextProcessor:
    """文本处理工具类"""
    
    @staticmethod
    def segment_text(text: str, cut_all: bool = False) -> List[str]:
        """
        中文分词
        
        参数:
            text: 待分词文本
            cut_all: 是否全模式分词
            
        返回:
            分词结果列表
        """
        if not text:
            return []
            
        # 加载医学词典
        try:
            jieba.load_userdict("app/data/medical_dict.txt")
        except:
            pass  # 词典不存在则忽略
            
        words = jieba.lcut(text, cut_all=cut_all)
        return [w for w in words if w.strip()]
    
    @staticmethod
    def extract_keywords(text: str, topk: int = 10) -> List[Tuple[str, float]]:
        """
        提取关键词
        
        参数:
            text: 输入文本
            topk: 提取前k个关键词
            
        返回:
            关键词及权重列表 [(word, weight), ...]
        """
        if not text:
            return []
            
        # 使用TF-IDF提取关键词
        from jieba import analyse
        keywords = analyse.extract_tags(text, topK=topk, withWeight=True)
        return keywords
    
    @staticmethod
    def extract_medical_entities(text: str) -> Dict[str, List[str]]:
        """
        提取医疗实体
        
        参数:
            text: 输入文本
            
        返回:
            实体字典 {entity_type: [entities]}
        """
        if not text:
            return {}
            
        entities = {
            "疾病": [],
            "症状": [],
            "药物": [],
            "检查": [],
            "手术": [],
            "身体部位": []
        }
        
        # 如果SpaCy可用，使用SpaCy进行实体识别
        if nlp is not None:
            try:
                doc = nlp(text)
                # 根据SpaCy的结果提取实体
                for ent in doc.ents:
                    # 根据实体类型分类
                    if ent.label_ == "DISEASE":
                        entities["疾病"].append(ent.text)
                    elif ent.label_ == "SYMPTOM":
                        entities["症状"].append(ent.text)
                    elif ent.label_ == "DRUG":
                        entities["药物"].append(ent.text)
                    elif ent.label_ == "BODY_PART":
                        entities["身体部位"].append(ent.text)
                    # 可以添加更多的实体类型判断
                
                # 如果通过SpaCy解析出了实体，则返回结果
                if any(len(v) > 0 for v in entities.values()):
                    return entities
            except Exception as e:
                logger.warning(f"使用SpaCy提取实体失败: {str(e)}")
                # 如果SpaCy出错，继续使用规则方法
        
        # 规则匹配方法（作为后备方案）
        # 使用简单的关键词匹配
        disease_keywords = ["糖尿病", "高血压", "肺炎", "感冒", "肝炎", "心脏病", "脑梗", "癌症"]
        symptom_keywords = ["头痛", "发热", "咳嗽", "乏力", "恶心", "呕吐", "腹痛", "胸闷"]
        drug_keywords = ["阿司匹林", "布洛芬", "青霉素", "头孢", "胰岛素", "降压药"]
        exam_keywords = ["血常规", "尿常规", "CT", "核磁", "超声", "心电图", "X光"]
        
        # 提取实体
        for keyword in disease_keywords:
            if keyword in text:
                entities["疾病"].append(keyword)
                
        for keyword in symptom_keywords:
            if keyword in text:
                entities["症状"].append(keyword)
                
        for keyword in drug_keywords:
            if keyword in text:
                entities["药物"].append(keyword)
                
        for keyword in exam_keywords:
            if keyword in text:
                entities["检查"].append(keyword)
        
        return entities
    
    @staticmethod
    def get_word_frequency(text: str, stop_words: Optional[List[str]] = None) -> Dict[str, int]:
        """
        获取词频统计
        
        参数:
            text: 输入文本
            stop_words: 停用词列表
            
        返回:
            词频字典 {word: frequency}
        """
        if not text:
            return {}
            
        # 分词
        words = TextProcessor.segment_text(text)
        
        # 过滤停用词
        if stop_words:
            words = [w for w in words if w not in stop_words]
        
        # 统计词频
        word_freq = Counter(words)
        return dict(word_freq)
    
    @staticmethod
    def text_similarity(text1: str, text2: str) -> float:
        """
        计算文本相似度（基于词袋模型和余弦相似度）
        
        参数:
            text1: 第一个文本
            text2: 第二个文本
            
        返回:
            相似度得分(0-1)
        """
        if not text1 or not text2:
            return 0.0
            
        # 分词
        words1 = set(TextProcessor.segment_text(text1))
        words2 = set(TextProcessor.segment_text(text2))
        
        # 构建词袋
        all_words = list(words1.union(words2))
        
        # 计算词向量
        vector1 = np.array([1 if word in words1 else 0 for word in all_words])
        vector2 = np.array([1 if word in words2 else 0 for word in all_words])
        
        # 计算余弦相似度
        dot_product = np.dot(vector1, vector2)
        norm1 = np.linalg.norm(vector1)
        norm2 = np.linalg.norm(vector2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)
    
    @staticmethod
    def classify_medical_text(text: str) -> str:
        """
        医疗文本分类
        
        参数:
            text: 输入文本
            
        返回:
            分类结果
        """
        if not text:
            return "未知"
            
        # 简单规则分类，实际应用中应使用机器学习模型
        keywords = {
            "门诊记录": ["门诊", "复诊", "初诊", "就诊"],
            "住院记录": ["住院", "入院", "出院", "病房"],
            "病历": ["病历", "病史", "既往史", "现病史"],
            "检查报告": ["化验", "检验", "检查", "CT", "核磁", "X光", "超声"],
            "手术记录": ["手术", "术前", "术后", "麻醉"],
            "用药记录": ["用药", "处方", "给药", "配药", "药物"]
        }
        
        # 分词
        words = set(TextProcessor.segment_text(text))
        
        # 关键词匹配计数
        category_scores = {}
        for category, category_keywords in keywords.items():
            matches = sum(1 for keyword in category_keywords if keyword in words)
            if matches > 0:
                category_scores[category] = matches
        
        # 返回得分最高的分类
        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]
        
        return "其他"


class MedicalTermExtractor:
    """医学术语提取工具类"""
    
    @staticmethod
    def extract_diagnoses(text: str) -> List[str]:
        """
        提取诊断信息
        
        参数:
            text: 医疗文本
            
        返回:
            诊断信息列表
        """
        if not text:
            return []
            
        # 诊断提取规则
        patterns = [
            r'诊断(?:为|:)?\s*([^，。；,;!?？！\n]+)',
            r'(?:初步|最终|临床|明确)诊断(?:为|:)?\s*([^，。；,;!?？！\n]+)',
            r'(?:患有|患|确诊为|诊断为)\s*([^，。；,;!?？！\n]+?)(?:病|症)?'
        ]
        
        diagnoses = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            diagnoses.extend(matches)
        
        # 去重
        return list(set(diagnoses))
    
    @staticmethod
    def extract_medications(text: str) -> List[Dict[str, str]]:
        """
        提取用药信息
        
        参数:
            text: 医疗文本
            
        返回:
            用药信息列表，包含药名、剂量、频次
        """
        if not text:
            return []
            
        # 提取药物名、剂量、频次
        medication_pattern = r'(?:给予|用|服用|使用|处方|开具)?\s*([^，。；,;!?？！\n]+?)\s*(?:剂量|用量)?\s*([0-9.]+\s*(?:mg|g|ml|片|支|瓶|丸|毫克|克|毫升|单位)?)?\s*(?:每日|每天|每周|每月|隔日|bid|tid|qd|qid|prn)?\s*([0-9]*\s*次)?'
        
        medications = []
        matches = re.finditer(medication_pattern, text)
        
        for match in matches:
            if match.group(1):  # 至少要有药名
                medication = {
                    "药名": match.group(1).strip(),
                    "剂量": match.group(2).strip() if match.group(2) else "",
                    "频次": match.group(3).strip() if match.group(3) else ""
                }
                medications.append(medication)
        
        return medications
    
    @staticmethod
    def extract_lab_values(text: str) -> List[Dict[str, Any]]:
        """
        提取化验值
        
        参数:
            text: 医疗文本
            
        返回:
            化验项目及数值列表
        """
        if not text:
            return []
            
        # 提取化验项目及数值
        lab_pattern = r'([^，。；,;!?？！\n]+?)(?::|：)\s*([0-9.]+\s*(?:[a-zA-Z%/]*))'
        
        lab_values = []
        matches = re.finditer(lab_pattern, text)
        
        for match in matches:
            if match.group(1) and match.group(2):
                lab = {
                    "项目": match.group(1).strip(),
                    "数值": match.group(2).strip()
                }
                lab_values.append(lab)
        
        return lab_values 