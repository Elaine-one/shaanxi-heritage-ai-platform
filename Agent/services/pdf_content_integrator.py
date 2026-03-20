# -*- coding: utf-8 -*-
"""
PDF内容整合器
负责协调各个模块，整合旅游规划数据并生成PDF文档
使用 ReportLab 生成 PDF（不再使用 wkhtmltopdf）
"""

from typing import Dict, List, Any, Optional
from loguru import logger

from Agent.services.content_integrator import AIContentIntegrator
from Agent.utils.content_extractor import ContentExtractor

from Agent.services.pdf_generator_optimized import get_optimized_pdf_generator


class PDFContentIntegrator:
    """
    PDF内容整合器，负责协调各个模块，整合旅游规划数据并生成PDF文档
    使用 ReportLab 生成 PDF
    """
    
    def __init__(self, llm_model=None, wkhtmltopdf_path: Optional[str] = None):
        self.llm_model = llm_model
        
        self.ai_integrator = AIContentIntegrator(llm_model)
        
        self.pdf_generator = get_optimized_pdf_generator()
        self._generator_type = "ReportLab"
        
        self.content_extractor = ContentExtractor()
        
        logger.info(f"PDF内容整合器初始化完成（使用 {self._generator_type} 生成器）")
    
    async def integrate_travel_plan_content(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        整合旅游规划内容，让AI自主规划表格结构和内容
        
        Args:
            result: 原始旅游规划数据（可能是combined_data，包含plan_data和conversation_history）
            
        Returns:
            Dict: AI自主整合后的PDF内容数据
        """
        return await self.ai_integrator.integrate_travel_plan_content(result)
    
    async def generate_pdf_document(self, content: Dict[str, Any], output_filename: Optional[str] = None) -> Dict[str, Any]:
        """
        生成PDF文档
        
        Args:
            content: 整合后的内容
            output_filename: 输出文件名
            
        Returns:
            Dict: PDF生成结果
        """
        return await self.pdf_generator.generate_pdf_document(content, output_filename)
    
    async def integrate_and_export(self, plan_data: Dict[str, Any], conversation_history: List[Dict] = None, output_filename: str = None) -> Dict[str, Any]:
        """
        整合旅游规划内容并导出为PDF
        
        Args:
            plan_data: 原始旅游规划数据
            conversation_history: 对话历史记录
            output_filename: 输出文件名
            
        Returns:
            Dict: 导出结果，包含success和pdf_path字段
        """
        try:
            if conversation_history:
                logger.info(f"接收到对话历史，共 {len(conversation_history)} 条记录")
                
                valid_conversation = True
                for i, msg in enumerate(conversation_history):
                    if not isinstance(msg, dict):
                        logger.warning(f"对话历史第{i+1}条记录格式错误: 不是字典类型")
                        valid_conversation = False
                    elif 'role' not in msg or 'content' not in msg:
                        logger.warning(f"对话历史第{i+1}条记录缺少必要字段: role或content")
                        valid_conversation = False
                
                if not valid_conversation:
                    logger.error("对话历史格式验证失败，可能导致PDF内容与对话无关")
                
                if hasattr(self.ai_integrator, '_content_cache'):
                    self.ai_integrator._content_cache.clear()
                    logger.info("已清除AI内容缓存，确保使用最新的对话历史")
                
                plan_data['conversation_history'] = conversation_history
                logger.info(f"已将对话历史添加到plan_data中，共 {len(conversation_history)} 条记录")
            
            integrated_content = await self.integrate_travel_plan_content(plan_data)
            
            pdf_result = await self.generate_pdf_document(integrated_content, output_filename)
            
            return pdf_result
        except Exception as e:
            logger.error(f"整合和导出PDF时发生错误: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f"PDF导出失败: {str(e)}"
            }
    
    def format_weather_info(self, weather_info: Dict[str, Any]) -> str:
        """
        格式化天气信息为文本
        
        Args:
            weather_info: 天气信息字典
            
        Returns:
            str: 格式化后的天气信息文本
        """
        return self.content_extractor.format_weather_info(weather_info)
