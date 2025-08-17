# app/adapters/db/sqlalchemy_social_repository.py
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.models.social import Forum, Post, Comment
from app.schemas.social import (
    ForumCreate, 
    ForumUpdate, 
    PostCreate, 
    PostUpdate, 
    CommentCreate, 
    CommentUpdate
)
from app.adapters.db.sqlalchemy_base_repository import SQLAlchemyRepository
from app.ports.repositories.social_repository import ForumRepository, PostRepository, CommentRepository
from app.core.exceptions import DatabaseError, ConflictError
from app.utils.logger import get_logger

logger = get_logger("social_repository")

class SQLAlchemyForumRepository(SQLAlchemyRepository[Forum, ForumCreate, ForumUpdate], ForumRepository):
    """SQLAlchemy implementation of ForumRepository"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Forum, session)

    # BaseRepository abstract methods implementation
    async def count(self, **filters) -> int:
        """Count forums with optional filters"""
        try:
            stmt = select(func.count(Forum.id))
            
            # Apply filters if provided
            for key, value in filters.items():
                if hasattr(Forum, key) and value is not None:
                    stmt = stmt.where(getattr(Forum, key) == value)
            
            result = await self.session.execute(stmt)
            return result.scalar_one()
        except Exception as e:
            logger.error(f"Error counting forums: {e}")
            raise DatabaseError("Failed to count forums")
    
    async def exists(self, entity_id: UUID) -> bool:
        """Check if forum exists by ID"""
        try:
            stmt = select(func.count(Forum.id)).where(Forum.id == entity_id)
            result = await self.session.execute(stmt)
            return result.scalar_one() > 0
        except Exception as e:
            logger.error(f"Error checking forum existence {entity_id}: {e}")
            raise DatabaseError("Failed to check forum existence")
    
    async def get_multi(self, skip: int = 0, limit: int = 100, **filters) -> List[Forum]:
        """Get multiple forums with optional filters"""
        try:
            stmt = select(Forum)
            
            # Apply filters if provided
            for key, value in filters.items():
                if hasattr(Forum, key) and value is not None:
                    stmt = stmt.where(getattr(Forum, key) == value)
            
            stmt = (
                stmt.offset(skip)
                .limit(limit)
                .order_by(Forum.created_at.desc())
            )
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting multiple forums: {e}")
            raise DatabaseError("Failed to get forums")

    async def create(self, forum_data: ForumCreate, creator_type: str, creator_id: UUID) -> Optional[Forum]:
        try:
            forum_dict = forum_data.dict()
            forum_dict['creator_type'] = creator_type
            forum_dict['creator_id'] = creator_id
            
            forum = Forum(**forum_dict)
            self.session.add(forum)
            await self.session.commit()
            await self.session.refresh(forum)
            return forum
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Integrity error creating forum: {e}")
            raise ConflictError("Forum name already exists")
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating forum: {e}")
            raise DatabaseError("Failed to create forum")
    
    async def get_by_id(self, forum_id: UUID) -> Optional[Forum]:
        try:
            stmt = select(Forum).where(Forum.id == forum_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting forum {forum_id}: {e}")
            raise DatabaseError("Failed to get forum")
    
    async def get_by_name(self, name: str) -> Optional[Forum]:
        try:
            stmt = select(Forum).where(Forum.name == name.lower())
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting forum by name {name}: {e}")
            raise DatabaseError("Failed to get forum")
    
    async def get_all(self, skip: int = 0, limit: int = 100, visibility: Optional[str] = None) -> List[Forum]:
        try:
            stmt = select(Forum)
            
            if visibility:
                stmt = stmt.where(Forum.visibility == visibility)
            
            stmt = (
                stmt.offset(skip)
                .limit(limit)
                .order_by(Forum.created_at.desc())
            )
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting all forums: {e}")
            raise DatabaseError("Failed to get forums")
    
    async def get_by_creator(self, creator_type: str, creator_id: UUID, skip: int = 0, limit: int = 100) -> List[Forum]:
        try:
            stmt = (
                select(Forum)
                .where(and_(Forum.creator_type == creator_type, Forum.creator_id == creator_id))
                .offset(skip)
                .limit(limit)
                .order_by(Forum.created_at.desc())
            )
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting forums by creator {creator_type} {creator_id}: {e}")
            raise DatabaseError("Failed to get forums")
    
    async def update(self, forum_id: UUID, update_data: ForumUpdate, creator_id: UUID) -> Optional[Forum]:
        try:
            stmt = (
                update(Forum)
                .where(and_(Forum.id == forum_id, Forum.creator_id == creator_id))
                .values(**update_data.dict(exclude_unset=True))
                .returning(Forum)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.scalar_one_or_none()
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating forum {forum_id}: {e}")
            raise DatabaseError("Failed to update forum")
    
    async def delete(self, forum_id: UUID, creator_id: UUID) -> bool:
        try:
            stmt = delete(Forum).where(and_(Forum.id == forum_id, Forum.creator_id == creator_id))
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting forum {forum_id}: {e}")
            raise DatabaseError("Failed to delete forum")
    
    async def search_forums(self, query: str, skip: int = 0, limit: int = 100) -> List[Forum]:
        try:
            search_term = f"%{query}%"
            stmt = (
                select(Forum)
                .where(or_(
                    Forum.title.ilike(search_term),
                    Forum.description.ilike(search_term)
                ))
                .offset(skip)
                .limit(limit)
                .order_by(Forum.created_at.desc())
            )
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error searching forums with query '{query}': {e}")
            raise DatabaseError("Failed to search forums")


class SQLAlchemyPostRepository(SQLAlchemyRepository[Post, PostCreate, PostUpdate], PostRepository):
    """SQLAlchemy implementation of PostRepository"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Post, session)

    # BaseRepository abstract methods implementation
    async def count(self, **filters) -> int:
        """Count posts with optional filters"""
        try:
            stmt = select(func.count(Post.id))
            
            # Apply filters if provided
            for key, value in filters.items():
                if hasattr(Post, key) and value is not None:
                    stmt = stmt.where(getattr(Post, key) == value)
            
            result = await self.session.execute(stmt)
            return result.scalar_one()
        except Exception as e:
            logger.error(f"Error counting posts: {e}")
            raise DatabaseError("Failed to count posts")
    
    async def exists(self, entity_id: UUID) -> bool:
        """Check if post exists by ID"""
        try:
            stmt = select(func.count(Post.id)).where(Post.id == entity_id)
            result = await self.session.execute(stmt)
            return result.scalar_one() > 0
        except Exception as e:
            logger.error(f"Error checking post existence {entity_id}: {e}")
            raise DatabaseError("Failed to check post existence")
    
    async def get_multi(self, skip: int = 0, limit: int = 100, **filters) -> List[Post]:
        """Get multiple posts with optional filters"""
        try:
            stmt = select(Post)
            
            # Apply filters if provided
            for key, value in filters.items():
                if hasattr(Post, key) and value is not None:
                    stmt = stmt.where(getattr(Post, key) == value)
            
            stmt = (
                stmt.offset(skip)
                .limit(limit)
                .order_by(Post.created_at.desc())
            )
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting multiple posts: {e}")
            raise DatabaseError("Failed to get posts")
    
    async def create(self, post_data: PostCreate, author_type: str, author_id: UUID, media_urls: Optional[List[str]] = None) -> Optional[Post]:
        try:
            post_dict = post_data.dict()
            post_dict['author_type'] = author_type
            post_dict['author_id'] = author_id
            if media_urls:
                post_dict['media_urls'] = media_urls
            
            post = Post(**post_dict)
            self.session.add(post)
            await self.session.commit()
            await self.session.refresh(post)
            return post
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Integrity error creating post: {e}")
            raise ConflictError("Post references invalid entities")
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating post: {e}")
            raise DatabaseError("Failed to create post")
    
    async def get_by_id(self, post_id: UUID) -> Optional[Post]:
        try:
            stmt = select(Post).where(Post.id == post_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting post {post_id}: {e}")
            raise DatabaseError("Failed to get post")
    
    async def get_by_forum(self, forum_id: UUID, skip: int = 0, limit: int = 100) -> List[Post]:
        try:
            stmt = (
                select(Post)
                .where(Post.forum_id == forum_id)
                .offset(skip)
                .limit(limit)
                .order_by(Post.created_at.desc())
            )
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting posts for forum {forum_id}: {e}")
            raise DatabaseError("Failed to get posts")
    
    async def get_by_author(self, author_type: str, author_id: UUID, skip: int = 0, limit: int = 100) -> List[Post]:
        try:
            stmt = (
                select(Post)
                .where(and_(Post.author_type == author_type, Post.author_id == author_id))
                .offset(skip)
                .limit(limit)
                .order_by(Post.created_at.desc())
            )
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting posts by author {author_type} {author_id}: {e}")
            raise DatabaseError("Failed to get posts")
    
    async def get_recent_posts(self, skip: int = 0, limit: int = 100) -> List[Post]:
        try:
            stmt = (
                select(Post)
                .offset(skip)
                .limit(limit)
                .order_by(Post.created_at.desc())
            )
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting recent posts: {e}")
            raise DatabaseError("Failed to get recent posts")
    
    async def update(self, post_id: UUID, update_data: PostUpdate, author_id: UUID) -> Optional[Post]:
        try:
            stmt = (
                update(Post)
                .where(and_(Post.id == post_id, Post.author_id == author_id))
                .values(**update_data.dict(exclude_unset=True))
                .returning(Post)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.scalar_one_or_none()
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating post {post_id}: {e}")
            raise DatabaseError("Failed to update post")
    
    async def delete(self, post_id: UUID, author_id: UUID) -> bool:
        try:
            stmt = delete(Post).where(and_(Post.id == post_id, Post.author_id == author_id))
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting post {post_id}: {e}")
            raise DatabaseError("Failed to delete post")
    
    async def search_posts(self, query: str, forum_id: Optional[UUID] = None, skip: int = 0, limit: int = 100) -> List[Post]:
        try:
            search_term = f"%{query}%"
            stmt = select(Post).where(or_(
                Post.title.ilike(search_term),
                Post.body.ilike(search_term)
            ))
            
            if forum_id:
                stmt = stmt.where(Post.forum_id == forum_id)
            
            stmt = (
                stmt.offset(skip)
                .limit(limit)
                .order_by(Post.created_at.desc())
            )
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error searching posts with query '{query}': {e}")
            raise DatabaseError("Failed to search posts")


class SQLAlchemyCommentRepository(SQLAlchemyRepository[Comment, CommentCreate, CommentUpdate], CommentRepository):
    """SQLAlchemy implementation of CommentRepository"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Comment, session)

    # BaseRepository abstract methods implementation
    async def count(self, **filters) -> int:
        """Count comments with optional filters"""
        try:
            stmt = select(func.count(Comment.id))
            
            # Apply filters if provided
            for key, value in filters.items():
                if hasattr(Comment, key) and value is not None:
                    stmt = stmt.where(getattr(Comment, key) == value)
            
            result = await self.session.execute(stmt)
            return result.scalar_one()
        except Exception as e:
            logger.error(f"Error counting comments: {e}")
            raise DatabaseError("Failed to count comments")
    
    async def exists(self, entity_id: UUID) -> bool:
        """Check if comment exists by ID"""
        try:
            stmt = select(func.count(Comment.id)).where(Comment.id == entity_id)
            result = await self.session.execute(stmt)
            return result.scalar_one() > 0
        except Exception as e:
            logger.error(f"Error checking comment existence {entity_id}: {e}")
            raise DatabaseError("Failed to check comment existence")
    
    async def get_multi(self, skip: int = 0, limit: int = 100, **filters) -> List[Comment]:
        """Get multiple comments with optional filters"""
        try:
            stmt = select(Comment)
            
            # Apply filters if provided
            for key, value in filters.items():
                if hasattr(Comment, key) and value is not None:
                    stmt = stmt.where(getattr(Comment, key) == value)
            
            stmt = (
                stmt.offset(skip)
                .limit(limit)
                .order_by(Comment.created_at.desc())
            )
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting multiple comments: {e}")
            raise DatabaseError("Failed to get comments")
    
    async def create(self, comment_data: CommentCreate, author_type: str, author_id: UUID) -> Optional[Comment]:
        try:
            comment_dict = comment_data.dict()
            comment_dict['author_type'] = author_type
            comment_dict['author_id'] = author_id
            
            comment = Comment(**comment_dict)
            self.session.add(comment)
            await self.session.commit()
            await self.session.refresh(comment)
            return comment
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Integrity error creating comment: {e}")
            raise ConflictError("Comment references invalid entities")
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating comment: {e}")
            raise DatabaseError("Failed to create comment")
    
    async def get_by_id(self, comment_id: UUID) -> Optional[Comment]:
        try:
            stmt = select(Comment).where(Comment.id == comment_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting comment {comment_id}: {e}")
            raise DatabaseError("Failed to get comment")
    
    async def get_by_target(self, target_type: str, target_id: UUID, skip: int = 0, limit: int = 100) -> List[Comment]:
        try:
            stmt = (
                select(Comment)
                .where(and_(
                    Comment.target_type == target_type,
                    Comment.target_id == target_id,
                    Comment.parent_comment_id.is_(None)  # Only top-level comments
                ))
                .offset(skip)
                .limit(limit)
                .order_by(Comment.created_at.asc())
            )
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting comments for {target_type} {target_id}: {e}")
            raise DatabaseError("Failed to get comments")
    
    async def get_by_author(self, author_type: str, author_id: UUID, skip: int = 0, limit: int = 100) -> List[Comment]:
        try:
            stmt = (
                select(Comment)
                .where(and_(Comment.author_type == author_type, Comment.author_id == author_id))
                .offset(skip)
                .limit(limit)
                .order_by(Comment.created_at.desc())
            )
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting comments by author {author_type} {author_id}: {e}")
            raise DatabaseError("Failed to get comments")
    
    async def get_replies(self, parent_comment_id: UUID, skip: int = 0, limit: int = 100) -> List[Comment]:
        try:
            stmt = (
                select(Comment)
                .where(Comment.parent_comment_id == parent_comment_id)
                .offset(skip)
                .limit(limit)
                .order_by(Comment.created_at.asc())
            )
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting replies for comment {parent_comment_id}: {e}")
            raise DatabaseError("Failed to get replies")
    
    async def get_thread(self, comment_id: UUID) -> List[Comment]:
        try:
            # This is a simplified version - for a full thread implementation,
            # you'd need recursive CTEs or multiple queries
            stmt = (
                select(Comment)
                .where(or_(
                    Comment.id == comment_id,
                    Comment.parent_comment_id == comment_id
                ))
                .order_by(Comment.created_at.asc())
            )
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting thread for comment {comment_id}: {e}")
            raise DatabaseError("Failed to get comment thread")
    
    async def update(self, comment_id: UUID, update_data: CommentUpdate, author_id: UUID) -> Optional[Comment]:
        try:
            stmt = (
                update(Comment)
                .where(and_(Comment.id == comment_id, Comment.author_id == author_id))
                .values(**update_data.dict(exclude_unset=True))
                .returning(Comment)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.scalar_one_or_none()
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating comment {comment_id}: {e}")
            raise DatabaseError("Failed to update comment")
    
    async def delete(self, comment_id: UUID, author_id: UUID) -> bool:
        try:
            stmt = delete(Comment).where(and_(Comment.id == comment_id, Comment.author_id == author_id))
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting comment {comment_id}: {e}")
            raise DatabaseError("Failed to delete comment")
    
    async def get_recent_comments(self, skip: int = 0, limit: int = 100) -> List[Comment]:
        try:
            stmt = (
                select(Comment)
                .offset(skip)
                .limit(limit)
                .order_by(Comment.created_at.desc())
            )
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting recent comments: {e}")
            raise DatabaseError("Failed to get recent comments")