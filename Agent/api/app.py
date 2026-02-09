# -*- coding: utf-8 -*-
"""
FastAPI应用主文件
提供旅游规划的HTTP API接口
"""

import asyncio
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from loguru import logger
from contextlib import asynccontextmanager

import sys
import os
from pathlib import Path

# --- 关键路径修复开始 ---
# 1. 添加项目根目录到Python路径 (用于引用 core, utils, main 等)
# 需要指向 shaanxi-heritage-ai-platform 目录，以便可以使用 from Agent.xxx import xxx
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 2. 添加当前 api 目录到Python路径 (用于引用 edit_endpoints, weather_endpoints 等同级模块)
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))
# --- 关键路径修复结束 ---

from Agent.main import get_agent
from Agent.agent.travel_planner import get_travel_planner
from Agent.utils.logger_config import setup_logger
from Agent.api.session_dependencies import get_current_user_from_session, TokenData
from Agent.config.settings import Config

# 导入路由
from api.edit_endpoints import edit_router
from api.weather_endpoints import router as weather_router
from api.conversation_endpoints import router as conversation_router

# 设置日志
setup_logger()

# 全局变量存储进度回调
progress_callbacks = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("智能旅游规划Agent API启动")
    try:
        agent = get_agent()
        planner = get_travel_planner()
        logger.info("核心组件初始化完成")
    except Exception as e:
        logger.error(f"核心组件初始化失败: {str(e)}")
    yield
    logger.info("智能旅游规划Agent API关闭")
    try:
        planner = get_travel_planner()
        planner.cleanup_old_progress(hours=1)
    except Exception:
        pass

# 创建FastAPI应用
app = FastAPI(
    title="非遗旅游规划API",
    description="基于陕西非遗文化的智能旅游规划服务",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
# 从环境变量加载允许的跨域来源，必须配置
origins_str = Config.AGENT_CORS_ALLOWED_ORIGINS
if not origins_str:
    logger.error("环境变量 AGENT_CORS_ALLOWED_ORIGINS 未配置")
    raise ValueError("Missing required environment variable: AGENT_CORS_ALLOWED_ORIGINS")

origins = [origin.strip() for origin in origins_str.split(',')]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由器
app.include_router(edit_router)
app.include_router(weather_router)
app.include_router(conversation_router)

# --- 数据模型定义 ---

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
    format: str = Field(default="json", description="导出格式 (json, csv, pdf)")

class PDFExportRequest(BaseModel):
    """PDF导出请求模型"""
    title: Optional[str] = "我的旅游规划"
    destination: Optional[str] = None
    duration: Optional[str] = None
    weather_info: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    # 关键字段：接收前端传来的完整数据（包含对话历史）
    complete_plan_data: Optional[Dict[str, Any]] = None
    ai_descriptions: Optional[List[str]] = None

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

# --- API 接口实现 ---

@app.get("/")
async def root():
    return {"message": "Agent API Running", "status": "ok"}

@app.get("/health")
async def health_check():
    """健康检查端点"""
    from Agent.memory import get_session_pool
    from Agent.memory.redis_session import RedisSessionPool
    
    health_info = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }
    
    # 检查会话存储
    try:
        session_pool = get_session_pool()
        if isinstance(session_pool, RedisSessionPool):
            redis_health = session_pool.health_check()
            health_info["components"]["session_storage"] = {
                "type": "redis",
                **redis_health
            }
        else:
            stats = session_pool.get_session_stats()
            health_info["components"]["session_storage"] = {
                "type": "memory",
                **stats
            }
    except Exception as e:
        health_info["components"]["session_storage"] = {
            "type": "unknown",
            "status": "error",
            "error": str(e)
        }
    
    return health_info

