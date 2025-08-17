# app/api/routes/social.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import List, Optional, Union
from uuid import UUID

from app.services.social import SocialService
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
    FeedResponse
)
from app.api.dependencies import (
    get_social_service,
    get_current_user_soft,
    get_current_org_soft,
    validate_upload_file
)
from app.models.auth import User, Organization
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Helper function to determine author type and ID
def get_author_info(user: Optional[User] = None, org: Optional[Organization] = None):
    if user:
        return "user", user.id
    elif org:
        return "organization", org.id
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

# FORUM ROUTES

@router.post("/forums", response_model=ForumResponse, status_code=status.HTTP_201_CREATED)
async def create_forum(
    forum_data: ForumCreate,
    service: SocialService = Depends(get_social_service),
    user: Optional[User] = Depends(get_current_user_soft),
    org: Optional[Organization] = Depends(get_current_org_soft)
):
    """Create a new forum"""
    try:
        author_type, author_id = get_author_info(user, org)
        response = await service.create_forum(forum_data, author_type, author_id)
        
        if response.error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=response.message
            )
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating forum: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create forum"
        )

@router.get("/forums", response_model=ForumListResponse)
async def get_forums(
    skip: int = 0,
    limit: int = 100,
    visibility: Optional[str] = None,
    search: Optional[str] = None,
    service: SocialService = Depends(get_social_service)
):
    """Get all forums or search forums"""
    try:
        if search:
            response = await service.search_forums(search, skip, limit)
        else:
            response = await service.get_all_forums(skip, limit, visibility)
        return response
    except Exception as e:
        logger.error(f"Error getting forums: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get forums"
        )

@router.get("/forums/{forum_id}", response_model=ForumResponse)
async def get_forum(
    forum_id: UUID,
    service: SocialService = Depends(get_social_service)
):
    """Get a specific forum"""
    response = await service.get_forum(forum_id)
    if response.error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=response.message
        )
    return response

@router.get("/forums/name/{forum_name}", response_model=ForumResponse)
async def get_forum_by_name(
    forum_name: str,
    service: SocialService = Depends(get_social_service)
):
    """Get a forum by its unique name"""
    response = await service.get_forum_by_name(forum_name)
    if response.error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=response.message
        )
    return response

@router.patch("/forums/{forum_id}", response_model=ForumResponse)
async def update_forum(
    forum_id: UUID,
    update_data: ForumUpdate,
    service: SocialService = Depends(get_social_service),
    user: Optional[User] = Depends(get_current_user_soft),
    org: Optional[Organization] = Depends(get_current_org_soft)
):
    """Update a forum (only by creator)"""
    try:
        author_type, author_id = get_author_info(user, org)
        response = await service.update_forum(forum_id, update_data, author_id)
        
        if response.error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=response.message
            )
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating forum: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update forum"
        )

@router.delete("/forums/{forum_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_forum(
    forum_id: UUID,
    service: SocialService = Depends(get_social_service),
    user: Optional[User] = Depends(get_current_user_soft),
    org: Optional[Organization] = Depends(get_current_org_soft)
):
    """Delete a forum (only by creator)"""
    try:
        author_type, author_id = get_author_info(user, org)
        success = await service.delete_forum(forum_id, author_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Forum not found or permission denied"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting forum: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete forum"
        )

# POST ROUTES

@router.post("/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    forum_id: UUID = Form(...),
    title: str = Form(...),
    body: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # JSON string of tags
    media_files: Optional[List[UploadFile]] = File(None),
    service: SocialService = Depends(get_social_service),
    user: Optional[User] = Depends(get_current_user_soft),
    org: Optional[Organization] = Depends(get_current_org_soft)
):
    """Create a new post with optional media"""
    try:
        author_type, author_id = get_author_info(user, org)
        
        # Parse tags if provided
        parsed_tags = []
        if tags:
            import json
            parsed_tags = json.loads(tags)
        
        post_data = PostCreate(
            forum_id=forum_id,
            title=title,
            body=body,
            tags=parsed_tags
        )
        
        response = await service.create_post(post_data, author_type, author_id, media_files)
        
        if response.error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=response.message
            )
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating post: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create post"
        )

@router.get("/posts/recent", response_model=PostListResponse)
async def get_recent_posts(
    skip: int = 0,
    limit: int = 100,
    service: SocialService = Depends(get_social_service)
):
    """Get recent posts across all forums"""
    try:
        response = await service.get_recent_posts(skip, limit)
        return response
    except Exception as e:
        logger.error(f"Error getting recent posts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recent posts"
        )

@router.get("/posts/search", response_model=PostListResponse)
async def search_posts(
    q: str,
    forum_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100,
    service: SocialService = Depends(get_social_service)
):
    """Search posts"""
    try:
        response = await service.search_posts(q, forum_id, skip, limit)
        return response
    except Exception as e:
        logger.error(f"Error searching posts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search posts"
        )

@router.get("/posts/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: UUID,
    service: SocialService = Depends(get_social_service)
):
    """Get a specific post"""
    response = await service.get_post(post_id)
    if response.error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=response.message
        )
    return response

@router.get("/forums/{forum_id}/posts", response_model=PostListResponse)
async def get_forum_posts(
    forum_id: UUID,
    skip: int = 0,
    limit: int = 100,
    service: SocialService = Depends(get_social_service)
):
    """Get posts in a specific forum"""
    try:
        response = await service.get_forum_posts(forum_id, skip, limit)
        return response
    except Exception as e:
        logger.error(f"Error getting forum posts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get forum posts"
        )

