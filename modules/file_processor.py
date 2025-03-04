import os
import pandas as pd
import PyPDF2
import pdfplumber
import docx
import pytesseract
from PIL import Image
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import re
import io
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 确保NLTK数据已下载
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

def extract_text_from_pdf(file_path):
    """
    从PDF文件中提取文本
    
    参数:
        file_path: PDF文件路径
        
    返回:
        str: 提取的文本内容
    """
    try:
        # 首先尝试使用PyPDF2
        text = ""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text() + "\n"
        
        # 如果PyPDF2提取的文本很少，尝试使用pdfplumber
        if len(text.strip()) < 100:
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        
        return text
    except Exception as e:
        logger.error(f"从PDF提取文本时出错: {str(e)}")
        return f"无法提取PDF文本: {str(e)}"

def extract_text_from_docx(file_path):
    """
    从DOCX文件中提取文本
    
    参数:
        file_path: DOCX文件路径
        
    返回:
        str: 提取的文本内容
    """
    try:
        doc = docx.Document(file_path)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except Exception as e:
        logger.error(f"从DOCX提取文本时出错: {str(e)}")
        return f"无法提取DOCX文本: {str(e)}"

def extract_text_from_txt(file_path):
    """
    从TXT文件中提取文本
    
    参数:
        file_path: TXT文件路径
        
    返回:
        str: 提取的文本内容
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except UnicodeDecodeError:
        # 如果UTF-8解码失败，尝试其他编码
        try:
            with open(file_path, 'r', encoding='gbk') as file:
                return file.read()
        except Exception as e:
            logger.error(f"从TXT提取文本时出错: {str(e)}")
            return f"无法提取TXT文本: {str(e)}"
    except Exception as e:
        logger.error(f"从TXT提取文本时出错: {str(e)}")
        return f"无法提取TXT文本: {str(e)}"

def extract_text_from_image(file_path):
    """
    从图像文件中提取文本（OCR）
    
    参数:
        file_path: 图像文件路径
        
    返回:
        str: 提取的文本内容
    """
    try:
        # 检查是否安装了tesseract
        import shutil
        if shutil.which('tesseract') is None:
            return "未安装tesseract-ocr，无法进行OCR识别。请安装tesseract-ocr后再试。"
        
        # 打开图像
        image = Image.open(file_path)
        
        # 使用pytesseract进行OCR识别
        text = pytesseract.image_to_string(image, lang='chi_sim+eng')
        return text
    except Exception as e:
        logger.error(f"从图像提取文本时出错: {str(e)}")
        return f"无法提取图像文本: {str(e)}"

def preprocess_text(text):
    """
    预处理文本（去除停用词、标点符号等）
    
    参数:
        text: 原始文本
        
    返回:
        str: 预处理后的文本
    """
    # 转换为小写
    text = text.lower()
    
    # 去除特殊字符和数字
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\d+', ' ', text)
    
    # 分词
    tokens = word_tokenize(text)
    
    # 去除停用词
    stop_words = set(stopwords.words('english'))
    filtered_tokens = [word for word in tokens if word not in stop_words]
    
    # 重新组合文本
    preprocessed_text = ' '.join(filtered_tokens)
    return preprocessed_text

def get_latest_file(directory='static/uploads/documents'):
    """
    获取最新上传的文件及其内容
    
    参数:
        directory: 文件目录
        
    返回:
        tuple: (文件路径, 文件类型, 文件内容)
    """
    try:
        # 确保目录存在
        if not os.path.exists(directory):
            logger.error(f"目录不存在: {directory}")
            return None
        
        # 获取目录中的所有文件
        files = [os.path.join(directory, f) for f in os.listdir(directory) 
                if os.path.isfile(os.path.join(directory, f))]
        
        # 如果没有文件，返回None
        if not files:
            logger.error(f"目录中没有文件: {directory}")
            return None
        
        # 按修改时间排序文件
        files.sort(key=os.path.getmtime, reverse=True)
        
        # 获取最新的文件
        file_path = files[0]
        filename = os.path.basename(file_path)
        logger.info(f"尝试处理文件: {filename}")
        
        # 获取文件扩展名
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        
        # 如果没有扩展名，尝试根据文件名推断类型
        if not ext:
            # 检查文件名是否包含类型提示
            if 'xlsx' in filename.lower() or 'excel' in filename.lower():
                ext = '.xlsx'
            elif 'xls' in filename.lower():
                ext = '.xls'
            elif 'csv' in filename.lower():
                ext = '.csv'
            elif 'pdf' in filename.lower():
                ext = '.pdf'
            elif 'docx' in filename.lower() or 'doc' in filename.lower():
                ext = '.docx'
            elif 'txt' in filename.lower() or 'text' in filename.lower():
                ext = '.txt'
            else:
                # 尝试读取文件内容的前几个字节来判断文件类型
                try:
                    with open(file_path, 'rb') as f:
                        header = f.read(8)
                        # Excel文件的魔数
                        if header.startswith(b'\x50\x4B\x03\x04'):  # XLSX, XLSM, DOCX
                            # 默认假设为xlsx
                            ext = '.xlsx'
                        elif header.startswith(b'\xD0\xCF\x11\xE0'):  # XLS, DOC
                            # 默认假设为xls
                            ext = '.xls'
                        elif header.startswith(b'%PDF'):  # PDF
                            ext = '.pdf'
                        else:
                            # 默认假设为xlsx
                            ext = '.xlsx'
                except Exception as e:
                    logger.error(f"读取文件头时出错: {str(e)}")
                    # 默认假设为xlsx
                    ext = '.xlsx'
        
        # 提取文件类型（不带点）
        file_type = ext[1:] if ext.startswith('.') else ext
        
        # 根据文件类型提取内容
        if file_type in ['xlsx', 'xls', 'xlsm', 'ods']:
            # Excel文件
            try:
                if file_type in ['xlsx', 'xlsm']:
                    df = pd.read_excel(file_path, engine='openpyxl')
                elif file_type == 'xls':
                    df = pd.read_excel(file_path, engine='xlrd')
                elif file_type == 'ods':
                    df = pd.read_excel(file_path, engine='odf')
                return (file_path, file_type, df)
            except Exception as e:
                logger.error(f"读取Excel文件时出错: {str(e)}")
                return None
        elif file_type == 'csv':
            # CSV文件
            try:
                df = pd.read_csv(file_path)
                return (file_path, file_type, df)
            except Exception as e:
                logger.error(f"读取CSV文件时出错: {str(e)}")
                return None
        elif file_type == 'pdf':
            # PDF文件
            text = extract_text_from_pdf(file_path)
            return (file_path, file_type, text)
        elif file_type == 'docx':
            # DOCX文件
            text = extract_text_from_docx(file_path)
            return (file_path, file_type, text)
        elif file_type == 'txt':
            # TXT文件
            text = extract_text_from_txt(file_path)
            return (file_path, file_type, text)
        elif file_type in ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif']:
            # 图像文件
            text = extract_text_from_image(file_path)
            return (file_path, file_type, text)
        else:
            # 不支持的文件类型
            logger.error(f"不支持的文件类型: {file_type}")
            return None
    
    except Exception as e:
        logger.error(f"获取最新文件时出错: {str(e)}")
        return None

def analyze_text_content(text, user_message):
    """
    分析文本内容
    
    参数:
        text: 文本内容
        user_message: 用户问题
        
    返回:
        str: 分析结果
    """
    # 这里可以添加更复杂的文本分析逻辑
    # 目前只返回基本信息
    
    # 计算文本长度
    total_chars = len(text)
    
    # 计算单词数（简单分词）
    words = text.split()
    total_words = len(words)
    
    # 计算段落数（按换行符分割）
    paragraphs = text.split('\n\n')
    total_paragraphs = len(paragraphs)
    
    # 提取关键词（简单实现，取频率最高的10个词）
    word_freq = {}
    for word in words:
        if len(word) > 1:  # 忽略单字符词
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # 按频率排序
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    top_keywords = sorted_words[:10] if len(sorted_words) >= 10 else sorted_words
    
    # 生成分析结果
    result = f"## 文本分析结果\n\n"
    result += f"- 总字符数: {total_chars}\n"
    result += f"- 总单词数: {total_words}\n"
    result += f"- 总段落数: {total_paragraphs}\n\n"
    
    result += "### 关键词\n\n"
    for word, freq in top_keywords:
        result += f"- {word}: {freq}次\n"
    
    result += "\n### 内容预览\n\n"
    preview = text[:500] + "..." if len(text) > 500 else text
    result += preview
    
    return result 