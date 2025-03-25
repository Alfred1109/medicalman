"""
工作量模型模块 - 定义工作量相关数据模型
"""
from typing import Dict, List, Any, Optional, ClassVar
import datetime

from app.models.base_model import BaseModel
from app.utils.utils import format_datetime

class WorkloadCategory(BaseModel):
    """工作量类别模型类"""
    
    # 表名与主键
    __tablename__: ClassVar[str] = "workload_categories"
    __primary_key__: ClassVar[str] = "id"
    
    # 默认排序
    __order_by__: ClassVar[str] = "name ASC"
    
    # 字段定义
    __fields__: ClassVar[Dict[str, str]] = {
        "name": "类别名称",
        "description": "类别描述",
        "department": "所属科室",
        "points_rule": "分值规则",
        "is_active": "是否启用",
        "created_at": "创建时间",
        "updated_at": "更新时间",
        "parent_id": "父类别ID",
        "order": "排序"
    }
    
    # 日期时间字段
    __datetime_fields__: ClassVar[List[str]] = ["created_at", "updated_at"]
    
    # JSON字段
    __json_fields__: ClassVar[List[str]] = ["points_rule"]
    
    def __init__(self, **kwargs):
        """
        初始化工作量类别实例
        
        参数:
            **kwargs: 工作量类别属性
        """
        # 设置默认值
        now = datetime.datetime.now()
        defaults = {
            "created_at": now,
            "updated_at": now,
            "is_active": True,
            "points_rule": {},
            "order": 0
        }
        
        # 合并默认值和传入的值
        data = {**defaults, **kwargs}
        
        # 调用父类初始化方法
        super().__init__(**data)
    
    @classmethod
    def get_all_active(cls) -> List['WorkloadCategory']:
        """
        获取所有启用的工作量类别
        
        返回:
            启用的工作量类别列表
        """
        return cls.find(is_active=True)
    
    @classmethod
    def get_by_department(cls, department: str) -> List['WorkloadCategory']:
        """
        获取指定科室的工作量类别
        
        参数:
            department: 科室名称
            
        返回:
            工作量类别列表
        """
        return cls.find(department=department, is_active=True)
    
    @classmethod
    def get_root_categories(cls) -> List['WorkloadCategory']:
        """
        获取所有根类别（没有父类别的类别）
        
        返回:
            根类别列表
        """
        condition = "(parent_id IS NULL OR parent_id = '') AND is_active = 1"
        return cls.get_all(condition)
    
    @classmethod
    def get_subcategories(cls, parent_id: str) -> List['WorkloadCategory']:
        """
        获取指定父类别的子类别
        
        参数:
            parent_id: 父类别ID
            
        返回:
            子类别列表
        """
        return cls.find(parent_id=parent_id, is_active=True)

