#!/usr/bin/env python
"""
丰富仪表盘数据脚本 - 完善数据库中的记录，使仪表盘显示更加真实
"""
import os
import sys
import sqlite3
import random
from datetime import datetime, timedelta
import pandas as pd

# 添加父目录到sys.path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from app import create_app
from app.config import config

# 内科常见诊断及症状
INTERNAL_MEDICINE_DIAGNOSES = [
    "高血压", "2型糖尿病", "冠心病", "慢性阻塞性肺疾病", "支气管哮喘", 
    "胃食管反流病", "慢性胃炎", "消化性溃疡", "急性胰腺炎", "慢性肾脏病",
    "肝硬化", "甲状腺功能亢进症", "贫血", "心房颤动", "心力衰竭"
]
INTERNAL_MEDICINE_SYMPTOMS = [
    "头痛", "胸痛", "呼吸困难", "腹痛", "腹泻", "恶心", "呕吐", "疲劳",
    "体重下降", "食欲不振", "发热", "水肿", "黄疸", "头晕", "心悸"
]

# 外科常见诊断及症状
SURGERY_DIAGNOSES = [
    "阑尾炎", "胆囊炎", "疝气", "肠梗阻", "胃溃疡穿孔", 
    "外伤性骨折", "颅内血肿", "肠套叠", "软组织感染", "脾破裂"
]
SURGERY_SYMPTOMS = [
    "腹痛", "腹胀", "恶心", "呕吐", "发热", "黄疸", "腹部压痛", 
    "腹部反跳痛", "无法排便排气", "肠鸣音亢进"
]

# 儿科常见诊断及症状
PEDIATRICS_DIAGNOSES = [
    "急性上呼吸道感染", "中耳炎", "肺炎", "腹泻", "手足口病", 
    "猩红热", "川崎病", "儿童哮喘", "营养不良", "发育迟缓"
]
PEDIATRICS_SYMPTOMS = [
    "发热", "咳嗽", "流涕", "喉咙痛", "头痛", "呕吐", "腹泻", 
    "皮疹", "食欲不振", "烦躁不安", "嗜睡"
]

# 妇产科常见诊断及症状
OBSTETRICS_DIAGNOSES = [
    "妊娠期高血压", "妊娠期糖尿病", "先兆流产", "先兆子痫", "胎盘早剥", 
    "前置胎盘", "妊娠剧吐", "多囊卵巢综合征", "子宫内膜异位症", "子宫肌瘤"
]
OBSTETRICS_SYMPTOMS = [
    "腹痛", "阴道出血", "恶心", "呕吐", "水肿", "头痛", "视力模糊", 
    "月经不规律", "痛经", "下腹坠胀感"
]

# 更多科室的诊断...
DEPT_DIAGNOSES = {
    "内科": INTERNAL_MEDICINE_DIAGNOSES,
    "外科": SURGERY_DIAGNOSES,
    "儿科": PEDIATRICS_DIAGNOSES,
    "妇产科": OBSTETRICS_DIAGNOSES,
    "神经内科": ["偏头痛", "癫痫", "帕金森病", "多发性硬化", "脑卒中", "阿尔茨海默病"],
    "心脏科": ["心肌梗死", "心绞痛", "心律失常", "风湿性心脏病", "冠心病", "高血压性心脏病"],
    "呼吸科": ["慢性阻塞性肺疾病", "肺炎", "支气管哮喘", "肺结核", "肺纤维化", "肺癌"],
    "消化科": ["胃炎", "消化性溃疡", "肝炎", "肝硬化", "胰腺炎", "结肠炎", "克罗恩病"],
    "神经外科": ["颅内肿瘤", "脑出血", "硬膜下血肿", "蛛网膜下腔出血", "椎间盘突出"],
    "骨科": ["骨折", "关节炎", "脊柱侧弯", "腰椎间盘突出", "腱鞘炎", "骨质疏松症"],
    "泌尿外科": ["肾结石", "尿路感染", "前列腺增生", "膀胱癌", "肾癌", "尿道狭窄"],
    "眼科": ["白内障", "青光眼", "结膜炎", "角膜炎", "视网膜脱离", "近视", "远视"],
    "耳鼻喉科": ["中耳炎", "鼻窦炎", "扁桃体炎", "咽喉炎", "过敏性鼻炎", "梅尼埃病"],
    "皮肤科": ["湿疹", "荨麻疹", "银屑病", "痤疮", "带状疱疹", "皮肤癌", "真菌感染"],
    "肿瘤科": ["肺癌", "肝癌", "胃癌", "结直肠癌", "乳腺癌", "前列腺癌", "白血病"],
    "急诊科": ["多发性创伤", "急性心肌梗死", "急性呼吸窘迫", "中毒", "休克", "脓毒症"],
    "精神科": ["抑郁症", "焦虑症", "双相情感障碍", "精神分裂症", "强迫症", "睡眠障碍"],
    "口腔科": ["龋齿", "牙周炎", "牙髓炎", "口腔溃疡", "口腔癌", "颞下颌关节紊乱"]
}

