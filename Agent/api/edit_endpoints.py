# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from loguru import logger
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import uuid

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from Agent.api.session_dependencies import get_current_user_from_session, TokenData

edit_router = APIRouter(prefix='/api/agent', tags=['规划编辑'])

_pdf_tasks: Dict[str, Dict[str, Any]] = {}
_pdf_async_tasks: Dict[str, asyncio.Task] = {}


def _get_session_pool():
    from Agent.memory.session_provider import get_session_pool
    return get_session_pool()


def _get_plan_editor():
    from Agent.agent.plan_editor import get_plan_editor
    return get_plan_editor()


def _verify_session_owner(session_id: str, current_user_id: str):
    """验证会话归属，非本人会话返回 403"""
    session_pool = _get_session_pool()
    session = session_pool.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")
    if session.user_id is not None and str(session.user_id) != str(current_user_id):
        logger.warning(f"用户 {current_user_id} 尝试访问非本人会话 {session_id} (owner={session.user_id})")
        raise HTTPException(status_code=403, detail="无权访问此会话")
    if session.user_id is None:
        session_pool.update_session_user_id(session_id, current_user_id)
        logger.info(f"会话 {session_id} 未绑定用户，已绑定到 {current_user_id}")
    return session


async def _run_pdf_export(task_id: str, session_id: str, output_filename: Optional[str], user_id: str, username: str):
    """后台执行 PDF 生成任务"""
    _pdf_tasks[task_id]['status'] = 'processing'
    try:
        session_pool = _get_session_pool()
        session = session_pool.get_session(session_id)
        if not session:
            _pdf_tasks[task_id] = {'status': 'failed', 'error': '会话不存在或已过期'}
            return

        current_plan = session.current_plan
        conversation_history = session.conversation_history

        _pdf_tasks[task_id]['progress'] = 20
        logger.info(f"PDF任务 {task_id}: 开始生成，对话历史 {len(conversation_history)} 条")

        from Agent.services.pdf_content_integrator import PDFContentIntegrator
        from Agent.agent import get_travel_planner

        travel_planner = get_travel_planner()
        if not travel_planner.llm_model:
            _pdf_tasks[task_id] = {'status': 'failed', 'error': 'AI模型未初始化'}
            return

        pdf_integrator = PDFContentIntegrator(llm_model=travel_planner.llm_model)
        plan_data = {**current_plan, 'conversation_history': conversation_history}

        _pdf_tasks[task_id]['progress'] = 30

        result = await pdf_integrator.integrate_and_export(
            plan_data=plan_data,
            conversation_history=conversation_history,
            output_filename=output_filename
        )

        if not result['success']:
            _pdf_tasks[task_id] = {'status': 'failed', 'error': result.get('error', '生成失败')}
            logger.warning(f"PDF任务 {task_id}: 生成失败 - {result.get('error')}")
            return

        pdf_url = await _upload_and_cleanup_pdf(result, user_id, username, session_id, len(conversation_history), current_plan, session)

        _persist_export_to_graph(user_id, username, current_plan, session_id)

        _pdf_tasks[task_id] = {
            'status': 'completed',
            'progress': 100,
            'pdf_url': pdf_url,
            'filename': result.get('filename', output_filename or '定制路书.pdf'),
            'message': f"已根据您的{len(conversation_history)}条对话记录定制生成"
        }
        logger.info(f"PDF任务 {task_id}: 生成成功, pdf_url={'有' if pdf_url else '无'}")

    except asyncio.CancelledError:
        _pdf_tasks[task_id] = {'status': 'cancelled', 'error': '任务被取消'}
        logger.info(f"PDF任务 {task_id}: 已被取消")
    except Exception as e:
        import traceback
        _pdf_tasks[task_id] = {'status': 'failed', 'error': str(e)}
        logger.error(f"PDF任务 {task_id}: 异常 - {str(e)}\n{traceback.format_exc()}")
    finally:
        _pdf_async_tasks.pop(task_id, None)