class WorkloadRecord(BaseModel):
    """工作量记录模型类"""
    
    # 表名与主键
    __tablename__: ClassVar[str] = "workload_records"
    __primary_key__: ClassVar[str] = "id"
    
    # 默认排序
    __order_by__: ClassVar[str] = "record_date DESC"
    
    # 字段定义
    __fields__: ClassVar[Dict[str, str]] = {
        "doctor_id": "医生ID",
        "category_id": "工作量类别ID",
        "record_date": "记录日期",
        "points": "分值",
        "quantity": "数量",
        "description": "描述",
        "reference_id": "关联记录ID",
        "reference_type": "关联记录类型",
        "status": "状态",
        "approved_by": "审核人",
        "approved_at": "审核时间",
        "created_at": "创建时间",
        "updated_at": "更新时间",
        "metadata": "元数据"
    }
    
    # 日期时间字段
    __datetime_fields__: ClassVar[List[str]] = ["record_date", "approved_at", "created_at", "updated_at"]
    
    # JSON字段
    __json_fields__: ClassVar[List[str]] = ["metadata"]
    
    def __init__(self, **kwargs):
        """
        初始化工作量记录实例
        
        参数:
            **kwargs: 工作量记录属性
        """
        # 设置默认值
        now = datetime.datetime.now()
        defaults = {
            "created_at": now,
            "updated_at": now,
            "record_date": now,
            "status": "待审核",
            "quantity": 1,
            "points": 0,
            "metadata": {}
        }
        
        # 合并默认值和传入的值
        data = {**defaults, **kwargs}
        
        # 调用父类初始化方法
        super().__init__(**data)
    
    def approve(self, approved_by: str) -> None:
        """
        审核工作量记录
        
        参数:
            approved_by: 审核人ID
        """
        self.status = "已审核"
        self.approved_by = approved_by
        self.approved_at = datetime.datetime.now()
        self.updated_at = datetime.datetime.now()
    
    def reject(self, approved_by: str, reason: str = None) -> None:
        """
        拒绝工作量记录
        
        参数:
            approved_by: 审核人ID
            reason: 拒绝原因
        """
        self.status = "已拒绝"
        self.approved_by = approved_by
        self.approved_at = datetime.datetime.now()
        self.updated_at = datetime.datetime.now()
        
        if reason:
            if not hasattr(self, "metadata") or self.metadata is None:
                self.metadata = {}
            self.metadata["reject_reason"] = reason
    
    @classmethod
    def find_by_doctor(cls, doctor_id: str, 
                        start_date: Optional[datetime.datetime] = None,
                        end_date: Optional[datetime.datetime] = None,
                        status: Optional[str] = None) -> List['WorkloadRecord']:
        """
        查找医生的工作量记录
        
        参数:
            doctor_id: 医生ID
            start_date: 开始日期
            end_date: 结束日期
            status: 状态
            
        返回:
            工作量记录列表
        """
        conditions = ["doctor_id = ?"]
        params = [doctor_id]
        
        if start_date:
            conditions.append("record_date >= ?")
            params.append(start_date.isoformat() if isinstance(start_date, datetime.datetime) else start_date)
            
        if end_date:
            conditions.append("record_date <= ?")
            params.append(end_date.isoformat() if isinstance(end_date, datetime.datetime) else end_date)
            
        if status:
            conditions.append("status = ?")
            params.append(status)
            
        condition = " AND ".join(conditions)
        
        return cls.get_all(condition, tuple(params))
    
    @classmethod
    def find_by_category(cls, category_id: str,
                         start_date: Optional[datetime.datetime] = None,
                         end_date: Optional[datetime.datetime] = None) -> List['WorkloadRecord']:
        """
        查找类别的工作量记录
        
        参数:
            category_id: 类别ID
            start_date: 开始日期
            end_date: 结束日期
            
        返回:
            工作量记录列表
        """
        conditions = ["category_id = ?"]
        params = [category_id]
        
        if start_date:
            conditions.append("record_date >= ?")
            params.append(start_date.isoformat() if isinstance(start_date, datetime.datetime) else start_date)
            
        if end_date:
            conditions.append("record_date <= ?")
            params.append(end_date.isoformat() if isinstance(end_date, datetime.datetime) else end_date)
            
        condition = " AND ".join(conditions)
        
        return cls.get_all(condition, tuple(params))
    
    @classmethod
    def get_pending_approvals(cls) -> List['WorkloadRecord']:
        """
        获取待审核的工作量记录
        
        返回:
            待审核的工作量记录列表
        """
        return cls.find(status="待审核")
    
    @classmethod
    def get_summary_by_doctor(cls, doctor_id: str, 
                           start_date: Optional[datetime.datetime] = None,
                           end_date: Optional[datetime.datetime] = None) -> Dict[str, Any]:
        """
        获取医生的工作量汇总
        
        参数:
            doctor_id: 医生ID
            start_date: 开始日期
            end_date: 结束日期
            
        返回:
            工作量汇总数据
        """
        conditions = ["doctor_id = ? AND status = '已审核'"]
        params = [doctor_id]
        
        if start_date:
            conditions.append("record_date >= ?")
            params.append(start_date.isoformat() if isinstance(start_date, datetime.datetime) else start_date)
            
        if end_date:
            conditions.append("record_date <= ?")
            params.append(end_date.isoformat() if isinstance(end_date, datetime.datetime) else end_date)
            
        condition = " AND ".join(conditions)
        
        # 获取记录
        records = cls.get_all(condition, tuple(params))
        
        # 计算总分值
        total_points = sum(record.points for record in records if hasattr(record, "points") and record.points)
        
        # 按类别分组
        category_summary = {}
        for record in records:
            if not hasattr(record, "category_id") or not record.category_id:
                continue
                
            if record.category_id not in category_summary:
                category_summary[record.category_id] = {
                    "count": 0,
                    "points": 0
                }
                
            category_summary[record.category_id]["count"] += 1
            category_summary[record.category_id]["points"] += record.points if hasattr(record, "points") and record.points else 0
            
        return {
            "doctor_id": doctor_id,
            "total_records": len(records),
            "total_points": total_points,
            "by_category": category_summary,
            "start_date": start_date.isoformat() if isinstance(start_date, datetime.datetime) else start_date,
            "end_date": end_date.isoformat() if isinstance(end_date, datetime.datetime) else end_date
        }
    
    @classmethod
    def get_summary_by_period(cls, period_type: str = "month",
                            start_date: Optional[datetime.datetime] = None,
                            end_date: Optional[datetime.datetime] = None) -> Dict[str, Any]:
        """
        获取指定时间段的工作量汇总
        
        参数:
            period_type: 时间段类型 (day, week, month, year)
            start_date: 开始日期
            end_date: 结束日期
            
        返回:
            工作量汇总数据
        """
        conditions = ["status = '已审核'"]
        params = []
        
        if start_date:
            conditions.append("record_date >= ?")
            params.append(start_date.isoformat() if isinstance(start_date, datetime.datetime) else start_date)
            
        if end_date:
            conditions.append("record_date <= ?")
            params.append(end_date.isoformat() if isinstance(end_date, datetime.datetime) else end_date)
            
        condition = " AND ".join(conditions)
        
        # 获取记录
        records = cls.get_all(condition, tuple(params))
        
        # 按时间段和医生ID分组
        period_summary = {}
        doctor_summary = {}
        
        for record in records:
            if not hasattr(record, "record_date") or not record.record_date:
                continue
                
            # 处理日期
            if isinstance(record.record_date, str):
                try:
                    record_date = datetime.datetime.fromisoformat(record.record_date.replace('Z', '+00:00'))
                except ValueError:
                    continue
            else:
                record_date = record.record_date
                
            # 获取时间段键
            if period_type == "day":
                period_key = record_date.strftime("%Y-%m-%d")
            elif period_type == "week":
                # 使用ISO周数
                period_key = f"{record_date.year}-W{record_date.isocalendar()[1]:02d}"
            elif period_type == "month":
                period_key = record_date.strftime("%Y-%m")
            elif period_type == "year":
                period_key = str(record_date.year)
            else:
                period_key = record_date.strftime("%Y-%m")  # 默认按月
                
            # 按时间段汇总
            if period_key not in period_summary:
                period_summary[period_key] = {
                    "count": 0,
                    "points": 0
                }
                
            period_summary[period_key]["count"] += 1
            period_summary[period_key]["points"] += record.points if hasattr(record, "points") and record.points else 0
            
            # 按医生汇总
            if not hasattr(record, "doctor_id") or not record.doctor_id:
                continue
                
            if record.doctor_id not in doctor_summary:
                doctor_summary[record.doctor_id] = {
                    "count": 0,
                    "points": 0
                }
                
            doctor_summary[record.doctor_id]["count"] += 1
            doctor_summary[record.doctor_id]["points"] += record.points if hasattr(record, "points") and record.points else 0
            
        return {
            "total_records": len(records),
            "total_points": sum(record.points for record in records if hasattr(record, "points") and record.points),
            "by_period": period_summary,
            "by_doctor": doctor_summary,
            "period_type": period_type,
            "start_date": start_date.isoformat() if isinstance(start_date, datetime.datetime) else start_date,
            "end_date": end_date.isoformat() if isinstance(end_date, datetime.datetime) else end_date
        } 