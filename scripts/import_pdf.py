"""
PDF数据导入脚本
"""
import os
import sys
import sqlite3
import PyPDF2
import pdfplumber
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 默认使用instance目录下的数据库
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "instance", "medical_workload.db")

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
                extracted_text = page.extract_text()
                if extracted_text:
                    text += extracted_text + "\n"
        
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

def create_knowledge_base_table(db_file=None):
    """
    创建知识库表
    
    参数:
        db_file: 数据库文件路径
    """
    if db_file is None:
        db_file = DEFAULT_DB_PATH
        
    logger.info(f"将创建知识库表到数据库: {db_file}")
    
    # 确保instance目录存在
    os.makedirs(os.path.dirname(db_file), exist_ok=True)
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    try:
        # 创建知识库表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            source TEXT,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        logger.info("知识库表创建成功")
    except Exception as e:
        logger.error(f"创建知识库表时出错: {str(e)}")
    finally:
        conn.close()

def import_pdf_to_database(pdf_file='docs/科室运营成本与医保临床路径建设版本（中电）.pdf', db_file=None):
    """
    将PDF文件内容导入到数据库
    
    参数:
        pdf_file: PDF文件路径
        db_file: 数据库文件路径
    """
    if db_file is None:
        db_file = DEFAULT_DB_PATH
        
    logger.info(f"将导入PDF到数据库: {db_file}")
    
    # 检查文件是否存在
    if not os.path.exists(pdf_file):
        logger.error(f"PDF文件不存在: {pdf_file}")
        return
    
    # 提取文本
    logger.info(f"正在从 {pdf_file} 提取文本...")
    text = extract_text_from_pdf(pdf_file)
    
    if not text or text.startswith("无法提取PDF文本"):
        logger.error(f"无法从文件提取文本: {pdf_file}")
        return
    
    # 获取文件名作为标题（不带扩展名）
    title = os.path.basename(pdf_file)
    title = os.path.splitext(title)[0]
    
    # 连接到数据库
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    try:
        # 首先检查是否已存在相同标题的条目
        cursor.execute("SELECT id FROM knowledge_base WHERE title = ?", (title,))
        existing_id = cursor.fetchone()
        
        if existing_id:
            logger.info(f"更新已存在的知识库条目: {title}")
            cursor.execute(
                "UPDATE knowledge_base SET content = ?, source = ? WHERE id = ?",
                (text, pdf_file, existing_id[0])
            )
        else:
            logger.info(f"添加新的知识库条目: {title}")
            cursor.execute(
                "INSERT INTO knowledge_base (title, content, source, category) VALUES (?, ?, ?, ?)",
                (title, text, pdf_file, "医疗知识")
            )
        
        conn.commit()
        logger.info(f"文件 {pdf_file} 成功导入到数据库")
    except Exception as e:
        logger.error(f"导入PDF到数据库时出错: {str(e)}")
    finally:
        conn.close()

def split_pdf_content_into_chunks(db_file=None, chunk_size=1000):
    """
    将PDF内容拆分成更小的块，并存储到knowledge_base_chunks表中
    
    参数:
        db_file: 数据库文件路径
        chunk_size: 每个块的最大字符数
    """
    if db_file is None:
        db_file = DEFAULT_DB_PATH
        
    logger.info(f"将拆分内容并存储到数据库: {db_file}")
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    try:
        # 创建chunks表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_base_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            knowledge_id INTEGER,
            chunk_index INTEGER,
            content TEXT,
            FOREIGN KEY (knowledge_id) REFERENCES knowledge_base (id)
        )
        ''')
        
        # 获取所有知识库条目
        cursor.execute("SELECT id, title, content FROM knowledge_base")
        entries = cursor.fetchall()
        
        # 清空现有chunks
        cursor.execute("DELETE FROM knowledge_base_chunks")
        
        for entry_id, title, content in entries:
            if not content:
                continue
                
            # 按段落分割内容
            paragraphs = content.split('\n')
            
            # 合并段落成chunks
            current_chunk = ""
            chunk_index = 0
            
            for paragraph in paragraphs:
                # 如果添加此段落会超出chunk_size，则保存当前chunk并开始新的chunk
                if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
                    cursor.execute(
                        "INSERT INTO knowledge_base_chunks (knowledge_id, chunk_index, content) VALUES (?, ?, ?)",
                        (entry_id, chunk_index, current_chunk)
                    )
                    chunk_index += 1
                    current_chunk = paragraph
                else:
                    if current_chunk:
                        current_chunk += "\n" + paragraph
                    else:
                        current_chunk = paragraph
            
            # 保存最后一个chunk
            if current_chunk:
                cursor.execute(
                    "INSERT INTO knowledge_base_chunks (knowledge_id, chunk_index, content) VALUES (?, ?, ?)",
                    (entry_id, chunk_index, current_chunk)
                )
        
        conn.commit()
        logger.info(f"已将知识库内容分割成块并存储到knowledge_base_chunks表中")
    except Exception as e:
        logger.error(f"分割知识库内容时出错: {str(e)}")
    finally:
        conn.close()

if __name__ == '__main__':
    # 创建知识库表
    create_knowledge_base_table()
    
    # 导入PDF文件
    import_pdf_to_database()
    
    # 分割成小块
    split_pdf_content_into_chunks()
    
    logger.info("PDF导入完成") 