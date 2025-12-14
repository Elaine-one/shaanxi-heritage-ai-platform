/**
 * @author isee15
 * @description Lunar-Solar-Calendar-Converter
 * https://github.com/isee15/Lunar-Solar-Calendar-Converter
 */

var lunarInfo = [
    0x04bd8, 0x04ae0, 0x0a570, 0x054d5, 0x0d260, 0x0d950, 0x16554, 0x056a0, 0x09ad0, 0x055d2,
    0x04ae0, 0x0a5b6, 0x0a4d0, 0x0d250, 0x1d255, 0x0b540, 0x0d6a0, 0x0ada2, 0x095b0, 0x14977,
    0x04970, 0x0a4b0, 0x0b4b5, 0x06a50, 0x06d40, 0x1ab54, 0x02b60, 0x09570, 0x052f2, 0x04970,
    0x06566, 0x0d4a0, 0x0ea50, 0x06e95, 0x05ad0, 0x02b60, 0x186e3, 0x092e0, 0x1c8d7, 0x0c950,
    0x0d4a0, 0x1d8a6, 0x0b550, 0x056a0, 0x1a5b4, 0x025d0, 0x092d0, 0x0d2b2, 0x0a950, 0x0b557,
    0x06ca0, 0x0b550, 0x15355, 0x04da0, 0x0a5d0, 0x14573, 0x052d0, 0x0a9a8, 0x0e950, 0x06aa0,
    0x0aea6, 0x0ab50, 0x04b60, 0x0aae4, 0x0a570, 0x05260, 0x0f263, 0x0d950, 0x05b57, 0x056a0,
    0x096d0, 0x04dd5, 0x04ad0, 0x0a4d0, 0x0d4d4, 0x0d250, 0x0d558, 0x0b540, 0x0b5a0, 0x195a6,
    0x095b0, 0x049b0, 0x0a974, 0x0a4b0, 0x0b27a, 0x06a50, 0x06d40, 0x0af46, 0x0ab60, 0x09570,
    0x04af5, 0x04970, 0x064b0, 0x074a3, 0x0ea50, 0x06b58, 0x055c0, 0x0ab60, 0x096d5, 0x092e0,
    0x0c960, 0x0d954, 0x0d4a0, 0x0da50, 0x07552, 0x056a0, 0x0abb7, 0x025d0, 0x092d0, 0x0cab5,
    0x0a950, 0x0b4a0, 0x0baa4, 0x0ad50, 0x055d9, 0x04ba0, 0x0a5b0, 0x15176, 0x052b0, 0x0a930,
    0x07954, 0x06aa0, 0x0ad50, 0x05b52, 0x04b60, 0x0a6e6, 0x0a4e0, 0x0d260, 0x0ea65, 0x0d530,
    0x05aa0, 0x076a3, 0x096d0, 0x04bd7, 0x04ad0, 0x0a4d0, 0x1d0b6, 0x0d250, 0x0d520, 0x0dd45,
    0x0b5a0, 0x056d0, 0x055b2, 0x049b0, 0x0a577, 0x0a4b0, 0x0aa50, 0x1b255, 0x06d20, 0x0ada0
];

var solarMonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
var Gan = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"];
var Zhi = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"];
var Animals = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"];
var solarTerm = ["小寒", "大寒", "立春", "雨水", "惊蛰", "春分", "清明", "谷雨", "立夏", "小满", "芒种", "夏至", "小暑", "大暑", "立秋", "处暑", "白露", "秋分", "寒露", "霜降", "立冬", "小雪", "大雪", "冬至"];
var sTermInfo = [0, 21208, 42467, 63836, 85337, 107014, 128867, 150921, 173149, 195551, 218072, 240693, 263343, 285989, 308563, 331033, 353350, 375494, 397447, 419210, 440795, 462224, 483532, 504758];
var nStr1 = ['日', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十'];
var nStr2 = ['初', '十', '廿', '卅', ' '];
var monthName = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];

