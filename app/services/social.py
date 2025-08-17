# app/services/social.py
from typing import List, Optional
from uuid import UUID

from app.ports.repositories.social_repository import ForumRepository, PostRepository, CommentRepository
from app.utils.file_utils import FileUtils
from app.schemas.social import (
    ForumCreate,
    ForumUpdate,
    ForumResponse,
    ForumListResponse,
    PostCreate,
    PostUpdate,
    PostResponse,
    PostListResponse,
    CommentCreate,
    CommentUpdate,
    CommentResponse,
    CommentListResponse,
    FeedResponse,
    FeedItemBase
)
from app.utils.logger import get_logger
from app.ports.providers.storage_provider import StorageProvider

logger = get_logger(__name__)

class SocialService:
    def __init__(
        self, 
        forum_repository: ForumRepository,
        post_repository: PostRepository,
        comment_repository: CommentRepository,
        file_utils: FileUtils,
        storage_provider: StorageProvider
    ):
        self.forum_repository = forum_repository
        self.post_repository = post_repository
        self.comment_repository = comment_repository
        self.file_utils = file_utils
        self.storage_provider = storage_provider

    # Forum methods
    async def create_forum(self, forum_data: ForumCreate, creator_type: str, creator_id: UUID) -> ForumResponse:
        """Create a new forum"""
        try:
            # Check if forum name already exists
            existing_forum = await self.forum_repository.get_by_name(forum_data.name)
            if existing_forum:
                return ForumResponse(
                    error=True,
                    message="Forum name already exists",
                    data=None
                )
            
            forum = await self.forum_repository.create(forum_data, creator_type, creator_id)
            return ForumResponse.from_orm_model(forum)
        except Exception as e:
            logger.error(f"Error creating forum: {str(e)}")
            return ForumResponse(
                error=True,
                message="Failed to create forum",
                data=None
            )
    
    async def get_forum(self, forum_id: UUID) -> ForumResponse:
        """Get a specific forum by ID"""
        try:
            forum = await self.forum_repository.get_by_id(forum_id)
            return ForumResponse.from_orm_model(forum)
        except Exception as e:
            logger.error(f"Error getting forum {forum_id}: {str(e)}")
            return ForumResponse(
                error=True,
                message="Forum not found",
                data=None
            )
    
    async def get_forum_by_name(self, name: str) -> ForumResponse:
        """Get a specific forum by name"""
        try:
            forum = await self.forum_repository.get_by_name(name)
            return ForumResponse.from_orm_model(forum)
        except Exception as e:
            logger.error(f"Error getting forum by name {name}: {str(e)}")
            return ForumResponse(
                error=True,
                message="Forum not found",
                data=None
            )
    
    async def get_all_forums(self, skip: int = 0, limit: int = 100, visibility: Optional[str] = None) -> ForumListResponse:
        """Get all forums"""
        try:
            forums = await self.forum_repository.get_all(skip, limit, visibility)
            return ForumListResponse.from_orm_models(forums)
        except Exception as e:
            logger.error(f"Error getting all forums: {str(e)}")
            return ForumListResponse(
                error=True,
                message="Failed to get forums",
                data=[]
            )
    
    async def get_user_forums(self, creator_type: str, creator_id: UUID, skip: int = 0, limit: int = 100) -> ForumListResponse:
        """Get forums created by a specific user/org"""
        try:
            forums = await self.forum_repository.get_by_creator(creator_type, creator_id, skip, limit)
            return ForumListResponse.from_orm_models(forums)
        except Exception as e:
            logger.error(f"Error getting forums for creator {creator_type} {creator_id}: {str(e)}")
            return ForumListResponse(
                error=True,
                message="Failed to get forums",
                data=[]
            )
    
    async def update_forum(self, forum_id: UUID, update_data: ForumUpdate, creator_id: UUID) -> ForumResponse:
        """Update a forum (only by creator)"""
        try:
            updated_forum = await self.forum_repository.update(forum_id, update_data, creator_id)
            if not updated_forum:
                return ForumResponse(
                    error=True,
                    message="Forum not found or permission denied",
                    data=None
                )
            return ForumResponse.from_orm_model(updated_forum)
        except Exception as e:
            logger.error(f"Error updating forum {forum_id}: {str(e)}")
            return ForumResponse(
                error=True,
                message="Failed to update forum",
                data=None
            )
    
    async def delete_forum(self, forum_id: UUID, creator_id: UUID) -> bool:
        """Delete a forum (only by creator)"""
        try:
            return await self.forum_repository.delete(forum_id, creator_id)
        except Exception as e:
            logger.error(f"Error deleting forum {forum_id}: {str(e)}")
            return False
    
    async def search_forums(self, query: str, skip: int = 0, limit: int = 100) -> ForumListResponse:
        """Search forums"""
        try:
            forums = await self.forum_repository.search_forums(query, skip, limit)
            return ForumListResponse.from_orm_models(forums)
        except Exception as e:
            logger.error(f"Error searching forums: {str(e)}")
            return ForumListResponse(
                error=True,
                message="Failed to search forums",
                data=[]
            )

    # Post methods
    async def create_post(self, post_data: PostCreate, author_type: str, author_id: UUID, media_files: Optional[List] = None) -> PostResponse:
        """Create a new post with optional media"""
        try:
            media_urls = []
            
            # Handle media upload if files provided
            if media_files:
                for file in media_files:
                    upload_result = await self.storage_provider.upload_file(
                        file, 
                        file.filename, 
                        file.content_type
                    )
                    if upload_result.url:
                        media_urls.append(upload_result.url)
            
            post = await self.post_repository.create(post_data, author_type, author_id, media_urls)
            return PostResponse.from_orm_model(post)
        except Exception as e:
            logger.error(f"Error creating post: {str(e)}")
            return PostResponse(
                error=True,
                message="Failed to create post",
                data=None
            )
    
    async def get_post(self, post_id: UUID) -> PostResponse:
        """Get a specific post by ID"""
        try:
            post = await self.post_repository.get_by_id(post_id)
            return PostResponse.from_orm_model(post)
        except Exception as e:
            logger.error(f"Error getting post {post_id}: {str(e)}")
            return PostResponse(
                error=True,
                message="Post not found",
                data=None
            )
    
    async def get_forum_posts(self, forum_id: UUID, skip: int = 0, limit: int = 100) -> PostListResponse:
        """Get posts in a specific forum"""
        try:
            posts = await self.post_repository.get_by_forum(forum_id, skip, limit)
            return PostListResponse.from_orm_models(posts)
        except Exception as e:
            logger.error(f"Error getting posts for forum {forum_id}: {str(e)}")
            return PostListResponse(
                error=True,
                message="Failed to get posts",
                data=[]
            )
    
    async def get_user_posts(self, author_type: str, author_id: UUID, skip: int = 0, limit: int = 100) -> PostListResponse:
        """Get posts by a specific user/org"""
        try:
            posts = await self.post_repository.get_by_author(author_type, author_id, skip, limit)
            return PostListResponse.from_orm_models(posts)
        except Exception as e:
            logger.error(f"Error getting posts for author {author_type} {author_id}: {str(e)}")
            return PostListResponse(
                error=True,
                message="Failed to get posts",
                data=[]
            )
    
    async def get_recent_posts(self, skip: int = 0, limit: int = 100) -> PostListResponse:
        """Get recent posts across all forums"""
        try:
            posts = await self.post_repository.get_recent_posts(skip, limit)
            return PostListResponse.from_orm_models(posts)
        except Exception as e:
            logger.error(f"Error getting recent posts: {str(e)}")
            return PostListResponse(
                error=True,
                message="Failed to get recent posts",
                data=[]
            )
    
    async def update_post(self, post_id: UUID, update_data: PostUpdate, author_id: UUID) -> PostResponse:
        """Update a post (only by author)"""
        try:
            updated_post = await self.post_repository.update(post_id, update_data, author_id)
            if not updated_post:
                return PostResponse(
                    error=True,
                    message="Post not found or permission denied",
                    data=None
                )
            return PostResponse.from_orm_model(updated_post)
        except Exception as e:
            logger.error(f"Error updating post {post_id}: {str(e)}")
            return PostResponse(
                error=True,
                message="Failed to update post",
                data=None
            )
    
    async def delete_post(self, post_id: UUID, author_id: UUID) -> bool:
        """Delete a post (only by author)"""
        try:
            return await self.post_repository.delete(post_id, author_id)
        except Exception as e:
            logger.error(f"Error deleting post {post_id}: {str(e)}")
            return False
    
    async def search_posts(self, query: str, forum_id: Optional[UUID] = None, skip: int = 0, limit: int = 100) -> PostListResponse:
        """Search posts"""
        try:
            posts = await self.post_repository.search_posts(query, forum_id, skip, limit)
            return PostListResponse.from_orm_models(posts)
        except Exception as e:
            logger.error(f"Error searching posts: {str(e)}")
            return PostListResponse(
                error=True,
                message="Failed to search posts",
                data=[]
            )

    # Comment methods
    async def create_comment(self, comment_data: CommentCreate, author_type: str, author_id: UUID) -> CommentResponse:
        """Create a new comment"""
        try:
            comment = await self.comment_repository.create(comment_data, author_type, author_id)
            return CommentResponse.from_orm_model(comment)
        except Exception as e:
            logger.error(f"Error creating comment: {str(e)}")
            return CommentResponse(
                error=True,
                message="Failed to create comment",
                data=None
            )
    
    async def get_comment(self, comment_id: UUID) -> CommentResponse:
        """Get a specific comment by ID"""
        try:
            comment = await self.comment_repository.get_by_id(comment_id)
            return CommentResponse.from_orm_model(comment)
        except Exception as e:
            logger.error(f"Error getting comment {comment_id}: {str(e)}")
            return CommentResponse(
                error=True,
                message="Comment not found",
                data=None
            )
    
    async def get_target_comments(self, target_type: str, target_id: UUID, skip: int = 0, limit: int = 100) -> CommentListResponse:
        """Get comments for a specific target (post, comment, etc.)"""
        try:
            comments = await self.comment_repository.get_by_target(target_type, target_id, skip, limit)
            return CommentListResponse.from_orm_models(comments)
        except Exception as e:
            logger.error(f"Error getting comments for {target_type} {target_id}: {str(e)}")
            return CommentListResponse(
                error=True,
                message="Failed to get comments",
                data=[]
            )
    
    async def get_comment_replies(self, parent_comment_id: UUID, skip: int = 0, limit: int = 100) -> CommentListResponse:
        """Get replies to a specific comment"""
        try:
            replies = await self.comment_repository.get_replies(parent_comment_id, skip, limit)
            return CommentListResponse.from_orm_models(replies)
        except Exception as e:
            logger.error(f"Error getting replies for comment {parent_comment_id}: {str(e)}")
            return CommentListResponse(
                error=True,
                message="Failed to get replies",
                data=[]
            )
    
    async def get_comment_thread(self, comment_id: UUID) -> CommentListResponse:
        """Get full comment thread"""
        try:
            thread = await self.comment_repository.get_thread(comment_id)
            return CommentListResponse.from_orm_models(thread)
        except Exception as e:
            logger.error(f"Error getting thread for comment {comment_id}: {str(e)}")
            return CommentListResponse(
                error=True,
                message="Failed to get comment thread",
                data=[]
            )
    
    async def update_comment(self, comment_id: UUID, update_data: CommentUpdate, author_id: UUID) -> CommentResponse:
        """Update a comment (only by author)"""
        try:
            updated_comment = await self.comment_repository.update(comment_id, update_data, author_id)
            if not updated_comment:
                return CommentResponse(
                    error=True,
                    message="Comment not found or permission denied",
                    data=None
                )
            return CommentResponse.from_orm_model(updated_comment)
        except Exception as e:
            logger.error(f"Error updating comment {comment_id}: {str(e)}")
            return CommentResponse(
                error=True,
                message="Failed to update comment",
                data=None
            )
    
    async def delete_comment(self, comment_id: UUID, author_id: UUID) -> bool:
        """Delete a comment (only by author)"""
        try:
            return await self.comment_repository.delete(comment_id, author_id)
        except Exception as e:
            logger.error(f"Error deleting comment {comment_id}: {str(e)}")
            return False

    # Feed methods
    async def get_social_feed(self, skip: int = 0, limit: int = 50) -> FeedResponse:
        """Get mixed social feed of recent posts and comments"""
        try:
            feed_items = []
            
            # Get recent posts
            posts_response = await self.get_recent_posts(0, limit // 2)
            if not posts_response.error:
                for post in posts_response.data:
                    feed_items.append(FeedItemBase(
                        item_type="post",
                        item_id=post.id,
                        title=post.title,
                        body=post.body,
                        author_type=post.author_type,
                        author_id=post.author_id,
                        created_at=post.created_at,
                        forum_id=post.forum_id
                    ))
            
            # Get recent comments
            comments = await self.comment_repository.get_recent_comments(0, limit // 2)
            for comment in comments:
                feed_items.append(FeedItemBase(
                    item_type="comment",
                    item_id=comment.id,
                    body=comment.body,
                    author_type=comment.author_type,
                    author_id=comment.author_id,
                    created_at=comment.created_at,
                    post_id=comment.target_id if comment.target_type == "post" else None
                ))
            
            # Sort by creation time and limit
            feed_items.sort(key=lambda x: x.created_at, reverse=True)
            feed_items = feed_items[skip:skip + limit]
            
            return FeedResponse(
                error=False,
                message="Success",
                data=feed_items
            )
        except Exception as e:
            logger.error(f"Error getting social feed: {str(e)}")
            return FeedResponse(
                error=True,
                message="Failed to get social feed",
                data=[]
            )
    
    async def get_recent_posts(self, skip: int = 0, limit: int = 100) -> PostListResponse:
        """Get recent posts across all forums"""
        try:
            posts = await self.post_repository.get_recent_posts(skip, limit)
            return PostListResponse.from_orm_models(posts)
        except Exception as e:
            logger.error(f"Error getting recent posts: {str(e)}")
            return PostListResponse(
                error=True,
                message="Failed to get recent posts",
                data=[]
            )