# 更多科室的症状...
DEPT_SYMPTOMS = {
    "内科": INTERNAL_MEDICINE_SYMPTOMS,
    "外科": SURGERY_SYMPTOMS,
    "儿科": PEDIATRICS_SYMPTOMS,
    "妇产科": OBSTETRICS_SYMPTOMS,
    "神经内科": ["头痛", "头晕", "肢体麻木", "肢体无力", "平衡障碍", "记忆力减退", "意识障碍"],
    "心脏科": ["胸痛", "心悸", "呼吸困难", "水肿", "晕厥", "乏力", "心前区不适"],
    "呼吸科": ["咳嗽", "咳痰", "呼吸困难", "胸痛", "咯血", "发热", "夜间呼吸困难"],
    "消化科": ["腹痛", "腹泻", "便秘", "黄疸", "恶心", "呕吐", "消化不良", "嗳气", "黑便"],
    "神经外科": ["剧烈头痛", "呕吐", "肢体瘫痪", "视力障碍", "癫痫发作", "意识障碍"],
    "骨科": ["关节痛", "肢体变形", "行走困难", "骨折", "肿胀", "活动受限", "脊柱疼痛"],
    "泌尿外科": ["尿频", "尿急", "尿痛", "血尿", "腰痛", "下腹痛", "排尿困难"],
    "眼科": ["视力下降", "眼痛", "畏光", "眼红", "流泪", "视野缺损", "眼内异物感"],
    "耳鼻喉科": ["耳痛", "听力下降", "耳鸣", "眩晕", "鼻塞", "流涕", "咽痛", "声音嘶哑"],
    "皮肤科": ["皮疹", "瘙痒", "脱发", "皮肤干燥", "色素沉着", "皮肤溃疡", "水疱"],
    "肿瘤科": ["不明原因体重减轻", "疲乏", "发热", "盗汗", "局部肿块", "疼痛", "贫血"],
    "急诊科": ["突发疼痛", "呼吸困难", "意识障碍", "大出血", "恶心呕吐", "心悸"],
    "精神科": ["情绪低落", "焦虑不安", "幻觉", "妄想", "思维障碍", "睡眠障碍", "食欲改变"],
    "口腔科": ["牙痛", "牙龈出血", "口腔溃疡", "牙齿松动", "口臭", "咀嚼困难", "张口受限"]
}

# 手术类型
SURGERY_TYPES = {
    "普通外科": ["阑尾切除术", "胆囊切除术", "疝修补术", "乳腺肿物切除术", "痔切除术", "甲状腺切除术"],
    "神经外科": ["颅内肿瘤切除术", "脑出血清除术", "椎板切除术", "脑室分流术"],
    "骨科": ["骨折内固定术", "关节置换术", "脊柱融合术", "韧带修复术", "截肢术"],
    "泌尿外科": ["前列腺切除术", "肾切除术", "膀胱肿瘤切除术", "尿路结石取出术"],
    "心胸外科": ["冠状动脉搭桥术", "心脏瓣膜置换术", "肺叶切除术", "食管切除术"],
    "妇产科": ["剖宫产术", "子宫肌瘤切除术", "宫颈锥切术", "卵巢囊肿摘除术"],
    "眼科": ["白内障摘除及人工晶体植入术", "青光眼手术", "视网膜脱离修复术"],
    "耳鼻喉科": ["扁桃体切除术", "鼻窦手术", "耳廓成形术", "鼓膜修补术"],
    "口腔科": ["牙齿拔除术", "牙周手术", "种植牙术", "正畸治疗"]
}

