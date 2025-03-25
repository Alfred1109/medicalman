"""
医生模型模块 - 定义医生相关数据模型
"""
from typing import Dict, List, Any, Optional, ClassVar
import datetime

from app.models.base_model import BaseModel
from app.utils.utils import format_datetime, md5_hash

class Doctor(BaseModel):
    """医生模型类"""
    
    # 表名与主键
    __tablename__: ClassVar[str] = "doctors"
    __primary_key__: ClassVar[str] = "id"
    
    # 默认排序
    __order_by__: ClassVar[str] = "name ASC"
    
    # 字段定义
    __fields__: ClassVar[Dict[str, str]] = {
        "name": "姓名",
        "gender": "性别",
        "birth_date": "出生日期",
        "phone": "电话",
        "email": "邮箱",
        "id_card": "身份证号",
        "license_number": "执业证号",
        "speciality": "专业",
        "department": "科室",
        "position": "职位",
        "title": "职称",
        "hire_date": "入职日期",
        "status": "状态",
        "workload_target": "工作量目标",
        "workload_points": "工作量分值",
        "specializations": "专长",
        "education": "教育背景",
        "certifications": "认证",
        "schedule": "排班",
        "created_at": "创建时间",
        "updated_at": "更新时间",
        "is_active": "是否在职",
        "notes": "备注",
        "password_hash": "密码哈希"
    }
    
    # 日期时间字段
    __datetime_fields__: ClassVar[List[str]] = ["birth_date", "hire_date", "created_at", "updated_at"]
    
    # JSON字段
    __json_fields__: ClassVar[List[str]] = [
        "specializations", "education", "certifications", "schedule"
    ]
    
    def __init__(self, **kwargs):
        """
        初始化医生实例
        
        参数:
            **kwargs: 医生属性
        """
        # 设置默认值
        now = datetime.datetime.now()
        defaults = {
            "created_at": now,
            "updated_at": now,
            "is_active": True,
            "gender": "未知",
            "status": "正常",
            "workload_points": 0,
            "specializations": [],
            "education": [],
            "certifications": [],
            "schedule": {}
        }
        
        # 合并默认值和传入的值
        data = {**defaults, **kwargs}
        
        # 处理密码
        if "password" in data:
            password = data.pop("password")
            data["password_hash"] = self.hash_password(password)
        
        # 调用父类初始化方法
        super().__init__(**data)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        哈希密码
        
        参数:
            password: 明文密码
            
        返回:
            密码哈希
        """
        return md5_hash(password)
    
    def verify_password(self, password: str) -> bool:
        """
        验证密码
        
        参数:
            password: 明文密码
            
        返回:
            密码是否正确
        """
        if not hasattr(self, "password_hash") or not self.password_hash:
            return False
            
        return self.password_hash == self.hash_password(password)
    
    def change_password(self, new_password: str) -> None:
        """
        修改密码
        
        参数:
            new_password: 新密码
        """
        self.password_hash = self.hash_password(new_password)
        self.updated_at = datetime.datetime.now()
    
    @property
    def age(self) -> Optional[int]:
        """
        计算年龄
        
        返回:
            计算出的年龄或None
        """
        if not hasattr(self, "birth_date") or not self.birth_date:
            return None
            
        if isinstance(self.birth_date, str):
            try:
                self.birth_date = datetime.datetime.fromisoformat(self.birth_date.replace('Z', '+00:00'))
            except ValueError:
                return None
                
        today = datetime.date.today()
        birth_date = self.birth_date.date() if isinstance(self.birth_date, datetime.datetime) else self.birth_date
        
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age
    
    def add_specialization(self, specialization: str) -> None:
        """
        添加专长
        
        参数:
            specialization: 专长描述
        """
        if not hasattr(self, "specializations") or self.specializations is None:
            self.specializations = []
            
        if specialization not in self.specializations:
            self.specializations.append(specialization)
            self.updated_at = datetime.datetime.now()
    
    def add_education(self, education_data: Dict[str, Any]) -> None:
        """
        添加教育背景
        
        参数:
            education_data: 教育背景数据
        """
        if not hasattr(self, "education") or self.education is None:
            self.education = []
            
        if not isinstance(education_data, dict):
            raise ValueError("教育背景必须是字典格式")
            
        required_fields = ["institution", "degree", "field"]
        for field in required_fields:
            if field not in education_data:
                raise ValueError(f"教育背景数据缺少必要字段: {field}")
                
        self.education.append(education_data)
        self.updated_at = datetime.datetime.now()
    
    def add_certification(self, certification_data: Dict[str, Any]) -> None:
        """
        添加认证
        
        参数:
            certification_data: 认证数据
        """
        if not hasattr(self, "certifications") or self.certifications is None:
            self.certifications = []
            
        if not isinstance(certification_data, dict):
            raise ValueError("认证必须是字典格式")
            
        required_fields = ["name", "issuer", "date"]
        for field in required_fields:
            if field not in certification_data:
                raise ValueError(f"认证数据缺少必要字段: {field}")
                
        self.certifications.append(certification_data)
        self.updated_at = datetime.datetime.now()
    
    def update_workload(self, points: float) -> None:
        """
        更新工作量
        
        参数:
            points: 工作量分值
        """
        if not hasattr(self, "workload_points") or self.workload_points is None:
            self.workload_points = 0
            
        self.workload_points += points
        self.updated_at = datetime.datetime.now()
    
    def set_schedule(self, schedule_data: Dict[str, Any]) -> None:
        """
        设置排班
        
        参数:
            schedule_data: 排班数据
        """
        if not isinstance(schedule_data, dict):
            raise ValueError("排班数据必须是字典格式")
            
        self.schedule = schedule_data
        self.updated_at = datetime.datetime.now()
    
    @classmethod
    def find_by_department(cls, department: str) -> List['Doctor']:
        """
        查找科室中的医生
        
        参数:
            department: 科室名称
            
        返回:
            医生列表
        """
        return cls.find(department=department, is_active=True)
    
    @classmethod
    def find_by_speciality(cls, speciality: str) -> List['Doctor']:
        """
        查找专业的医生
        
        参数:
            speciality: 专业名称
            
        返回:
            医生列表
        """
        return cls.find(speciality=speciality, is_active=True)
    
    @classmethod
    def find_by_title(cls, title: str) -> List['Doctor']:
        """
        查找指定职称的医生
        
        参数:
            title: 职称
            
        返回:
            医生列表
        """
        return cls.find(title=title, is_active=True)
    
    @classmethod
    def find_by_license(cls, license_number: str) -> Optional['Doctor']:
        """
        通过执业证号查找医生
        
        参数:
            license_number: 执业证号
            
        返回:
            医生实例或None
        """
        return cls.find_one(license_number=license_number)
    
    @classmethod
    def authenticate(cls, email: str, password: str) -> Optional['Doctor']:
        """
        验证医生凭据
        
        参数:
            email: 电子邮件
            password: 密码
            
        返回:
            验证成功的医生实例或None
        """
        doctor = cls.find_one(email=email)
        
        if doctor and doctor.verify_password(password):
            return doctor
            
        return None
    
    @classmethod
    def search(cls, keyword: str) -> List['Doctor']:
        """
        搜索医生
        
        参数:
            keyword: 搜索关键词
            
        返回:
            匹配的医生列表
        """
        condition = """
            name LIKE ? OR 
            phone LIKE ? OR 
            email LIKE ? OR 
            department LIKE ? OR
            speciality LIKE ? OR
            title LIKE ?
        """
        params = tuple([f"%{keyword}%"] * 6)
        
        return cls.get_all(condition, params)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将医生转换为字典
        
        返回:
            医生数据字典
        """
        data = super().to_dict()
        
        # 移除敏感字段
        if "password_hash" in data:
            del data["password_hash"]
            
        # 添加计算出的年龄
        data["age"] = self.age
            
        return data 