#!/usr/bin/env python
"""
初始化数据库脚本
"""
import os
import sys
import sqlite3

# 添加父目录到sys.path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from app import create_app
from app.extensions import db
from app.models.user import User

def init_database():
    """初始化数据库"""
    app = create_app()
    
    # 获取实例目录路径
    instance_path = app.instance_path
    db_path = os.path.join(instance_path, 'medical_workload.db')
    
    with app.app_context():
        # 先备份现有数据库
        if os.path.exists(db_path):
            backup_path = os.path.join(instance_path, 'medical_workload.db.bak')
            print(f"备份数据库到 {backup_path}")
            try:
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                import shutil
                shutil.copy2(db_path, backup_path)
            except Exception as e:
                print(f"备份数据库失败: {str(e)}")
                return
        
        # 删除现有表并重新创建
        print("重建数据库表...")
        db.drop_all()
        db.create_all()
        
        # 恢复必要的数据表
        try:
            restore_data(db_path, backup_path)
        except Exception as e:
            print(f"恢复数据失败: {str(e)}")
        
        # 创建管理员用户
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("创建管理员用户...")
            admin = User(username='admin', email='admin@example.com', is_admin=True)
            admin.set_password('Admin123!')
            db.session.add(admin)
            db.session.commit()
        
        print("数据库初始化完成")

def restore_data(db_path, backup_path):
    """恢复数据到新表结构"""
    if not os.path.exists(backup_path):
        print("没有找到备份数据库，跳过数据恢复")
        return
    
    # 连接备份数据库
    backup_conn = sqlite3.connect(backup_path)
    backup_conn.row_factory = sqlite3.Row
    
    # 连接新数据库
    db_conn = sqlite3.connect(db_path)
    
    # 恢复门诊量表
    try:
        print("恢复门诊量表数据...")
        rows = backup_conn.execute("SELECT * FROM 门诊量").fetchall()
        for row in rows:
            db_conn.execute(
                "INSERT INTO 门诊量(科室, 专科, 日期, 数量) VALUES(?, ?, ?, ?)",
                (row['科室'], row['专科'], row['日期'], row['数量'])
            )
        db_conn.commit()
        print(f"已恢复 {len(rows)} 条门诊量记录")
    except Exception as e:
        print(f"恢复门诊量表失败: {str(e)}")
    
    # 恢复目标值表
    try:
        print("恢复目标值表数据...")
        rows = backup_conn.execute("SELECT * FROM 目标值").fetchall()
        for row in rows:
            db_conn.execute(
                "INSERT INTO 目标值(科室, 专科, 年, 月, 目标值) VALUES(?, ?, ?, ?, ?)",
                (row['科室'], row['专科'], row['年'], row['月'], row['目标值'])
            )
        db_conn.commit()
        print(f"已恢复 {len(rows)} 条目标值记录")
    except Exception as e:
        print(f"恢复目标值表失败: {str(e)}")
    
    # 恢复DRG记录表
    try:
        print("恢复DRG记录表数据...")
        rows = backup_conn.execute("SELECT * FROM drg_records").fetchall()
        for row in rows:
            db_conn.execute(
                """INSERT INTO drg_records(record_date, department, drg_group, 
                weight_score, cost_index, time_index, total_cost, length_of_stay) 
                VALUES(?, ?, ?, ?, ?, ?, ?, ?)""",
                (row['record_date'], row['department'], row['drg_group'], 
                 row['weight_score'], row['cost_index'], row['time_index'], 
                 row['total_cost'], row['length_of_stay'])
            )
        db_conn.commit()
        print(f"已恢复 {len(rows)} 条DRG记录")
    except Exception as e:
        print(f"恢复DRG记录表失败: {str(e)}")
    
    # 关闭连接
    backup_conn.close()
    db_conn.close()

if __name__ == '__main__':
    init_database() 