import sqlite3

# 创建知识库表
def create_knowledge_base_tables():
    """创建知识库相关表"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # 创建知识库主表
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
    
    # 创建知识库分块表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS knowledge_base_chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        knowledge_id INTEGER,
        chunk_index INTEGER,
        content TEXT,
        FOREIGN KEY (knowledge_id) REFERENCES knowledge_base (id)
    )
    ''')
    
    conn.commit()
    conn.close()
    print("知识库表创建完成")

# 主函数
def main():
    # ... existing code ...
    
    # 创建知识库表
    create_knowledge_base_tables()
    
    # ... existing code ... 