# -*- coding: utf-8 -*-
"""
JSON导出模块
负责处理旅游规划的JSON导出功能
"""

import json
import tempfile
import os
from datetime import datetime
from typing import Dict, Any
from loguru import logger
from fastapi import HTTPException
from fastapi.responses import FileResponse


class JSONExporter:
    """
    JSON导出器类，负责处理JSON导出的核心逻辑
    """
    
    def __init__(self):
        """
        初始化JSON导出器
        """
        logger.info("JSON导出器初始化完成")
    
    async def export_as_json(self, plan_id: str, result: Dict[str, Any]) -> FileResponse:
        """
        导出为JSON格式
        
        Args:
            plan_id (str): 规划ID
            result (Dict[str, Any]): 规划结果
        
        Returns:
            FileResponse: JSON文件响应
        """
        try:
            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
            
            # 写入JSON数据
            json.dump(result, temp_file, ensure_ascii=False, indent=2)
            temp_file.close()
            
            filename = f"travel_plan_{plan_id}.json"
            
            return FileResponse(
                path=temp_file.name,
                filename=filename,
                media_type='application/json',
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
            
        except Exception as e:
            # 清理临时文件
            if 'temp_file' in locals():
                temp_file.close()
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
            
            logger.error(f"导出为JSON时发生错误: {str(e)}")
            raise HTTPException(status_code=500, detail=f"JSON导出失败: {str(e)}")


# 创建全局JSON导出器实例
json_exporter = JSONExporter()

def get_json_exporter() -> JSONExporter:
    """
    获取JSON导出器实例
    
    Returns:
        JSONExporter: JSON导出器实例
    """
    return json_exporter
