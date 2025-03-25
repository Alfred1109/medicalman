"""
仪表盘数据修复脚本 - 确保数据库表结构正确并有足够的演示数据
"""
import os
import sqlite3
import datetime
import random
import sys

# 获取项目根目录
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT_DIR, 'instance', 'medical_workload.db')

def verify_table_schema():
    """验证数据库表结构是否正确"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查visits表结构
        cursor.execute("PRAGMA table_info(visits)")
        visits_columns = [column[1] for column in cursor.fetchall()]
        
        # 如果表结构不正确，重新创建
        if not 'date' in visits_columns:
            print("visits表结构不正确，重新创建...")
            cursor.execute("DROP TABLE IF EXISTS visits")
            cursor.execute("""
            CREATE TABLE visits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                patient_id INTEGER,
                department TEXT,
                doctor TEXT,
                diagnosis TEXT,
                fee REAL
            )
            """)
            
        # 检查admissions表结构
        cursor.execute("PRAGMA table_info(admissions)")
        admissions_columns = [column[1] for column in cursor.fetchall()]
        
        if not 'admission_date' in admissions_columns:
            print("admissions表结构不正确，重新创建...")
            cursor.execute("DROP TABLE IF EXISTS admissions")
            cursor.execute("""
            CREATE TABLE admissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admission_date TEXT,
                discharge_date TEXT,
                patient_id INTEGER,
                department TEXT,
                diagnosis_group TEXT,
                length_of_stay INTEGER,
                fee REAL
            )
            """)
            
        # 检查revenue表结构
        cursor.execute("PRAGMA table_info(revenue)")
        revenue_columns = [column[1] for column in cursor.fetchall()]
        
        if not 'revenue_type' in revenue_columns:
            print("revenue表结构不正确，重新创建...")
            cursor.execute("DROP TABLE IF EXISTS revenue")
            cursor.execute("""
            CREATE TABLE revenue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                revenue_type TEXT,
                amount REAL,
                description TEXT
            )
            """)
            
        # 检查surgeries表结构
        cursor.execute("PRAGMA table_info(surgeries)")
        surgeries_columns = [column[1] for column in cursor.fetchall()]
        
        if not 'surgery_date' in surgeries_columns:
            print("surgeries表结构不正确，重新创建...")
            cursor.execute("DROP TABLE IF EXISTS surgeries")
            cursor.execute("""
            CREATE TABLE surgeries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                surgery_date TEXT,
                patient_id INTEGER,
                department TEXT,
                surgery_type TEXT,
                duration INTEGER,
                fee REAL
            )
            """)
            
        # 检查alerts表结构
        cursor.execute("PRAGMA table_info(alerts)")
        alerts_columns = [column[1] for column in cursor.fetchall()]
        
        if not 'alert_type' in alerts_columns:
            print("alerts表结构不正确，重新创建...")
            cursor.execute("DROP TABLE IF EXISTS alerts")
            cursor.execute("""
            CREATE TABLE alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_time TEXT,
                alert_type TEXT,
                description TEXT,
                status TEXT
            )
            """)
            
        conn.commit()
        print("数据库表结构验证完成")
    except Exception as e:
        print(f"验证表结构时出错: {str(e)}")
    finally:
        if conn:
            conn.close()

def check_data_amount():
    """检查各表中的数据量"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        tables = ['visits', 'admissions', 'revenue', 'surgeries', 'alerts']
        data_counts = {}
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                data_counts[table] = count
            except sqlite3.OperationalError:
                data_counts[table] = 0
        
        print("各表数据量:")
        for table, count in data_counts.items():
            print(f"  {table}: {count}条记录")
            
        return data_counts
    except Exception as e:
        print(f"检查数据量时出错: {str(e)}")
        return {}
    finally:
        if conn:
            conn.close()

def generate_demo_data():
    """调用项目中的演示数据生成函数"""
    try:
        print("开始生成演示数据...")
        # 使用正确的路径导入数据库初始化模块
        sys.path.insert(0, ROOT_DIR)
        from app.routes.dashboard_routes import initialize_demo_data
        
        # 执行数据初始化
        initialize_demo_data()
        print("演示数据生成完成")
    except Exception as e:
        print(f"生成演示数据时出错: {str(e)}")
        import traceback
        traceback.print_exc()

def clear_data():
    """清空所有表中的数据"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        tables = ['visits', 'admissions', 'revenue', 'surgeries', 'alerts']
        
        for table in tables:
            try:
                cursor.execute(f"DELETE FROM {table}")
                print(f"已清空表 {table}")
            except sqlite3.OperationalError:
                print(f"表 {table} 不存在，跳过")
        
        conn.commit()
        print("所有表数据已清空")
    except Exception as e:
        print(f"清空数据时出错: {str(e)}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print(f"数据库路径: {DB_PATH}")
    
    # 检查数据库是否存在
    if not os.path.exists(DB_PATH):
        print("数据库文件不存在，将创建新的数据库")
        # 确保目录存在
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # 验证表结构
    verify_table_schema()
    
    # 检查数据量
    data_counts = check_data_amount()
    
    # 如果数据量不足，生成演示数据
    if any(count < 100 for count in data_counts.values()):
        user_input = input("数据量不足，是否重新生成演示数据？(y/n): ")
        if user_input.lower() == 'y':
            # 清空现有数据
            clear_data()
            # 生成新的演示数据
            generate_demo_data()
            # 再次检查数据量
            check_data_amount()
    
    print("数据库检查和修复完成") 