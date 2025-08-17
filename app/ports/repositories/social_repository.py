# app/ports/repositories/social_repository.py
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from app.models.social import Forum, Post, Comment
from app.schemas.social import (
    ForumCreate, 
    ForumUpdate, 
    PostCreate, 
    PostUpdate, 
    CommentCreate, 
    CommentUpdate
)

from .base_repository import BaseRepository

class ForumRepository(BaseRepository[Forum, ForumCreate, ForumUpdate], ABC):
    """Abstract forum repository interface"""
    
    @abstractmethod
    async def create(self, forum_data: ForumCreate, creator_type: str, creator_id: UUID) -> Optional[Forum]:
        """Create a new forum"""
        pass
    
    @abstractmethod
    async def get_by_id(self, forum_id: UUID) -> Optional[Forum]:
        """Get forum by ID"""
        pass
    
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Forum]:
        """Get forum by unique name"""
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100, visibility: Optional[str] = None) -> List[Forum]:
        """Get all forums with optional visibility filter"""
        pass
    
    @abstractmethod
    async def get_by_creator(self, creator_type: str, creator_id: UUID, skip: int = 0, limit: int = 100) -> List[Forum]:
        """Get forums by creator"""
        pass
    
    @abstractmethod
    async def update(self, forum_id: UUID, update_data: ForumUpdate, creator_id: UUID) -> Optional[Forum]:
        """Update forum (only by creator)"""
        pass
    
    @abstractmethod
    async def delete(self, forum_id: UUID, creator_id: UUID) -> bool:
        """Delete forum (only by creator)"""
        pass
    
    @abstractmethod
    async def search_forums(self, query: str, skip: int = 0, limit: int = 100) -> List[Forum]:
        """Search forums by title or description"""
        pass

class PostRepository(BaseRepository[Post, PostCreate, PostUpdate], ABC):
    """Abstract post repository interface"""
    
    @abstractmethod
    async def create(self, post_data: PostCreate, author_type: str, author_id: UUID, media_urls: Optional[List[str]] = None) -> Optional[Post]:
        """Create a new post"""
        pass
    
    @abstractmethod
    async def get_by_id(self, post_id: UUID) -> Optional[Post]:
        """Get post by ID"""
        pass
    
    @abstractmethod
    async def get_by_forum(self, forum_id: UUID, skip: int = 0, limit: int = 100) -> List[Post]:
        """Get posts in a specific forum"""
        pass
    
    @abstractmethod
    async def get_by_author(self, author_type: str, author_id: UUID, skip: int = 0, limit: int = 100) -> List[Post]:
        """Get posts by author"""
        pass
    
    @abstractmethod
    async def get_recent_posts(self, skip: int = 0, limit: int = 100) -> List[Post]:
        """Get recent posts across all forums"""
        pass
    
    @abstractmethod
    async def update(self, post_id: UUID, update_data: PostUpdate, author_id: UUID) -> Optional[Post]:
        """Update post (only by author)"""
        pass
    
    @abstractmethod
    async def delete(self, post_id: UUID, author_id: UUID) -> bool:
        """Delete post (only by author)"""
        pass
    
    @abstractmethod
    async def search_posts(self, query: str, forum_id: Optional[UUID] = None, skip: int = 0, limit: int = 100) -> List[Post]:
        """Search posts by title or body"""
        pass

class CommentRepository(BaseRepository[Comment, CommentCreate, CommentUpdate], ABC):
    """Abstract comment repository interface"""
    
    @abstractmethod
    async def create(self, comment_data: CommentCreate, author_type: str, author_id: UUID) -> Optional[Comment]:
        """Create a new comment"""
        pass
    
    @abstractmethod
    async def get_by_id(self, comment_id: UUID) -> Optional[Comment]:
        """Get comment by ID"""
        pass
    
    @abstractmethod
    async def get_by_target(self, target_type: str, target_id: UUID, skip: int = 0, limit: int = 100) -> List[Comment]:
        """Get comments for a specific target (post, comment, etc.)"""
        pass
    
    @abstractmethod
    async def get_by_author(self, author_type: str, author_id: UUID, skip: int = 0, limit: int = 100) -> List[Comment]:
        """Get comments by author"""
        pass
    
    @abstractmethod
    async def get_replies(self, parent_comment_id: UUID, skip: int = 0, limit: int = 100) -> List[Comment]:
        """Get replies to a specific comment"""
        pass
    
    @abstractmethod
    async def get_thread(self, comment_id: UUID) -> List[Comment]:
        """Get full comment thread starting from a comment"""
        pass
    
    @abstractmethod
    async def update(self, comment_id: UUID, update_data: CommentUpdate, author_id: UUID) -> Optional[Comment]:
        """Update comment (only by author)"""
        pass
    
    @abstractmethod
    async def delete(self, comment_id: UUID, author_id: UUID) -> bool:
        """Delete comment (only by author)"""
        pass
    
    @abstractmethod
    async def get_recent_comments(self, skip: int = 0, limit: int = 100) -> List[Comment]:
        """Get recent comments across all targets"""
        pass