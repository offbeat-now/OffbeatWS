from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, DateTime, func

Base = declarative_base()

class BaseModel(Base):
    """Base model class that includes common columns for all models"""
    __abstract__ = True
    
    id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())