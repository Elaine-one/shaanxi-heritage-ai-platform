#--- START OF FILE core/pdf_generator.py ---

# -*- coding: utf-8 -*-
"""
PDF生成器核心模块 (修复重复参数错误版)
负责将Markdown内容渲染为精美的PDF文档
"""

import os
import re
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger

# ReportLab 相关
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT

class PDFGenerator:
    """
    PDF生成器，负责将内容渲染为PDF文档
    """
    
    def __init__(self, pdf_cache_dir: Optional[str] = None):
        self.pdf_cache_dir = pdf_cache_dir or os.path.join(os.getcwd(), 'pdf_cache')
        if not os.path.exists(self.pdf_cache_dir):
            os.makedirs(self.pdf_cache_dir)
        logger.info("PDF生成器初始化完成")
    
    async def generate_pdf_document(self, content: Dict[str, Any], output_filename: Optional[str] = None) -> Dict[str, Any]:
        """
        生成PDF文档
        """
        try:
            # 1. 路径准备
            if not output_filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_filename = f'Travel_Plan_{timestamp}.pdf'
            
            if not output_filename.endswith('.pdf'):
                output_filename += '.pdf'
            
            output_path = os.path.join(self.pdf_cache_dir, output_filename)
            logger.info(f"PDF将保存到: {output_path}")
            
            # 2. 创建PDF模板 (设置页边距，上下留白增加)
            doc = SimpleDocTemplate(
                output_path, 
                pagesize=A4,
                rightMargin=25*mm, leftMargin=25*mm, 
                topMargin=30*mm, bottomMargin=30*mm
            )
            
            story = []
            
            # 3. 字体注册
            from Agent.utils.font_manager import register_chinese_font
            chinese_font = register_chinese_font()
            if not chinese_font:
                logger.warning("未检测到中文字体，使用默认字体")
                chinese_font = 'Helvetica'
            
            # 4. 定义样式 (Design System)
            styles = getSampleStyleSheet()
            
            # 配色方案
            COLOR_PRIMARY = colors.HexColor('#2c3e50')    # 深蓝灰 (正文)
            COLOR_ACCENT = colors.HexColor('#e67e22')     # 活力橙 (强调/装饰线)
            COLOR_H1 = colors.HexColor('#8e44ad')         # 紫色 (一级标题)
            COLOR_H2 = colors.HexColor('#2980b9')         # 蓝色 (二级标题)
            COLOR_H3 = colors.HexColor('#16a085')         # 青色 (三级标题)
            COLOR_BG_QUOTE = colors.HexColor('#f4f6f7')   # 极淡灰背景 (引用块)
            
            # 主标题样式
            style_title = ParagraphStyle(
                'CustomTitle', parent=styles['Heading1'], fontName=chinese_font,
                fontSize=28, leading=36, alignment=TA_CENTER, spaceAfter=20,
                textColor=COLOR_PRIMARY
            )
            
            # 一级标题 (带下划线效果)
            style_h1 = ParagraphStyle(
                'CustomH1', parent=styles['Heading2'], fontName=chinese_font,
                fontSize=18, leading=24, spaceBefore=25, spaceAfter=15,
                textColor=COLOR_H1,
                borderWidth=0
            )
            
            # 二级标题
            style_h2 = ParagraphStyle(
                'CustomH2', parent=styles['Heading3'], fontName=chinese_font,
                fontSize=15, leading=20, spaceBefore=15, spaceAfter=10,
                textColor=COLOR_H2
            )

            # 三级标题 (修复了重复参数错误)
            style_h3 = ParagraphStyle(
                'CustomH3', parent=styles['Heading4'], 
                fontName=chinese_font, # 只保留这一个 fontName
                fontSize=13, leading=18, spaceBefore=10, spaceAfter=5,
                textColor=COLOR_H3
            )
            
            # 正文样式 (增加行距)
            style_normal = ParagraphStyle(
                'CustomNormal', parent=styles['Normal'], fontName=chinese_font,
                fontSize=11, leading=18, alignment=TA_JUSTIFY, spaceAfter=8,
                textColor=COLOR_PRIMARY
            )
            
            # 列表样式
            style_list = ParagraphStyle(
                'CustomList', parent=style_normal,
                leftIndent=15, firstLineIndent=-10,
                spaceAfter=4
            )
            
            # 时间轴样式 (加粗)
            style_timeline = ParagraphStyle(
                'CustomTimeline', parent=style_normal,
                leftIndent=0, spaceBefore=6, textColor=colors.black,
                fontSize=11.5
            )
            
            # 引用块/Tips (卡片式设计)
            style_quote = ParagraphStyle(
                'CustomQuote', parent=style_normal,
                fontSize=10, textColor=colors.HexColor('#555555'),
                leftIndent=10, rightIndent=10,
                backColor=COLOR_BG_QUOTE, 
                borderPadding=12,
                borderRadius=5,
                spaceBefore=12, spaceAfter=12,
                fontName=chinese_font
            )

            # 5. 内容渲染逻辑
            text_content = content.get('text_content', '')
            
            if content.get('content_type') == 'rich_text' and text_content:
                self._parse_markdown_to_story(
                    story, text_content, 
                    style_title, style_h1, style_h2, style_h3, style_normal, 
                    style_list, style_timeline, style_quote
                )
            else:
                self._add_fallback_content(story, content, style_title, style_normal)
            
            # 6. 生成文件
            doc.build(story)
            
            # 7. 验证
            if os.path.exists(output_path) and os.path.getsize(output_path) > 100:
                logger.info(f"PDF生成成功: {output_path}")
                return {
                    'success': True,
                    'pdf_path': output_path,
                    'filename': os.path.basename(output_path),
                    'file_size': os.path.getsize(output_path),
                    'message': 'PDF文档生成成功'
                }
            else:
                return {
                    'success': False,
                    'error': '生成的文件无效',
                    'message': 'PDF生成失败'
                }
            
        except Exception as e:
            logger.error(f"PDF生成严重错误: {str(e)}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return {
                'success': False,
                'error': str(e),
                'message': 'PDF生成失败'
            }

    def _parse_markdown_to_story(self, story, text, s_title, s_h1, s_h2, s_h3, s_norm, s_list, s_time, s_quote):
        """解析 Markdown 并添加到 PDF"""
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 处理行内样式
            line = self._process_inline_markdown(line)
            
            # 1级标题 (#)
            if line.startswith('# '):
                story.append(Spacer(1, 10))
                story.append(Paragraph(line[2:].strip(), s_title))
                story.append(Spacer(1, 10))
                # 主标题下加一条装饰线 (橙色)
                story.append(HRFlowable(width="60%", thickness=1, color=colors.HexColor('#e67e22'), spaceAfter=20))
                
            # 2级标题 (##)
            elif line.startswith('## '):
                story.append(Spacer(1, 15)) # 增加间距
                story.append(Paragraph(line[3:].strip(), s_h1))
                
            # 3级标题 (###)
            elif line.startswith('### '):
                story.append(Paragraph(line[4:].strip(), s_h2))

            # 4级标题 (####)
            elif line.startswith('#### '):
                story.append(Paragraph(line[5:].strip(), s_h3))
                
            # 引用块 (>)
            elif line.startswith('> '):
                quote_text = line[2:].strip()
                story.append(Paragraph(quote_text, s_quote))
            
            # 分割线 (---)
            elif line == '---' or line == '***' or line == '___':
                story.append(Spacer(1, 10))
                story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceAfter=10))
                
            # 列表项 (- 或 *)
            elif line.startswith('- ') or line.startswith('* '):
                content = line[2:].strip()
                # 识别时间轴格式: "09:00 - 10:00 | 活动"
                if '|' in content and re.match(r'\d{1,2}:\d{2}', content):
                    parts = content.split('|', 1)
                    if len(parts) == 2:
                        formatted = f"<b>{parts[0].strip()}</b> | {parts[1].strip()}"
                        story.append(Paragraph(formatted, s_time))
                        continue
                story.append(Paragraph(f"• {content}", s_list))
                
            # 普通文本
            else:
                story.append(Paragraph(line, s_norm))
    
    def _process_inline_markdown(self, text: str) -> str:
        """处理行内 Markdown"""
        # 粗体
        text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
        # 斜体
        text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
        # 代码/高亮 (用橙色突出)
        text = re.sub(r'`(.+?)`', r'<font color="#e67e22"><b>\1</b></font>', text) 
        return text

    def _add_fallback_content(self, story, content, s_title, s_norm):
        """兼容旧版数据"""
        story.append(Paragraph("旅游规划", s_title))
        story.append(Spacer(1, 20))
        story.append(Paragraph("无法生成富文本内容，请联系管理员。", s_norm))