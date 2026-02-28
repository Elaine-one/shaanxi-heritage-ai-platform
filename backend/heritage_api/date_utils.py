from datetime import datetime
from zhdate import ZhDate

def get_lunar_date(target_date=None):
    """获取农历日期
    
    Args:
        target_date: 目标日期（datetime对象），默认为当前日期
    
    Returns:
        str: 农历日期字符串，如"农历三月廿八"
    """
    if target_date is None:
        target_date = datetime.now()
    
    zh_date = ZhDate.from_datetime(target_date)
    lunar_month = zh_date.lunar_month
    lunar_day = zh_date.lunar_day
    
    month_names = ["正", "二", "三", "四", "五", "六", "七", "八", "九", "十", "冬", "腊"]
    day_names = ["初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十",
                "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十",
                "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十"]
    
    month_str = month_names[lunar_month - 1]
    day_str = day_names[lunar_day - 1]
    
    return f"农历{month_str}月{day_str}"

def get_solar_term(target_date=None):
    """获取节气
    
    Args:
        target_date: 目标日期（datetime对象），默认为当前日期
    
    Returns:
        str: 节气名称，如"清明"，如果不是节气日则返回空字符串
    """
    if target_date is None:
        target_date = datetime.now()
    
    zh_date = ZhDate.from_datetime(target_date)
    return zh_date.solar_term() if hasattr(zh_date, 'solar_term') else ""

def get_formatted_date(target_date=None):
    """获取格式化的日期时间，包括农历和节气
    
    Args:
        target_date: 目标日期（datetime对象），默认为当前日期
    
    Returns:
        dict: 包含年月日时分秒、星期、农历日期和节气的字典
    """
    if target_date is None:
        target_date = datetime.now()
    
    weekdays = ["日", "一", "二", "三", "四", "五", "六"]
    
    formatted_date = {
        "year": target_date.year,
        "month": str(target_date.month).zfill(2),
        "day": str(target_date.day).zfill(2),
        "hour": str(target_date.hour).zfill(2),
        "minute": str(target_date.minute).zfill(2),
        "weekday": weekdays[target_date.weekday()],
        "lunar_date": get_lunar_date(target_date),
        "solar_term": get_solar_term(target_date)
    }
    
    return formatted_date