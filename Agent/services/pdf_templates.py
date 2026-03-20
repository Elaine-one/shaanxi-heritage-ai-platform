# -*- coding: utf-8 -*-
"""
PDF 模板和样式
专业的旅游规划文档模板
"""

PDF_CSS_STYLE = """
<style>
/* 基础样式 */
body {
    font-family: 'Microsoft YaHei', 'SimHei', sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #2c3e50;
}

/* 标题样式 */
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

/* 段落样式 */
p {
    text-align: justify;
    margin-bottom: 10px;
}

/* 列表样式 */
ul, ol {
    margin-left: 20px;
    margin-bottom: 10px;
}

li {
    margin-bottom: 5px;
}

/* 引用块样式 */
blockquote {
    background-color: #f8f9fa;
    border-left: 4px solid #e67e22;
    padding: 10px 15px;
    margin: 15px 0;
    font-style: italic;
    color: #555;
}

/* 表格样式 */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 15px 0;
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
    background-color: #f2f2f2;
}

/* 强调样式 */
strong {
    color: #e67e22;
    font-weight: bold;
}

em {
    color: #8e44ad;
    font-style: italic;
}

/* 代码样式 */
code {
    background-color: #f4f4f4;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'Consolas', monospace;
    color: #e74c3c;
}

/* 分割线 */
hr {
    border: none;
    border-top: 1px solid #ddd;
    margin: 20px 0;
}

/* 时间轴样式 */
.timeline {
    margin: 15px 0;
    padding-left: 20px;
    border-left: 2px solid #e67e22;
}

.timeline-item {
    margin-bottom: 15px;
    position: relative;
}

.timeline-item::before {
    content: '';
    position: absolute;
    left: -26px;
    top: 5px;
    width: 10px;
    height: 10px;
    background-color: #e67e22;
    border-radius: 50%;
}

/* 提示框样式 */
.tip-box {
    background-color: #e8f6f3;
    border: 1px solid #16a085;
    border-radius: 5px;
    padding: 10px 15px;
    margin: 10px 0;
}

.warning-box {
    background-color: #fef9e7;
    border: 1px solid #f39c12;
    border-radius: 5px;
    padding: 10px 15px;
    margin: 10px 0;
}

/* 信息卡片 */
.info-card {
    background-color: #f8f9fa;
    border-radius: 8px;
    padding: 15px;
    margin: 15px 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
</style>
"""

PDF_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    {css}
</head>
<body>
    <div class="header">
        <h1>{main_title}</h1>
        <p class="subtitle">{subtitle}</p>
    </div>
    
    <div class="content">
        {content}
    </div>
    
    <div class="footer">
        <hr>
        <p class="footer-text">
            生成时间: {generated_time}<br>
            陕西非遗文化旅游智能助手
        </p>
    </div>
</body>
</html>
"""

PDF_COVER_TEMPLATE = """
<div class="cover-page">
    <div class="cover-title">
        <h1>{title}</h1>
        <p class="cover-subtitle">{subtitle}</p>
    </div>
    
    <div class="cover-info">
        <table class="cover-table">
            <tr>
                <td><strong>目的地</strong></td>
                <td>{destination}</td>
            </tr>
            <tr>
                <td><strong>出发地</strong></td>
                <td>{departure}</td>
            </tr>
            <tr>
                <td><strong>行程天数</strong></td>
                <td>{days}天</td>
            </tr>
            <tr>
                <td><strong>出行方式</strong></td>
                <td>{travel_mode}</td>
            </tr>
            <tr>
                <td><strong>出行人数</strong></td>
                <td>{group_size}人</td>
            </tr>
            <tr>
                <td><strong>预算范围</strong></td>
                <td>{budget}</td>
            </tr>
        </table>
    </div>
    
    <div class="cover-footer">
        <p>生成日期: {date}</p>
        <p>陕西非遗文化旅游智能助手</p>
    </div>
</div>
"""

PDF_DAY_TEMPLATE = """
<div class="day-section">
    <h2>第 {day} 天：{theme}</h2>
    
    <div class="day-overview">
        <p><strong>今日亮点：</strong>{highlight}</p>
        <p><strong>预计行程：</strong>{distance}</p>
    </div>
    
    <div class="timeline">
        {items}
    </div>
</div>
"""

PDF_ITEM_TEMPLATE = """
<div class="timeline-item">
    <h4>{time} | {name}</h4>
    <p>{description}</p>
    {extra_info}
</div>
"""

PDF_TIPS_TEMPLATE = """
<div class="tips-section">
    <h2>实用贴士</h2>
    
    <div class="tip-box">
        <h4>🌤️ 天气提示</h4>
        <p>{weather_tips}</p>
    </div>
    
    <div class="tip-box">
        <h4>🎒 行前准备</h4>
        <ul>
            {packing_list}
        </ul>
    </div>
    
    <div class="warning-box">
        <h4>⚠️ 注意事项</h4>
        <ul>
            {warnings}
        </ul>
    </div>
</div>
"""

PDF_HERITAGE_TEMPLATE = """
<div class="heritage-section">
    <h2>非遗项目介绍</h2>
    
    {heritage_items}
</div>
"""

PDF_HERITAGE_ITEM_TEMPLATE = """
<div class="info-card">
    <h3>{name}</h3>
    <p class="heritage-meta">
        <strong>地区：</strong>{region} | 
        <strong>级别：</strong>{level} | 
        <strong>类别：</strong>{category}
    </p>
    <p>{description}</p>
    <p><strong>文化价值：</strong>{value}</p>
</div>
"""


def get_pdf_style() -> str:
    """获取 PDF 样式"""
    return PDF_CSS_STYLE


def get_html_template() -> str:
    """获取 HTML 模板"""
    return PDF_HTML_TEMPLATE


def get_cover_template() -> str:
    """获取封面模板"""
    return PDF_COVER_TEMPLATE


def get_day_template() -> str:
    """获取日程模板"""
    return PDF_DAY_TEMPLATE


def get_item_template() -> str:
    """获取项目模板"""
    return PDF_ITEM_TEMPLATE


def get_tips_template() -> str:
    """获取贴士模板"""
    return PDF_TIPS_TEMPLATE


def get_heritage_template() -> str:
    """获取非遗介绍模板"""
    return PDF_HERITAGE_TEMPLATE


def get_heritage_item_template() -> str:
    """获取非遗项目模板"""
    return PDF_HERITAGE_ITEM_TEMPLATE
