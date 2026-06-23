# -*- coding: utf-8 -*-
"""旅游规划 API 路由 — 创建、进度、结果、取消、导出."""

import asyncio
import uuid
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from loguru import logger

from Agent.api.cache import progress_callbacks
from Agent.api.session_dependencies import get_current_user_from_session, TokenData
from Agent.agent.travel_planner import get_travel_planner

travel_router = APIRouter(prefix='/api/agent/travel-plan', tags=['旅游规划'])


# ── Pydantic models ──────────────────────────────────────────────────

class TravelPlanRequest(BaseModel):
    heritage_ids: List[int] = Field(..., description="选中的非遗项目ID列表")
    user_id: Optional[str] = Field(None, description="用户ID")
    travel_days: int = Field(..., ge=1, le=30, description="旅游天数")
    departure_location: str = Field("", description="出发地")
    travel_mode: str = Field("自驾", description="出行方式")
    budget_range: str = Field("中等", description="预算范围")
    group_size: int = Field(2, ge=1, le=50, description="团队人数")
    special_requirements: List[str] = Field(default_factory=list, description="特殊要求")
    contact_info: Optional[Dict[str, str]] = Field(None, description="联系信息")


class ExportRequest(BaseModel):
    format: str = Field(default="json", description="导出格式 (json, pdf)")


class PlanResponse(BaseModel):
    success: bool
    plan_id: str
    message: str
    data: Optional[Dict[str, Any]] = None


class ProgressResponse(BaseModel):
    plan_id: str
    status: str
    progress: int
    current_step: str
    steps: List[str]
    start_time: str
    end_time: Optional[str] = None
    error_message: Optional[str] = None


# ── Helpers ───────────────────────────────────────────────────────────

async def execute_travel_planning(request: Dict[str, Any], callback: callable):
    try:
        planner = get_travel_planner()
        skip_ai = request.get('skip_ai_suggestions', True)
        result = await planner.create_travel_plan(request, callback, skip_ai_suggestions=skip_ai)
        pid = request['plan_id']
        if pid in progress_callbacks:
            try:
                json.dumps(result, default=str)
            except TypeError as e:
                logger.warning(f"规划结果不可序列化: {e}")
                result = {"error": "result_serialization_failed", "raw_type": str(type(result))}
            progress_callbacks[pid]['result'] = result
            progress_callbacks[pid]['status'] = 'completed'
            progress_callbacks[pid]['progress'] = 100
            progress_callbacks[pid]['end_time'] = datetime.now().isoformat()
        logger.info(f"规划任务完成: {pid}")
    except Exception as e:
        logger.error(f"规划执行异常: {str(e)}")
        pid = request.get('plan_id')
        if pid in progress_callbacks:
            progress_callbacks[pid].update({'status': 'error', 'error_message': str(e)})


async def cleanup_temp_file(path: str):
    await asyncio.sleep(60)
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


# ── Routes ────────────────────────────────────────────────────────────

