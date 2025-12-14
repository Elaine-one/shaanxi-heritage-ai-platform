from datetime import datetime
import math

def get_lunar_date():
    """获取农历日期"""
    # 这里使用简化版的农历转换，实际应用中应使用专业的农历转换库
    lunarMonths = ["正", "二", "三", "四", "五", "六", "七", "八", "九", "十", "冬", "腊"]
    lunarDays = ["初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十",
                "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十",
                "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十"]
    
    now = datetime.now()
    month = now.month
    day = now.day
    
    lunarMonth = lunarMonths[(month - 1) % 12]
    lunarDay = lunarDays[(day - 1) % 30]
    
    return f"农历{lunarMonth}月{lunarDay}"

def get_solar_term():
    """获取节气"""
    solarTerms = [
        {"name": "小寒", "month": 1, "day": 6},
        {"name": "大寒", "month": 1, "day": 20},
        {"name": "立春", "month": 2, "day": 4},
        {"name": "雨水", "month": 2, "day": 19},
        {"name": "惊蛰", "month": 3, "day": 6},
        {"name": "春分", "month": 3, "day": 21},
        {"name": "清明", "month": 4, "day": 5},
        {"name": "谷雨", "month": 4, "day": 20},
        {"name": "立夏", "month": 5, "day": 6},
        {"name": "小满", "month": 5, "day": 21},
        {"name": "芒种", "month": 6, "day": 6},
        {"name": "夏至", "month": 6, "day": 21},
        {"name": "小暑", "month": 7, "day": 7},
        {"name": "大暑", "month": 7, "day": 23},
        {"name": "立秋", "month": 8, "day": 8},
        {"name": "处暑", "month": 8, "day": 23},
        {"name": "白露", "month": 9, "day": 8},
        {"name": "秋分", "month": 9, "day": 23},
        {"name": "寒露", "month": 10, "day": 8},
        {"name": "霜降", "month": 10, "day": 24},
        {"name": "立冬", "month": 11, "day": 8},
        {"name": "小雪", "month": 11, "day": 22},
        {"name": "大雪", "month": 12, "day": 7},
        {"name": "冬至", "month": 12, "day": 22}
    ]
    
    now = datetime.now()
    month = now.month
    day = now.day
    
    for term in solarTerms:
        if term["month"] == month and abs(term["day"] - day) <= 1:
            return term["name"]
    
    return ""

def get_formatted_date():
    """获取格式化的日期时间，包括农历和节气"""
    now = datetime.now()
    weekdays = ["日", "一", "二", "三", "四", "五", "六"]
    
    formatted_date = {
        "year": now.year,
        "month": str(now.month).zfill(2),
        "day": str(now.day).zfill(2),
        "hour": str(now.hour).zfill(2),
        "minute": str(now.minute).zfill(2),
        "weekday": weekdays[now.weekday()],
        "lunar_date": get_lunar_date(),
        "solar_term": get_solar_term()
    }
    
    return formatted_date