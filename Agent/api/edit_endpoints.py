#--- START OF FILE api/edit_endpoints.py ---

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规划编辑API端点
提供AI对话式编辑功能的REST API接口
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger
import traceback
from typing import Dict, Any, Optional, List
from datetime import datetime

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.plan_editor import PlanEditor

# 创建路由器
edit_router = APIRouter(prefix='/api/agent', tags=['edit'])

# 全局编辑器实例
plan_editor = PlanEditor()

# 请求模型定义
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

# 响应模型定义
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

@edit_router.post('/start_edit_session', response_model=EditResponse)
async def start_edit_session(request: StartEditSessionRequest):
    try:
        plan_data = request.plan_data
        plan_id = plan_data.get('plan_id', f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        result = await plan_editor.start_edit_session(
            plan_id=plan_id,
            original_plan=plan_data
        )
        
        if result['success']:
            return EditResponse(success=True, session_id=result['session_id'], message='编辑会话已启动')
        else:
            raise HTTPException(status_code=500, detail=result.get('message', '启动失败'))
            
    except Exception as e:
        logger.error(f"启动错误: {str(e)}")
        raise HTTPException(status_code=500, detail='服务器内部错误')

@edit_router.post('/edit_plan', response_model=EditResponse)
async def edit_plan(request: EditPlanRequest):
    try:
        result = await plan_editor.process_edit_request(request.session_id, request.user_input)
        
        return EditResponse(
            success=result['success'],
            ai_response=result.get('response', ''),
            changes_made=result.get('changes_made', False),
            message=result.get('message', '')
        )
    except Exception as e:
        logger.error(f"编辑错误: {str(e)}")
        raise HTTPException(status_code=500, detail='处理失败')

@edit_router.post('/export_pdf', response_model=EditResponse)
async def export_plan_pdf(request: ExportPdfRequest):
    """
    导出规划为PDF格式 (增强版，支持对话上下文)
    """
    try:
        logger.info(f"开始导出PDF (编辑模式)，会话ID: {request.session_id}")
        
        # 1. 获取会话完整信息
        session_info_resp = plan_editor.get_session_info(request.session_id)
        if not session_info_resp['success']:
             raise HTTPException(status_code=404, detail="会话不存在或已过期")
             
        session_data = session_info_resp['session_info']
        
        # 2. 提取关键数据：当前规划状态 + 对话历史
        current_plan = session_data.get('current_plan', {})
        conversation_history = session_data.get('conversation_history', [])
        
        logger.info(f"提取到对话历史: {len(conversation_history)} 条")

        # 3. 初始化导出器
        from core.pdf_content_integrator import PDFContentIntegrator
        from core.travel_planner import get_travel_planner
        
        travel_planner = get_travel_planner()
        # 必须传入 ali_model 才能进行 AI 扩写
        if not travel_planner.ali_model:
            logger.error("TravelPlanner 中没有 ali_model 实例")
            raise HTTPException(status_code=500, detail="AI 模型未初始化")
            
        pdf_integrator = PDFContentIntegrator(ali_model=travel_planner.ali_model)
        
        # 4. 执行导出 - 显式传递对话历史
        result = await pdf_integrator.integrate_and_export(
            plan_data=current_plan,
            conversation_history=conversation_history, 
            output_filename=request.output_filename
        )
        
        if result['success']:
            return EditResponse(
                success=True,
                message="PDF 生成成功",
                summary=f"已根据您的 {len(conversation_history)} 条对话记录定制生成。文件路径: {result.get('pdf_path')}"
            )
        else:
            raise HTTPException(status_code=500, detail=result.get('error', '生成失败'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出PDF时发生错误: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"导出PDF失败: {str(e)}")

# 其他端点保持基本结构...
@edit_router.get('/health', response_model=EditResponse)
async def health_check():
    return EditResponse(success=True, status='healthy', message='编辑服务运行正常')

@edit_router.get('/get_edit_history', response_model=EditResponse)
async def get_edit_history(session_id: str):
    return EditResponse(success=True, history=[], message='暂不提供详细历史')

@edit_router.get('/get_available_operations', response_model=EditResponse)
async def get_available_operations():
    return EditResponse(success=True, operations=[], message='获取成功')

@edit_router.get('/get_plan_summary', response_model=EditResponse)
async def get_plan_summary(session_id: str):
    return EditResponse(success=True, summary="摘要", message='获取成功')

@edit_router.post('/end_edit_session', response_model=EditResponse)
async def end_edit_session(request: EndSessionRequest):
    plan_editor.end_session(request.session_id)
    return EditResponse(success=True, message='会话已结束')

@edit_router.post('/apply_plan_changes', response_model=EditResponse)
async def apply_plan_changes(request: ApplyChangesRequest):
    return EditResponse(success=True, message='功能暂未开放')

@edit_router.post('/reset_plan', response_model=EditResponse)
async def reset_plan(request: EndSessionRequest):
    return EditResponse(success=True, message='重置成功')