@travel_router.post("/create", summary="创建规划", response_model=PlanResponse)
async def create_travel_plan(request: TravelPlanRequest, background_tasks: BackgroundTasks,
                              current_user: TokenData = Depends(get_current_user_from_session)):
    """创建新的旅游规划任务"""
    try:
        plan_id = f"plan_{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"收到旅游规划请求: {plan_id}, 用户: {current_user.user_id}, 非遗项目: {request.heritage_ids}")

        planning_request = request.model_dump()
        planning_request['plan_id'] = plan_id

        progress_callbacks[plan_id] = {
            'status': 'processing',
            'progress': 5,
            'current_step': '正在启动规划引擎...',
            'steps': ['分析非遗项目', '获取天气信息', '生成AI建议', '路径规划计算', '生成路书', '完成'],
            'start_time': datetime.now().isoformat()
        }

        async def progress_callback(pid: str, pdata: Dict[str, Any]):
            progress_callbacks[pid] = pdata

        background_tasks.add_task(execute_travel_planning, planning_request, progress_callback)

        return PlanResponse(
            success=True,
            plan_id=plan_id,
            message="旅游规划任务已启动",
            data={"plan_id": plan_id, "travel_days": request.travel_days}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建规划失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@travel_router.get("/progress/{plan_id}", summary="规划进度", response_model=ProgressResponse)
async def get_planning_progress(plan_id: str, current_user: TokenData = Depends(get_current_user_from_session)):
    """查询旅游规划的生成进度"""
    logger.info(f"[进度查询] 收到请求: plan_id={plan_id}")

    if plan_id in progress_callbacks:
        data = progress_callbacks[plan_id]
        logger.info(f"[进度查询] 从 callbacks 找到: {data.get('progress')}% - {data.get('status')}")
        return ProgressResponse(
            plan_id=plan_id,
            status=data.get('status', 'unknown'),
            progress=data.get('progress', 0),
            current_step=data.get('current_step', ''),
            steps=data.get('steps', []),
            start_time=data.get('start_time', ''),
            end_time=data.get('end_time'),
            error_message=data.get('error_message')
        )
    planner = get_travel_planner()
    data = planner.get_planning_progress(plan_id)
    logger.info(f"[进度查询] 从 planner 获取: {data}")
    if data.get('status') != 'not_found':
        return ProgressResponse(
            plan_id=plan_id,
            status=data.get('status', 'unknown'),
            progress=data.get('progress', 0),
            current_step=data.get('current_step', ''),
            steps=data.get('steps', []),
            start_time=data.get('start_time', ''),
            end_time=data.get('end_time'),
            error_message=data.get('error_message')
        )
    raise HTTPException(status_code=404, detail="规划不存在")


@travel_router.get("/progress-stream/{plan_id}", summary="规划进度流（SSE）")
async def get_planning_progress_stream(plan_id: str, current_user: TokenData = Depends(get_current_user_from_session)):
    """使用 Server-Sent Events (SSE) 实时推送旅游规划的生成进度"""
    logger.info(f"[进度流] 收到SSE连接请求: plan_id={plan_id}")

    async def event_generator():
        last_progress = -1
        while True:
            if plan_id in progress_callbacks:
                data = progress_callbacks[plan_id]
                current_progress = data.get('progress', 0)
                if current_progress != last_progress:
                    logger.info(f"[进度流] 发送进度: {current_progress}% - {data.get('current_step')}")
                    yield f"data: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"
                    last_progress = current_progress
                if data.get('status') in ['completed', 'error']:
                    logger.info(f"[进度流] 任务完成，断开连接: {data.get('status')}")
                    break
            else:
                logger.warning(f"[进度流] plan_id 不存在: {plan_id}")
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@travel_router.get("/result/{plan_id}", summary="规划结果")
async def get_planning_result(plan_id: str, current_user: TokenData = Depends(get_current_user_from_session)):
    """获取已完成的旅游规划结果"""
    if plan_id in progress_callbacks:
        data = progress_callbacks[plan_id]
        if data.get('status') == 'completed':
            return {"success": True, "plan_id": plan_id, "data": data['result']}
        elif data.get('status') == 'error':
            return {"success": False, "plan_id": plan_id, "error": data.get('error_message')}
        else:
            return {"success": False, "status": data.get('status'), "message": "规划进行中"}
    raise HTTPException(status_code=404, detail="结果不存在")


@travel_router.post("/cancel/{plan_id}", summary="取消规划")
async def cancel_planning(plan_id: str, current_user: TokenData = Depends(get_current_user_from_session)):
    """取消正在进行的旅游规划任务"""
    logger.info(f"[取消规划] 收到取消请求: plan_id={plan_id}")

    if plan_id in progress_callbacks:
        data = progress_callbacks[plan_id]
        if data.get('status') == 'processing':
            progress_callbacks[plan_id].update({
                'status': 'cancelled',
                'progress': data.get('progress', 0),
                'current_step': '规划已取消',
                'end_time': datetime.now().isoformat()
            })
            logger.info(f"[取消规划] 规划已取消: {plan_id}")
            return {"success": True, "message": "规划已取消"}
        else:
            logger.warning(f"[取消规划] 规划状态不允许取消: {data.get('status')}")
            return {"success": False, "message": f"规划状态为 {data.get('status')}，无法取消"}
    else:
        logger.warning(f"[取消规划] 规划不存在: {plan_id}")
        raise HTTPException(status_code=404, detail="规划不存在")


@travel_router.post("/export/{plan_id}", summary="导出规划")
async def export_travel_plan(plan_id: str, export_request: ExportRequest,
                              background_tasks: BackgroundTasks = None,
                              current_user: TokenData = Depends(get_current_user_from_session)):
    """导出旅游规划为PDF或JSON格式"""
    try:
        result = None
        if plan_id in progress_callbacks and progress_callbacks[plan_id].get('status') == 'completed':
            result = progress_callbacks[plan_id]['result']
        if not result:
            planner = get_travel_planner()
            result = planner.get_planning_result(plan_id)

        if not result:
            raise HTTPException(status_code=404, detail="规划数据未找到")

        from Agent.agent import get_plan_editor
        get_plan_editor()

        final_plan_data = result
        conversation_history = []

        try:
            from Agent.memory.session import get_session_pool
            session_pool = get_session_pool()
            all_sessions = getattr(session_pool, 'sessions', {})
            if not all_sessions and hasattr(session_pool, '_redis_client'):
                all_sessions = {}
            for sess_id, sess in all_sessions.items():
                if getattr(sess, 'plan_id', None) == plan_id:
                    final_plan_data = sess.current_plan if hasattr(sess, 'current_plan') and sess.current_plan else result
                    if hasattr(sess, 'conversation_history') and sess.conversation_history:
                        conversation_history = [
                            {"role": t.get('role', ''), "content": t.get('content', '')}
                            for t in sess.conversation_history
                            if isinstance(t, dict) and 'role' in t and 'content' in t
                        ]
                        final_plan_data['conversation_history'] = conversation_history
                    logger.info(f"使用活跃会话数据导出: {sess_id}")
                    break
        except Exception as e:
            logger.debug(f"查找活跃会话失败（使用原始数据）: {e}")

        fmt = export_request.format.lower()
        if fmt == "pdf":
            from Agent.services.pdf_content_integrator import PDFContentIntegrator
            from Agent.services.minio_storage import get_minio_service

            planner = get_travel_planner()
            integrator = PDFContentIntegrator(llm_model=planner.llm_model)

            file_response = await integrator.integrate_and_export(
                plan_data=final_plan_data,
                conversation_history=conversation_history,
                output_filename=None
            )

            if file_response.get('success'):
                path = file_response.get('pdf_path')
                minio_url = None
                try:
                    with open(path, 'rb') as f:
                        pdf_bytes = f.read()
                    minio_service = get_minio_service()
                    upload_result = minio_service.upload_pdf(
                        username=current_user.username,
                        pdf_bytes=pdf_bytes,
                        metadata={
                            "destination": final_plan_data.get("basic_info", {}).get("destination", "unknown"),
                            "title": final_plan_data.get("basic_info", {}).get("title", f"Plan {plan_id}"),
                            "exported_by": current_user.user_id,
                            "plan_id": plan_id
                        }
                    )
                    if upload_result.get('success'):
                        minio_url = upload_result.get('url')
                        logger.info(f"PDF已上传到MinIO: {upload_result.get('object_path')}")
                except Exception as e:
                    logger.error(f"MinIO上传失败: {str(e)}")

                if background_tasks:
                    background_tasks.add_task(cleanup_temp_file, path)

                headers = {"Content-Disposition": f'attachment; filename="plan_{plan_id}.pdf"'}
                if minio_url:
                    headers["X-MinIO-URL"] = minio_url
                    headers["X-MinIO-Status"] = "success"
                else:
                    headers["X-MinIO-Status"] = "failed"

                return FileResponse(path, filename=f"plan_{plan_id}.pdf", media_type='application/pdf', headers=headers)
            else:
                raise HTTPException(status_code=500, detail="PDF生成失败")

        elif fmt == "json":
            import tempfile
            fd, path = tempfile.mkstemp(suffix=".json")
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(final_plan_data, f, ensure_ascii=False, indent=2)
            if background_tasks:
                background_tasks.add_task(cleanup_temp_file, path)
            return FileResponse(path, filename=f"plan_{plan_id}.json", media_type='application/json')

        else:
            raise HTTPException(status_code=400, detail="不支持的格式")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
