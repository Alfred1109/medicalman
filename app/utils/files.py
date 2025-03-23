import os
from datetime import datetime
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

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'xlsx', 'xls', 'csv', 'xlsm', 'ods'}

def allowed_file(filename):
    """
    检查文件是否具有允许的扩展名
    
    参数:
        filename (str): 文件名
        
    返回:
        bool: 如果文件扩展名允许，则为True，否则为False
    """
    # 如果文件名中没有点号，表示没有扩展名，我们也允许上传
    if '.' not in filename:
        return True
    return filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_latest_file(directory='static/uploads/documents'):
    """
    获取指定目录中最新的文件
    
    参数:
        directory (str): 目录路径
        
    返回:
        str: 最新文件的文件名，如果没有文件则返回None
    """
    if not os.path.exists(directory):
        return None
    
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    if not files:
        return None
    
    # 按文件修改时间排序
    files.sort(key=lambda x: os.path.getmtime(os.path.join(directory, x)), reverse=True)
    return files[0]

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
    从图像文件中提取文本(OCR)
    
    参数:
        file_path: 图像文件路径
        
    返回:
        str: 提取的文本内容
    """
    try:
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img, lang='chi_sim+eng')
        return text
    except Exception as e:
        logger.error(f"从图像提取文本时出错: {str(e)}")
        return f"无法提取图像文本: {str(e)}"

def preprocess_text(text):
    """
    预处理文本(分词、去停用词等)
    
    参数:
        text: 输入文本
        
    返回:
        str: 预处理后的文本
    """
    try:
        # 转换为小写
        text = text.lower()
        
        # 移除特殊字符
        text = re.sub(r'[^\w\s]', '', text)
        
        # 分词
        tokens = word_tokenize(text)
        
        # 去停用词
        stop_words = set(stopwords.words('english'))
        filtered_tokens = [word for word in tokens if word not in stop_words]
        
        # 重新组合文本
        return ' '.join(filtered_tokens)
    except Exception as e:
        logger.error(f"预处理文本时出错: {str(e)}")
        return text

def extract_tables_from_excel(file_path):
    """
    从Excel文件中提取表格数据
    
    参数:
        file_path: Excel文件路径
        
    返回:
        dict: 工作表名称和对应的DataFrame
    """
    try:
        # 读取所有工作表
        excel_data = {}
        xls = pd.ExcelFile(file_path)
        
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            excel_data[sheet_name] = df
        
        return excel_data
    except Exception as e:
        logger.error(f"从Excel提取表格时出错: {str(e)}")
        return {"error": str(e)}

def extract_tables_from_csv(file_path):
    """
    从CSV文件中提取表格数据
    
    参数:
        file_path: CSV文件路径
        
    返回:
        pandas.DataFrame: CSV数据
    """
    try:
        # 尝试不同的编码和分隔符
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
        separators = [',', '\t', ';']
        
        for encoding in encodings:
            for sep in separators:
                try:
                    df = pd.read_csv(file_path, encoding=encoding, sep=sep)
                    if len(df.columns) > 1:  # 如果只有一列，可能是分隔符不对
                        return df
                except:
                    continue
        
        # 如果所有组合都失败，使用默认设置
        return pd.read_csv(file_path)
    except Exception as e:
        logger.error(f"从CSV提取表格时出错: {str(e)}")
        return pd.DataFrame({"error": [str(e)]})

def analyze_text_content(text, user_message):
    """
    分析文本内容并返回相关信息
    
    参数:
        text: 文本内容
        user_message: 用户查询消息
        
    返回:
        分析结果，或者错误时返回None
    """
    try:
        # 计算字数
        word_count = len(re.findall(r'\w+', text))
        
        # 分段
        paragraphs = text.split('\n\n')
        paragraph_count = len([p for p in paragraphs if p.strip()])
        
        # 提取可能的标题
        titles = []
        for line in text.split('\n'):
            if line.strip() and len(line.strip()) < 100 and (line.isupper() or line.istitle() or re.match(r'^[一二三四五六七八九十]+[、.．]', line)):
                titles.append(line.strip())
        
        # 根据用户消息查找相关段落
        relevant_paragraphs = []
        
        try:
            # 尝试使用NLTK进行分词
            query_tokens = word_tokenize(user_message.lower())
        except Exception as nltk_error:
            # 如果NLTK不可用，使用简单的空格分割
            logger.warning(f"NLTK分词失败，使用简单分词: {str(nltk_error)}")
            query_tokens = user_message.lower().split()
        
        for para in paragraphs:
            if para.strip():
                para_lower = para.lower()
                # 计算简单的相关性分数
                relevance_score = sum(1 for token in query_tokens if token in para_lower)
                if relevance_score > 0:
                    relevant_paragraphs.append({
                        "text": para.strip(),
                        "relevance": relevance_score
                    })
        
        # 按相关性排序
        relevant_paragraphs.sort(key=lambda x: x["relevance"], reverse=True)
        
        return {
            "word_count": word_count,
            "paragraph_count": paragraph_count,
            "titles": titles[:10],  # 最多返回10个标题
            "relevant_paragraphs": relevant_paragraphs[:5]  # 最多返回5个相关段落
        }
    except Exception as e:
        logger.error(f"分析文本内容时出错: {str(e)}")
        # 出错时返回None而不是空字典，避免后续代码尝试访问不存在的键
        return None 