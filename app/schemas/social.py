# app/schemas/social.py
from datetime import datetime
from enum import Enum
from typing import Optional, List, TypeVar, Generic
from uuid import UUID
from pydantic import BaseModel, Field, validator

T = TypeVar("T")

# Enums
class CreatorType(str, Enum):
    USER = "user"
    ORGANIZATION = "organization"

class ForumVisibility(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"

class TargetType(str, Enum):
    POST = "post"
    COMMENT = "comment"
    BLOG = "blog"
    JOB = "job"
    ACCOMMODATION = "accommodation"

# Forum Schemas
class ForumBase(BaseModel):
    id: UUID
    creator_type: CreatorType
    creator_id: UUID
    name: str
    title: str
    description: Optional[str] = None
    tags: Optional[List[str]] = []
    visibility: ForumVisibility
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ForumCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = Field(default_factory=list)
    visibility: ForumVisibility = ForumVisibility.PUBLIC

    @validator('name')
    def validate_name(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Name can only contain letters, numbers, hyphens, and underscores')
        return v.lower()

class ForumUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = None
    visibility: Optional[ForumVisibility] = None

# Post Schemas
class PostBase(BaseModel):
    id: UUID
    forum_id: UUID
    author_type: CreatorType
    author_id: UUID
    title: str
    body: Optional[str] = None
    media_urls: Optional[List[str]] = []
    tags: Optional[List[str]] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PostCreate(BaseModel):
    forum_id: UUID
    title: str = Field(..., min_length=3, max_length=300)
    body: Optional[str] = Field(None, max_length=10000)
    tags: Optional[List[str]] = Field(default_factory=list)

class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=300)
    body: Optional[str] = Field(None, max_length=10000)
    tags: Optional[List[str]] = None

# Comment Schemas
class CommentBase(BaseModel):
    id: UUID
    target_type: TargetType
    target_id: UUID
    parent_comment_id: Optional[UUID] = None
    author_type: CreatorType
    author_id: UUID
    body: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CommentCreate(BaseModel):
    target_type: TargetType
    target_id: UUID
    parent_comment_id: Optional[UUID] = None
    body: str = Field(..., min_length=1, max_length=2000)

class CommentUpdate(BaseModel):
    body: str = Field(..., min_length=1, max_length=2000)

# Response Schemas
class BaseResponse(BaseModel, Generic[T]):
    error: bool = False
    message: str = "Success"
    data: Optional[T] = None

class ForumResponse(BaseResponse):
    data: Optional[ForumBase] = None

    @classmethod
    def from_orm_model(cls, orm_model):
        if orm_model is None:
            return cls(error=True, message="Forum not found", data=None)
        
        if isinstance(orm_model, dict):
            base_data = ForumBase(**orm_model)
        else:
            base_data = ForumBase.model_validate(orm_model.__dict__)
        
        return cls(error=False, message="Success", data=base_data)

class ForumListResponse(BaseResponse):
    data: List[ForumBase] = []

    @classmethod
    def from_orm_models(cls, orm_models):
        forums = []
        for model in orm_models:
            if isinstance(model, dict):
                forums.append(ForumBase(**model))
            else:
                forums.append(ForumBase.model_validate(model.__dict__))
        
        return cls(error=False, message="Success", data=forums)

class PostResponse(BaseResponse):
    data: Optional[PostBase] = None

    @classmethod
    def from_orm_model(cls, orm_model):
        if orm_model is None:
            return cls(error=True, message="Post not found", data=None)
        
        if isinstance(orm_model, dict):
            base_data = PostBase(**orm_model)
        else:
            base_data = PostBase.model_validate(orm_model.__dict__)
        
        return cls(error=False, message="Success", data=base_data)

class PostListResponse(BaseResponse):
    data: List[PostBase] = []

    @classmethod
    def from_orm_models(cls, orm_models):
        posts = []
        for model in orm_models:
            if isinstance(model, dict):
                posts.append(PostBase(**model))
            else:
                posts.append(PostBase.model_validate(model.__dict__))
        
        return cls(error=False, message="Success", data=posts)

class CommentResponse(BaseResponse):
    data: Optional[CommentBase] = None

    @classmethod
    def from_orm_model(cls, orm_model):
        if orm_model is None:
            return cls(error=True, message="Comment not found", data=None)
        
        if isinstance(orm_model, dict):
            base_data = CommentBase(**orm_model)
        else:
            base_data = CommentBase.model_validate(orm_model.__dict__)
        
        return cls(error=False, message="Success", data=base_data)

class CommentListResponse(BaseResponse):
    data: List[CommentBase] = []

    @classmethod
    def from_orm_models(cls, orm_models):
        comments = []
        for model in orm_models:
            if isinstance(model, dict):
                comments.append(CommentBase(**model))
            else:
                comments.append(CommentBase.model_validate(model.__dict__))
        
        return cls(error=False, message="Success", data=comments)

# Feed Response (for combined social feed)
class FeedItemBase(BaseModel):
    item_type: str  # "forum", "post", "comment"
    item_id: UUID
    title: Optional[str] = None
    body: Optional[str] = None
    author_type: CreatorType
    author_id: UUID
    created_at: datetime
    forum_id: Optional[UUID] = None  # For posts
    post_id: Optional[UUID] = None  # For comments

class FeedResponse(BaseResponse):
    data: List[FeedItemBase] = []