//公历节日
var sFtv = [
    "0101*元旦",
    "0214 情人节",
    "0308 妇女节",
    "0312 植树节",
    "0315 消费者权益日",
    "0401 愚人节",
    "0501 劳动节",
    "0504 青年节",
    "0512 护士节",
    "0601 儿童节",
    "0701 建党节",
    "0801 建军节",
    "0909 毛泽东逝世纪念",
    "0910 教师节",
    "0928 孔子诞辰",
    "1001*国庆节",
    "1006 老人节",
    "1024 联合国日",
    "1224 平安夜",
    "1225 圣诞节"
];

//农历节日
var lFtv = [
    "0101*春节",
    "0115 元宵节",
    "0505 端午节",
    "0707 七夕情人节",
    "0715 中元节",
    "0815 中秋节",
    "0909 重阳节",
    "1208 腊八节",
    "1224 小年",
    "0100*除夕"
];

/**
 * LunarSolarConverter
 * @constructor
 */
function LunarSolarConverter() {
}

/**
 * 传入offset 返回干支, 0=甲子
 * @param {number} objDate
 * @return {string}
 */
LunarSolarConverter.prototype.cyclical = function (num) {
    return (Gan[num % 10] + Zhi[num % 12]);
};

/**
 * 返回公历年节气的日期
 * @param {number} year 公历年
 * @param {number} n 第几个节气
 * @return {number}
 */
LunarSolarConverter.prototype.sTerm = function (year, n) {
    var offDate = new Date((31556925974.7 * (year - 1900) + sTermInfo[n] * 60000) + Date.UTC(1900, 0, 6, 2, 5));
    return (offDate.getUTCDate());
};

/**
 * 返回农历y年闰月的天数
 * @param {number} y 农历y年
 * @return {number}
 */
LunarSolarConverter.prototype.leapDays = function (y) {
    if (this.leapMonth(y))
        return ((lunarInfo[y - 1900] & 0x10000) ? 30 : 29);
    else
        return (0);
};

/**
 * 返回农历y年闰哪个月 1-12 , 没闰返回0
 * @param {number} y 农历y年
 * @return {number}
 */
LunarSolarConverter.prototype.leapMonth = function (y) {
    return (lunarInfo[y - 1900] & 0xf);
};

/**
 * 返回农历y年m月的总天数
 * @param {number} y 农历y年
 * @param {number} m 农历m月
 * @return {number}
 */
LunarSolarConverter.prototype.monthDays = function (y, m) {
    return ((lunarInfo[y - 1900] & (0x10000 >> m)) ? 30 : 29);
};

/**
 * 农历年份转换为干支年份
 * @param {number} lYear 农历年份
 * @return {string}
 */
LunarSolarConverter.prototype.toGanZhiYear = function (lYear) {
    var ganKey = (lYear - 3) % 10;
    var zhiKey = (lYear - 3) % 12;
    if (ganKey == 0) ganKey = 10; // 如果余数为0则为最后一个天干
    if (zhiKey == 0) zhiKey = 12; // 如果余数为0则为最后一个地支
    return Gan[ganKey - 1] + Zhi[zhiKey - 1];
};

/**
 * 公历月、日判断所属星座
 * @param {number} cMonth 公历月
 * @param {number} cDay 公历日
 * @return {string}
 */
LunarSolarConverter.prototype.toAstro = function (cMonth, cDay) {
    var s = "魔羯水瓶双鱼 Aries Taurus Gemini Cancer Leo Virgo Libra Scorpio Sagittarius 魔羯".split(' ');
    var arr = [20, 19, 21, 21, 21, 22, 23, 23, 23, 23, 22, 22];
    return s[cMonth - 1 + (cDay >= arr[cMonth - 1] ? 1 : 0)];
};

