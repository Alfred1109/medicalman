"""
医疗记录模型模块 - 定义医疗记录相关数据模型
"""
from typing import Dict, List, Any, Optional, ClassVar
import datetime

from app.models.base_model import BaseModel
from app.utils.utils import format_datetime

class MedicalRecord(BaseModel):
    """医疗记录模型类"""
    
    # 表名与主键
    __tablename__: ClassVar[str] = "medical_records"
    __primary_key__: ClassVar[str] = "id"
    
    # 默认排序
    __order_by__: ClassVar[str] = "record_date DESC"
    
    # 字段定义
    __fields__: ClassVar[Dict[str, str]] = {
        "patient_id": "患者ID",
        "doctor_id": "医生ID",
        "record_date": "记录日期",
        "visit_type": "就诊类型",
        "chief_complaint": "主诉",
        "present_illness": "现病史",
        "past_history": "既往史",
        "physical_examination": "体格检查",
        "diagnosis": "诊断",
        "treatment_plan": "治疗方案",
        "prescriptions": "处方",
        "lab_results": "检验结果",
        "imaging_results": "影像结果",
        "notes": "备注",
        "follow_up": "随访计划",
        "department": "科室",
        "is_completed": "是否完成",
        "created_at": "创建时间",
        "updated_at": "更新时间",
        "workload_points": "工作量分值"
    }
    
    # 日期时间字段
    __datetime_fields__: ClassVar[List[str]] = ["record_date", "created_at", "updated_at"]
    
    # JSON字段
    __json_fields__: ClassVar[List[str]] = [
        "diagnosis", "treatment_plan", "prescriptions", 
        "lab_results", "imaging_results", "follow_up"
    ]
    
    def __init__(self, **kwargs):
        """
        初始化医疗记录实例
        
        参数:
            **kwargs: 医疗记录属性
        """
        # 设置默认值
        now = datetime.datetime.now()
        defaults = {
            "created_at": now,
            "updated_at": now,
            "record_date": now,
            "is_completed": False,
            "workload_points": 0,
            "diagnosis": [],
            "treatment_plan": {},
            "prescriptions": [],
            "lab_results": [],
            "imaging_results": []
        }
        
        # 合并默认值和传入的值
        data = {**defaults, **kwargs}
        
        # 调用父类初始化方法
        super().__init__(**data)
    
    def format_record_date(self, format_str: str = '%Y-%m-%d %H:%M') -> str:
        """
        格式化记录日期
        
        参数:
            format_str: 日期格式字符串
            
        返回:
            格式化后的日期
        """
        if not hasattr(self, "record_date") or not self.record_date:
            return ""
            
        if isinstance(self.record_date, str):
            try:
                self.record_date = datetime.datetime.fromisoformat(self.record_date.replace('Z', '+00:00'))
            except ValueError:
                return self.record_date
                
        return format_datetime(self.record_date, format_str)
    
    def add_diagnosis(self, diagnosis: str, diagnosis_type: str = "初步诊断", icd_code: str = "") -> None:
        """
        添加诊断
        
        参数:
            diagnosis: 诊断名称
            diagnosis_type: 诊断类型
            icd_code: ICD编码
        """
        if not hasattr(self, "diagnosis") or self.diagnosis is None:
            self.diagnosis = []
            
        diagnosis_item = {
            "diagnosis": diagnosis,
            "type": diagnosis_type,
            "icd_code": icd_code,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        self.diagnosis.append(diagnosis_item)
        self.updated_at = datetime.datetime.now()
    
    def add_prescription(self, prescription: Dict[str, Any]) -> None:
        """
        添加处方
        
        参数:
            prescription: 处方数据
        """
        if not hasattr(self, "prescriptions") or self.prescriptions is None:
            self.prescriptions = []
            
        if not isinstance(prescription, dict):
            raise ValueError("处方必须是字典格式")
            
        # 确保处方有时间戳
        if "timestamp" not in prescription:
            prescription["timestamp"] = datetime.datetime.now().isoformat()
            
        self.prescriptions.append(prescription)
        self.updated_at = datetime.datetime.now()
    
    def add_lab_result(self, lab_result: Dict[str, Any]) -> None:
        """
        添加检验结果
        
        参数:
            lab_result: 检验结果数据
        """
        if not hasattr(self, "lab_results") or self.lab_results is None:
            self.lab_results = []
            
        if not isinstance(lab_result, dict):
            raise ValueError("检验结果必须是字典格式")
            
        # 确保结果有时间戳
        if "timestamp" not in lab_result:
            lab_result["timestamp"] = datetime.datetime.now().isoformat()
            
        self.lab_results.append(lab_result)
        self.updated_at = datetime.datetime.now()
    
    def add_imaging_result(self, imaging_result: Dict[str, Any]) -> None:
        """
        添加影像结果
        
        参数:
            imaging_result: 影像结果数据
        """
        if not hasattr(self, "imaging_results") or self.imaging_results is None:
            self.imaging_results = []
            
        if not isinstance(imaging_result, dict):
            raise ValueError("影像结果必须是字典格式")
            
        # 确保结果有时间戳
        if "timestamp" not in imaging_result:
            imaging_result["timestamp"] = datetime.datetime.now().isoformat()
            
        self.imaging_results.append(imaging_result)
        self.updated_at = datetime.datetime.now()
    
    def complete_record(self, workload_points: float = None) -> None:
        """
        完成医疗记录
        
        参数:
            workload_points: 工作量分值
        """
        self.is_completed = True
        if workload_points is not None:
            self.workload_points = workload_points
        self.updated_at = datetime.datetime.now()
    
    @classmethod
    def find_by_patient(cls, patient_id: str) -> List['MedicalRecord']:
        """
        查找患者的所有医疗记录
        
        参数:
            patient_id: 患者ID
            
        返回:
            医疗记录列表
        """
        return cls.find(patient_id=patient_id)
    
    @classmethod
    def find_by_doctor(cls, doctor_id: str) -> List['MedicalRecord']:
        """
        查找医生的所有医疗记录
        
        参数:
            doctor_id: 医生ID
            
        返回:
            医疗记录列表
        """
        return cls.find(doctor_id=doctor_id)
    
    @classmethod
    def find_by_department(cls, department: str) -> List['MedicalRecord']:
        """
        查找科室的所有医疗记录
        
        参数:
            department: 科室
            
        返回:
            医疗记录列表
        """
        return cls.find(department=department)
    
    @classmethod
    def find_recent(cls, days: int = 7) -> List['MedicalRecord']:
        """
        查找最近的医疗记录
        
        参数:
            days: 天数
            
        返回:
            医疗记录列表
        """
        date_threshold = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
        
        condition = "record_date >= ?"
        params = (date_threshold,)
        
        return cls.get_all(condition, params)
    
    @classmethod
    def search(cls, keyword: str) -> List['MedicalRecord']:
        """
        搜索医疗记录
        
        参数:
            keyword: 搜索关键词
            
        返回:
            匹配的医疗记录列表
        """
        condition = """
            chief_complaint LIKE ? OR 
            present_illness LIKE ? OR 
            diagnosis LIKE ? OR 
            treatment_plan LIKE ? OR
            notes LIKE ?
        """
        params = tuple([f"%{keyword}%"] * 5)
        
        return cls.get_all(condition, params) 