# -*- coding: utf-8 -*-
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from loguru import logger

from Agent.api.session_dependencies import get_current_user_from_session, TokenData
from Agent.services.conversation_service import get_conversation_service
from Agent.services.user_history_service import get_user_history_service
from Agent.memory import get_session_pool

router = APIRouter(prefix="/api/conversations", tags=["对话管理"])


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    type: str
    timestamp: str
    extra_data: Optional[dict] = None


class ConversationSummaryResponse(BaseModel):
    session_id: str
    plan_id: str
    title: str
    destination: str
    message_count: int
    created_at: str
    last_activity: str
    status: str
    has_export: bool


class ConversationDetailResponse(BaseModel):
    session_id: str
    metadata: dict
    context: dict
    messages: List[MessageResponse]


class ConversationListResponse(BaseModel):
    total: int
    conversations: List[ConversationSummaryResponse]


class UserStatsResponse(BaseModel):
    user_id: str
    total_sessions: int
    total_messages: int
    total_exports: int
    favorite_count: int
    destinations: List[str]
    active_sessions: int
    first_session: Optional[str]
    last_session: Optional[str]


class ArchiveResponse(BaseModel):
    success: bool
    object_path: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None


@router.get("", summary="对话列表", response_model=ConversationListResponse)
async def list_conversations(
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    current_user: TokenData = Depends(get_current_user_from_session)
):
    """获取当前用户的所有对话记录"""
    try:
        user_history_service = get_user_history_service()
        sessions = user_history_service.get_recent_sessions(
            user_id=current_user.user_id,
            limit=limit
        )
        return ConversationListResponse(total=len(sessions), conversations=sessions)
    except Exception as e:
        logger.error(f"获取对话列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}", summary="对话详情", response_model=ConversationDetailResponse)
async def get_conversation(
    session_id: str,
    current_user: TokenData = Depends(get_current_user_from_session)
):
    """获取指定对话的完整信息，包括所有消息记录"""
    try:
        conversation_service = get_conversation_service()
        conversation = conversation_service.get_conversation(session_id)
        
        if not conversation:
            raise HTTPException(status_code=404, detail="对话记录不存在")
        
        session_pool = get_session_pool()
        session = session_pool.get_session(session_id)
        
        if session and session.user_id and session.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="无权访问此对话")
        
        return ConversationDetailResponse(**conversation)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取对话详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/archive", summary="归档对话", response_model=ArchiveResponse)
async def archive_conversation(
    session_id: str,
    current_user: TokenData = Depends(get_current_user_from_session)
):
    """将对话记录归档存储到MinIO"""
    try:
        conversation_service = get_conversation_service()
        session_pool = get_session_pool()
        session = session_pool.get_session(session_id)
        
        if session and session.user_id and session.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="无权归档此对话")
        
        result = conversation_service.archive_conversation(
            session_id=session_id,
            username=current_user.username
        )
        return ArchiveResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"归档对话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}", summary="删除对话")
async def delete_conversation(
    session_id: str,
    current_user: TokenData = Depends(get_current_user_from_session)
):
    """删除指定的对话记录"""
    try:
        session_pool = get_session_pool()
        session = session_pool.get_session(session_id)
        
        if session and session.user_id and session.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="无权删除此对话")
        
        success = session_pool.remove_session(session_id)
        
        if success:
            return {"success": True, "message": "对话已删除"}
        raise HTTPException(status_code=404, detail="对话不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除对话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", summary="搜索对话", response_model=ConversationListResponse)
async def search_conversations(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    current_user: TokenData = Depends(get_current_user_from_session)
):
    """根据关键词搜索对话内容"""
    try:
        conversation_service = get_conversation_service()
        results = conversation_service.search_conversations(
            user_id=current_user.user_id,
            keyword=q
        )
        return ConversationListResponse(total=len(results), conversations=results)
    except Exception as e:
        logger.error(f"搜索对话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/stats", summary="使用统计", response_model=UserStatsResponse)
async def get_user_stats(current_user: TokenData = Depends(get_current_user_from_session)):
    """获取用户的对话使用统计信息"""
    try:
        user_history_service = get_user_history_service()
        stats = user_history_service.get_session_stats(current_user.user_id)
        return UserStatsResponse(user_id=current_user.user_id, **stats)
    except Exception as e:
        logger.error(f"获取用户统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/timeline", summary="时间线")
async def get_timeline(
    days: int = Query(30, ge=1, le=365, description="查询天数"),
    current_user: TokenData = Depends(get_current_user_from_session)
):
    """按时间线查看对话记录"""
    try:
        user_history_service = get_user_history_service()
        timeline = user_history_service.get_timeline(
            user_id=current_user.user_id,
            days=days
        )
        return {
            "user_id": current_user.user_id,
            "days": days,
            "total_sessions": len(timeline),
            "timeline": timeline
        }
    except Exception as e:
        logger.error(f"获取时间线失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/favorite", summary="收藏对话")
async def add_favorite(
    session_id: str,
    current_user: TokenData = Depends(get_current_user_from_session)
):
    """将对话添加到收藏"""
    try:
        user_history_service = get_user_history_service()
        session_pool = get_session_pool()
        session = session_pool.get_session(session_id)
        
        if session and session.user_id and session.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="无权收藏此对话")
        
        success = user_history_service.add_favorite(
            user_id=current_user.user_id,
            session_id=session_id
        )
        
        if success:
            return {"success": True, "message": "已收藏"}
        raise HTTPException(status_code=500, detail="收藏失败")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"收藏失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}/favorite", summary="取消收藏")
async def remove_favorite(
    session_id: str,
    current_user: TokenData = Depends(get_current_user_from_session)
):
    """取消收藏对话"""
    try:
        user_history_service = get_user_history_service()
        success = user_history_service.remove_favorite(
            user_id=current_user.user_id,
            session_id=session_id
        )
        
        if success:
            return {"success": True, "message": "已取消收藏"}
        raise HTTPException(status_code=500, detail="取消收藏失败")
    except Exception as e:
        logger.error(f"取消收藏失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/favorites/list", summary="收藏列表")
async def list_favorites(current_user: TokenData = Depends(get_current_user_from_session)):
    """获取收藏的对话列表"""
    try:
        user_history_service = get_user_history_service()
        favorites = user_history_service.get_favorites(current_user.user_id)
        return {
            "user_id": current_user.user_id,
            "total": len(favorites),
            "favorites": favorites
        }
    except Exception as e:
        logger.error(f"获取收藏列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