/**
 * 传入日期的offset计算农历日期
 * @param {number} objDate 传入日期
 * @return {Lunar}
 */
LunarSolarConverter.prototype.Lunar = function (objDate) {
    var i, leap = 0, temp = 0;
    var baseDate = new Date(1900, 0, 31);
    var offset = (objDate - baseDate) / 86400000;

    this.dayCyl = offset + 40;
    this.monCyl = 14;

    for (i = 1900; i < 2050 && offset > 0; i++) {
        temp = this.lYearDays(i);
        offset -= temp;
        this.monCyl += 12;
    }
    if (offset < 0) {
        offset += temp;
        i--;
        this.monCyl -= 12;
    }

    this.year = i;
    this.yearCyl = i - 1864;

    leap = this.leapMonth(i); //闰哪个月
    this.isLeap = false;

    for (i = 1; i < 13 && offset > 0; i++) {
        //闰月
        if (leap > 0 && i == (leap + 1) && this.isLeap == false) {
            --i;
            this.isLeap = true;
            temp = this.leapDays(this.year);
        }
        else {
            temp = this.monthDays(this.year, i);
        }

        //解除闰月
        if (this.isLeap == true && i == (leap + 1)) this.isLeap = false;

        offset -= temp;
        if (this.isLeap == false) this.monCyl++;
    }

    if (offset == 0 && leap > 0 && i == leap + 1)
        if (this.isLeap) {
            this.isLeap = false;
        }
        else {
            this.isLeap = true;
            --i;
            --this.monCyl;
        }

    if (offset < 0) {
        offset += temp;
        --i;
        --this.monCyl;
    }

    this.month = i;
    this.day = offset + 1;

    var lunar = new Lunar();
    lunar.lunarYear = this.year;
    lunar.lunarMonth = this.month;
    lunar.lunarDay = this.day;
    lunar.isLeap = this.isLeap;
    return lunar;
};

/**
 * 返回农历y年一整年的总天数
 * @param {number} y 农历y年
 * @return {number}
 */
LunarSolarConverter.prototype.lYearDays = function (y) {
    var i, sum = 348;
    for (i = 0x8000; i > 0x8; i >>= 1) sum += (lunarInfo[y - 1900] & i) ? 1 : 0;
    return (sum + this.leapDays(y));
};

/**
 * 返回该年的生肖
 * @param {number} year 年份
 * @return {string}
 */
LunarSolarConverter.prototype.Animals = function (year) {
    return Animals[(year - 4) % 12];
};

/**
 * 传入 月日的offset 获取星座
 * @param {number} m 月
 * @param {number} d 日
 * @return {string}
 */
LunarSolarConverter.prototype.astro = function (m, d) {
    return "魔羯水瓶双鱼白羊金牛双子巨蟹狮子处女天秤天蝎射手魔羯".substr(m * 2 - (d < "102223444433".charAt(m - 1) - -19) * 2, 2);
};

/**
 * 转换为农历显示字符串
 * @param {number} month 农历月份
 * @param {number} day 农历日期
 * @return {string}
 */
LunarSolarConverter.prototype.toChinaMonth = function (month) { // 月名称
    var s = '';
    switch (month) {
        case 1: s = '正月'; break;
        case 2: s = '二月'; break;
        case 3: s = '三月'; break;
        case 4: s = '四月'; break;
        case 5: s = '五月'; break;
        case 6: s = '六月'; break;
        case 7: s = '七月'; break;
        case 8: s = '八月'; break;
        case 9: s = '九月'; break;
        case 10: s = '十月'; break;
        case 11: s = '冬月'; break;
        case 12: s = '腊月'; break;
        default:
    }
    return s;
};

/**
 * 转换为农历显示字符串
 * @param {number} day 农历日期
 * @return {string}
 */
