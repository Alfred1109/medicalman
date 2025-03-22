"""
数据导入脚本
"""
import pandas as pd
import sqlite3
from datetime import datetime
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def import_excel_to_sqlite(excel_file='docs/医疗数据表.xlsx', db_file='medical_workload.db'):
    """
    将Excel文件导入到SQLite数据库
    
    参数:
        excel_file: Excel文件路径
        db_file: 数据库文件路径
    """
    # 连接到SQLite数据库
    conn = sqlite3.connect(db_file)
    
    try:
        # 读取Excel文件中的所有sheet
        excel_file = pd.ExcelFile(excel_file)
        sheet_names = excel_file.sheet_names
        
        print(f"找到以下工作表: {', '.join(sheet_names)}")
        
        # 遍历所有sheet并导入
        for sheet_name in sheet_names:
            print(f"\n正在处理工作表: {sheet_name}")
            
            try:
                # 读取sheet数据
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                
                # 检查是否为空sheet
                if df.empty:
                    print(f"工作表 {sheet_name} 为空，跳过导入")
                    continue
                    
                # 删除全为空值的行和列
                df = df.dropna(how='all', axis=0)  # 删除全为空的行
                df = df.dropna(how='all', axis=1)  # 删除全为空的列
                
                if df.empty:
                    print(f"工作表 {sheet_name} 清理后为空，跳过导入")
                    continue
                
                # 处理日期列（如果存在）
                date_columns = df.select_dtypes(include=['datetime64[ns]']).columns
                for col in date_columns:
                    df[col] = df[col].dt.strftime('%Y-%m-%d')
                
                # 将DataFrame写入SQLite
                table_name = sheet_name.lower().replace(' ', '_')
                df.to_sql(table_name, conn, if_exists='replace', index=False)
                print(f"已导入表 {table_name}，共 {len(df)} 条记录")
                print(f"表结构: {', '.join(df.columns)}")
                
            except Exception as e:
                print(f"处理工作表 {sheet_name} 时出错: {str(e)}")
                continue
        
        print("\n所有数据导入完成！")
        
    except Exception as e:
        print(f"导入过程中出错: {str(e)}")
    finally:
        conn.close()

def create_users_table(db_file='medical_workload.db'):
    """
    创建用户表
    
    参数:
        db_file: 数据库文件路径
    """
    # 连接到SQLite数据库
    conn = sqlite3.connect(db_file)
    
    try:
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            email TEXT,
            department TEXT
        )
        ''')
        
        # 检查是否已存在管理员用户
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        admin_count = cursor.fetchone()[0]
        
        # 如果不存在管理员用户，创建默认管理员
        if admin_count == 0:
            from app.models.user import User
            
            # 创建默认管理员
            admin_password_hash = User.hash_password('Admin123!')
            cursor.execute('''
            INSERT INTO users (username, password_hash, role, email, department)
            VALUES (?, ?, ?, ?, ?)
            ''', ('admin', admin_password_hash, 'admin', 'admin@example.com', '管理部门'))
            
            print("已创建默认管理员用户 (用户名: admin, 密码: Admin123!)")
        
        conn.commit()
        print("用户表创建/更新成功")
        
    except Exception as e:
        print(f"创建用户表时出错: {str(e)}")
    finally:
        conn.close()

if __name__ == '__main__':
    # 导入Excel数据
    import_excel_to_sqlite()
    
    # 创建用户表
    create_users_table() 