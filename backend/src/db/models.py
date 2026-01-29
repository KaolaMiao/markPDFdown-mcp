from datetime import datetime
from enum import Enum
from typing import Optional
import uuid

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Enum as SAEnum, BigInteger
from sqlalchemy.orm import declarative_base, relationship
from pydantic import BaseModel, ConfigDict

Base = declarative_base()

class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    file_name = Column(String, nullable=True)  # 原始文件名
    status = Column(SAEnum(TaskStatus), default=TaskStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 时间追踪
    started_at = Column(DateTime, nullable=True)  # 任务开始时间
    completed_at = Column(DateTime, nullable=True)  # 任务完成时间

    # 结果信息
    result_path = Column(String, nullable=True)
    total_pages = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    # Token 统计
    input_tokens = Column(BigInteger, default=0)  # 输入 token 总数
    output_tokens = Column(BigInteger, default=0)  # 输出 token 总数
    total_tokens = Column(BigInteger, default=0)  # 总 token 数 (计算字段)

    details = relationship("TaskDetail", back_populates="task", cascade="all, delete-orphan")

class TaskDetail(Base):
    __tablename__ = "task_details"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    page_num = Column(Integer, nullable=False)
    status = Column(SAEnum(TaskStatus), default=TaskStatus.PENDING)
    content = Column(Text, nullable=True)
    image_path = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)

    task = relationship("Task", back_populates="details")

# Pydantic Schemas
class TaskBase(BaseModel):
    pass

class TaskCreate(TaskBase):
    pass

class TaskResponse(TaskBase):
    id: str
    file_name: Optional[str] = None  # 原始文件名
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_pages: int
    result_path: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    model_config = ConfigDict(from_attributes=True)

class TaskDetailResponse(BaseModel):
    page_num: int
    status: TaskStatus
    content: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
