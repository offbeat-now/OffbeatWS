from sqlalchemy import Column, String, Integer
from app.models.base import BaseModel

class JobTitleEnum(BaseModel):
    __tablename__ = "job_title_enum"

    id = Column(Integer, primary_key=True, autoincrement=True)
    values = Column(String, unique=True, nullable=False)

    def __repr__(self):
        return f"<JobTitleEnum {self.values}>"