# 手术并发症
SURGERY_COMPLICATIONS = ["出血", "感染", "肺炎", "血栓", "伤口裂开", "麻醉并发症", "心律失常", "过敏反应", "没有并发症"]

def enrich_dashboard_data():
    """丰富仪表盘数据"""
    print("开始丰富仪表盘数据...")
    
    # 获取数据库路径
    app = create_app()
    with app.app_context():
        db_path = config.DATABASE_PATH
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. 丰富visits表的数据
        enrich_visits_data(cursor)
        
        # 2. 丰富admissions表的数据
        enrich_admissions_data(cursor)
        
        # 3. 丰富revenue表的数据
        enrich_revenue_data(cursor)
        
        # 4. 丰富surgeries表的数据
        enrich_surgeries_data(cursor)
        
        # 5. 创建更多警报数据
        create_more_alerts(cursor)
        
        # 提交所有更改
        conn.commit()
        print("仪表盘数据丰富完成！")
    
    except Exception as e:
        conn.rollback()
        print(f"丰富仪表盘数据时出错: {str(e)}")
    finally:
        conn.close()

def enrich_visits_data(cursor):
    """丰富门诊数据"""
    print("丰富门诊数据...")
    
    # 获取所有缺少visit_reason或diagnosis的visits记录
    cursor.execute("""
    SELECT id, department FROM visits 
    WHERE visit_reason IS NULL OR diagnosis IS NULL OR visit_reason = '' OR diagnosis = ''
    """)
    visits = cursor.fetchall()
    
    updated_count = 0
    
    for visit in visits:
        visit_id, department = visit
        
        # 为特定科室生成诊断和症状
        if department in DEPT_DIAGNOSES:
            diagnosis = random.choice(DEPT_DIAGNOSES[department])
            symptom = random.choice(DEPT_SYMPTOMS.get(department, ["不适"]))
            visit_reason = f"因{symptom}就诊"
            
            # 更新记录
            cursor.execute("""
            UPDATE visits
            SET visit_reason = ?, diagnosis = ?
            WHERE id = ?
            """, (visit_reason, diagnosis, visit_id))
            
            updated_count += 1
    
    print(f"更新了 {updated_count} 条门诊记录")

def enrich_admissions_data(cursor):
    """丰富住院数据"""
    print("丰富住院数据...")
    
    # 获取所有缺少诊断组或状态的admissions记录
    cursor.execute("""
    SELECT id, department FROM admissions 
    WHERE diagnosis_group IS NULL OR diagnosis_group = '' OR notes IS NULL OR notes = ''
    """)
    admissions = cursor.fetchall()
    
    updated_count = 0
    
    for admission in admissions:
        admission_id, department = admission
        
        # 生成诊断组
        if department in DEPT_DIAGNOSES:
            diagnosis = random.choice(DEPT_DIAGNOSES[department])
            diagnosis_group = f"{department}常见疾病"
            
            # 生成住院说明
            symptoms = random.sample(DEPT_SYMPTOMS.get(department, ["不适"]), min(3, len(DEPT_SYMPTOMS.get(department, ["不适"]))))
            symptom_text = "、".join(symptoms)
            notes = f"患者因{symptom_text}入院，诊断为{diagnosis}，需住院治疗。"
            
            # 更新记录
            cursor.execute("""
            UPDATE admissions
            SET diagnosis_group = ?, notes = ?
            WHERE id = ?
            """, (diagnosis_group, notes, admission_id))
            
            updated_count += 1
    
    print(f"更新了 {updated_count} 条住院记录")

def enrich_revenue_data(cursor):
    """丰富收入数据"""
    print("丰富收入数据...")
    
    # 获取所有缺少科室的revenue记录
    cursor.execute("""
    SELECT id, revenue_type FROM revenue 
    WHERE department IS NULL OR department = ''
    """)
    revenues = cursor.fetchall()
    
    departments = list(DEPT_DIAGNOSES.keys())
    updated_count = 0
    
    for revenue in revenues:
        revenue_id, revenue_type = revenue
        
        # 为收入记录分配科室
        department = random.choice(departments)
        
        # 更新说明
        description = f"{department}{revenue_type}"
        
        # 更新记录
        cursor.execute("""
        UPDATE revenue
        SET department = ?, description = ?
        WHERE id = ?
        """, (department, description, revenue_id))
        
        updated_count += 1
    
    print(f"更新了 {updated_count} 条收入记录")

