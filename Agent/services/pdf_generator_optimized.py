# -*- coding: utf-8 -*-
"""
PDF生成器
使用 ReportLab 生成 PDF，支持专业排版、表格和图片嵌入
"""

import os
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, Flowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


class CalloutBox(Flowable):
    def __init__(self, text, box_type, font_name, width=420):
        Flowable.__init__(self)
        self.text = text
        self.box_type = box_type
        self.font_name = font_name
        self.box_width = width
        
        type_config = {
            'tip':    {'bg': '#E8F5E9', 'border': '#2E7D32', 'icon': '\u3010\u5B9E\u7528\u8D34\u58EB\u3011', 'text_color': '#1B5E20'},
            'warning': {'bg': '#FFF3E0', 'border': '#E65100', 'icon': '\u3010\u6CE8\u610F\u4E8B\u9879\u3011', 'text_color': '#BF360C'},
            'highlight': {'bg': '#FBE9E7', 'border': '#C41A1A', 'icon': '\u3010\u884C\u7A0B\u4EAE\u70B9\u3011', 'text_color': '#B71C1C'},
        }
        config = type_config.get(box_type, type_config['tip'])
        self.bg_color = colors.HexColor(config['bg'])
        self.border_color = colors.HexColor(config['border'])
        self.icon_text = config['icon']
        self.text_color = colors.HexColor(config['text_color'])
        
        self._style = ParagraphStyle(
            f'callout_{box_type}',
            fontName=font_name,
            fontSize=10,
            leading=15,
            textColor=self.text_color,
        )
        self._icon_style = ParagraphStyle(
            f'callout_icon_{box_type}',
            fontName=font_name,
            fontSize=10,
            leading=15,
            textColor=self.border_color,
        )
        
        self._para = Paragraph(self.text, self._style)
        self._icon_para = Paragraph(f'<b>{self.icon_text}</b>', self._icon_style)
        
        pw, ph = self._para.wrap(self.box_width - 30, 1000)
        iw, ih = self._icon_para.wrap(self.box_width - 30, 1000)
        self.box_height = ph + ih + 20
    
    def wrap(self, availWidth, availHeight):
        return self.box_width, self.box_height
    
    def draw(self):
        canvas = self.canv
        canvas.saveState()
        
        canvas.setFillColor(self.bg_color)
        canvas.rect(0, 0, self.box_width, self.box_height, fill=1, stroke=0)
        
        canvas.setStrokeColor(self.border_color)
        canvas.setLineWidth(3)
        canvas.line(0, 0, 0, self.box_height)
        
        y = self.box_height - 10
        self._icon_para.drawOn(canvas, 10, y - 12)
        y -= 18
        
        self._para.drawOn(canvas, 10, y - self._para.height + 5)
        
        canvas.restoreState()


class DayBanner(Flowable):
    def __init__(self, day_text, date_text, font_name, width=420):
        Flowable.__init__(self)
        self.day_text = day_text
        self.date_text = date_text
        self.font_name = font_name
        self.banner_width = width
        self.banner_height = 36
    
    def wrap(self, availWidth, availHeight):
        return self.banner_width, self.banner_height + 8
    
    def draw(self):
        canvas = self.canv
        canvas.saveState()
        
        canvas.setFillColor(colors.HexColor('#C41A1A'))
        canvas.rect(0, 8, self.banner_width, self.banner_height, fill=1, stroke=0)
        
        canvas.setFillColor(colors.HexColor('#D4A574'))
        canvas.rect(0, 8, 6, self.banner_height, fill=1, stroke=0)
        
        canvas.setFont(self.font_name, 14)
        canvas.setFillColor(colors.white)
        canvas.drawString(16, 20, self.day_text)
        
        if self.date_text:
            canvas.setFont(self.font_name, 10)
            canvas.setFillColor(colors.HexColor('#FFD5D5'))
            canvas.drawRightString(self.banner_width - 10, 22, self.date_text)
        
        canvas.restoreState()


