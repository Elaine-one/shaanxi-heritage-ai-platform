# -*- coding: utf-8 -*-
"""
PDF生成器
使用 ReportLab 生成 PDF，支持专业排版、表格和图片嵌入
"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


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
        """注册中文字体"""
        font_paths = [
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/simsun.ttc",
            "/System/Library/Fonts/PingFang.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
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
        """创建样式"""
        styles = getSampleStyleSheet()
        
        COLOR_PRIMARY = colors.HexColor('#2c3e50')
        COLOR_ACCENT = colors.HexColor('#e67e22')
        COLOR_H1 = colors.HexColor('#8e44ad')
        COLOR_H2 = colors.HexColor('#2980b9')
        COLOR_H3 = colors.HexColor('#16a085')
        
        custom_styles = {
            'title': ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontName=self.chinese_font,
                fontSize=26,
                leading=34,
                alignment=TA_CENTER,
                spaceAfter=20,
                textColor=COLOR_H1
            ),
            'subtitle': ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Normal'],
                fontName=self.chinese_font,
                fontSize=12,
                leading=16,
                alignment=TA_CENTER,
                spaceAfter=30,
                textColor=colors.gray
            ),
            'h1': ParagraphStyle(
                'CustomH1',
                parent=styles['Heading1'],
                fontName=self.chinese_font,
                fontSize=18,
                leading=24,
                spaceBefore=20,
                spaceAfter=12,
                textColor=COLOR_H1
            ),
            'h2': ParagraphStyle(
                'CustomH2',
                parent=styles['Heading2'],
                fontName=self.chinese_font,
                fontSize=15,
                leading=20,
                spaceBefore=15,
                spaceAfter=10,
                textColor=COLOR_H2
            ),
            'h3': ParagraphStyle(
                'CustomH3',
                parent=styles['Heading3'],
                fontName=self.chinese_font,
                fontSize=13,
                leading=18,
                spaceBefore=12,
                spaceAfter=8,
                textColor=COLOR_H3
            ),
            'normal': ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontName=self.chinese_font,
                fontSize=11,
                leading=16,
                alignment=TA_JUSTIFY,
                spaceAfter=8,
                textColor=COLOR_PRIMARY
            ),
            'list': ParagraphStyle(
                'CustomList',
                parent=styles['Normal'],
                fontName=self.chinese_font,
                fontSize=11,
                leading=16,
                leftIndent=15,
                spaceAfter=4,
                textColor=COLOR_PRIMARY
            ),
            'quote': ParagraphStyle(
                'CustomQuote',
                parent=styles['Normal'],
                fontName=self.chinese_font,
                fontSize=10,
                leading=14,
                leftIndent=20,
                rightIndent=20,
                spaceBefore=10,
                spaceAfter=10,
                textColor=colors.HexColor('#555555'),
                backColor=colors.HexColor('#f8f9fa')
            ),
            'highlight': ParagraphStyle(
                'CustomHighlight',
                parent=styles['Normal'],
                fontName=self.chinese_font,
                fontSize=11,
                leading=16,
                textColor=COLOR_ACCENT
            ),
            'footer': ParagraphStyle(
                'CustomFooter',
                parent=styles['Normal'],
                fontName=self.chinese_font,
                fontSize=9,
                leading=12,
                alignment=TA_CENTER,
                textColor=colors.gray
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
                rightMargin=20*mm,
                leftMargin=20*mm,
                topMargin=25*mm,
                bottomMargin=25*mm
            )
            
            story = []
            
            content_type = content.get('content_type', 'rich_text')
            
            if content_type == 'rich_text':
                text_content = content.get('text_content', '')
                self._parse_markdown_to_story(story, text_content)
            elif content_type == 'structured':
                self._build_structured_content(story, content)
            else:
                self._add_fallback_content(story, content)
            
            doc.build(story, onFirstPage=self._add_page_header, onLaterPages=self._add_page_header)
            
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
        """添加页眉页脚"""
        canvas.saveState()
        
        canvas.setFont(self.chinese_font, 9)
        canvas.setFillColor(colors.gray)
        
        canvas.drawString(doc.leftMargin, doc.height + doc.topMargin + 10*mm, "陕西非遗文化旅游规划")
        
        canvas.drawCentredString(doc.width / 2 + doc.leftMargin, 10*mm, f"第 {doc.page} 页")
        
        canvas.restoreState()
    
    def _remove_emojis(self, text: str) -> str:
        """处理不支持的 emoji"""
        emoji_replacements = {
            '📢': '【定制说明】',
            '🎒': '【行前准备】',
            '🚗': '【出行方式】',
            '💰': '【费用预算】',
            '📜': '【每日行程】',
            '🍽️': '【今日三餐】',
            '📍': '【项目详情】',
            '💡': '【实用贴士】',
            '★': '*',
            '☆': ' ',
            '✓': '√',
            '✗': '×',
        }
        
        for emoji, replacement in emoji_replacements.items():
            text = text.replace(emoji, replacement)
        
        return text
    
    def _parse_markdown_to_story(self, story: List, text: str):
        """解析 Markdown 内容，支持表格和 emoji 处理"""
        lines = text.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            i += 1
            
            if not line:
                continue
            
            line = self._remove_emojis(line)
            line = self._process_inline_markdown(line)
            
            if line.startswith('# ') and not line.startswith('## '):
                story.append(Spacer(1, 10))
                story.append(Paragraph(line[2:], self.styles['title']))
                story.append(HRFlowable(width="60%", thickness=2, color=colors.HexColor('#e67e22'), spaceAfter=20))
            
            elif line.startswith('## '):
                story.append(Spacer(1, 15))
                story.append(Paragraph(line[3:], self.styles['h1']))
                story.append(HRFlowable(width="30%", thickness=1, color=colors.HexColor('#2980b9'), spaceAfter=10))
            
            elif line.startswith('### '):
                story.append(Spacer(1, 8))
                story.append(Paragraph(line[4:], self.styles['h2']))
            
            elif line.startswith('#### '):
                story.append(Spacer(1, 6))
                story.append(Paragraph(line[5:], self.styles['h3']))
            
            elif line.startswith('> '):
                story.append(Spacer(1, 5))
                story.append(Paragraph(line[2:], self.styles['quote']))
                story.append(Spacer(1, 5))
            
            elif line == '---' or line == '***':
                story.append(Spacer(1, 15))
                story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#95a5a6'), spaceAfter=15))
            
            elif line.startswith('|'):
                i = self._parse_markdown_table(story, lines, i - 1)
            
            elif line.startswith('- ') or line.startswith('* '):
                content = line[2:]
                if '|' in content and self._is_time_format(content.split('|')[0].strip()):
                    parts = content.split('|', 1)
                    if len(parts) == 2:
                        formatted = f"<b>{parts[0].strip()}</b> | {parts[1].strip()}"
                        story.append(Paragraph(formatted, self.styles['list']))
                        continue
                story.append(Paragraph(f"• {content}", self.styles['list']))
            
            else:
                story.append(Paragraph(line, self.styles['normal']))
    
    def _parse_markdown_table(self, story: List, lines: List[str], start_idx: int) -> int:
        """解析 Markdown 表格，支持自动换行"""
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
                
                style = TableStyle([
                    ('FONTNAME', (0, 0), (-1, 0), self.chinese_font),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                    ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 1), (-1, -1), 'TOP'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 10),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#2c3e50')),
                    ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#2c3e50')),
                ])
                
                if len(formatted_data) > 1:
                    style.add('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecf0f1')])
                
                table.setStyle(style)
                story.append(Spacer(1, 12))
                story.append(table)
                story.append(Spacer(1, 12))
                
            except Exception as e:
                logger.warning(f"表格渲染失败: {e}")
        
        return i
    
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
                    result.append(f'<font color="#e67e22"><b>{content}</b></font>')
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
    
    def _add_cover_page(self, story: List, plan_data: Dict[str, Any]):
        """添加封面"""
        story.append(Spacer(1, 50))
        
        title = plan_data.get('basic_info', {}).get('title', '陕西非遗文化旅游规划')
        story.append(Paragraph(title, self.styles['title']))
        story.append(HRFlowable(width="60%", thickness=2, color=colors.HexColor('#e67e22'), spaceAfter=30))
        
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
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2980b9')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2c3e50')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 30))
        
        story.append(Paragraph(f"生成时间: {datetime.now().strftime('%Y年%m月%d日')}", self.styles['footer']))
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
