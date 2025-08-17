from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_mixin
from app.models.base import BaseModel

@declarative_mixin
class BaseEnum(BaseModel):
    __abstract__ = True  # SQLAlchemy will not create a table for this

    id = Column(Integer, primary_key=True, autoincrement=True)
    values = Column(String, unique=True, nullable=False)

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.values}>"
