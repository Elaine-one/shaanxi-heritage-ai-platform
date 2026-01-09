# -*- coding: utf-8 -*-
"""
PDF导出模块
负责处理旅游规划的PDF导出功能
"""

import tempfile
import os
from io import BytesIO
from datetime import datetime
from typing import Dict, Any, List
from loguru import logger
from fastapi import HTTPException
from fastapi.responses import FileResponse

from Agent.services.pdf_content_integrator import PDFContentIntegrator
from Agent.main import get_agent


class PDFExporter:
    """
    PDF导出器类，负责处理PDF导出的核心逻辑
    """
    
    def __init__(self):
        """
        初始化PDF导出器
        """
        self.integrator = None
        logger.info("PDF导出器初始化完成")
    
    async def _initialize_integrator(self):
        """
        初始化PDF内容整合器
        """
        try:
            agent = get_agent()
            ali_model = agent.ali_model if hasattr(agent, 'ali_model') else None
            self.integrator = PDFContentIntegrator(ali_model=ali_model)
            logger.info("PDF内容整合器初始化完成")
        except Exception as e:
            logger.error(f"初始化PDF内容整合器失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"PDF导出服务初始化失败: {str(e)}")
    
    async def export_plan_pdf(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        导出旅游规划为PDF格式
        
        Args:
            plan_data (Dict[str, Any]): 规划数据
        
        Returns:
            Dict[str, Any]: 导出结果，包含success和pdf_path字段
        """
        try:
            if not self.integrator:
                await self._initialize_integrator()
            
            # 使用传递的对话历史，如果没有则创建基本的历史
            conversation_history = plan_data.get('conversation_history', [])
            
            # 如果没有对话历史但有ai_descriptions，则创建基本历史（向后兼容）
            if not conversation_history and plan_data.get('ai_descriptions'):
                for desc in plan_data['ai_descriptions']:
                    conversation_history.append({
                        'role': 'assistant',
                        'content': desc,
                        'timestamp': datetime.now().isoformat()
                    })
                
                if plan_data.get('ai_summary'):
                    conversation_history.append({
                        'role': 'assistant', 
                        'content': f"总结: {plan_data['ai_summary']}",
                        'timestamp': datetime.now().isoformat()
                    })
            
            # 生成唯一的文件名
            plan_id = plan_data.get('plan_id', f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            output_filename = f"travel_plan_{plan_id}.pdf"
            
            # 执行PDF导出
            export_result = await self.integrator.integrate_and_export(
                plan_data=plan_data,
                conversation_history=conversation_history,
                output_filename=output_filename
            )
            
            if export_result.get('success'):
                logger.info(f"PDF导出成功: {export_result.get('pdf_path')}")
                return export_result
            else:
                logger.warning(f"PDF导出失败: {export_result.get('message')}")
                raise HTTPException(status_code=500, detail=f"PDF导出失败: {export_result.get('message')}")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"导出PDF时发生错误: {str(e)}")
            raise HTTPException(status_code=500, detail=f"PDF导出失败: {str(e)}")
    
    async def export_as_pdf(self, plan_id: str, result: Dict[str, Any]) -> FileResponse:
        """
        导出为PDF格式（传统接口）
        
        Args:
            plan_id (str): 规划ID
            result (Dict[str, Any]): 规划结果
        
        Returns:
            FileResponse: PDF文件响应
        """
        try:
            # 使用统一的PDF导出逻辑
            export_result = await self.export_plan_pdf(result)
            
            if export_result.get('success'):
                pdf_path = export_result.get('pdf_path')
                
                if pdf_path and os.path.exists(pdf_path):
                    # 确保文件名使用正确的编码
                    destination = result.get('destination', '旅游规划')
                    safe_filename = f"{destination}_{plan_id}.pdf".replace('/','_').replace('\\','_').replace(':','_')
                    
                    # 正确处理中文文件名，使用FastAPI内置的filename参数，它会自动处理编码
                    return FileResponse(
                        path=pdf_path,
                        filename=safe_filename,
                        media_type='application/pdf',
                        headers={
                            "Content-Type": "application/pdf",
                            "Cache-Control": "no-cache, no-store, must-revalidate",
                            "Pragma": "no-cache",
                            "Expires": "0"
                        }
                    )
                else:
                    logger.error(f"PDF文件不存在: {pdf_path}")
                    raise HTTPException(status_code=500, detail="PDF文件生成失败")
                    
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"导出为PDF时发生错误: {str(e)}")
            raise HTTPException(status_code=500, detail=f"PDF导出失败: {str(e)}")


# 创建全局PDF导出器实例
pdf_exporter = PDFExporter()

def get_pdf_exporter() -> PDFExporter:
    """
    获取PDF导出器实例
    
    Returns:
        PDFExporter: PDF导出器实例
    """
    return pdf_exporter
