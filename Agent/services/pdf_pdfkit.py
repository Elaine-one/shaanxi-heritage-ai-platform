# -*- coding: utf-8 -*-
"""
基于 pdfkit 的 PDF 生成器
使用 wkhtmltopdf 引擎，支持 HTML + CSS 渲染
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger

import markdown

_PDFKIT_AVAILABLE = False
try:
    import pdfkit
    _PDFKIT_AVAILABLE = True
except ImportError:
    logger.warning("pdfkit 未安装，请运行: pip install pdfkit")


class PDFKitGenerator:
    """
    基于 pdfkit 的 PDF 生成器
    使用 wkhtmltopdf 引擎，支持 HTML + CSS 渲染
    
    依赖:
    - pdfkit: pip install pdfkit
    - wkhtmltopdf: https://wkhtmltopdf.org/downloads.html
    """
    
    WKHTMLTOPDF_PATH = None
    
    CSS_STYLE = """
    <style>
        @page {
            size: A4;
            margin: 2cm;
        }
        
        * {
            font-family: 'Microsoft YaHei', 'SimHei', 'PingFang SC', sans-serif;
        }
        
        body {
            font-size: 11pt;
            line-height: 1.6;
            color: #2c3e50;
            max-width: 210mm;
            margin: 0 auto;
        }
        
        h1 {
            font-size: 24pt;
            color: #8e44ad;
            text-align: center;
            margin-bottom: 20px;
            border-bottom: 2px solid #e67e22;
            padding-bottom: 10px;
        }
        
        h2 {
            font-size: 16pt;
            color: #2980b9;
            margin-top: 25px;
            margin-bottom: 15px;
            border-left: 4px solid #e67e22;
            padding-left: 10px;
        }
        
        h3 {
            font-size: 14pt;
            color: #16a085;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        
        h4 {
            font-size: 12pt;
            color: #34495e;
            margin-top: 15px;
            margin-bottom: 8px;
        }
        
        p {
            text-align: justify;
            margin-bottom: 10px;
        }
        
        ul, ol {
            margin-left: 20px;
            margin-bottom: 10px;
        }
        
        li {
            margin-bottom: 5px;
        }
        
        blockquote {
            background-color: #f8f9fa;
            border-left: 4px solid #e67e22;
            padding: 10px 15px;
            margin: 15px 0;
            color: #555;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 10pt;
        }
        
        th, td {
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: left;
        }
        
        th {
            background-color: #2980b9;
            color: white;
            font-weight: bold;
        }
        
        tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        
        hr {
            border: none;
            border-top: 1px solid #e67e22;
            margin: 20px 0;
        }
        
        strong {
            color: #e67e22;
        }
        
        em {
            color: #8e44ad;
        }
        
        code {
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            color: #e74c3c;
        }
        
        .highlight {
            color: #e67e22;
            font-weight: bold;
        }
        
        .info-box {
            background-color: #e3f2fd;
            border: 1px solid #2196f3;
            border-radius: 4px;
            padding: 10px;
            margin: 10px 0;
        }
        
        .warning-box {
            background-color: #fff3e0;
            border: 1px solid #ff9800;
            border-radius: 4px;
            padding: 10px;
            margin: 10px 0;
        }
        
        .footer {
            text-align: center;
            color: #666;
            margin-top: 30px;
            font-size: 10pt;
        }
    </style>
    """
    
    def __init__(self, pdf_cache_dir: Optional[str] = None, wkhtmltopdf_path: Optional[str] = None):
        if pdf_cache_dir is None:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            pdf_cache_dir = os.path.join(project_root, 'pdf_cache')
        
        self.pdf_cache_dir = pdf_cache_dir
        if not os.path.exists(self.pdf_cache_dir):
            os.makedirs(self.pdf_cache_dir, exist_ok=True)
        
        self._find_wkhtmltopdf(wkhtmltopdf_path)
        
        if self.WKHTMLTOPDF_PATH and os.path.exists(self.WKHTMLTOPDF_PATH):
            self.config = pdfkit.configuration(wkhtmltopdf=self.WKHTMLTOPDF_PATH)
            self._available = True
            logger.info(f"pdfkit PDF 生成器初始化完成，wkhtmltopdf: {self.WKHTMLTOPDF_PATH}")
        else:
            self._available = False
            logger.warning("wkhtmltopdf 未找到，PDF生成功能不可用")
    
    def _find_wkhtmltopdf(self, custom_path: Optional[str] = None):
        """查找 wkhtmltopdf 可执行文件"""
        import subprocess
        
        if custom_path and os.path.exists(custom_path):
            self.WKHTMLTOPDF_PATH = custom_path
            return
        
        # 使用 subprocess 检测（带完整 PATH）
        try:
            result = subprocess.run(['wkhtmltopdf', '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.WKHTMLTOPDF_PATH = 'wkhtmltopdf'
                return
        except:
            pass
        
        # 检查常见路径
        common_paths = [
            r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe",
            r"C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe",
            r"D:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe",
            os.environ.get('ProgramFiles', '') + r"\wkhtmltopdf\bin\wkhtmltopdf.exe" if os.environ.get('ProgramFiles') else None,
            os.environ.get('ProgramFiles(x86)', '') + r"\wkhtmltopdf\bin\wkhtmltopdf.exe" if os.environ.get('ProgramFiles(x86)') else None,
            os.environ.get('LocalAppData', '') + r"\Programs\wkhtmltopdf\wkhtmltopdf\bin\wkhtmltopdf.exe" if os.environ.get('LocalAppData') else None,
            "/usr/local/bin/wkhtmltopdf",
            "/usr/bin/wkhtmltopdf",
        ]
        
        for path in common_paths:
            if path and os.path.exists(path):
                self.WKHTMLTOPDF_PATH = path
                return
        
        # 如果仍然找不到，尝试从 PATH 环境变量中查找
        path_env = os.environ.get('PATH', '')
        if path_env:
            for path_dir in path_env.split(os.pathsep):
                wkhtmltopdf_path = os.path.join(path_dir, 'wkhtmltopdf.exe')
                if os.path.exists(wkhtmltopdf_path):
                    self.WKHTMLTOPDF_PATH = wkhtmltopdf_path
                    return
        
        self.WKHTMLTOPDF_PATH = None
    
    def is_available(self) -> bool:
        """检查 PDF 生成器是否可用"""
        return self._available and _PDFKIT_AVAILABLE
    
    def _markdown_to_html(self, markdown_text: str) -> str:
        """将 Markdown 转换为 HTML"""
        extensions = [
            'markdown.extensions.extra',
            'markdown.extensions.codehilite',
            'markdown.extensions.tables',
            'markdown.extensions.toc',
            'markdown.extensions.nl2br',
            'markdown.extensions.sane_lists',
        ]
        
        html = markdown.markdown(markdown_text, extensions=extensions)
        return html
    
    def _build_html_document(self, content: Dict[str, Any]) -> str:
        """构建完整的 HTML 文档"""
        content_type = content.get('content_type', 'rich_text')
        
        if content_type == 'rich_text':
            text_content = content.get('text_content', '')
            body_html = self._markdown_to_html(text_content)
        elif content_type == 'structured':
            body_html = self._build_structured_html(content)
        else:
            body_html = "<p>无法生成详细内容，请联系管理员。</p>"
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>陕西非遗文化旅游规划</title>
    {self.CSS_STYLE}
</head>
<body>
    {body_html}
    
    <div class="footer">
        <hr>
        <p>文档生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}</p>
        <p>陕西非遗文化旅游智能助手</p>
    </div>
</body>
</html>"""
        
        return html
    
    def _build_structured_html(self, content: Dict[str, Any]) -> str:
        """构建结构化内容的 HTML"""
        plan_data = content.get('plan_data', {})
        
        html_parts = []
        
        html_parts.append(self._build_cover_html(plan_data))
        
        itinerary = plan_data.get('itinerary', [])
        for day_plan in itinerary:
            html_parts.append(self._build_day_html(day_plan))
        
        heritage_items = plan_data.get('heritage_items', [])
        if heritage_items:
            html_parts.append(self._build_heritage_html(heritage_items))
        
        recommendations = plan_data.get('recommendations', {})
        if recommendations:
            html_parts.append(self._build_tips_html(recommendations))
        
        return '\n'.join(html_parts)
    
    def _build_cover_html(self, plan_data: Dict[str, Any]) -> str:
        """构建封面 HTML"""
        basic_info = plan_data.get('basic_info', {})
        title = basic_info.get('title', '陕西非遗文化旅游规划')
        
        return f"""
        <h1>{title}</h1>
        <hr>
        <p><strong>目的地：</strong>{basic_info.get('destination', '陕西')}</p>
        <p><strong>出发地：</strong>{basic_info.get('departure', '未指定')}</p>
        <p><strong>行程天数：</strong>{basic_info.get('travel_days', 3)} 天</p>
        <p><strong>出行方式：</strong>{basic_info.get('travel_mode', '自驾')}</p>
        <p><strong>预算范围：</strong>{basic_info.get('budget_range', '中等')}</p>
        """
    
    def _build_day_html(self, day_plan: Dict[str, Any]) -> str:
        """构建每日行程 HTML"""
        day = day_plan.get('day', 1)
        theme = day_plan.get('theme', f'第 {day} 天行程')
        
        html_parts = [f'<h2>第 {day} 天：{theme}</h2>']
        
        items = day_plan.get('items', [])
        if items:
            html_parts.append('<table>')
            html_parts.append('<thead><tr><th>时间</th><th>项目</th><th>地点</th><th>备注</th></tr></thead>')
            html_parts.append('<tbody>')
            for item in items:
                name = item.get('name', '未命名')
                time = item.get('time', '待定')
                location = item.get('location', '')
                description = item.get('description', '')[:50]
                html_parts.append(f'<tr><td>{time}</td><td>{name}</td><td>{location}</td><td>{description}</td></tr>')
            html_parts.append('</tbody></table>')
        
        return '\n'.join(html_parts)
    
    def _build_heritage_html(self, heritage_items: list) -> str:
        """构建非遗介绍 HTML"""
        html_parts = ['<h2>非遗项目介绍</h2>', '<hr>']
        
        for item in heritage_items[:5]:
            name = item.get('name', '未知项目')
            region = item.get('region', '')
            level = item.get('level', '')
            description = item.get('description', '')[:200]
            
            html_parts.append(f'<h3>{name}</h3>')
            html_parts.append(f'<p class="highlight">地区: {region} | 级别: {level}</p>')
            if description:
                html_parts.append(f'<p>{description}</p>')
        
        return '\n'.join(html_parts)
    
    def _build_tips_html(self, recommendations: Dict[str, Any]) -> str:
        """构建贴士 HTML"""
        html_parts = ['<h2>实用贴士</h2>', '<hr>']
        
        travel_tips = recommendations.get('travel_tips', [])
        if travel_tips:
            html_parts.append('<h3>旅行建议</h3>')
            html_parts.append('<ul>')
            for tip in travel_tips[:5]:
                html_parts.append(f'<li>{tip}</li>')
            html_parts.append('</ul>')
        
        packing_list = recommendations.get('packing_list', [])
        if packing_list:
            html_parts.append('<h3>行前准备</h3>')
            html_parts.append('<ul>')
            for item in packing_list[:8]:
                html_parts.append(f'<li>{item}</li>')
            html_parts.append('</ul>')
        
        return '\n'.join(html_parts)
    
    async def generate_pdf_document(self, content: Dict[str, Any], output_filename: Optional[str] = None) -> Dict[str, Any]:
        """
        生成 PDF 文档
        
        Args:
            content: 内容数据
            output_filename: 输出文件名
        
        Returns:
            Dict: 生成结果
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'pdfkit 或 wkhtmltopdf 不可用',
                'message': 'PDF 生成器不可用'
            }
        
        try:
            if not output_filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_filename = f'Travel_Plan_{timestamp}.pdf'
            
            if not output_filename.endswith('.pdf'):
                output_filename += '.pdf'
            
            output_path = os.path.join(self.pdf_cache_dir, output_filename)
            
            logger.info(f"开始生成 PDF (pdfkit): {output_path}")
            
            html_content = self._build_html_document(content)
            
            options = {
                'page-size': 'A4',
                'margin-top': '20mm',
                'margin-right': '20mm',
                'margin-bottom': '20mm',
                'margin-left': '20mm',
                'encoding': 'UTF-8',
                'enable-local-file-access': None,
                'quiet': '',
            }
            
            pdfkit.from_string(html_content, output_path, configuration=self.config, options=options)
            
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


_pdfkit_generator: Optional[PDFKitGenerator] = None


def get_pdfkit_generator(wkhtmltopdf_path: Optional[str] = None) -> PDFKitGenerator:
    """获取 pdfkit PDF 生成器单例"""
    global _pdfkit_generator
    if _pdfkit_generator is None:
        _pdfkit_generator = PDFKitGenerator(wkhtmltopdf_path=wkhtmltopdf_path)
    return _pdfkit_generator