@router.patch("/posts/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: UUID,
    update_data: PostUpdate,
    service: SocialService = Depends(get_social_service),
    user: Optional[User] = Depends(get_current_user_soft),
    org: Optional[Organization] = Depends(get_current_org_soft)
):
    """Update a post (only by author)"""
    try:
        author_type, author_id = get_author_info(user, org)
        response = await service.update_post(post_id, update_data, author_id)
        
        if response.error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=response.message
            )
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating post: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update post"
        )

@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: UUID,
    service: SocialService = Depends(get_social_service),
    user: Optional[User] = Depends(get_current_user_soft),
    org: Optional[Organization] = Depends(get_current_org_soft)
):
    """Delete a post (only by author)"""
    try:
        author_type, author_id = get_author_info(user, org)
        success = await service.delete_post(post_id, author_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found or permission denied"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting post: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete post"
        )

# COMMENT ROUTES

@router.post("/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment_data: CommentCreate,
    service: SocialService = Depends(get_social_service),
    user: Optional[User] = Depends(get_current_user_soft),
    org: Optional[Organization] = Depends(get_current_org_soft)
):
    """Create a new comment"""
    try:
        author_type, author_id = get_author_info(user, org)
        response = await service.create_comment(comment_data, author_type, author_id)
        
        if response.error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=response.message
            )
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating comment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create comment"
        )

@router.get("/comments/{comment_id}", response_model=CommentResponse)
async def get_comment(
    comment_id: UUID,
    service: SocialService = Depends(get_social_service)
):
    """Get a specific comment"""
    response = await service.get_comment(comment_id)
    if response.error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=response.message
        )
    return response

@router.get("/comments/{comment_id}/replies", response_model=CommentListResponse)
async def get_comment_replies(
    comment_id: UUID,
    skip: int = 0,
    limit: int = 100,
    service: SocialService = Depends(get_social_service)
):
    """Get replies to a specific comment"""
    try:
        response = await service.get_comment_replies(comment_id, skip, limit)
        return response
    except Exception as e:
        logger.error(f"Error getting comment replies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get comment replies"
        )

@router.get("/comments/{comment_id}/thread", response_model=CommentListResponse)
async def get_comment_thread(
    comment_id: UUID,
    service: SocialService = Depends(get_social_service)
):
    """Get full comment thread"""
    try:
        response = await service.get_comment_thread(comment_id)
        return response
    except Exception as e:
        logger.error(f"Error getting comment thread: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get comment thread"
        )

@router.get("/{target_type}/{target_id}/comments", response_model=CommentListResponse)
async def get_target_comments(
    target_type: str,
    target_id: UUID,
    skip: int = 0,
    limit: int = 100,
    service: SocialService = Depends(get_social_service)
):
    """Get comments for a specific target (post, comment, etc.)"""
    try:
        response = await service.get_target_comments(target_type, target_id, skip, limit)
        return response
    except Exception as e:
        logger.error(f"Error getting target comments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get comments"
        )

@router.patch("/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: UUID,
    update_data: CommentUpdate,
    service: SocialService = Depends(get_social_service),
    user: Optional[User] = Depends(get_current_user_soft),
    org: Optional[Organization] = Depends(get_current_org_soft)
):
    """Update a comment (only by author)"""
    try:
        author_type, author_id = get_author_info(user, org)
        response = await service.update_comment(comment_id, update_data, author_id)
        
        if response.error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=response.message
            )
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating comment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update comment"
        )

@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: UUID,
    service: SocialService = Depends(get_social_service),
    user: Optional[User] = Depends(get_current_user_soft),
    org: Optional[Organization] = Depends(get_current_org_soft)
):
    """Delete a comment (only by author)"""
    try:
        author_type, author_id = get_author_info(user, org)
        success = await service.delete_comment(comment_id, author_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found or permission denied"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting comment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete comment"
        )

# FEED AND DISCOVERY ROUTES

@router.get("/feed", response_model=FeedResponse)
async def get_social_feed(
    skip: int = 0,
    limit: int = 50,
    service: SocialService = Depends(get_social_service)
):
    """Get mixed social feed of recent posts and comments"""
    try:
        response = await service.get_social_feed(skip, limit)
        return response
    except Exception as e:
        logger.error(f"Error getting social feed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get social feed"
        )

@router.get("/my/forums", response_model=ForumListResponse)
async def get_my_forums(
    skip: int = 0,
    limit: int = 100,
    service: SocialService = Depends(get_social_service),
    user: Optional[User] = Depends(get_current_user_soft),
    org: Optional[Organization] = Depends(get_current_org_soft)
):
    """Get forums created by current user/org"""
    try:
        author_type, author_id = get_author_info(user, org)
        response = await service.get_user_forums(author_type, author_id, skip, limit)
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user forums: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user forums"
        )

@router.get("/my/posts", response_model=PostListResponse)
async def get_my_posts(
    skip: int = 0,
    limit: int = 100,
    service: SocialService = Depends(get_social_service),
    user: Optional[User] = Depends(get_current_user_soft),
    org: Optional[Organization] = Depends(get_current_org_soft)
):
    """Get posts created by current user/org"""
    try:
        author_type, author_id = get_author_info(user, org)
        response = await service.get_user_posts(author_type, author_id, skip, limit)
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user posts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user posts"
        )