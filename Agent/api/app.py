# -*- coding: utf-8 -*-
"""
FastAPI应用主文件
提供旅游规划的HTTP API接口
"""

import asyncio
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks
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
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 2. 添加当前 api 目录到Python路径 (用于引用 edit_endpoints, weather_endpoints 等同级模块)
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))
# --- 关键路径修复结束 ---

from main import get_agent
from core.travel_planner import get_travel_planner
from utils.logger_config import setup_logger

# 导入路由
try:
    from edit_endpoints import edit_router
    from weather_endpoints import router as weather_router
except ImportError as e:
    logger.warning(f"尝试相对导入失败，使用绝对路径: {e}")
    from api.edit_endpoints import edit_router
    from api.weather_endpoints import router as weather_router

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
    title="智能旅游规划Agent API",
    description="基于非遗文化的智能旅游规划服务",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由器
app.include_router(edit_router)
app.include_router(weather_router)

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
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/travel-plan/create", response_model=PlanResponse)
async def create_travel_plan(request: TravelPlanRequest, background_tasks: BackgroundTasks):
    """创建旅游规划任务"""
    try:
        plan_id = f"plan_{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"收到旅游规划请求: {plan_id}, 非遗项目: {request.heritage_ids}")
        
        planning_request = request.dict()
        planning_request['plan_id'] = plan_id
        
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

@app.get("/api/travel-plan/progress/{plan_id}", response_model=ProgressResponse)
async def get_planning_progress(plan_id: str):
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

@app.get("/api/travel-plan/result/{plan_id}")
async def get_planning_result(plan_id: str):
    if plan_id in progress_callbacks:
        data = progress_callbacks[plan_id]
        if data.get('status') == 'completed':
            return {"success": True, "plan_id": plan_id, "data": data['result']}
        elif data.get('status') == 'error':
            return {"success": False, "plan_id": plan_id, "error": data.get('error_message')}
        else:
            return {"success": False, "status": data.get('status'), "message": "规划进行中"}
    raise HTTPException(status_code=404, detail="结果不存在")

# --- 核心导出接口（AI 增强版） ---
@app.post("/api/agent/export_plan_pdf")
async def export_plan_pdf(request: PDFExportRequest, background_tasks: BackgroundTasks):
    """
    AI编辑后的PDF导出专用接口
    直接使用前端传入的最新数据（含对话历史），确保所见即所得
    """
    try:
        logger.info(f"收到AI PDF导出请求，目的地: {request.destination}")
        
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
        from core.pdf_content_integrator import PDFContentIntegrator
        from core.travel_planner import get_travel_planner
        
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
            background_tasks.add_task(cleanup_temp_file, path)
            filename = f"TravelPlan_{request.destination}_{datetime.now().strftime('%H%M%S')}.pdf"
            
            # 使用 FileResponse 返回文件流
            return FileResponse(
                path=path, 
                filename=filename, 
                media_type='application/pdf'
            )
        else:
            raise HTTPException(status_code=500, detail=file_response.get('error', '生成失败'))

    except Exception as e:
        logger.error(f"AI导出失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# 传统的导出接口 (保留用于兼容)
@app.post("/api/travel-plan/export/{plan_id}")
async def export_travel_plan(plan_id: str, export_request: ExportRequest, background_tasks: BackgroundTasks = None):
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
        from core.plan_editor import get_plan_editor
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
            from core.pdf_content_integrator import PDFContentIntegrator
            from core.travel_planner import get_travel_planner
            planner = get_travel_planner()
            integrator = PDFContentIntegrator(ali_model=planner.ali_model)
            
            file_response = await integrator.integrate_and_export(
                plan_data=final_plan_data,
                conversation_history=conversation_history,
                output_filename=None
            )
            
            if file_response.get('success'):
                path = file_response.get('pdf_path')
                if background_tasks: background_tasks.add_task(cleanup_temp_file, path)
                return FileResponse(path, filename=f"plan_{plan_id}.pdf", media_type='application/pdf')
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

@app.post("/api/agent/chat")
async def agent_chat(request: Dict[str, Any]):
    try:
        msg = request.get('message', '')
        sid = request.get('session_id', str(uuid.uuid4()))
        agent = get_agent()
        resp = await agent.process_message(msg, sid)
        return {"success": True, "data": resp, "session_id": sid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/travel-plan/{plan_id}")
async def delete_plan(plan_id: str):
    if plan_id in progress_callbacks:
        del progress_callbacks[plan_id]
        return {"success": True}
    raise HTTPException(status_code=404)

@app.get("/api/travel-plan/list")
async def list_plans():
    plans = [{"plan_id": k, "status": v.get('status')} for k, v in progress_callbacks.items()]
    return {"success": True, "data": {"total": len(plans), "plans": plans}}

if __name__ == "__main__":
    import uvicorn
    os.makedirs("logs", exist_ok=True)
    os.makedirs("pdf_cache", exist_ok=True)
    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=True)