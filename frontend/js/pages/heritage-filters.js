/**
 * 非遗地图筛选功能
 */

window.HeritageFilters = {};

// 添加重试计数器，防止无限循环
let filterInitRetryCount = 0;
const MAX_RETRY_COUNT = 3;

/**
 * 初始化筛选功能
 * @param {Array} data 非遗项目数据数组
 */
window.HeritageFilters.initFilters = function(data) {
    if (!data || !Array.isArray(data)) {
        console.error('筛选初始化失败：数据无效');
        return;
    }
    console.log('初始化筛选功能，数据项数：', data.length);
    
    // 获取筛选控件
    const levelFilter = document.getElementById('map-level-filter');
    const categoryFilter = document.getElementById('map-category-filter');
    
    // 检查是否真的存在筛选控件
    if (!levelFilter || !categoryFilter) {
        // 避免无限重试
        if (filterInitRetryCount >= MAX_RETRY_COUNT) {
            console.warn(`筛选控件在${MAX_RETRY_COUNT}次重试后仍未找到，放弃初始化筛选功能`);
            return;
        }
        
        console.warn(`筛选控件未找到，可能尚未加载DOM (重试 ${filterInitRetryCount + 1}/${MAX_RETRY_COUNT})`);
        filterInitRetryCount++;
        
        // 延迟重试
        setTimeout(() => window.HeritageFilters.initFilters(data), 500);
        return;
    }
    
    // 重置重试计数器
    filterInitRetryCount = 0;
    
    // 填充筛选选项（简化版本，移除regionFilter参数）
    window.HeritageFilters.populateFilterOptions(data, levelFilter, categoryFilter);
    
    // 为筛选控件添加变更事件（选择后立即筛选）
    levelFilter.addEventListener('change', function() {
        window.HeritageFilters.applyFilters(data);
    });
    
    categoryFilter.addEventListener('change', function() {
        window.HeritageFilters.applyFilters(data);
    });
    
    // 初始化后立即应用一次筛选（显示所有数据）
    window.HeritageFilters.applyFilters(data);
    
    console.log('筛选功能初始化完成');
}

/**
 * 填充筛选选项
 * @param {Array} data 非遗项目数据
 * @param {HTMLElement} levelFilter 级别筛选控件
 * @param {HTMLElement} categoryFilter 类别筛选控件
 */
window.HeritageFilters.populateFilterOptions = function(data, levelFilter, categoryFilter) {
    // 收集唯一的级别和类别
    const levels = new Set();
    const categories = new Set();
    
    // 遍历数据收集选项
    data.forEach(item => {
        if (item.level) levels.add(item.level);
        if (item.category) categories.add(item.category);
    });
    
    // 填充级别选项（保留现有选项）
    if (levelFilter && levelFilter.options.length <= 1) {
        levelFilter.innerHTML = '<option value="全部">全部</option>';
        Array.from(levels).sort().forEach(level => {
            levelFilter.innerHTML += `<option value="${level}">${level}</option>`;
        });
    }
    
    // 填充类别选项（保留现有选项）
    if (categoryFilter && categoryFilter.options.length <= 1) {
        categoryFilter.innerHTML = '<option value="全部">全部</option>';
        Array.from(categories).sort().forEach(category => {
            categoryFilter.innerHTML += `<option value="${category}">${category}</option>`;
        });
    }
}

/**
 * 应用筛选条件
 * @param {Array} data 原始数据
 */
window.HeritageFilters.applyFilters = function(data) {
    // 检查数据是否有效
    if (!data || !Array.isArray(data) || data.length === 0) {
        console.warn('筛选数据无效或为空');
        return;
    }

    // 获取筛选值
    const levelFilter = document.getElementById('map-level-filter');
    const categoryFilter = document.getElementById('map-category-filter');
    
    const levelValue = levelFilter ? levelFilter.value : '全部';
    const categoryValue = categoryFilter ? categoryFilter.value : '全部';
    
    console.log('应用筛选条件:', { level: levelValue, category: categoryValue });
    
    // 筛选数据
    const filteredData = data.filter(item => {
        // 级别筛选
        if (levelValue !== '全部' && item.level !== levelValue) {
            return false;
        }
        
        // 类别筛选
        if (categoryValue !== '全部' && item.category !== categoryValue) {
            return false;
        }
        
        return true;
    });
    
    console.log('筛选后数据项数:', filteredData.length);
    
    // 更新地图标记
    if (typeof addMarkers === 'function') {
        addMarkers(filteredData);
    } else if (typeof window.addMarkers === 'function') {
        window.addMarkers(filteredData);
    } else if (window.MapCore && typeof window.MapCore.addMarkers === 'function') {
        window.MapCore.addMarkers(filteredData);
    }
    
    // 更新侧边栏项目列表
    if (typeof updateFilteredProjectList === 'function') {
        updateFilteredProjectList(filteredData);
    } else if (typeof window.updateFilteredProjectList === 'function') {
        window.updateFilteredProjectList(filteredData);
    }
}

/**
 * 重置筛选条件
 * @param {Array} data 原始数据
 */
window.HeritageFilters.resetFilters = function(data) {
    // 重置筛选控件
    const levelFilter = document.getElementById('map-level-filter');
    const categoryFilter = document.getElementById('map-category-filter');
    
    if (levelFilter) levelFilter.value = '全部';
    if (categoryFilter) categoryFilter.value = '全部';
    
    console.log('重置筛选条件');
    
    // 应用筛选（相当于显示所有数据）
    window.HeritageFilters.applyFilters(data);
}

// 为了向后兼容，将函数挂载到全局window对象
window.initFilters = window.HeritageFilters.initFilters;
window.applyFilters = window.HeritageFilters.applyFilters;
window.resetFilters = window.HeritageFilters.resetFilters;