@app.post("/api/travel-plan/create", summary="创建规划", response_model=PlanResponse)
async def create_travel_plan(request: TravelPlanRequest, background_tasks: BackgroundTasks, current_user: TokenData = Depends(get_current_user_from_session)):
    """创建新的旅游规划任务"""
    try:
        plan_id = f"plan_{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"收到旅游规划请求: {plan_id}, 用户: {current_user.user_id}, 非遗项目: {request.heritage_ids}")
        
        planning_request = request.dict()
        planning_request['plan_id'] = plan_id
        
        # 立即初始化进度，避免前端首次轮询出现 404
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
    except Exception as e:
        logger.error(f"创建规划失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def execute_travel_planning(request: Dict[str, Any], callback: callable):
    try:
        planner = get_travel_planner()
        result = await planner.create_travel_plan(request, callback)
        pid = request['plan_id']
        if pid in progress_callbacks:
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

@app.get("/api/travel-plan/progress/{plan_id}", summary="规划进度", response_model=ProgressResponse)
async def get_planning_progress(plan_id: str, current_user: TokenData = Depends(get_current_user_from_session)):
    """查询旅游规划的生成进度"""
    if plan_id in progress_callbacks:
        data = progress_callbacks[plan_id]
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

@app.get("/api/travel-plan/result/{plan_id}", summary="规划结果")
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

@app.post("/api/agent/export_plan_pdf", summary="导出PDF")
async def export_plan_pdf(request: PDFExportRequest, background_tasks: BackgroundTasks, current_user: TokenData = Depends(get_current_user_from_session)):
    """将旅游规划导出为PDF文件，自动上传到对象存储"""
    try:
        logger.info(f"收到AI PDF导出请求，目的地: {request.destination}, 用户: {current_user.username}")
        
        # 1. 获取完整数据
        plan_data = request.complete_plan_data or {}
        
        # 2. 提取前端注入的对话历史
        conversation_history = plan_data.get('conversation_history', [])
        
        # 如果 plan_data 里没有，尝试从 ai_descriptions 恢复（兼容旧逻辑）
        if not conversation_history and request.ai_descriptions:
            conversation_history = [
                {'role': 'user', 'content': '导出历史摘要'}, 
                {'role': 'assistant', 'content': '\n'.join(request.ai_descriptions)}
            ]
        
        logger.info(f"导出上下文包含 {len(conversation_history)} 条对话记录")

        # 3. 执行导出
        from Agent.services.pdf_content_integrator import PDFContentIntegrator
        from Agent.agent import get_travel_planner
        from Agent.services.minio_storage import get_minio_service
        
        planner = get_travel_planner()
        integrator = PDFContentIntegrator(ali_model=planner.ali_model)
        
        # 关键：调用 integrate_and_export
        file_response = await integrator.integrate_and_export(
            plan_data=plan_data,
            conversation_history=conversation_history,
            output_filename=None
        )
        
        if file_response.get('success'):
            path = file_response.get('pdf_path')
            
            # 4. 读取PDF文件并上传到MinIO
            minio_url = None
            upload_success = False
            try:
                with open(path, 'rb') as f:
                    pdf_bytes = f.read()
                
                minio_service = get_minio_service()
                upload_result = minio_service.upload_pdf(
                    username=current_user.username,
                    pdf_bytes=pdf_bytes,
                    metadata={
                        "destination": request.destination,
                        "duration": request.duration,
                        "title": request.title,
                        "exported_by": current_user.user_id,
                        "session_id": request.session_id,
                        "message_count": len(conversation_history)
                    }
                )
                
                if upload_result.get('success'):
                    minio_url = upload_result.get('url')
                    upload_success = True
                    logger.info(f"PDF已上传到MinIO: {upload_result.get('object_path')}")
                else:
                    logger.warning(f"MinIO上传失败: {upload_result.get('error')}")
            except Exception as e:
                logger.error(f"MinIO上传过程异常: {str(e)}")

            # 5. 清理临时文件（在返回FileResponse后异步清理）
            background_tasks.add_task(cleanup_temp_file, path)
            
            filename = f"TravelPlan_{request.destination}_{datetime.now().strftime('%H%M%S')}.pdf"
            
            # 构建响应头
            headers = {
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
            if minio_url:
                headers["X-MinIO-URL"] = minio_url
                headers["X-MinIO-Status"] = "success"
            else:
                headers["X-MinIO-Status"] = "failed"
            
            # 返回PDF文件内容
            return FileResponse(
                path=path,
                filename=filename,
                media_type='application/pdf',
                headers=headers
            )
        else:
            raise HTTPException(status_code=500, detail=file_response.get('error', '生成失败'))

    except Exception as e:
        logger.error(f"AI导出失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/travel-plan/export/{plan_id}", summary="导出规划")
async def export_travel_plan(plan_id: str, export_request: ExportRequest, background_tasks: BackgroundTasks = None, current_user: TokenData = Depends(get_current_user_from_session)):
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

        # 智能查找：尝试从 PlanEditor 查找是否有该 plan_id 的活跃编辑会话
        from Agent.agent import get_plan_editor
        plan_editor = get_plan_editor()
        
        final_plan_data = result
        conversation_history = []
        
        active_session = None
        if hasattr(plan_editor, 'active_sessions'):
            for sess_id, sess_data in plan_editor.active_sessions.items():
                if sess_data.get('plan_id') == plan_id:
                    active_session = sess_data
                    break
        
        if active_session:
            logger.info(f"使用活跃会话数据导出: {active_session.get('session_id')}")
            final_plan_data = active_session.get('current_plan', result)
            conversation_history = active_session.get('conversation_history', [])
            final_plan_data['conversation_history'] = conversation_history

        fmt = export_request.format.lower()
        if fmt == "pdf":
            from Agent.services.pdf_content_integrator import PDFContentIntegrator
            from Agent.agent import get_travel_planner
            from Agent.services.minio_storage import get_minio_service

            planner = get_travel_planner()
            integrator = PDFContentIntegrator(ali_model=planner.ali_model)
            
            file_response = await integrator.integrate_and_export(
                plan_data=final_plan_data,
                conversation_history=conversation_history,
                output_filename=None
            )
            
            if file_response.get('success'):
                path = file_response.get('pdf_path')
                
                # 读取PDF并上传到MinIO
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

                if background_tasks: background_tasks.add_task(cleanup_temp_file, path)
                
                headers = {
                    "Content-Disposition": f'attachment; filename="plan_{plan_id}.pdf"'
                }
                if minio_url:
                    headers["X-MinIO-URL"] = minio_url
                    headers["X-MinIO-Status"] = "success"
                else:
                    headers["X-MinIO-Status"] = "failed"

                return FileResponse(path, filename=f"plan_{plan_id}.pdf", media_type='application/pdf', headers=headers)
            else:
                raise HTTPException(status_code=500, detail="PDF生成失败")
        
        elif fmt == "json":
            import json, tempfile
            fd, path = tempfile.mkstemp(suffix=".json")
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(final_plan_data, f, ensure_ascii=False, indent=2)
            if background_tasks: background_tasks.add_task(cleanup_temp_file, path)
            return FileResponse(path, filename=f"plan_{plan_id}.json", media_type='application/json')
            
        else:
            raise HTTPException(status_code=400, detail="不支持的格式")

    except Exception as e:
        logger.error(f"导出失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def cleanup_temp_file(path: str):
    import asyncio
    await asyncio.sleep(60)
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception: pass

@app.post("/api/agent/chat", summary="AI对话")
async def agent_chat(request: Dict[str, Any], current_user: TokenData = Depends(get_current_user_from_session)):
    """与AI助手进行对话交互"""
    try:
        msg = request.get('message', '')
        sid = request.get('session_id', str(uuid.uuid4()))
        agent = get_agent()
        resp = await agent.process_message(msg, sid)
        return {"success": True, "data": resp, "session_id": sid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/travel-plan/{plan_id}", summary="删除规划")
async def delete_plan(plan_id: str):
    """删除指定的旅游规划任务"""
    if plan_id in progress_callbacks:
        del progress_callbacks[plan_id]
        return {"success": True}
    raise HTTPException(status_code=404)

@app.get("/api/travel-plan/list", summary="规划列表")
async def list_plans():
    """获取所有旅游规划任务列表"""
    plans = [{"plan_id": k, "status": v.get('status')} for k, v in progress_callbacks.items()]
    return {"success": True, "data": {"total": len(plans), "plans": plans}}

if __name__ == "__main__":
    import uvicorn
    os.makedirs("logs", exist_ok=True)
    os.makedirs("pdf_cache", exist_ok=True)
    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=True)