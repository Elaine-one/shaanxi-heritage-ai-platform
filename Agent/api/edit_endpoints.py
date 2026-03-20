# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from loguru import logger
from typing import Dict, Any, Optional, List
from datetime import datetime

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from Agent.agent.plan_editor import PlanEditor
from Agent.api.session_dependencies import get_current_user_from_session, TokenData
from Agent.memory.session import get_session_pool

edit_router = APIRouter(prefix='/api/agent', tags=['规划编辑'])

plan_editor = PlanEditor()
session_pool = get_session_pool()


class StartEditSessionRequest(BaseModel):
    plan_data: Dict[str, Any]


class EditPlanRequest(BaseModel):
    session_id: str
    user_input: str


class ApplyChangesRequest(BaseModel):
    session_id: str
    final_plan: Dict[str, Any]


class EndSessionRequest(BaseModel):
    session_id: str


class ExportPdfRequest(BaseModel):
    session_id: str
    output_filename: Optional[str] = None


class EditResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    session_id: Optional[str] = None
    ai_response: Optional[str] = None
    changes_made: Optional[bool] = None
    updated_plan: Optional[Dict[str, Any]] = None
    changes: Optional[Dict[str, Any]] = None
    original_plan: Optional[Dict[str, Any]] = None
    history: Optional[List[Dict[str, Any]]] = None
    operations: Optional[List[Dict[str, Any]]] = None
    summary: Optional[str] = None
    active_sessions: Optional[int] = None
    status: Optional[str] = None


@edit_router.post('/start_edit_session', summary="开始编辑", response_model=EditResponse)
async def start_edit_session(request: StartEditSessionRequest, current_user: TokenData = Depends(get_current_user_from_session)):
    """启动一个新的规划编辑会话"""
    try:
        plan_data = request.plan_data
        plan_id = plan_data.get('plan_id', f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        session = await session_pool.create_session(
            plan_id=plan_id,
            original_plan=plan_data,
            user_id=current_user.user_id
        )
        
        logger.info(f"编辑会话已创建: {session.session_id}, 出发地: {session.departure_location}, 人数: {session.group_size}")
        
        return EditResponse(success=True, session_id=session.session_id, message='编辑会话已启动')
    except Exception as e:
        logger.error(f"启动错误: {str(e)}")
        raise HTTPException(status_code=500, detail='服务器内部错误')


@edit_router.post('/export_pdf', summary="导出PDF", response_model=EditResponse)
async def export_plan_pdf(request: ExportPdfRequest, current_user: TokenData = Depends(get_current_user_from_session)):
    """将当前编辑的规划导出为PDF文件"""
    try:
        logger.info(f"开始导出PDF，会话ID: {request.session_id}")
        
        session = session_pool.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在或已过期")
        
        current_plan = session.current_plan
        conversation_history = session.conversation_history
        
        logger.info(f"提取到对话历史: {len(conversation_history)} 条")
        
        from Agent.services.pdf_content_integrator import PDFContentIntegrator
        from Agent.agent import get_travel_planner
        
        travel_planner = get_travel_planner()
        if not travel_planner.llm_model:
            raise HTTPException(status_code=500, detail="AI模型未初始化")
        
        pdf_integrator = PDFContentIntegrator(llm_model=travel_planner.llm_model)
        current_plan['conversation_history'] = conversation_history
        
        result = await pdf_integrator.integrate_and_export(
            plan_data=current_plan,
            conversation_history=conversation_history,
            output_filename=request.output_filename
        )
        
        if result['success']:
            return EditResponse(
                success=True,
                message="PDF生成成功",
                summary=f"已根据您的{len(conversation_history)}条对话记录定制生成"
            )
        raise HTTPException(status_code=500, detail=result.get('error', '生成失败'))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出PDF错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导出PDF失败: {str(e)}")


@edit_router.get('/health', summary="服务状态", response_model=EditResponse)
async def health_check():
    """检查编辑服务运行状态"""
    return EditResponse(success=True, status='healthy', message='编辑服务运行正常')


@edit_router.get('/get_edit_history', summary="编辑历史", response_model=EditResponse)
async def get_edit_history(session_id: str):
    """获取会话的编辑历史记录"""
    return EditResponse(success=True, history=[], message='暂不提供详细历史')


@edit_router.get('/get_available_operations', summary="可用操作", response_model=EditResponse)
async def get_available_operations():
    """获取可用的编辑操作列表"""
    return EditResponse(success=True, operations=[], message='获取成功')


@edit_router.get('/get_plan_summary', summary="规划摘要", response_model=EditResponse)
async def get_plan_summary(session_id: str):
    """获取当前规划的摘要信息"""
    return EditResponse(success=True, summary="摘要", message='获取成功')


@edit_router.post('/end_edit_session', summary="结束编辑", response_model=EditResponse)
async def end_edit_session(request: EndSessionRequest):
    """结束编辑会话"""
    session_pool.remove_session(request.session_id)
    return EditResponse(success=True, message='会话已结束')


@edit_router.post('/apply_plan_changes', summary="应用修改", response_model=EditResponse)
async def apply_plan_changes(request: ApplyChangesRequest):
    """应用规划修改"""
    return EditResponse(success=True, message='功能暂未开放')
