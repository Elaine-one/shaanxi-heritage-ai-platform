##--- START OF FILE pdf_generator.py ---

# -*- coding: utf-8 -*-
"""
PDF生成器核心模块 (长文阅读优化版)
负责将Markdown内容渲染为精美的PDF文档
"""

import os
import re
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger

# ReportLab 相关
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT

class PDFGenerator:
    
    def __init__(self, pdf_cache_dir: Optional[str] = None):
        self.pdf_cache_dir = pdf_cache_dir or os.path.join(os.getcwd(), 'pdf_cache')
        if not os.path.exists(self.pdf_cache_dir):
            os.makedirs(self.pdf_cache_dir)
        logger.info("PDF生成器初始化完成")
    
    async def generate_pdf_document(self, content: Dict[str, Any], output_filename: Optional[str] = None) -> Dict[str, Any]:
        try:
            # 1. 路径准备
            if not output_filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_filename = f'Travel_Plan_{timestamp}.pdf'
            if not output_filename.endswith('.pdf'):
                output_filename += '.pdf'
            
            output_path = os.path.join(self.pdf_cache_dir, output_filename)
            logger.info(f"PDF将保存到: {output_path}")
            
            # 2. 创建PDF模板 (上下左右边距 2.5cm)
            doc = SimpleDocTemplate(
                output_path, 
                pagesize=A4,
                rightMargin=25*mm, leftMargin=25*mm, 
                topMargin=25*mm, bottomMargin=25*mm
            )
            
            story = []
            
            # 3. 字体注册
            from .font_manager import register_chinese_font
            chinese_font = register_chinese_font()
            if not chinese_font:
                logger.warning("未检测到中文字体，使用默认字体")
                chinese_font = 'Helvetica'
            
            # 4. 样式定义 (阅读优化)
            styles = getSampleStyleSheet()
            
            # 颜色
            COLOR_TITLE = colors.HexColor('#2c3e50')
            COLOR_H1 = colors.HexColor('#c0392b') # 红色系标题
            COLOR_H2 = colors.HexColor('#2980b9') # 蓝色系标题
            COLOR_TEXT = colors.HexColor('#34495e')
            COLOR_BG_QUOTE = colors.HexColor('#f2f3f4') # 浅灰背景
            
            # 样式
            style_title = ParagraphStyle(
                'CustomTitle', parent=styles['Heading1'], fontName=chinese_font,
                fontSize=24, leading=30, alignment=TA_CENTER, spaceAfter=20,
                textColor=COLOR_TITLE
            )
            
            style_h1 = ParagraphStyle(
                'CustomH1', parent=styles['Heading2'], fontName=chinese_font,
                fontSize=16, leading=22, spaceBefore=15, spaceAfter=10,
                textColor=COLOR_H1,
                borderWidth=0
            )
            
            style_h2 = ParagraphStyle(
                'CustomH2', parent=styles['Heading3'], fontName=chinese_font,
                fontSize=14, leading=18, spaceBefore=10, spaceAfter=8,
                textColor=COLOR_H2
            )
            
            style_normal = ParagraphStyle(
                'CustomNormal', parent=styles['Normal'], fontName=chinese_font,
                fontSize=10.5, leading=16, alignment=TA_JUSTIFY, spaceAfter=6,
                textColor=COLOR_TEXT
            )
            
            style_list = ParagraphStyle(
                'CustomList', parent=style_normal,
                leftIndent=15, firstLineIndent=-10
            )
            
            # 时间轴样式 (加粗)
            style_timeline = ParagraphStyle(
                'CustomTimeline', parent=style_normal,
                leftIndent=0, spaceBefore=5, textColor=colors.black
            )
            
            # 引用块/Tips (带背景色)
            style_quote = ParagraphStyle(
                'CustomQuote', parent=style_normal,
                fontSize=9.5, textColor=colors.HexColor('#555555'),
                leftIndent=10, rightIndent=10,
                backColor=COLOR_BG_QUOTE, borderPadding=8,
                spaceBefore=8, spaceAfter=8,
                fontName=chinese_font
            )

            # 5. 内容渲染
            text_content = content.get('text_content', '')
            
            if content.get('content_type') == 'rich_text' and text_content:
                self._parse_markdown_to_story(
                    story, text_content, 
                    style_title, style_h1, style_h2, style_normal, 
                    style_list, style_timeline, style_quote
                )
            else:
                # 兼容旧数据
                self._add_traditional_table_content(story, content, style_title, style_h1, style_normal, chinese_font)
            
            # 6. 生成文件
            doc.build(story)
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 100:
                return {
                    'success': True,
                    'pdf_path': output_path,
                    'filename': os.path.basename(output_path),
                    'message': 'PDF文档生成成功'
                }
            else:
                return {'success': False, 'error': '生成文件为空', 'message': 'PDF生成失败'}
            
        except Exception as e:
            logger.error(f"PDF生成严重错误: {str(e)}")
            return {'success': False, 'error': str(e), 'message': 'PDF生成失败'}

    def _parse_markdown_to_story(self, story, text, s_title, s_h1, s_h2, s_norm, s_list, s_time, s_quote):
        """解析 Markdown 并添加到 PDF"""
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 处理行内样式
            line = self._process_inline_markdown(line)
            
            if line.startswith('# '):
                story.append(Spacer(1, 10))
                story.append(Paragraph(line[2:].strip(), s_title))
                story.append(Spacer(1, 20))
                
            elif line.startswith('## '):
                story.append(Spacer(1, 10))
                story.append(Paragraph(line[3:].strip(), s_h1))
                
            elif line.startswith('### '):
                story.append(Paragraph(line[4:].strip(), s_h2))
                
            elif line.startswith('> '):
                # 引用块，去掉 > 符号
                quote_text = line[2:].strip()
                story.append(Paragraph(quote_text, s_quote))
                
            elif line.startswith('- ') or line.startswith('* '):
                content = line[2:].strip()
                # 识别时间轴格式: "09:00 - 10:00 | 活动"
                if '|' in content and re.match(r'\d{1,2}:\d{2}', content):
                    parts = content.split('|', 1)
                    if len(parts) == 2:
                        # 时间加粗
                        formatted = f"<b>{parts[0].strip()}</b> | {parts[1].strip()}"
                        story.append(Paragraph(formatted, s_time)) # 使用时间轴专用样式
                        continue
                story.append(Paragraph(f"• {content}", s_list))
                
            else:
                story.append(Paragraph(line, s_norm))
    
    def _process_inline_markdown(self, text: str) -> str:
        """处理行内 Markdown"""
        text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text) # 粗体
        text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)     # 斜体
        # 代码块不高亮背景，只变色，防止PDF排版错乱
        text = re.sub(r'`(.+?)`', r'<font color="#c0392b">\1</font>', text) 
        return text

    def _add_traditional_table_content(self, story, content, title_style, heading_style, normal_style, chinese_font):
        """兼容旧版数据"""
        try:
            logger.info("使用传统表格模式渲染PDF")
            basic_info = content.get('basic_info', {})
            title = basic_info.get('title', '旅游规划')
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 12))
            
            if basic_info:
                story.append(Paragraph('基本信息', heading_style))
                data = [[k, v] for k, v in basic_info.items() if k != 'title']
                if data:
                    t = Table(data, colWidths=[2*inch, 4*inch])
                    t.setStyle(TableStyle([
                        ('FONTNAME', (0,0), (-1,-1), chinese_font),
                        ('GRID', (0,0), (-1,-1), 1, colors.grey),
                        ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke),
                        ('PADDING', (0,0), (-1,-1), 6),
                    ]))
                    story.append(t)
            story.append(Paragraph("注：此为基础行程表。", normal_style))
        except Exception as e:
            logger.error(f"传统表格渲染失败: {e}")
            story.append(Paragraph("数据渲染出错", normal_style))