async def _upload_and_cleanup_pdf(result: Dict[str, Any], user_id: str, username: str, session_id: str, msg_count: int, current_plan: Dict = None, session=None) -> str:
    import os
    pdf_path = result.get('pdf_path', '')
    if not pdf_path or not os.path.exists(pdf_path):
        raise RuntimeError(f"PDF本地文件不存在: {pdf_path}")

    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()

    destination = ""
    if current_plan:
        basic_info = current_plan.get('basic_info', {})
        destination = basic_info.get('destination', '') or basic_info.get('departure', '')
        logger.debug(f"PDF destination from basic_info: '{destination}', basic_info keys: {list(basic_info.keys()) if basic_info else 'NONE'}")
    if not destination and session:
        destination = getattr(session, 'departure_location', '') or ''
        logger.debug(f"PDF destination from session.departure_location: '{destination}'")
    if not destination and current_plan:
        for item in current_plan.get('heritage_items', []):
            region = item.get('region', '')
            if region:
                destination = region
                break
        logger.debug(f"PDF destination from heritage_items region: '{destination}'")
    if not destination:
        destination = "unknown"
    logger.info(f"PDF destination final: '{destination}'")

    from Agent.services.minio_storage import get_minio_service
    minio_service = get_minio_service()
    upload_result = await asyncio.to_thread(
        minio_service.upload_pdf,
        username=username,
        pdf_bytes=pdf_bytes,
        metadata={
            "exported_by": username,
            "user_id": str(user_id),
            "session_id": session_id,
            "message_count": str(msg_count),
            "destination": destination,
        }
    )

    if not upload_result.get('success'):
        _cleanup_local_file(pdf_path)
        raise RuntimeError(f"MinIO上传失败: {upload_result.get('error')}")

    logger.info(f"PDF已上传MinIO: {upload_result.get('object_path')}")
    _cleanup_local_file(pdf_path)
    return upload_result.get('url', '')


def _cleanup_local_file(path: str):
    """删除本地临时PDF文件"""
    import os
    try:
        if os.path.exists(path):
            os.remove(path)
            logger.info(f"已删除本地临时文件: {path}")
    except Exception as e:
        logger.warning(f"删除本地临时文件失败: {path}, {e}")


