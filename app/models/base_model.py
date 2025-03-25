"""
模型基类模块 - 提供所有模型的基础功能
"""
import json
from typing import Dict, List, Any, Optional, Type, ClassVar, TypeVar, Generic, Tuple
import time
import datetime
from dataclasses import dataclass, field, asdict, is_dataclass

from app.utils.database import (
    insert_record, update_record, delete_record,
    get_record, get_records, count_records,
    QueryBuilder
)
from app.utils.utils import to_json, generate_uuid

T = TypeVar('T', bound='BaseModel')

class ModelMeta(type):
    """模型元类，用于注册模型类"""
    
    _models: Dict[str, Type] = {}
    
    def __new__(mcs, name, bases, attrs):
        cls = super().__new__(mcs, name, bases, attrs)
        
        # 注册非BaseModel的子类
        if name != 'BaseModel' and not name.startswith('_'):
            mcs._models[name] = cls
            
        return cls
    
    @classmethod
    def get_model(mcs, name: str) -> Optional[Type]:
        """获取模型类"""
        return mcs._models.get(name)
    
    @classmethod
    def get_models(mcs) -> Dict[str, Type]:
        """获取所有模型类"""
        return mcs._models.copy()

class BaseModel(metaclass=ModelMeta):
    """模型基类"""
    
    # 表名与主键
    __tablename__: ClassVar[str] = ""
    __primary_key__: ClassVar[str] = "id"
    
    # 默认排序
    __order_by__: ClassVar[str] = ""
    
    # 字段定义
    __fields__: ClassVar[Dict[str, str]] = {}
    
    # JSON字段
    __json_fields__: ClassVar[List[str]] = []
    
    # 日期时间字段
    __datetime_fields__: ClassVar[List[str]] = []
    
    # 关联字段
    __relations__: ClassVar[Dict[str, Dict[str, Any]]] = {}
    
    def __init__(self, **kwargs):
        """
        初始化模型实例
        
        参数:
            **kwargs: 属性值
        """
        # 设置属性
        for key, value in kwargs.items():
            if key in self.__fields__ or key == self.__primary_key__:
                setattr(self, key, value)
                
        # 为未设置的字段设置默认值
        for field_name in self.__fields__:
            if not hasattr(self, field_name):
                setattr(self, field_name, None)
                
        # 如果主键未设置，则生成一个
        if not hasattr(self, self.__primary_key__) or getattr(self, self.__primary_key__) is None:
            setattr(self, self.__primary_key__, generate_uuid())
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        从字典创建模型实例
        
        参数:
            data: 数据字典
            
        返回:
            模型实例
        """
        # 解析JSON字段
        for field in cls.__json_fields__:
            if field in data and isinstance(data[field], str):
                try:
                    data[field] = json.loads(data[field])
                except (json.JSONDecodeError, TypeError):
                    pass
                    
        # 解析日期时间字段
        for field in cls.__datetime_fields__:
            if field in data and isinstance(data[field], str):
                try:
                    data[field] = datetime.datetime.fromisoformat(data[field].replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    pass
                    
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将模型转换为字典
        
        返回:
            数据字典
        """
        data = {}
        
        # 添加所有字段
        for field_name in [self.__primary_key__] + list(self.__fields__.keys()):
            if hasattr(self, field_name):
                value = getattr(self, field_name)
                
                # 处理日期时间字段
                if field_name in self.__datetime_fields__ and isinstance(value, datetime.datetime):
                    value = value.isoformat()
                
                data[field_name] = value
                
        return data
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.__class__.__name__}({self.to_dict()})"
    
    def __repr__(self) -> str:
        """表示形式"""
        return self.__str__()
    
    # 保存方法
    def save(self) -> bool:
        """
        保存模型，如果主键存在则更新，否则插入
        
        返回:
            是否成功
        """
        data = self.to_dict()
        pk_value = data.pop(self.__primary_key__, None)
        
        # 处理JSON字段
        for field in self.__json_fields__:
            if field in data and (isinstance(data[field], dict) or isinstance(data[field], list)):
                data[field] = json.dumps(data[field], ensure_ascii=False)
        
        # 如果主键存在且不为None，则更新
        if pk_value is not None:
            # 获取现有记录
            existing = self.get_by_id(pk_value)
            
            if existing:
                success = update_record(
                    self.__tablename__,
                    data,
                    f"{self.__primary_key__} = ?",
                    (pk_value,)
                )
                return success
        
        # 插入记录
        if pk_value:
            data[self.__primary_key__] = pk_value
            
        record_id = insert_record(self.__tablename__, data)
        
        # 更新主键
        if record_id and not pk_value:
            setattr(self, self.__primary_key__, record_id)
            
        return record_id is not None
    
    def delete(self) -> bool:
        """
        删除模型
        
        返回:
            是否成功
        """
        pk_value = getattr(self, self.__primary_key__, None)
        
        if pk_value is None:
            return False
            
        return delete_record(
            self.__tablename__,
            f"{self.__primary_key__} = ?",
            (pk_value,)
        )
    
    @classmethod
    def create(cls: Type[T], **kwargs) -> Optional[T]:
        """
        创建并保存一个新模型
        
        参数:
            **kwargs: 属性值
            
        返回:
            模型实例或None
        """
        instance = cls(**kwargs)
        success = instance.save()
        
        return instance if success else None
    
    @classmethod
    def get_by_id(cls: Type[T], id_value: Any) -> Optional[T]:
        """
        通过ID获取模型
        
        参数:
            id_value: ID值
            
        返回:
            模型实例或None
        """
        record = get_record(
            cls.__tablename__,
            '*',
            f"{cls.__primary_key__} = ?",
            (id_value,)
        )
        
        return cls.from_dict(record) if record else None
    
    @classmethod
    def get_all(cls: Type[T], condition: str = '', params: Tuple = (), 
               order_by: str = '', limit: int = 0, offset: int = 0) -> List[T]:
        """
        获取多个模型
        
        参数:
            condition: 条件
            params: 条件参数
            order_by: 排序
            limit: 限制
            offset: 偏移
            
        返回:
            模型实例列表
        """
        if not order_by and cls.__order_by__:
            order_by = cls.__order_by__
            
        records = get_records(
            cls.__tablename__,
            '*',
            condition,
            params,
            order_by,
            limit,
            offset
        )
        
        return [cls.from_dict(record) for record in records]
    
    @classmethod
    def count(cls, condition: str = '', params: Tuple = ()) -> int:
        """
        统计记录数
        
        参数:
            condition: 条件
            params: 条件参数
            
        返回:
            记录数
        """
        return count_records(cls.__tablename__, condition, params)
    
    @classmethod
    def exists(cls, condition: str, params: Tuple) -> bool:
        """
        检查记录是否存在
        
        参数:
            condition: 条件
            params: 条件参数
            
        返回:
            是否存在
        """
        return cls.count(condition, params) > 0
    
    @classmethod
    def query(cls) -> QueryBuilder:
        """
        创建查询构建器
        
        返回:
            查询构建器
        """
        return QueryBuilder(cls.__tablename__)
    
    @classmethod
    def find(cls: Type[T], **kwargs) -> List[T]:
        """
        通过属性查找模型
        
        参数:
            **kwargs: 属性条件
            
        返回:
            模型实例列表
        """
        conditions = []
        params = []
        
        for key, value in kwargs.items():
            conditions.append(f"{key} = ?")
            params.append(value)
            
        condition = " AND ".join(conditions) if conditions else ""
        
        return cls.get_all(condition, tuple(params))
    
    @classmethod
    def find_one(cls: Type[T], **kwargs) -> Optional[T]:
        """
        通过属性查找单个模型
        
        参数:
            **kwargs: 属性条件
            
        返回:
            模型实例或None
        """
        results = cls.find(**kwargs)
        return results[0] if results else None

# 数据类模型基类
@dataclass
class DataModel:
    """数据类模型基类"""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """从字典创建数据类实例"""
        if not is_dataclass(cls):
            raise TypeError(f"{cls.__name__} is not a dataclass")
            
        # 过滤掉不在字段中的键
        field_names = {f.name for f in field(cls)}
        filtered_data = {k: v for k, v in data.items() if k in field_names}
        
        return cls(**filtered_data)
    
    def to_dict(self) -> Dict[str, Any]:
        """将数据类转换为字典"""
        if not is_dataclass(self.__class__):
            raise TypeError(f"{self.__class__.__name__} is not a dataclass")
            
        return asdict(self)
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.__class__.__name__}({self.to_dict()})" 