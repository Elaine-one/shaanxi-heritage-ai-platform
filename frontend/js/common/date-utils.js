/**
 * 日期时间工具模块
 * 提供统一的日期时间格式化和显示功能
 */

// 日期时间格式选项
const DATE_FORMAT_OPTIONS = {
    // 完整格式：年月日 星期 时分
    FULL: {
        year: 'numeric', 
        month: 'long', 
        day: 'numeric', 
        weekday: 'long',
        hour: '2-digit',
        minute: '2-digit'
    },
    // 日期格式：年月日 星期
    DATE_ONLY: {
        year: 'numeric', 
        month: 'long', 
        day: 'numeric', 
        weekday: 'long'
    },
    // 时间格式：时分
    TIME_ONLY: {
        hour: '2-digit',
        minute: '2-digit'
    }
};

/**
 * 获取格式化的日期时间字符串
 * @param {Object} options 格式化选项
 * @returns {string} 格式化后的日期时间字符串
 */
function getFormattedDateTime(options = DATE_FORMAT_OPTIONS.FULL) {
    const now = new Date();
    return now.toLocaleDateString('zh-CN', options);
}

/**
 * 获取农历日期
 * @returns {string} 农历日期字符串
 */
function getLunarDate() {
    const now = new Date();

    // Ensure LunarSolarConverter is available
    if (typeof LunarSolarConverter === 'undefined') {
        console.error('LunarSolarConverter is not loaded.');
        return '农历获取失败';
    }

    const converter = new LunarSolarConverter();
    const lunar = converter.Lunar(now);

    // 添加调试日志，以便观察从库返回的lunar对象
    console.log('Calculated Lunar Object:', JSON.stringify(lunar));

    const lunarMonths = ["", "正", "二", "三", "四", "五", "六", "七", "八", "九", "十", "冬", "腊"];
    const lunarDays = [
        "", "初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十",
        "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十",
        "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十"
    ];

    // 对 lunarDay 进行取整处理
    const dayIndex = Math.floor(lunar.lunarDay);
    
    let lunarDateStr = `农历`;
    if (lunar.isLeap) {
        lunarDateStr += '闰';
    }

    const monthName = lunarMonths[lunar.lunarMonth];
    let dayName = lunarDays[dayIndex]; // 使用取整后的索引

    // 有效性检查
    if (dayIndex < 1 || dayIndex > 30) {
        console.error(`Invalid lunar day index: ${dayIndex}`, lunar);
        dayName = '日期异常';
    }
    else if (dayName === undefined) {
        console.warn(`Lunar day ${dayIndex} mapping failed`, lunar);
        dayName = '未知日';
    }

    lunarDateStr += `${monthName}月${dayName}`;
    return lunarDateStr;
}

/**
 * 获取节气
 * @returns {string} 节气字符串，如果当天不是节气则返回空字符串
 */
function getSolarTerm() {
    const now = new Date();
    const month = now.getMonth() + 1;
    const day = now.getDate();
    
    // 简化的节气判断，实际应该使用更精确的计算
    const solarTerms = [
        {name: "立春", month: 2, day: 4},
        {name: "雨水", month: 2, day: 19},
        {name: "惊蛰", month: 3, day: 6},
        {name: "春分", month: 3, day: 21},
        {name: "清明", month: 4, day: 5},
        {name: "谷雨", month: 4, day: 20},
        {name: "立夏", month: 5, day: 6},
        {name: "小满", month: 5, day: 21},
        {name: "芒种", month: 6, day: 6},
        {name: "夏至", month: 6, day: 21},
        {name: "小暑", month: 7, day: 7},
        {name: "大暑", month: 7, day: 23},
        {name: "立秋", month: 8, day: 8},
        {name: "处暑", month: 8, day: 23},
        {name: "白露", month: 9, day: 8},
        {name: "秋分", month: 9, day: 23},
        {name: "寒露", month: 10, day: 8},
        {name: "霜降", month: 10, day: 24},
        {name: "立冬", month: 11, day: 8},
        {name: "小雪", month: 11, day: 22},
        {name: "大雪", month: 12, day: 7},
        {name: "冬至", month: 12, day: 22},
        {name: "小寒", month: 1, day: 6},
        {name: "大寒", month: 1, day: 20}
    ];
    
    for (let term of solarTerms) {
        // 简单判断，实际应该考虑年份差异
        if (term.month === month && Math.abs(term.day - day) <= 1) {
            return term.name;
        }
    }
    
    return "";
}

/**
 * 更新页面上的日期时间显示
 * @param {string} elementId 日期时间元素的ID
 * @param {Object} options 格式化选项
 */
function updateDateTimeDisplay(elementId = 'current-date', options = DATE_FORMAT_OPTIONS.FULL) {
    const dateElement = document.getElementById(elementId);
    if (!dateElement) return;

    const dateInfo = getFullDateTimeInfo();
    let dateTimeStr;

    switch(options) {
        case DATE_FORMAT_OPTIONS.FULL:
            dateTimeStr = `${dateInfo.formatted} ${dateInfo.time} ${dateInfo.lunar_date}`;
            if (dateInfo.solar_term) {
                dateTimeStr += ` ${dateInfo.solar_term}`;
            }
            break;
        default:
            dateTimeStr = dateInfo.formatted;
    }

    dateElement.textContent = dateTimeStr;
}

/**
 * 获取完整的日期时间信息（包括农历和节气）
 * @returns {Object} 包含日期时间信息的对象
 */
function getFullDateTimeInfo() {
    const now = new Date();
    return {
        date: now,
        formatted: getFormattedDateTime(DATE_FORMAT_OPTIONS.DATE_ONLY),
        time: getFormattedDateTime(DATE_FORMAT_OPTIONS.TIME_ONLY),
        weekday: now.toLocaleDateString('zh-CN', { weekday: 'long' }),
        lunar_date: getLunarDate(),
        solar_term: getSolarTerm()
    };
}

// 添加DOM就绪监听
document.addEventListener('DOMContentLoaded', function() {
    const dateElement = document.getElementById('current-date');
    if (dateElement) {
        updateDateTimeDisplay();
        setInterval(updateDateTimeDisplay, 60000);
    }
});

// 导出模块
const dateUtils = {
    FORMAT: DATE_FORMAT_OPTIONS,
    getFormattedDateTime,
    getLunarDate,
    getSolarTerm,
    updateDateTimeDisplay,
    getFullDateTimeInfo
};

// 如果在浏览器环境中，将模块添加到全局对象
if (typeof window !== 'undefined') {
    window.dateUtils = dateUtils;
}

// 全局暴露 dateUtils