def _persist_export_to_graph(user_id: str, username: str, current_plan: Dict[str, Any], session_id: str):
    try:
        from Agent.memory.l2_graph_store import get_l2_graph_store
        l2_store = get_l2_graph_store()
        if not l2_store.is_available() or not user_id:
            return
        heritage_ids = []
        for item in current_plan.get('heritage_items', []):
            hid = item.get('id')
            if hid is not None:
                try:
                    heritage_ids.append(int(hid))
                except (ValueError, TypeError):
                    pass
        if heritage_ids:
            l2_store.cleanup_user_planned_relations(user_id)
            l2_store.batch_link_heritages(
                user_id=user_id,
                heritage_ids=heritage_ids,
                rel_type="EXPORTED",
                source="pdf_export",
                extra_props={
                    "session_id": session_id,
                },
            )
            logger.info(f"导出非遗沉淀到图谱(已清理旧PLANNED): user={user_id}, count={len(heritage_ids)}")
    except Exception as e:
        logger.debug(f"导出非遗沉淀到图谱失败（不影响主流程）: {e}")


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
        
        logger.info(
            f"start_edit_session: plan_id={plan_id}, user_id={current_user.user_id}, "
            f"plan_data_keys={list(plan_data.keys())}, "
            f"heritage_items_count={len(plan_data.get('heritage_items', []))}, "
            f"departure={plan_data.get('basic_info', {}).get('departure', 'N/A')}"
        )

        session_pool = _get_session_pool()
        session = await session_pool.create_session(
            plan_id=plan_id,
            original_plan=plan_data,
            user_id=current_user.user_id,
            username=current_user.username
        )

        logger.info(f"编辑会话已创建: {session.session_id}, 出发地: {session.departure_location}, 人数: {session.group_size}")

        return EditResponse(success=True, session_id=session.session_id, message='编辑会话已启动')
    except Exception as e:
        import traceback
        logger.error(f"start_edit_session 启动错误: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f'服务器内部错误: {str(e)}')


@edit_router.post('/export_pdf', summary="导出PDF(异步)", response_model=EditResponse)
async def export_plan_pdf(request: ExportPdfRequest, current_user: TokenData = Depends(get_current_user_from_session)):
    """提交 PDF 导出任务，立即返回 task_id，前端轮询 /export_pdf_status 查询进度"""
    try:
        _verify_session_owner(request.session_id, current_user.user_id)

        for task_id, task in _pdf_tasks.items():
            if task.get('session_id') == request.session_id and task.get('status') in ('submitted', 'processing'):
                return EditResponse(success=True, status=task.get('status'), message=task_id)

        task_id = f"pdf_{uuid.uuid4().hex[:12]}"
        _pdf_tasks[task_id] = {
            'status': 'submitted',
            'progress': 0,
            'session_id': request.session_id,
            'created_at': datetime.now().isoformat(),
        }

        async_task = asyncio.create_task(_run_pdf_export(
            task_id=task_id,
            session_id=request.session_id,
            output_filename=request.output_filename,
            user_id=current_user.user_id,
            username=current_user.username,
        ))
        _pdf_async_tasks[task_id] = async_task

        logger.info(f"PDF导出任务已提交: task_id={task_id}, session_id={request.session_id}")
        return EditResponse(success=True, status='submitted', message=task_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"提交PDF导出任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"提交PDF导出任务失败: {str(e)}")


@edit_router.get('/export_pdf_status', summary="PDF导出状态", response_model=EditResponse)
async def export_pdf_status(task_id: str, current_user: TokenData = Depends(get_current_user_from_session)):
    """查询 PDF 导出任务状态"""
    task = _pdf_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return EditResponse(
        success=True,
        status=task.get('status', 'unknown'),
        message=task.get('message', task.get('error', '')),
        summary=task.get('pdf_url', ''),
        changes=task,
    )


@edit_router.get('/session_export_status', summary="会话导出状态")
async def session_export_status(session_id: str, current_user: TokenData = Depends(get_current_user_from_session)):
    """根据 session_id 查询当前关联的导出任务状态，前端无需存储 task_id"""
    _cleanup_old_tasks()

    latest_task = None
    latest_task_id = None
    latest_created = ''

    for task_id, task in _pdf_tasks.items():
        if task.get('session_id') != session_id:
            continue
        status = task.get('status', '')
        if status in ('submitted', 'processing', 'completed'):
            created = task.get('created_at', '')
            if created >= latest_created:
                latest_created = created
                latest_task = task
                latest_task_id = task_id

    if latest_task:
        return {
            'has_task': True,
            'task_id': latest_task_id,
            'status': latest_task.get('status'),
            'progress': latest_task.get('progress', 0),
            'filename': latest_task.get('filename', '定制路书.pdf'),
            'error': latest_task.get('error', ''),
        }

    return {'has_task': False, 'task_id': None, 'status': None, 'progress': 0}


def _cleanup_old_tasks():
    """清理超过1小时的已完成/失败/取消的任务，防止内存泄漏"""
    now = datetime.now()
    expired_ids = []
    for task_id, task in _pdf_tasks.items():
        if task.get('status') in ('completed', 'failed', 'cancelled'):
            created_str = task.get('created_at', '')
            if created_str:
                try:
                    created = datetime.fromisoformat(created_str)
                    if (now - created).total_seconds() > 3600:
                        expired_ids.append(task_id)
                except (ValueError, TypeError):
                    expired_ids.append(task_id)
    for task_id in expired_ids:
        del _pdf_tasks[task_id]
        _pdf_async_tasks.pop(task_id, None)
    if expired_ids:
        logger.info(f"清理了 {len(expired_ids)} 个过期PDF任务")


@edit_router.get('/download_pdf/{task_id}', summary="下载PDF文件")
async def download_pdf(task_id: str, current_user: TokenData = Depends(get_current_user_from_session)):
    """下载 PDF 文件，设置 Content-Disposition: attachment 触发浏览器自动下载"""
    task = _pdf_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.get('status') != 'completed':
        raise HTTPException(status_code=400, detail="PDF尚未生成完成")

    pdf_url = task.get('pdf_url', '')
    filename = task.get('filename', '定制路书.pdf')

    if not pdf_url:
        raise HTTPException(status_code=404, detail="PDF文件不可用")

    import httpx
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(pdf_url)
            if response.status_code != 200:
                raise HTTPException(status_code=502, detail="无法获取PDF文件")

        from fastapi.responses import Response
        return Response(
            content=response.content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(response.content)),
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF下载失败: {e}")
        raise HTTPException(status_code=500, detail=f"PDF下载失败: {str(e)}")


@edit_router.get('/health', summary="服务状态", response_model=EditResponse)
async def health_check():
    """检查编辑服务运行状态"""
    return EditResponse(success=True, status='healthy', message='编辑服务运行正常')


@edit_router.get('/get_edit_history', summary="编辑历史", response_model=EditResponse)
async def get_edit_history(session_id: str, current_user: TokenData = Depends(get_current_user_from_session)):
    """获取会话的编辑历史记录"""
    return EditResponse(success=True, history=[], message='暂不提供详细历史')


@edit_router.get('/get_available_operations', summary="可用操作", response_model=EditResponse)
async def get_available_operations(current_user: TokenData = Depends(get_current_user_from_session)):
    """获取可用的编辑操作列表"""
    return EditResponse(success=True, operations=[], message='获取成功')


@edit_router.get('/get_plan_summary', summary="规划摘要", response_model=EditResponse)
async def get_plan_summary(session_id: str, current_user: TokenData = Depends(get_current_user_from_session)):
    """获取当前规划的摘要信息"""
    _verify_session_owner(session_id, current_user.user_id)
    return EditResponse(success=True, summary="摘要", message='获取成功')


@edit_router.get('/session_info', summary="会话信息")
async def get_session_info(session_id: str, current_user: TokenData = Depends(get_current_user_from_session)):
    """获取编辑会话的详细信息，用于调试和管理"""
    _verify_session_owner(session_id, current_user.user_id)
    plan_editor = _get_plan_editor()
    return plan_editor.get_session_info(session_id)


@edit_router.post('/end_edit_session', summary="结束编辑", response_model=EditResponse)
async def end_edit_session(request: EndSessionRequest, current_user: TokenData = Depends(get_current_user_from_session)):
    """结束编辑会话，取消关联的PDF任务，清理会话资源"""
    _verify_session_owner(request.session_id, current_user.user_id)

    cancelled_tasks = []
    for task_id, task in list(_pdf_tasks.items()):
        if task.get('session_id') == request.session_id and task.get('status') in ('submitted', 'processing'):
            async_task = _pdf_async_tasks.pop(task_id, None)
            if async_task and not async_task.done():
                async_task.cancel()
                logger.info(f"已取消异步任务: {task_id}")
            _pdf_tasks[task_id] = {'status': 'cancelled', 'error': '用户关闭编辑器'}
            cancelled_tasks.append(task_id)

    if cancelled_tasks:
        logger.info(f"会话 {request.session_id} 关闭，取消PDF任务: {cancelled_tasks}")

    session_pool = _get_session_pool()
    session_pool.remove_session(request.session_id)
    return EditResponse(success=True, message='会话已结束')


@edit_router.post('/apply_plan_changes', summary="应用修改", response_model=EditResponse)
async def apply_plan_changes(request: ApplyChangesRequest, current_user: TokenData = Depends(get_current_user_from_session)):
    """应用规划修改"""
    _verify_session_owner(request.session_id, current_user.user_id)
    return EditResponse(success=True, message='功能暂未开放')
