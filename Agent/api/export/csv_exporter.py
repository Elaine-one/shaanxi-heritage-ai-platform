# -*- coding: utf-8 -*-
"""
CSV导出模块
负责处理旅游规划的CSV导出功能
"""

import csv
import tempfile
import os
from io import StringIO
from datetime import datetime
from typing import Dict, Any
from loguru import logger
from fastapi import HTTPException
from fastapi.responses import FileResponse


class CSVExporter:
    """
    CSV导出器类，负责处理CSV导出的核心逻辑
    """
    
    def __init__(self):
        """
        初始化CSV导出器
        """
        logger.info("CSV导出器初始化完成")
    
    async def export_as_csv(self, plan_id: str, result: Dict[str, Any]) -> FileResponse:
        """
        导出为CSV格式
        
        Args:
            plan_id (str): 规划ID
            result (Dict[str, Any]): 规划结果
        
        Returns:
            FileResponse: CSV文件响应
        """
        try:
            # 使用StringIO创建CSV内容
            output = StringIO()
            writer = csv.writer(output)
            
            # 写入标题
            writer.writerow(['非遗旅游规划详情'])
            writer.writerow([])
            
            # 写入基本信息
            writer.writerow(['基本信息'])
            writer.writerow(['项目', '内容'])
            
            # 处理基本信息
            if 'basic_info' in result:
                basic_info = result['basic_info']
                for key, value in basic_info.items():
                    writer.writerow([key, str(value)])
            
            writer.writerow([])
            
            # 写入行程安排
            writer.writerow(['行程安排'])
            writer.writerow(['天数', '日期', '景点名称', '类型', '预计时长', '描述'])
            
            if 'itinerary' in result:
                itinerary = result['itinerary']
                for day_plan in itinerary:
                    day = day_plan.get('day', '')
                    date = day_plan.get('date', '')
                    items = day_plan.get('items', [])
                    
                    for item in items:
                        writer.writerow([
                            day,
                            date,
                            item.get('name', ''),
                            item.get('type', ''),
                            f"{item.get('visit_duration', 0)}小时",
                            item.get('description', '')
                        ])
            
            # 获取CSV内容
            csv_content = output.getvalue()
            output.close()
            
            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig')
            temp_file.write(csv_content)
            temp_file.close()
            
            filename = f"travel_plan_{plan_id}.csv"
            
            return FileResponse(
                path=temp_file.name,
                filename=filename,
                media_type='text/csv; charset=utf-8',
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
            
        except Exception as e:
            # 清理临时文件
            if 'temp_file' in locals():
                temp_file.close()
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
            if 'output' in locals():
                output.close()
            
            logger.error(f"导出为CSV时发生错误: {str(e)}")
            raise HTTPException(status_code=500, detail=f"CSV导出失败: {str(e)}")


# 创建全局CSV导出器实例
csv_exporter = CSVExporter()

def get_csv_exporter() -> CSVExporter:
    """
    获取CSV导出器实例
    
    Returns:
        CSVExporter: CSV导出器实例
    """
    return csv_exporter
