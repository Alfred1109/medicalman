"""
患者模型模块 - 定义患者相关数据模型
"""
from typing import Dict, List, Any, Optional, ClassVar
import datetime

from app.models.base_model import BaseModel
from app.utils.utils import format_datetime, md5_hash

class Patient(BaseModel):
    """患者模型类"""
    
    # 表名与主键
    __tablename__: ClassVar[str] = "patients"
    __primary_key__: ClassVar[str] = "id"
    
    # 默认排序
    __order_by__: ClassVar[str] = "name ASC"
    
    # 字段定义
    __fields__: ClassVar[Dict[str, str]] = {
        "name": "姓名",
        "gender": "性别",
        "age": "年龄",
        "birth_date": "出生日期",
        "phone": "电话",
        "id_card": "身份证号",
        "address": "地址",
        "medical_insurance": "医保卡号",
        "blood_type": "血型",
        "allergies": "过敏史",
        "created_at": "创建时间",
        "updated_at": "更新时间",
        "is_active": "是否活跃",
        "medical_history": "病史",
        "notes": "备注"
    }
    
    # 日期时间字段
    __datetime_fields__: ClassVar[List[str]] = ["birth_date", "created_at", "updated_at"]
    
    # JSON字段
    __json_fields__: ClassVar[List[str]] = ["medical_history", "allergies"]
    
    def __init__(self, **kwargs):
        """
        初始化患者实例
        
        参数:
            **kwargs: 患者属性
        """
        # 设置默认值
        now = datetime.datetime.now()
        defaults = {
            "created_at": now,
            "updated_at": now,
            "is_active": True,
            "gender": "未知",
            "medical_history": [],
            "allergies": []
        }
        
        # 合并默认值和传入的值
        data = {**defaults, **kwargs}
        
        # 调用父类初始化方法
        super().__init__(**data)
    
    @property
    def age_calculated(self) -> Optional[int]:
        """
        根据出生日期计算年龄
        
        返回:
            计算出的年龄或None
        """
        if not hasattr(self, "birth_date") or not self.birth_date:
            return self.age if hasattr(self, "age") else None
            
        if isinstance(self.birth_date, str):
            try:
                self.birth_date = datetime.datetime.fromisoformat(self.birth_date.replace('Z', '+00:00'))
            except ValueError:
                return self.age if hasattr(self, "age") else None
                
        today = datetime.date.today()
        birth_date = self.birth_date.date() if isinstance(self.birth_date, datetime.datetime) else self.birth_date
        
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age
    
    def format_birth_date(self, format_str: str = '%Y-%m-%d') -> Optional[str]:
        """
        格式化出生日期
        
        参数:
            format_str: 日期格式字符串
            
        返回:
            格式化后的日期或None
        """
        if not hasattr(self, "birth_date") or not self.birth_date:
            return None
            
        if isinstance(self.birth_date, str):
            try:
                self.birth_date = datetime.datetime.fromisoformat(self.birth_date.replace('Z', '+00:00'))
            except ValueError:
                return self.birth_date
                
        return format_datetime(self.birth_date, format_str)
    
    def add_medical_history(self, record: Dict[str, Any]) -> None:
        """
        添加病史记录
        
        参数:
            record: 病史记录
        """
        if not hasattr(self, "medical_history") or self.medical_history is None:
            self.medical_history = []
            
        if not isinstance(record, dict):
            raise ValueError("病史记录必须是字典格式")
            
        # 确保记录有时间戳
        if "timestamp" not in record:
            record["timestamp"] = datetime.datetime.now().isoformat()
            
        self.medical_history.append(record)
        self.updated_at = datetime.datetime.now()
    
    def add_allergy(self, allergy: str) -> None:
        """
        添加过敏记录
        
        参数:
            allergy: 过敏物质
        """
        if not hasattr(self, "allergies") or self.allergies is None:
            self.allergies = []
            
        if allergy not in self.allergies:
            self.allergies.append(allergy)
            self.updated_at = datetime.datetime.now()
    
    @classmethod
    def find_by_id_card(cls, id_card: str) -> Optional['Patient']:
        """
        通过身份证号查找患者
        
        参数:
            id_card: 身份证号
            
        返回:
            患者实例或None
        """
        return cls.find_one(id_card=id_card)
    
    @classmethod
    def find_by_phone(cls, phone: str) -> Optional['Patient']:
        """
        通过电话号码查找患者
        
        参数:
            phone: 电话号码
            
        返回:
            患者实例或None
        """
        return cls.find_one(phone=phone)
    
    @classmethod
    def search(cls, keyword: str) -> List['Patient']:
        """
        搜索患者
        
        参数:
            keyword: 搜索关键词
            
        返回:
            匹配的患者列表
        """
        condition = """
            name LIKE ? OR 
            phone LIKE ? OR 
            id_card LIKE ? OR 
            address LIKE ? OR
            medical_insurance LIKE ?
        """
        params = tuple([f"%{keyword}%"] * 5)
        
        return cls.get_all(condition, params)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将患者转换为字典
        
        返回:
            患者数据字典
        """
        data = super().to_dict()
        
        # 添加计算出的年龄
        if not data.get("age") and self.birth_date:
            data["age"] = self.age_calculated
            
        return data 