def enrich_surgeries_data(cursor):
    """丰富手术数据"""
    print("丰富手术数据...")
    
    # 获取所有缺少具体手术类型或并发症的surgeries记录
    cursor.execute("""
    SELECT id, department FROM surgeries 
    WHERE surgery_type IS NULL OR surgery_type = '' OR complications IS NULL OR complications = ''
    """)
    surgeries = cursor.fetchall()
    
    updated_count = 0
    
    for surgery in surgeries:
        surgery_id, department = surgery
        
        # 生成手术类型
        surgery_type = "普通手术"
        for dept, types in SURGERY_TYPES.items():
            if department in dept or dept in department:
                surgery_type = random.choice(types)
                break
        
        # 生成并发症和备注
        complication = random.choice(SURGERY_COMPLICATIONS)
        patient_id = f"P{random.randint(10000, 99999)}"
        notes = f"患者{patient_id}的{surgery_type}"
        
        # 更新记录
        cursor.execute("""
        UPDATE surgeries
        SET surgery_type = ?, complications = ?, notes = ?
        WHERE id = ?
        """, (surgery_type, complication, notes, surgery_id))
        
        updated_count += 1
    
    print(f"更新了 {updated_count} 条手术记录")

def create_more_alerts(cursor):
    """创建更多警报数据"""
    print("创建更多警报数据...")
    
    # 警报类型
    alert_types = ["系统警报", "性能警报", "安全警报", "临床警报", "行政警报"]
    
    # 警报描述模板
    alert_templates = [
        "{}科室在过去{}小时内访问量异常{}，请关注",
        "系统检测到{}科室{}床位使用率已达{}%，接近饱和",
        "{}科室{}医生工作量超出正常范围{}%，建议调整",
        "药房{}类药品库存不足，剩余量低于安全阈值{}%",
        "{}科室{}设备报告错误，可能需要维护",
        "检测到潜在安全风险：{}，请相关部门关注",
        "{}科室{}患者生命体征异常波动，请立即关注",
        "系统备份延迟{}小时，请技术部门检查",
        "{}科室月度预算使用已达{}%，超出预期进度"
    ]
    
    # 获取现有科室列表
    cursor.execute("SELECT DISTINCT department FROM visits")
    departments = [row[0] for row in cursor.fetchall()]
    
    # 生成50条新警报
    new_alerts = []
    now = datetime.now()
    
    for i in range(50):
        alert_type = random.choice(alert_types)
        department = random.choice(departments)
        
        # 随机时间，最近48小时内
        alert_time = now - timedelta(hours=random.randint(0, 48))
        
        # 生成描述
        template = random.choice(alert_templates)
        if "{}" in template:
            if template.count("{}") == 1:
                description = template.format(department)
            elif template.count("{}") == 2:
                description = template.format(department, random.randint(10, 50))
            elif template.count("{}") == 3:
                description = template.format(department, random.choice(["上午", "下午", "夜间"]), random.randint(10, 50))
        else:
            description = f"{department}科室出现异常情况，请关注"
        
        # 状态
        status = random.choice(["新建", "已确认", "处理中", "已解决", "已关闭"])
        
        # 相关实体和ID
        related_entity = random.choice(["visit", "admission", "doctor", "department", "system", None])
        related_id = random.randint(1, 1000) if related_entity else None
        
        new_alerts.append((
            alert_time.strftime('%Y-%m-%d %H:%M:%S'),
            alert_type,
            description,
            status,
            related_entity,
            related_id
        ))
    
    # 添加到数据库
    cursor.executemany("""
    INSERT INTO alerts (alert_time, alert_type, description, status, related_entity, related_id)
    VALUES (?, ?, ?, ?, ?, ?)
    """, new_alerts)
    
    print(f"创建了 {len(new_alerts)} 条新警报")

if __name__ == "__main__":
    enrich_dashboard_data() 