"""
数据库元数据分析器
自动分析数据库结构，提供智能的表名和字段名匹配
"""

import sqlite3
import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from collections import defaultdict
import json

@dataclass
class TableInfo:
    """表信息"""
    name: str
    columns: List[str]
    column_types: Dict[str, str]
    sample_data: Dict[str, Any]
    semantic_tags: List[str]
    description: str

@dataclass
class ColumnInfo:
    """字段信息"""
    name: str
    type: str
    table: str
    sample_values: List[Any]
    semantic_tags: List[str]
    description: str

class DatabaseMetaAnalyzer:
    """数据库元数据分析器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.tables_info: Dict[str, TableInfo] = {}
        self.semantic_index: Dict[str, List[str]] = defaultdict(list)  # 语义 -> 表名列表
        self.column_index: Dict[str, List[Tuple[str, str]]] = defaultdict(list)  # 语义 -> (表名, 字段名)列表
        
        # 医疗领域语义映射
        self.medical_semantics = {
            # 门诊相关
            'outpatient': ['门诊', '门诊量', '门诊记录', '门诊数', '就诊', '看病'],
            'visit': ['就诊', '访问', '看诊', '诊疗', '门诊'],
            'visits_count': ['门诊量', '就诊量', '门诊数量', '诊疗次数'],
            
            # 住院相关
            'inpatient': ['住院', '住院量', '住院记录', '入院', '住院数'],
            'admission': ['入院', '住院', '收治', '住院记录'],
            'discharge': ['出院', '离院', '出院记录'],
            
            # 手术相关
            'surgery': ['手术', '手术量', '手术记录', '手术数', '外科'],
            'operation': ['手术', '操作', '治疗'],
            
            # 科室相关
            'department': ['科室', '部门', '科', '专科'],
            'specialty': ['专科', '专业', '科室', '专业科室'],
            
            # 医生相关
            'doctor': ['医生', '医师', '大夫', '医务人员'],
            'physician': ['内科医生', '医师'],
            
            # 患者相关
            'patient': ['患者', '病人', '病患', '就诊者'],
            
            # 收入相关
            'revenue': ['收入', '收益', '营收', '费用', '金额'],
            'income': ['收入', '收益', '进项'],
            'cost': ['成本', '费用', '花费', '支出'],
            
            # 时间相关
            'date': ['日期', '时间', '年份', '月份', '时段'],
            'year': ['年', '年份', '年度'],
            'month': ['月', '月份'],
            'day': ['日', '天', '日期'],
            
            # 数量相关
            'count': ['数量', '数', '次数', '个数', '总数'],
            'amount': ['金额', '数额', '总额'],
            'total': ['总计', '合计', '总量', '总数'],
            
            # 绩效相关
            'performance': ['绩效', '表现', '业绩', '成绩'],
            'efficiency': ['效率', '效能', '效果'],
            'workload': ['工作量', '负荷', '任务量'],
            
            # 分析相关
            'trend': ['趋势', '走势', '变化', '发展'],
            'comparison': ['对比', '比较', '对照'],
            'analysis': ['分析', '统计', '评估']
        }
        
        self._analyze_database()
    
    def _analyze_database(self):
        """分析数据库结构"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 获取所有表名
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row['name'] for row in cursor.fetchall()]
                
                for table_name in tables:
                    if table_name.startswith('sqlite_'):
                        continue
                        
                    # 分析每个表
                    table_info = self._analyze_table(conn, table_name)
                    self.tables_info[table_name] = table_info
                    
                    # 建立语义索引
                    self._build_semantic_index(table_info)
                    
                print(f"数据库元数据分析完成，共分析了 {len(self.tables_info)} 个表")
                print(f"语义索引: {dict(self.semantic_index)}")
                
        except Exception as e:
            print(f"数据库元数据分析失败: {str(e)}")
    
    def _analyze_table(self, conn: sqlite3.Connection, table_name: str) -> TableInfo:
        """分析单个表"""
        cursor = conn.cursor()
        
        # 获取表结构
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = cursor.fetchall()
        
        columns = [col['name'] for col in columns_info]
        column_types = {col['name']: col['type'] for col in columns_info}
        
        # 获取样本数据
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
        sample_rows = cursor.fetchall()
        sample_data = {}
        if sample_rows:
            sample_data = {col: [row[col] for row in sample_rows if row[col] is not None] 
                          for col in columns}
        
        # 推断语义标签
        semantic_tags = self._infer_table_semantics(table_name, columns, sample_data)
        
        # 生成描述
        description = self._generate_table_description(table_name, columns, semantic_tags)
        
        return TableInfo(
            name=table_name,
            columns=columns,
            column_types=column_types,
            sample_data=sample_data,
            semantic_tags=semantic_tags,
            description=description
        )
    
    def _infer_table_semantics(self, table_name: str, columns: List[str], sample_data: Dict) -> List[str]:
        """推断表的语义标签"""
        tags = []
        
        # 基于表名推断
        table_lower = table_name.lower()
        if 'visit' in table_lower:
            tags.extend(['outpatient', 'visit', 'medical_record'])
        elif 'admission' in table_lower:
            tags.extend(['inpatient', 'admission', 'hospital'])
        elif 'surgery' in table_lower or 'surgeries' in table_lower:
            tags.extend(['surgery', 'operation', 'medical'])
        elif 'revenue' in table_lower:
            tags.extend(['revenue', 'financial', 'income'])
        elif 'department' in table_lower:
            tags.extend(['department', 'organizational'])
        
        # 基于字段名推断
        column_lower = [col.lower() for col in columns]
        if any('department' in col for col in column_lower):
            tags.append('department')
        if any('date' in col or 'time' in col for col in column_lower):
            tags.append('temporal')
        if any('amount' in col or 'cost' in col or 'revenue' in col for col in column_lower):
            tags.append('financial')
        if any('patient' in col for col in column_lower):
            tags.append('patient')
        if any('doctor' in col for col in column_lower):
            tags.append('doctor')
            
        return list(set(tags))
    
    def _generate_table_description(self, table_name: str, columns: List[str], tags: List[str]) -> str:
        """生成表描述"""
        descriptions = {
            'visits': '门诊记录表，存储患者就诊信息',
            'admissions': '住院记录表，存储患者住院信息', 
            'surgeries': '手术记录表，存储手术相关信息',
            'revenue': '收入记录表，存储医疗收入数据',
            'department_workload': '科室工作量表，存储各科室工作量统计',
            'department_efficiency': '科室效率表，存储科室效率指标',
            'department_resources': '科室资源表，存储科室资源配置',
            'department_revenue': '科室收入表，存储各科室收入数据',
            'alerts': '警报表，存储系统警报信息',
            'users': '用户表，存储用户账户信息'
        }
        
        return descriptions.get(table_name, f'{table_name}表，包含字段：{", ".join(columns)}')
    
    def _build_semantic_index(self, table_info: TableInfo):
        """建立语义索引"""
        table_name = table_info.name
        
        # 为表建立索引
        for tag in table_info.semantic_tags:
            self.semantic_index[tag].append(table_name)
            
        # 基于医疗语义映射建立索引
        for semantic_key, keywords in self.medical_semantics.items():
            for keyword in keywords:
                # 检查表名或字段名是否匹配
                if self._semantic_match(keyword, table_name, table_info.columns):
                    self.semantic_index[keyword].append(table_name)
                    
        # 为字段建立索引
        for column in table_info.columns:
            for semantic_key, keywords in self.medical_semantics.items():
                for keyword in keywords:
                    if self._semantic_match(keyword, column, []):
                        self.column_index[keyword].append((table_name, column))
    
    def _semantic_match(self, keyword: str, target: str, columns: List[str] = None) -> bool:
        """语义匹配"""
        if not target:
            return False
            
        target_lower = target.lower()
        keyword_lower = keyword.lower()
        
        # 直接匹配
        if keyword_lower in target_lower:
            return True
            
        # 英文医疗术语匹配
        medical_terms = {
            '门诊': ['visit', 'outpatient'],
            '住院': ['admission', 'inpatient'], 
            '手术': ['surgery', 'operation'],
            '科室': ['department'],
            '收入': ['revenue', 'income'],
            '数量': ['count', 'amount', 'total']
        }
        
        if keyword in medical_terms:
            return any(term in target_lower for term in medical_terms[keyword])
            
        return False
    
    def find_relevant_tables(self, user_query: str) -> List[Tuple[str, float]]:
        """根据用户查询找到相关表"""
        query_lower = user_query.lower()
        table_scores = defaultdict(float)
        
        # 检查语义索引
        for keyword, tables in self.semantic_index.items():
            if keyword in query_lower:
                for table in tables:
                    table_scores[table] += 1.0
        
        # 检查医疗语义
        for semantic_key, keywords in self.medical_semantics.items():
            for keyword in keywords:
                if keyword in query_lower:
                    if semantic_key in self.semantic_index:
                        for table in self.semantic_index[semantic_key]:
                            table_scores[table] += 0.8
        
        # 直接匹配表名
        for table_name in self.tables_info:
            if table_name.lower() in query_lower:
                table_scores[table_name] += 2.0
                
        # 排序并返回
        sorted_tables = sorted(table_scores.items(), key=lambda x: x[1], reverse=True)
        return [(table, score) for table, score in sorted_tables if score > 0]
    
    def find_relevant_columns(self, user_query: str, table_name: str = None) -> List[Tuple[str, str, float]]:
        """根据用户查询找到相关字段"""
        query_lower = user_query.lower()
        column_scores = defaultdict(float)
        
        # 如果指定了表，只在该表中查找
        tables_to_search = [table_name] if table_name and table_name in self.tables_info else list(self.tables_info.keys())
        
        for table in tables_to_search:
            table_info = self.tables_info[table]
            for column in table_info.columns:
                column_lower = column.lower()
                
                # 直接匹配
                if any(keyword in query_lower for keyword in [column_lower]):
                    column_scores[(table, column)] += 2.0
                
                # 语义匹配
                for semantic_key, keywords in self.medical_semantics.items():
                    for keyword in keywords:
                        if keyword in query_lower and self._semantic_match(keyword, column):
                            column_scores[(table, column)] += 1.0
        
        # 排序并返回
        sorted_columns = sorted(column_scores.items(), key=lambda x: x[1], reverse=True)
        return [(table, column, score) for (table, column), score in sorted_columns if score > 0]
    
    def get_table_info(self, table_name: str) -> Optional[TableInfo]:
        """获取表信息"""
        return self.tables_info.get(table_name)
    
    def suggest_query_structure(self, user_query: str) -> Dict[str, Any]:
        """建议查询结构"""
        relevant_tables = self.find_relevant_tables(user_query)
        relevant_columns = self.find_relevant_columns(user_query)
        
        if not relevant_tables:
            return {"error": "未找到相关表", "suggestion": "请检查查询关键词"}
        
        primary_table = relevant_tables[0][0]
        primary_table_info = self.tables_info[primary_table]
        
        # 推荐字段
        recommended_columns = []
        if relevant_columns:
            # 优先选择高分字段
            for table, column, score in relevant_columns[:5]:
                if table == primary_table:
                    recommended_columns.append(column)
        
        # 如果没有找到相关字段，使用默认字段
        if not recommended_columns:
            # 基于查询类型推荐字段
            if any(keyword in user_query.lower() for keyword in ['趋势', '变化', '时间']):
                date_columns = [col for col in primary_table_info.columns if 'date' in col.lower() or 'time' in col.lower()]
                recommended_columns.extend(date_columns[:2])
            
            if any(keyword in user_query.lower() for keyword in ['科室', '部门']):
                dept_columns = [col for col in primary_table_info.columns if 'department' in col.lower()]
                recommended_columns.extend(dept_columns)
            
            if any(keyword in user_query.lower() for keyword in ['数量', '统计', '多少']):
                # 添加计数或数值字段
                recommended_columns.append('COUNT(*)')
        
        return {
            "primary_table": primary_table,
            "table_description": primary_table_info.description,
            "recommended_columns": recommended_columns[:5],
            "all_columns": primary_table_info.columns,
            "alternative_tables": [table for table, _ in relevant_tables[1:3]],
            "query_type": self._infer_query_type(user_query)
        }
    
    def _infer_query_type(self, user_query: str) -> str:
        """推断查询类型"""
        query_lower = user_query.lower()
        
        if any(keyword in query_lower for keyword in ['趋势', '变化', '发展']):
            return 'trend_analysis'
        elif any(keyword in query_lower for keyword in ['对比', '比较']):
            return 'comparison'
        elif any(keyword in query_lower for keyword in ['统计', '总计', '合计']):
            return 'aggregation'
        elif any(keyword in query_lower for keyword in ['排名', '最好', '最差', '排序']):
            return 'ranking'
        elif any(keyword in query_lower for keyword in ['详细', '明细', '列表']):
            return 'detailed_list'
        else:
            return 'general_query'
    
    def generate_smart_sql(self, user_query: str) -> Optional[str]:
        """智能生成SQL查询"""
        suggestion = self.suggest_query_structure(user_query)
        
        if "error" in suggestion:
            return None
            
        table = suggestion["primary_table"]
        columns = suggestion["recommended_columns"]
        query_type = suggestion["query_type"]
        
        # 根据查询类型生成SQL
        if query_type == 'trend_analysis':
            return self._generate_trend_sql(table, columns, user_query)
        elif query_type == 'comparison':
            return self._generate_comparison_sql(table, columns, user_query)
        elif query_type == 'aggregation':
            return self._generate_aggregation_sql(table, columns, user_query)
        elif query_type == 'ranking':
            return self._generate_ranking_sql(table, columns, user_query)
        else:
            return self._generate_general_sql(table, columns, user_query)
    
    def _generate_trend_sql(self, table: str, columns: List[str], user_query: str) -> str:
        """生成趋势分析SQL"""
        table_info = self.tables_info[table]
        
        # 找日期字段
        date_column = None
        for col in table_info.columns:
            if any(keyword in col.lower() for keyword in ['date', 'time', '日期', '时间']):
                date_column = col
                break
        
        if not date_column:
            date_column = 'created_at'  # 默认字段
            
        # 找聚合字段
        if 'department' in table_info.columns:
            return f"""
            SELECT DATE({date_column}) as date, 
                   department, 
                   COUNT(*) as count
            FROM {table} 
            GROUP BY DATE({date_column}), department 
            ORDER BY date, department
            """
        else:
            return f"""
            SELECT DATE({date_column}) as date, 
                   COUNT(*) as count
            FROM {table} 
            GROUP BY DATE({date_column}) 
            ORDER BY date
            """
    
    def _generate_comparison_sql(self, table: str, columns: List[str], user_query: str) -> str:
        """生成对比分析SQL"""
        table_info = self.tables_info[table]
        
        if 'department' in table_info.columns:
            return f"""
            SELECT department, 
                   COUNT(*) as total_count,
                   AVG(CASE WHEN created_at >= date('now', '-30 days') THEN 1 ELSE 0 END) as recent_activity
            FROM {table} 
            GROUP BY department 
            ORDER BY total_count DESC
            """
        else:
            return f"SELECT * FROM {table} LIMIT 20"
    
    def _generate_aggregation_sql(self, table: str, columns: List[str], user_query: str) -> str:
        """生成聚合统计SQL"""
        table_info = self.tables_info[table]
        
        if 'department' in table_info.columns:
            return f"""
            SELECT department,
                   COUNT(*) as total_count,
                   MIN(created_at) as first_record,
                   MAX(created_at) as last_record
            FROM {table} 
            GROUP BY department
            ORDER BY total_count DESC
            """
        else:
            return f"SELECT COUNT(*) as total_count FROM {table}"
    
    def _generate_ranking_sql(self, table: str, columns: List[str], user_query: str) -> str:
        """生成排名SQL"""
        table_info = self.tables_info[table]
        
        if 'department' in table_info.columns:
            return f"""
            SELECT department,
                   COUNT(*) as count,
                   RANK() OVER (ORDER BY COUNT(*) DESC) as ranking
            FROM {table} 
            GROUP BY department
            ORDER BY count DESC
            """
        else:
            return f"SELECT * FROM {table} ORDER BY id DESC LIMIT 10"
    
    def _generate_general_sql(self, table: str, columns: List[str], user_query: str) -> str:
        """生成通用SQL"""
        if columns and 'COUNT(*)' not in columns:
            column_str = ', '.join(columns)
            return f"SELECT {column_str} FROM {table} LIMIT 20"
        else:
            return f"SELECT * FROM {table} LIMIT 10"