class OptimizedPDFGenerator:
    """
    PDF生成器
    支持专业排版、表格、图片嵌入
    """
    
    def __init__(self, pdf_cache_dir: Optional[str] = None):
        if pdf_cache_dir is None:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            pdf_cache_dir = os.path.join(project_root, 'pdf_cache')
        
        self.pdf_cache_dir = pdf_cache_dir
        if not os.path.exists(self.pdf_cache_dir):
            os.makedirs(self.pdf_cache_dir, exist_ok=True)
        
        self.chinese_font = self._register_chinese_font()
        self.styles = self._create_styles()
        
        logger.info(f"PDF生成器初始化完成，字体: {self.chinese_font}")
    
    def _register_chinese_font(self) -> str:
        """注册中文字体，优先使用 font_cache 目录中的字体"""
        try:
            from Agent.utils.font_manager import register_chinese_font
            font_name = register_chinese_font()
            if font_name:
                logger.info(f"通过 font_manager 注册字体: {font_name}")
                return font_name
        except ImportError as e:
            logger.warning(f"font_manager 导入失败，使用默认字体查找: {e}")
        
        font_paths = [
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/simsun.ttc",
            "/System/Library/Fonts/PingFang.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    font_name = os.path.basename(font_path).split('.')[0]
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                    logger.info(f"成功注册中文字体: {font_name}")
                    return font_name
                except Exception as e:
                    logger.warning(f"注册字体失败 {font_path}: {e}")
        
        logger.warning("未找到中文字体，使用默认字体")
        return 'Helvetica'
    
    def _create_styles(self) -> Dict[str, ParagraphStyle]:
        styles = getSampleStyleSheet()
        
        COLOR_PRIMARY = colors.HexColor('#C41A1A')
        COLOR_ACCENT = colors.HexColor('#D4A574')
        COLOR_H1 = colors.HexColor('#C41A1A')
        COLOR_H2 = colors.HexColor('#2C5F2D')
        COLOR_H3 = colors.HexColor('#8B6914')
        COLOR_TEXT = colors.HexColor('#2D2D2D')
        COLOR_TEXT_LIGHT = colors.HexColor('#666666')
        COLOR_BG_WARM = colors.HexColor('#FDF6EC')
        COLOR_BG_CARD = colors.HexColor('#F5EDE0')
        
        custom_styles = {
            'title': ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontName=self.chinese_font,
                fontSize=28,
                leading=36,
                alignment=TA_CENTER,
                spaceAfter=8,
                textColor=COLOR_PRIMARY
            ),
            'subtitle': ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Normal'],
                fontName=self.chinese_font,
                fontSize=12,
                leading=16,
                alignment=TA_CENTER,
                spaceAfter=30,
                textColor=COLOR_TEXT_LIGHT
            ),
            'h1': ParagraphStyle(
                'CustomH1',
                parent=styles['Heading1'],
                fontName=self.chinese_font,
                fontSize=20,
                leading=28,
                spaceBefore=24,
                spaceAfter=14,
                textColor=COLOR_H1
            ),
            'h2': ParagraphStyle(
                'CustomH2',
                parent=styles['Heading2'],
                fontName=self.chinese_font,
                fontSize=16,
                leading=22,
                spaceBefore=18,
                spaceAfter=12,
                textColor=COLOR_H2
            ),
            'h3': ParagraphStyle(
                'CustomH3',
                parent=styles['Heading3'],
                fontName=self.chinese_font,
                fontSize=13,
                leading=18,
                spaceBefore=14,
                spaceAfter=8,
                textColor=COLOR_H3
            ),
            'normal': ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontName=self.chinese_font,
                fontSize=11,
                leading=18,
                alignment=TA_JUSTIFY,
                spaceAfter=10,
                textColor=COLOR_TEXT
            ),
            'list': ParagraphStyle(
                'CustomList',
                parent=styles['Normal'],
                fontName=self.chinese_font,
                fontSize=11,
                leading=18,
                leftIndent=20,
                spaceAfter=6,
                textColor=COLOR_TEXT
            ),
            'quote': ParagraphStyle(
                'CustomQuote',
                parent=styles['Normal'],
                fontName=self.chinese_font,
                fontSize=10,
                leading=15,
                leftIndent=25,
                rightIndent=20,
                spaceBefore=10,
                spaceAfter=10,
                textColor=COLOR_TEXT_LIGHT,
                backColor=COLOR_BG_WARM,
                borderPadding=8
            ),
            'highlight': ParagraphStyle(
                'CustomHighlight',
                parent=styles['Normal'],
                fontName=self.chinese_font,
                fontSize=11,
                leading=18,
                textColor=COLOR_ACCENT
            ),
            'footer': ParagraphStyle(
                'CustomFooter',
                parent=styles['Normal'],
                fontName=self.chinese_font,
                fontSize=9,
                leading=12,
                alignment=TA_CENTER,
                textColor=COLOR_TEXT_LIGHT
            ),
            'cover_info': ParagraphStyle(
                'CoverInfo',
                parent=styles['Normal'],
                fontName=self.chinese_font,
                fontSize=12,
                leading=18,
                alignment=TA_CENTER,
                textColor=COLOR_TEXT
            ),
            'section_header': ParagraphStyle(
                'SectionHeader',
                parent=styles['Normal'],
                fontName=self.chinese_font,
                fontSize=14,
                leading=20,
                textColor=colors.white,
                alignment=TA_LEFT,
                spaceBefore=16,
                spaceAfter=10
            ),
            'tip_text': ParagraphStyle(
                'TipText',
                parent=styles['Normal'],
                fontName=self.chinese_font,
                fontSize=10,
                leading=15,
                leftIndent=30,
                rightIndent=15,
                spaceAfter=6,
                textColor=COLOR_TEXT
            )
        }
        
        return custom_styles
    
    async def generate_pdf_document(self, content: Dict[str, Any], output_filename: Optional[str] = None) -> Dict[str, Any]:
        """
        生成 PDF 文档
        
        Args:
            content: 内容数据
            output_filename: 输出文件名
        
        Returns:
            Dict: 生成结果
        """
        try:
            if not output_filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_filename = f'Travel_Plan_{timestamp}.pdf'
            
            if not output_filename.endswith('.pdf'):
                output_filename += '.pdf'
            
            output_path = os.path.join(self.pdf_cache_dir, output_filename)
            
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=25*mm,
                leftMargin=25*mm,
                topMargin=30*mm,
                bottomMargin=25*mm
            )
            
            story = []
            
            content_type = content.get('content_type', 'rich_text')
            
            if content_type == 'rich_text':
                text_content = content.get('text_content', '')
                plan_data = content.get('plan_data', {})
                self._add_auto_cover(story, text_content, plan_data)
                self._parse_markdown_to_story(story, text_content)
            elif content_type == 'structured':
                self._build_structured_content(story, content)
            else:
                self._add_fallback_content(story, content)
            
            await asyncio.to_thread(doc.build, story, onFirstPage=self._add_page_header, onLaterPages=self._add_page_header)
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 100:
                file_size = os.path.getsize(output_path)
                logger.info(f"PDF 生成成功: {output_path}, 大小: {file_size} bytes")
                
                return {
                    'success': True,
                    'pdf_path': output_path,
                    'filename': os.path.basename(output_path),
                    'file_size': file_size,
                    'message': 'PDF 文档生成成功'
                }
            else:
                return {
                    'success': False,
                    'error': '生成的文件无效',
                    'message': 'PDF 生成失败'
                }
        
        except Exception as e:
            logger.error(f"PDF 生成错误: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e),
                'message': 'PDF 生成失败'
            }
    
    def _add_page_header(self, canvas, doc):
        canvas.saveState()
        
        canvas.setStrokeColor(colors.HexColor('#C41A1A'))
        canvas.setLineWidth(2)
        canvas.line(doc.leftMargin, doc.height + doc.topMargin + 6*mm, 
                     doc.width + doc.leftMargin, doc.height + doc.topMargin + 6*mm)
        
        canvas.setFont(self.chinese_font, 9)
        canvas.setFillColor(colors.HexColor('#C41A1A'))
        canvas.drawString(doc.leftMargin, doc.height + doc.topMargin + 9*mm, "陕西非遗文化旅游规划")
        
        canvas.setStrokeColor(colors.HexColor('#D4A574'))
        canvas.setLineWidth(0.5)
        canvas.line(doc.leftMargin, 15*mm, doc.width + doc.leftMargin, 15*mm)
        
        canvas.setFillColor(colors.HexColor('#999999'))
        canvas.setFont(self.chinese_font, 8)
        canvas.drawCentredString(doc.width / 2 + doc.leftMargin, 10*mm, f"— {doc.page} —")
        
        canvas.restoreState()
    
    def _remove_emojis(self, text: str) -> str:
        emoji_replacements = {
            '📢': '',
            '🎒': '',
            '🚗': '',
            '💰': '',
            '📜': '',
            '🍽️': '',
            '🍽': '',
            '📍': '',
            '💡': '',
            '⚠️': '',
            '⚠': '',
            '🌟': '',
            '✨': '',
            '🏨': '',
            '★': '*',
            '☆': ' ',
            '✓': '√',
            '✗': '×',
        }
        
        for emoji, replacement in emoji_replacements.items():
            text = text.replace(emoji, replacement)
        
        return text.strip()
    
    def _parse_markdown_to_story(self, story: List, text: str):
        lines = text.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            i += 1
            
            if not line:
                continue
            
            raw_line = line
            line = self._remove_emojis(line)
            line = self._process_inline_markdown(line)
            
            handlers = [
                (lambda l: l.startswith('# ') and not l.startswith('## '), self._handle_h1),
                (lambda l: l.startswith('## '), self._handle_h2),
                (lambda l: l.startswith('### '), self._handle_h3),
                (lambda l: l.startswith('#### '), self._handle_h4),
                (lambda l: l.startswith('> '), self._handle_quote),
                (lambda l: l in ('---', '***'), self._handle_hr),
                (lambda l: l.startswith('|'), self._handle_table_line),
                (lambda l: l.startswith(('- ', '* ')), self._handle_list),
            ]
            
            handled = False
            new_idx = None
            for matcher, handler in handlers:
                if matcher(line):
                    result = handler(story, line, lines, i)
                    if result is not None:
                        new_idx = result
                    handled = True
                    break
            
            if new_idx is not None:
                i = new_idx
            elif not handled:
                story.append(Paragraph(line, self.styles['normal']))

    def _handle_h1(self, story, line, lines, idx):
        story.append(Spacer(1, 12))
        story.append(HRFlowable(width="100%", thickness=3, color=colors.HexColor('#C41A1A'), spaceAfter=8))
        story.append(Paragraph(line[2:], self.styles['h1']))
        story.append(HRFlowable(width="40%", thickness=1, color=colors.HexColor('#D4A574'), spaceAfter=16))

    def _handle_h2(self, story, line, lines, idx):
        story.append(Spacer(1, 10))
        story.append(Paragraph(line[3:], self.styles['h2']))
        story.append(HRFlowable(width="25%", thickness=1, color=colors.HexColor('#2C5F2D'), spaceAfter=12))

    def _handle_h3(self, story, line, lines, idx):
        content = line[4:]
        is_day_title = False
        day_text = content
        date_text = ''
        
        for prefix in ['第', 'Day ', 'day ']:
            if content.startswith(prefix):
                is_day_title = True
                break
        
        if is_day_title:
            if '(' in content and ')' in content:
                paren_start = content.index('(')
                paren_end = content.index(')')
                date_text = content[paren_start+1:paren_end]
                day_text = content[:paren_start]
            elif '（' in content and '）' in content:
                paren_start = content.index('（')
                paren_end = content.index('）')
                date_text = content[paren_start+1:paren_end]
                day_text = content[:paren_start]
            elif '：' in content:
                parts = content.split('：', 1)
                day_text = parts[0]
                date_text = parts[1] if len(parts) > 1 else ''
            
            story.append(Spacer(1, 16))
            story.append(DayBanner(day_text, date_text, self.chinese_font))
            story.append(Spacer(1, 8))
        else:
            story.append(Spacer(1, 8))
            story.append(Paragraph(content, self.styles['h3']))

    def _handle_h4(self, story, line, lines, idx):
        story.append(Spacer(1, 6))
        story.append(Paragraph(line[5:], self.styles['h3']))

    def _handle_quote(self, story, line, lines, idx):
        content = line[2:]
        
        raw_content = content
        for emoji in ['💡', '⚠️', '⚠', '🌟', '✨', '🏨']:
            if raw_content.startswith(emoji):
                raw_content = raw_content[len(emoji):].strip()
                break
        
        if raw_content != content:
            content = self._process_inline_markdown(raw_content)
        
        if '【实用贴士】' in content or '【贴士】' in content or content.startswith('今日天气') or content.startswith('今日贴士') or content.startswith('推荐') or content.startswith('若遇') or content.startswith('建议'):
            story.append(Spacer(1, 6))
            story.append(CalloutBox(content, 'tip', self.chinese_font))
            story.append(Spacer(1, 6))
        elif '【注意事项】' in content or '【注意】' in content or content.startswith('注意') or content.startswith('请勿') or content.startswith('禁止') or content.startswith('参观寺庙'):
            story.append(Spacer(1, 6))
            story.append(CalloutBox(content, 'warning', self.chinese_font))
            story.append(Spacer(1, 6))
        elif '【行程亮点】' in content or '【亮点】' in content or content.startswith('亮点') or content.startswith('必看') or content.startswith('不可错过'):
            story.append(Spacer(1, 6))
            story.append(CalloutBox(content, 'highlight', self.chinese_font))
            story.append(Spacer(1, 6))
        else:
            story.append(Spacer(1, 5))
            story.append(Paragraph(content, self.styles['quote']))
            story.append(Spacer(1, 5))

    def _handle_hr(self, story, line, lines, idx):
        story.append(Spacer(1, 15))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#95a5a6'), spaceAfter=15))

    def _handle_table_line(self, story, line, lines, idx):
        return self._parse_markdown_table(story, lines, idx - 1)

    def _handle_list(self, story, line, lines, idx):
        content = line[2:]
        if '|' in content and self._is_time_format(content.split('|')[0].strip()):
            parts = content.split('|', 1)
            if len(parts) == 2:
                formatted = f"<b>{parts[0].strip()}</b> | {parts[1].strip()}"
                story.append(Paragraph(formatted, self.styles['list']))
                return
        story.append(Paragraph(f"• {content}", self.styles['list']))
    
    def _parse_markdown_table(self, story: List, lines: List[str], start_idx: int) -> int:
        table_data = []
        i = start_idx
        
        while i < len(lines):
            line = lines[i].strip()
            i += 1
            
            if not line:
                break
            
            if line.startswith('|'):
                parts = [p.strip() for p in line.split('|')]
                parts = [p for p in parts if p]
                
                is_separator = all('-' in p for p in parts)
                if not is_separator:
                    table_data.append(parts)
            else:
                i -= 1
                break
        
        if len(table_data) >= 1:
            try:
                col_count = len(table_data[0])
                col_width = 420 / col_count
                col_widths = [col_width] * col_count
                
                formatted_data = []
                for row_idx, row in enumerate(table_data):
                    formatted_row = []
                    for cell in row:
                        cell = self._remove_emojis(cell)
                        cell = self._process_inline_markdown(cell)
                        if row_idx == 0:
                            formatted_row.append(cell)
                        else:
                            formatted_row.append(Paragraph(cell, self.styles['normal']))
                    formatted_data.append(formatted_row)
                
                table = Table(formatted_data, colWidths=col_widths, repeatRows=1)
                
                header_text = ''.join(table_data[0]).lower() if table_data else ''
                table_type = self._detect_table_type(header_text)
                style = self._get_table_style(table_type)
                
                if len(formatted_data) > 1 and table_type == 'default':
                    style.add('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FDF6EC')])
                
                table.setStyle(style)
                story.append(Spacer(1, 12))
                story.append(table)
                story.append(Spacer(1, 12))
                
            except Exception as e:
                logger.warning(f"表格渲染失败: {e}")
        
        return i
    
    def _detect_table_type(self, header_text: str) -> str:
        dining_keywords = ['餐次', '餐厅', '招牌菜', '人均', '特色菜', '早餐', '午餐', '晚餐']
        transport_keywords = ['方式', '耗时', '舒适度', '推荐指数', '交通', '路段']
        budget_keywords = ['费用', '金额', '预算', '预估', '合计', '明细']
        checklist_keywords = ['勾选', '类别', '物品', '备注']
        emergency_keywords = ['电话', '紧急', '报警', '急救']
        
        for kw in dining_keywords:
            if kw in header_text:
                return 'dining'
        for kw in transport_keywords:
            if kw in header_text:
                return 'transport'
        for kw in budget_keywords:
            if kw in header_text:
                return 'budget'
        for kw in checklist_keywords:
            if kw in header_text:
                return 'checklist'
        for kw in emergency_keywords:
            if kw in header_text:
                return 'emergency'
        return 'default'
    
    def _get_table_style(self, table_type: str) -> TableStyle:
        base_style = [
            ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 1), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]
        
        type_styles = {
            'dining': [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E67E22')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#F0C080')),
                ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#E67E22')),
                ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#E67E22')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FFF8F0')]),
            ],
            'transport': [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2980B9')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#A0C8E8')),
                ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#2980B9')),
                ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#2980B9')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F7FC')]),
            ],
            'budget': [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C5F2D')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#A0C8A0')),
                ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#2C5F2D')),
                ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#2C5F2D')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F8F0')]),
            ],
            'checklist': [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5D6D7E')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#B0BEC5')),
                ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#5D6D7E')),
                ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#5D6D7E')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F7F8')]),
            ],
            'emergency': [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#C0392B')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E8A0A0')),
                ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#C0392B')),
                ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#C0392B')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FFF0F0')]),
            ],
            'default': [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#C41A1A')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D4A574')),
                ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#C41A1A')),
                ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#C41A1A')),
            ],
        }
        
        return TableStyle(base_style + type_styles.get(table_type, type_styles['default']))
    
    def _is_time_format(self, text: str) -> bool:
        """检查是否是时间格式（不使用正则）"""
        if not text:
            return False
        parts = text.split(':')
        if len(parts) != 2:
            return False
        hour, minute = parts
        if not (hour.isdigit() and minute.isdigit()):
            return False
        h, m = int(hour), int(minute)
        return 0 <= h <= 23 and 0 <= m <= 59
    
    def _process_inline_markdown(self, text: str) -> str:
        """处理行内 Markdown（不使用正则）"""
        text = self._replace_markdown_bold(text)
        text = self._replace_markdown_italic(text)
        text = self._replace_markdown_code(text)
        return text
    
    def _replace_markdown_bold(self, text: str) -> str:
        """替换 **text** 为 <b>text</b>"""
        result = []
        i = 0
        while i < len(text):
            if text[i:i+2] == '**':
                end = text.find('**', i + 2)
                if end != -1:
                    content = text[i+2:end]
                    result.append(f'<b>{content}</b>')
                    i = end + 2
                    continue
            result.append(text[i])
            i += 1
        return ''.join(result)
    
    def _replace_markdown_italic(self, text: str) -> str:
        """替换 *text* 为 <i>text</i>（排除 ** 的情况）"""
        result = []
        i = 0
        while i < len(text):
            if text[i] == '*' and (i == 0 or text[i-1] != '*') and (i + 1 >= len(text) or text[i+1] != '*'):
                end = text.find('*', i + 1)
                if end != -1 and (end + 1 >= len(text) or text[end+1] != '*'):
                    content = text[i+1:end]
                    result.append(f'<i>{content}</i>')
                    i = end + 1
                    continue
            result.append(text[i])
            i += 1
        return ''.join(result)
    
    def _replace_markdown_code(self, text: str) -> str:
        """替换 `text` 为 <font color="#e67e22"><b>text</b></font>"""
        result = []
        i = 0
        while i < len(text):
            if text[i] == '`':
                end = text.find('`', i + 1)
                if end != -1:
                    content = text[i+1:end]
                    result.append(f'<font color="#C41A1A"><b>{content}</b></font>')
                    i = end + 1
                    continue
            result.append(text[i])
            i += 1
        return ''.join(result)
    
    def _build_structured_content(self, story: List, content: Dict[str, Any]):
        """构建结构化内容"""
        plan_data = content.get('plan_data', {})
        
        self._add_cover_page(story, plan_data)
        
        self._add_toc_page(story, plan_data)
        
        itinerary = plan_data.get('itinerary', [])
        for day_plan in itinerary:
            self._add_day_section(story, day_plan)
        
        heritage_items = plan_data.get('heritage_items', [])
        if heritage_items:
            self._add_heritage_section(story, heritage_items)
        
        weather_info = plan_data.get('weather_info', {})
        if weather_info:
            self._add_weather_section(story, weather_info)
        
        route_info = plan_data.get('route_info', {})
        if route_info:
            self._add_route_section(story, route_info)
        
        recommendations = plan_data.get('recommendations', {})
        if recommendations:
            self._add_tips_section(story, recommendations)
        
        self._add_footer_section(story, plan_data)
    
    def _add_auto_cover(self, story: List, text_content: str, plan_data: Dict[str, Any]):
        story.append(Spacer(1, 60))
        
        story.append(HRFlowable(width="100%", thickness=4, color=colors.HexColor('#C41A1A'), spaceAfter=20))
        
        title = '陕西非遗文化旅游规划'
        for line in text_content.split('\n'):
            stripped = line.strip()
            if stripped and stripped.startswith('# '):
                title = stripped[2:].strip()
                break
        
        story.append(Paragraph(title, self.styles['title']))
        
        story.append(HRFlowable(width="40%", thickness=2, color=colors.HexColor('#D4A574'), spaceAfter=12))
        
        story.append(Paragraph("传承千年文化 · 领略三秦风韵", self.styles['subtitle']))
        story.append(Spacer(1, 20))
        
        basic_info = plan_data.get('basic_info', {})
        info_items = []
        destination = basic_info.get('destination', '')
        if destination:
            info_items.append(['目的地', destination])
        departure = basic_info.get('departure', '')
        if departure:
            info_items.append(['出发地', departure])
        travel_days = basic_info.get('travel_days', '')
        if travel_days:
            info_items.append(['行程天数', f"{travel_days} 天"])
        travel_mode = basic_info.get('travel_mode', '')
        if travel_mode:
            info_items.append(['出行方式', travel_mode])
        budget_range = basic_info.get('budget_range', '')
        if budget_range:
            info_items.append(['预算范围', budget_range])
        group_size = basic_info.get('group_size', '')
        if group_size:
            info_items.append(['出行人数', f"{group_size} 人"])
        
        if info_items:
            table = Table(info_items, colWidths=[80, 200])
            table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#C41A1A')),
                ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2D2D2D')),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FDF6EC')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#D4A574')),
                ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#E8D5B7')),
            ]))
            story.append(table)
        
        story.append(Spacer(1, 25))
        
        highlights = []
        for line in text_content.split('\n'):
            stripped = line.strip()
            if stripped.startswith('> ') and ('🌟' in stripped or '亮点' in stripped or '【行程亮点】' in stripped):
                clean = stripped[2:]
                for emoji in ['🌟', '✨']:
                    clean = clean.replace(emoji, '').strip()
                if clean:
                    highlights.append(clean)
                if len(highlights) >= 3:
                    break
        
        if highlights:
            story.append(Paragraph('<b>行程亮点</b>', ParagraphStyle(
                'CoverHighlightTitle',
                fontName=self.chinese_font,
                fontSize=13,
                leading=18,
                textColor=colors.HexColor('#C41A1A'),
                spaceAfter=8,
            )))
            for hl in highlights:
                story.append(Paragraph(f'<font color="#D4A574">\u25C6</font>  {hl}', ParagraphStyle(
                    'CoverHighlightItem',
                    fontName=self.chinese_font,
                    fontSize=10,
                    leading=15,
                    leftIndent=15,
                    textColor=colors.HexColor('#2D2D2D'),
                    spaceAfter=4,
                )))
        
        story.append(Spacer(1, 30))
        
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#D4A574'), spaceAfter=8))
        story.append(Paragraph(f"生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}", self.styles['footer']))
        story.append(HRFlowable(width="100%", thickness=4, color=colors.HexColor('#C41A1A'), spaceAfter=0))
        story.append(PageBreak())
    
    def _add_cover_page(self, story: List, plan_data: Dict[str, Any]):
        story.append(Spacer(1, 60))
        
        story.append(HRFlowable(width="100%", thickness=4, color=colors.HexColor('#C41A1A'), spaceAfter=20))
        
        title = plan_data.get('basic_info', {}).get('title', '陕西非遗文化旅游规划')
        story.append(Paragraph(title, self.styles['title']))
        
        story.append(HRFlowable(width="40%", thickness=2, color=colors.HexColor('#D4A574'), spaceAfter=10))
        
        story.append(Paragraph("—— 传承千年文化 · 领略三秦风韵 ——", self.styles['subtitle']))
        story.append(Spacer(1, 20))
        
        basic_info = plan_data.get('basic_info', {})
        
        info_data = [
            ['目的地', basic_info.get('destination', '陕西')],
            ['出发地', basic_info.get('departure', '未指定')],
            ['行程天数', f"{basic_info.get('travel_days', 3)} 天"],
            ['出行方式', basic_info.get('travel_mode', '自驾')],
            ['预算范围', basic_info.get('budget_range', '中等')],
        ]
        
        table = Table(info_data, colWidths=[80, 200])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#C41A1A')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2D2D2D')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FDF6EC')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#D4A574')),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#E8D5B7')),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 40))
        
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#D4A574'), spaceAfter=10))
        story.append(Paragraph(f"生成时间: {datetime.now().strftime('%Y年%m月%d日')}", self.styles['footer']))
        story.append(HRFlowable(width="100%", thickness=4, color=colors.HexColor('#C41A1A'), spaceAfter=0))
        story.append(PageBreak())
    
    def _add_day_section(self, story: List, day_plan: Dict[str, Any]):
        """添加日程部分"""
        day = day_plan.get('day', 1)
        theme = day_plan.get('theme', f'第 {day} 天行程')
        
        story.append(Paragraph(f"第 {day} 天：{theme}", self.styles['h1']))
        
        items = day_plan.get('items', [])
        for item in items:
            self._add_item_card(story, item)
        
        story.append(Spacer(1, 15))
    
    def _add_item_card(self, story: List, item: Dict[str, Any]):
        """添加项目卡片"""
        name = item.get('name', '未命名')
        time = item.get('time', '待定')
        description = item.get('description', '')
        
        story.append(Paragraph(f"<b>{time}</b> | {name}", self.styles['h3']))
        
        if description:
            story.append(Paragraph(description[:300], self.styles['normal']))
    
    def _add_heritage_section(self, story: List, heritage_items: List[Dict[str, Any]]):
        """添加非遗介绍部分"""
        story.append(PageBreak())
        story.append(Paragraph("非遗项目介绍", self.styles['h1']))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e67e22'), spaceAfter=15))
        
        for item in heritage_items[:5]:
            name = item.get('name', '未知项目')
            region = item.get('region', '')
            level = item.get('level', '')
            description = item.get('description', '')[:200]
            
            story.append(Paragraph(name, self.styles['h3']))
            
            meta = f"地区: {region} | 级别: {level}"
            story.append(Paragraph(meta, self.styles['highlight']))
            
            if description:
                story.append(Paragraph(description, self.styles['normal']))
            
            story.append(Spacer(1, 10))
    
    def _add_tips_section(self, story: List, recommendations: Dict[str, Any]):
        """添加贴士部分"""
        story.append(Spacer(1, 20))
        story.append(Paragraph("实用贴士", self.styles['h1']))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e67e22'), spaceAfter=15))
        
        travel_tips = recommendations.get('travel_tips', [])
        if travel_tips:
            story.append(Paragraph("旅行建议", self.styles['h3']))
            for tip in travel_tips[:5]:
                story.append(Paragraph(f"• {tip}", self.styles['list']))
        
        packing_list = recommendations.get('packing_list', [])
        if packing_list:
            story.append(Paragraph("行前准备", self.styles['h3']))
            for item in packing_list[:8]:
                story.append(Paragraph(f"• {item}", self.styles['list']))
    
    def _add_toc_page(self, story: List, plan_data: Dict[str, Any]):
        """添加目录页"""
        story.append(PageBreak())
        story.append(Paragraph("目录", self.styles['h1']))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e67e22'), spaceAfter=20))
        
        itinerary = plan_data.get('itinerary', [])
        heritage_items = plan_data.get('heritage_items', [])
        weather_info = plan_data.get('weather_info', {})
        route_info = plan_data.get('route_info', {})
        recommendations = plan_data.get('recommendations', {})
        
        toc_items = []
        toc_items.append("一、行程概览")
        
        for i, day_plan in enumerate(itinerary, 1):
            theme = day_plan.get('theme', f'第{i}天')
            toc_items.append(f"    {i}. {theme}")
        
        if heritage_items:
            toc_items.append("二、非遗项目介绍")
        
        if weather_info:
            toc_items.append("三、天气信息")
        
        if route_info:
            toc_items.append("四、路线详情")
        
        if recommendations:
            toc_items.append("五、实用贴士")
        
        for item in toc_items:
            story.append(Paragraph(item, self.styles['normal']))
        
        story.append(PageBreak())
    
    def _add_weather_section(self, story: List, weather_info: Dict[str, Any]):
        """添加天气信息部分"""
        story.append(PageBreak())
        story.append(Paragraph("天气信息", self.styles['h1']))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e67e22'), spaceAfter=15))
        
        locations = weather_info.get('locations', {})
        
        for location_name, weather_data in locations.items():
            story.append(Paragraph(f"{location_name} 天气预报", self.styles['h3']))
            
            forecasts = weather_data.get('forecasts', [])
            if forecasts:
                weather_table_data = [['日期', '天气', '温度', '风速']]
                
                for forecast in forecasts[:5]:
                    date = forecast.get('date', '')
                    weather = forecast.get('weather', '')
                    temp = f"{forecast.get('temp_min', '')}°C ~ {forecast.get('temp_max', '')}°C"
                    wind = forecast.get('wind', '')
                    weather_table_data.append([date, weather, temp, wind])
                
                weather_table = Table(weather_table_data, colWidths=[80, 80, 100, 80])
                weather_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2980b9')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                ]))
                
                story.append(weather_table)
                story.append(Spacer(1, 15))
    
    def _add_route_section(self, story: List, route_info: Dict[str, Any]):
        """添加路线详情部分"""
        story.append(PageBreak())
        story.append(Paragraph("路线详情", self.styles['h1']))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e67e22'), spaceAfter=15))
        
        total_distance = route_info.get('total_distance', 0)
        story.append(Paragraph(f"总行程距离: {total_distance} 公里", self.styles['highlight']))
        
        routes = route_info.get('routes', [])
        if routes:
            for i, route in enumerate(routes, 1):
                origin = route.get('origin', '')
                destination = route.get('destination', '')
                distance = route.get('distance', '')
                duration = route.get('duration', '')
                
                story.append(Paragraph(f"路段 {i}: {origin} → {destination}", self.styles['h3']))
                
                route_table_data = [
                    ['距离', '预计时间', '交通方式'],
                    [distance, duration, route.get('mode', '自驾')]
                ]
                
                route_table = Table(route_table_data, colWidths=[120, 120, 120])
                route_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16a085')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                ]))
                
                story.append(route_table)
                story.append(Spacer(1, 10))
        
        optimization_notes = route_info.get('optimization_notes', [])
        if optimization_notes:
            story.append(Paragraph("路线优化建议", self.styles['h3']))
            for note in optimization_notes[:5]:
                story.append(Paragraph(f"• {note}", self.styles['list']))
    
    def _add_footer_section(self, story: List, plan_data: Dict[str, Any]):
        """添加页脚部分"""
        story.append(Spacer(1, 30))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.gray, spaceAfter=15))
        
        story.append(Paragraph("关于本规划", self.styles['h3']))
        
        disclaimer = """
        本旅游规划由陕西非遗文化旅游智能助手生成，仅供参考。
        实际出行时请根据当地天气、交通等情况灵活调整。
        如需了解更多非遗项目信息，请访问陕西省文化和旅游厅官网。
        """
        story.append(Paragraph(disclaimer.strip(), self.styles['quote']))
        
        story.append(Spacer(1, 20))
        
        generated_time = datetime.now().strftime('%Y年%m月%d日 %H:%M')
        story.append(Paragraph(f"文档生成时间: {generated_time}", self.styles['footer']))
        story.append(Paragraph("陕西非遗文化旅游智能助手", self.styles['footer']))
    
    def _add_fallback_content(self, story: List, content: Dict[str, Any]):
        """添加备用内容"""
        story.append(Paragraph("旅游规划", self.styles['title']))
        story.append(Spacer(1, 20))
        story.append(Paragraph("无法生成详细内容，请联系管理员。", self.styles['normal']))


_optimized_pdf_generator: Optional[OptimizedPDFGenerator] = None


def get_optimized_pdf_generator() -> OptimizedPDFGenerator:
    """获取 PDF 生成器单例"""
    global _optimized_pdf_generator
    if _optimized_pdf_generator is None:
        _optimized_pdf_generator = OptimizedPDFGenerator()
    return _optimized_pdf_generator
