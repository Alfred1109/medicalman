import pandas as pd
import sqlite3
from datetime import datetime

def import_excel_to_sqlite():
    # 连接到SQLite数据库
    conn = sqlite3.connect('medical_workload.db')
    
    try:
        # 读取Excel文件中的所有sheet
        excel_file = pd.ExcelFile('医疗数据表.xlsx')
        sheet_names = excel_file.sheet_names
        
        # 删除原有的工作量表
        print("删除原有的工作量表...")
        conn.execute("DROP TABLE IF EXISTS workload")
        
        # 遍历所有sheet并导入
        for sheet_name in sheet_names:
            print(f"\n正在处理sheet: {sheet_name}")
            
            try:
                # 读取sheet数据
                df = pd.read_excel('医疗数据表.xlsx', sheet_name=sheet_name)
                
                # 检查是否为空sheet
                if df.empty:
                    print(f"Sheet {sheet_name} 为空，跳过导入")
                    continue
                    
                # 删除全为空值的行和列
                df = df.dropna(how='all', axis=0)  # 删除全为空的行
                df = df.dropna(how='all', axis=1)  # 删除全为空的列
                
                if df.empty:
                    print(f"Sheet {sheet_name} 清理后为空，跳过导入")
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
                print(f"处理 {sheet_name} 时出错: {str(e)}")
                continue
        
        print("\n所有数据导入完成！")
        
    except Exception as e:
        print(f"导入过程中出错: {str(e)}")
    finally:
        conn.close()

if __name__ == '__main__':
    import_excel_to_sqlite() 