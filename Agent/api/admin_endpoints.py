# -*- coding: utf-8 -*-
"""
知识图谱管理后台 API
提供数据同步、添加、更新、删除等管理功能
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
from loguru import logger

from Agent.core.startup import get_startup_manager
from Agent.memory.heritage_query_service import get_heritage_query_service
from Agent.api.session_dependencies import get_current_user_from_session, TokenData


admin_router = APIRouter(prefix='/api/admin/knowledge-graph', tags=['知识图谱管理'])


class HeritageData(BaseModel):
    id: int
    name: str
    pinyin_name: Optional[str] = None
    level: Optional[str] = None
    category: Optional[str] = None
    region: Optional[str] = None
    batch: Optional[str] = None
    description: Optional[str] = None
    history: Optional[str] = None
    features: Optional[str] = None
    value: Optional[str] = None
    status: Optional[str] = None
    protection_measures: Optional[str] = None
    inheritors: Optional[str] = None
    related_works: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class HeritageUpdateData(BaseModel):
    name: Optional[str] = None
    pinyin_name: Optional[str] = None
    level: Optional[str] = None
    category: Optional[str] = None
    region: Optional[str] = None
    batch: Optional[str] = None
    description: Optional[str] = None
    history: Optional[str] = None
    features: Optional[str] = None
    value: Optional[str] = None
    status: Optional[str] = None
    protection_measures: Optional[str] = None
    inheritors: Optional[str] = None
    related_works: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class SyncResponse(BaseModel):
    success: bool
    message: str
    heritage_count: Optional[int] = None
    category_count: Optional[int] = None
    region_count: Optional[int] = None
    vector_count: Optional[int] = None


class StatusResponse(BaseModel):
    knowledge_graph: Dict[str, Any]
    vector_store: Dict[str, Any]
    sync_status: Dict[str, Any]


@admin_router.post('/sync', summary="全量同步", response_model=SyncResponse)
async def sync_all_heritage(current_user: TokenData = Depends(get_current_user_from_session)):
    """
    全量同步 MySQL 中的非遗数据到知识图谱和向量数据库
    
    需要管理员权限
    """
    try:
        startup_manager = get_startup_manager()
        result = await startup_manager.auto_sync_heritage_data(force=True)
        
        if result.get('success'):
            return SyncResponse(
                success=True,
                message="全量同步完成",
                heritage_count=result.get('heritage_count', 0),
                category_count=result.get('knowledge_graph', {}).get('category_count', 0),
                region_count=result.get('knowledge_graph', {}).get('region_count', 0),
                vector_count=result.get('vector_store', {}).get('vector_count', 0)
            )
        else:
            return SyncResponse(
                success=False,
                message=result.get('error', '同步失败')
            )
    except Exception as e:
        logger.error(f"全量同步失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.get('/status', summary="获取状态", response_model=StatusResponse)
async def get_status(current_user: TokenData = Depends(get_current_user_from_session)):
    """
    获取知识图谱和向量数据库的状态信息
    """
    try:
        query_service = get_heritage_query_service()
        startup_manager = get_startup_manager()
        
        stats = query_service.get_stats()
        
        return StatusResponse(
            knowledge_graph=stats.get('knowledge_graph', {}),
            vector_store=stats.get('vector_store', {}),
            sync_status=startup_manager.get_sync_status()
        )
    except Exception as e:
        logger.error(f"获取状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.get('/query/{heritage_id}', summary="查询非遗")
async def query_heritage(heritage_id: int,
                         current_user: TokenData = Depends(get_current_user_from_session)):
    """
    查询单个非遗项目信息
    """
    try:
        query_service = get_heritage_query_service()
        result = query_service.get_heritage_full_info(heritage_id)
        
        if result:
            return result
        else:
            raise HTTPException(status_code=404, detail="非遗项目不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询非遗失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.get('/search', summary="语义搜索")
async def search_heritage(query: str,
                          region: Optional[str] = None,
                          category: Optional[str] = None,
                          top_k: int = 5,
                          current_user: TokenData = Depends(get_current_user_from_session)):
    """
    语义搜索非遗项目
    
    Args:
        query: 搜索关键词
        region: 地区过滤
        category: 类别过滤
        top_k: 返回数量
    """
    try:
        query_service = get_heritage_query_service()
        
        if region or category:
            results = query_service.hybrid_query(query, region, category, top_k)
        else:
            results = query_service.query_by_semantic(query, top_k)
        
        return {
            'success': True,
            'query': query,
            'count': len(results),
            'results': results
        }
    except Exception as e:
        logger.error(f"搜索非遗失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.get('/region/{region}', summary="按地区查询")
async def query_by_region(region: str,
                          limit: int = 10,
                          current_user: TokenData = Depends(get_current_user_from_session)):
    """
    查询指定地区的非遗项目
    """
    try:
        query_service = get_heritage_query_service()
        results = query_service.query_by_region(region, limit)
        
        return {
            'success': True,
            'region': region,
            'count': len(results),
            'results': results
        }
    except Exception as e:
        logger.error(f"按地区查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.get('/category/{category}', summary="按类别查询")
async def query_by_category(category: str,
                            limit: int = 10,
                            current_user: TokenData = Depends(get_current_user_from_session)):
    """
    查询指定类别的非遗项目
    """
    try:
        query_service = get_heritage_query_service()
        results = query_service.query_by_category(category, limit)
        
        return {
            'success': True,
            'category': category,
            'count': len(results),
            'results': results
        }
    except Exception as e:
        logger.error(f"按类别查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