LunarSolarConverter.prototype.toChinaDay = function (day) { // 日名称
    var s = '';
    switch (day) {
        case 10: s = '初十'; break;
        case 20: s = '二十'; break;
        case 30: s = '三十'; break;
        default: s = nStr2[Math.floor(day / 10)]; s += nStr1[day % 10];
    }
    return (s);
};

/**
 * 年份转甲子年
 * @param {number} year 年份
 * @return {string}
 */
LunarSolarConverter.prototype.getYearJiaZi = function (year) {
    return this.cyclical(year - 1900 + 36);
};

/**
 * 月份转甲子月
 * @param {number} year 年份
 * @param {number} month 月份
 * @return {string}
 */
LunarSolarConverter.prototype.getMonthJiaZi = function (year, month) {
    return this.cyclical((year - 1900) * 12 + month + 12);
};

/**
 * 日转甲子日
 * @param {number} year 年份
 * @param {number} month 月份
 * @param {number} day 日期
 * @return {string}
 */
LunarSolarConverter.prototype.getDayJiaZi = function (year, month, day) {
    var objDate = new Date(year, month - 1, day);
    return this.cyclical((objDate - new Date(1900, 0, 1)) / 86400000 + 1 + 10);
};

/**
 * Solar对象
 * @param {number} solarYear
 * @param {number} solarMonth
 * @param {number} solarDay
 * @constructor
 */
function Solar(solarYear, solarMonth, solarDay) {
    this.solarYear = solarYear;
    this.solarMonth = solarMonth;
    this.solarDay = solarDay;
}

/**
 * Lunar对象
 * @constructor
 */
function Lunar() {
    this.lunarYear = 0;
    this.lunarMonth = 0;
    this.lunarDay = 0;
    this.isLeap = false;
}

/**
 * 公历转农历
 * @param {Solar} solar 公历对象
 * @return {Lunar}
 */
LunarSolarConverter.prototype.SolarToLunar = function (solar) {
    var date = new Date(solar.solarYear, solar.solarMonth - 1, solar.solarDay);
    return this.Lunar(date);
};

/**
 * 农历转公历
 * @param {Lunar} lunar 农历对象
 * @return {Solar}
 */
LunarSolarConverter.prototype.LunarToSolar = function (lunar) {
    var leap = this.leapMonth(lunar.lunarYear);
    var days = this.monthDays(lunar.lunarYear, lunar.lunarMonth);
    if (lunar.isLeap && leap != lunar.lunarMonth) {
        //console.log("传入的月份并非闰月");
        return null;
    }
    if (lunar.lunarDay > days) {
        //console.log("传入的日期不存在");
        return null;
    }
    var offset = 0;
    for (var i = 1900; i < lunar.lunarYear; i++) {
        offset += this.lYearDays(i);
    }
    var leapMonth = this.leapMonth(lunar.lunarYear);
    if (lunar.isLeap && leapMonth < lunar.lunarMonth) {
        // 闰月在当前月之后
        for (var i = 1; i < lunar.lunarMonth; i++) {
            offset += this.monthDays(lunar.lunarYear, i);
        }
        if (lunar.lunarMonth > leapMonth) {
            offset += this.leapDays(lunar.lunarYear);
        }
        offset += lunar.lunarDay -1;
    } else {
        for (var i = 1; i < lunar.lunarMonth; i++) {
            offset += this.monthDays(lunar.lunarYear, i);
        }
        if (lunar.isLeap && lunar.lunarMonth == leapMonth) { // 闰月
            offset += this.leapDays(lunar.lunarYear);
        }
        offset += lunar.lunarDay -1;
    }

    var baseDate = new Date(1900, 0, 31);
    var solarDate = new Date(baseDate.getTime() + offset * 86400000);

    var solar = new Solar(solarDate.getFullYear(), solarDate.getMonth() + 1, solarDate.getDate());
    return solar;
};

// For Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        LunarSolarConverter: LunarSolarConverter,
        Solar: Solar,
        Lunar: Lunar
    };
}