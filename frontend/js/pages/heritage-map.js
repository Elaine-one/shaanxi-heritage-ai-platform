// 非遗地图核心功能

// 声明全局变量
let map = null; // 百度地图实例
let markers = []; // 地图标记数组
let markerClusterer = null; // 点聚合管理实例
let currentHighlightedMarker = null; // 当前高亮的标记

/**
 * 高亮显示标记
 * @param {BMap.Marker} marker 要高亮的标记
 */
function highlightMarker(marker) {
    // 如果有之前高亮的标记，先取消高亮
    if (currentHighlightedMarker && currentHighlightedMarker !== marker) {
        // 重置高亮状态
        currentHighlightedMarker.isHighlighted = false;
        
        // 恢复原始图标大小和颜色
        try {
            // 对于普通BMap，我们可能需要简单地替换图标
            const originalIcon = currentHighlightedMarker.getIcon();
            if (originalIcon) {
                // 恢复默认图标
                const defaultIcon = new window.BMap.Icon(
                    '/static/images/marker.png', // 修正图片路径
                    new window.BMap.Size(26, 26),
                    {
                        imageSize: new window.BMap.Size(26, 26),
                        anchor: new window.BMap.Size(13, 26)
                    }
                );
                currentHighlightedMarker.setIcon(defaultIcon);
            }
        } catch (e) {
            console.warn('恢复标记图标时出错:', e);
        }
        
        // 隐藏标签
        const label = currentHighlightedMarker.getLabel();
        if (label) {
            label.setStyle({
                display: 'none'
            });
        }
    }
    
    // 设置当前标记为高亮
    currentHighlightedMarker = marker;
    marker.isHighlighted = true;
    
    try {
        // 设置高亮图标
        const highlightIcon = new window.BMap.Icon(
            '/static/images/marker-highlight.png', // 修正高亮图标路径
            new window.BMap.Size(32, 32),
            {
                imageSize: new window.BMap.Size(32, 32),
                anchor: new window.BMap.Size(16, 32)
            }
        );
        marker.setIcon(highlightIcon);
    } catch (e) {
        console.warn('设置高亮图标时出错:', e);
    }
    
    // 确保标签显示
    const label = marker.getLabel();
    if (label) {
        label.setStyle({
            display: 'block',
            backgroundColor: 'rgba(255, 255, 255, 1)',
            border: '2px solid #E83B36',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.25)',
            zIndex: 10000
        });
    }
    
    // 将地图中心点移动到标记位置
    map.panTo(marker.getPosition());
}

/**
 * 显示项目预览
 * @param {Object} item 项目数据
 */
function showHeritagePreview(item) {
    // 在侧边栏显示项目预览
    if (typeof window.showHeritagePreview === 'function') {
        window.showHeritagePreview(item);
    }
}

/**
 * 显示地图错误信息
 * @param {string} message 错误信息
 */
function showMapError(message) {
    const mapContainer = document.getElementById('baidu-map');
    if (mapContainer) {
        mapContainer.innerHTML = `<div class="map-error">
            <h3>地图加载失败</h3>
            <p>${message || '未知错误'}</p>
            <button onclick="location.reload()">重新加载</button>
        </div>`;
    }
    console.error('地图错误:', message);
}

/**
 * 地图核心功能
 */
window.MapCore = {
    /**
     * 初始化地图
     */
    init: async function() {
        console.log('[MapCore.init] Attempting to initialize map...');
        try {
            // 初始化地图容器
            const mapContainer = document.getElementById("baidu-map");
            if (!mapContainer) {
                console.error('[MapCore.init] Map container element #baidu-map not found.');
                throw new Error('地图容器元素不存在');
            }
            mapContainer.innerHTML = ''; // Clear previous content if any
            console.log('[MapCore.init] Map container cleared.');

            // 创建地图实例
            if (typeof window.BMap === 'undefined' || typeof window.BMap.Map === 'undefined') {
                console.error('[MapCore.init] window.BMap or window.BMap.Map is not defined. Baidu Maps API might not be loaded correctly.');
                showMapError('百度地图API未能正确加载，请检查网络或API密钥。');
                return false;
            }
            console.log('[MapCore.init] window.BMap object is available. Creating map instance...');
            map = new window.BMap.Map("baidu-map");
            const centerPoint = new window.BMap.Point(108.948024, 34.263161); // 陕西省大致中心
            map.centerAndZoom(centerPoint, 8);
            console.log('[MapCore.init] Map instance created and centered.');
            
            window.map = map; // 全局暴露map实例
            
            // 继续初始化其他地图功能
            console.log('[MapCore.init] Calling initWithMap...');
            return await this.initWithMap(map);
        } catch (error) {
            console.error('[MapCore.init] Map initialization failed:', error);
            showMapError(error.message || '地图初始化时发生未知错误');
            return false;
        }
    },
    
    /**
     * 使用已创建的地图实例继续初始化
     * @param {BMap.Map} mapInstance 已创建的地图实例
     */
    initWithMap: async function(mapInstance) {
        console.log('[MapCore.initWithMap] Starting with map instance.');
        try {
            if (!mapInstance || !(mapInstance instanceof window.BMap.Map)) {
                console.error('[MapCore.initWithMap] Invalid map instance provided.');
                return false;
            }
            
            // 保存地图实例引用
            map = mapInstance;
            window.map = map;
            console.log('[MapCore.initWithMap] Map instance confirmed.');
            
            // 添加地图控件
            this.addMapControls();
            console.log('[MapCore.initWithMap] Map controls added.');
            
            // 添加陕西省边界
            this.addShaanxiBoundary();
            console.log('[MapCore.initWithMap] Shaanxi boundary added.');
            
            // 等待聚合库加载完成，但不要阻塞流程
            this.waitForBMapLib().catch(err => {
                console.warn('[MapCore.initWithMap] Error while waiting for BMap libraries:', err);
            });
            console.log('[MapCore.initWithMap] Waiting for BMap libraries (non-blocking).');
            
            // 从API获取非遗数据
            try {
                console.log('[MapCore.initWithMap] Attempting to load heritage data...');
                const heritageData = await loadHeritageData(); // Ensure loadHeritageData is defined and working
                console.log('[MapCore.initWithMap] Heritage data received:', heritageData ? heritageData.length + ' items' : 'null or empty');
                
                if (heritageData && heritageData.length > 0) {
                    this.addMarkers(heritageData);
                    console.log('[MapCore.initWithMap] Markers added.');
                    
                    if (typeof window.initSidebar === 'function') {
                        window.initSidebar(heritageData);
                        console.log('[MapCore.initWithMap] Sidebar initialized.');
                    } else {
                        console.warn('[MapCore.initWithMap] initSidebar function not found.');
                    }
                } else {
                    console.warn('[MapCore.initWithMap] No heritage data loaded or data is empty.');
                    const mapContainer = document.getElementById('baidu-map');
                    if (mapContainer) {
                        const infoDiv = document.createElement('div');
                        infoDiv.className = 'map-info-overlay';
                        infoDiv.innerHTML = `
                            <div class="map-info-content">
                                <h3>数据加载提示</h3>
                                <p>未能获取到非遗项目数据，请检查API连接或稍后再试。</p>
                            </div>
                        `;
                        mapContainer.appendChild(infoDiv);
                    }
                }
            } catch (dataError) {
                console.error('[MapCore.initWithMap] Failed to load heritage data:', dataError);
                const mapContainer = document.getElementById('baidu-map');
                if (mapContainer) {
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'map-error-overlay';
                    errorDiv.innerHTML = `
                        <div class="map-error-content">
                            <h3>数据加载错误</h3>
                            <p>${dataError.message || '获取数据时发生未知错误'}</p>
                            <button onclick="window.MapCore.reloadData()">重新加载数据</button>
                        </div>
                    `;
                    mapContainer.appendChild(errorDiv);
                }
            }
            console.log('[MapCore.initWithMap] Initialization process completed.');
            return true;
        } catch (error) {
            console.error('[MapCore.initWithMap] Map features initialization failed:', error);
            showMapError(error.message || '地图功能初始化时发生未知错误');
            return false;
        }
    },
    
    /**
     * 重新加载非遗数据
     * 用于数据加载失败后的重试
     */
    reloadData: async function() {
        // console.log('正在重新加载非遗数据...');
        
        // 移除现有的错误提示
        const mapContainer = document.getElementById('baidu-map');
        if (mapContainer) {
            const errorOverlays = mapContainer.querySelectorAll('.map-error-overlay, .map-info-overlay');
            errorOverlays.forEach(overlay => overlay.remove());
        }
        
        try {
            // 重新从API获取数据
            const heritageData = await loadHeritageData();
            
            if (heritageData && heritageData.length > 0) {
                // console.log(`重新加载成功，获取到${heritageData.length}个非遗项目数据`);
                // 添加标记
                this.addMarkers(heritageData);
                
                // 更新侧边栏
                if (typeof window.initSidebar === 'function') {
                    window.initSidebar(heritageData);
                }
                
                // 显示成功提示（2秒后自动消失）
                const successDiv = document.createElement('div');
                successDiv.className = 'map-success-overlay';
                successDiv.innerHTML = `
                    <div class="map-success-content">
                        <h3>数据加载成功</h3>
                        <p>已成功加载${heritageData.length}个非遗项目数据</p>
                    </div>
                `;
                mapContainer.appendChild(successDiv);
                
                // 2秒后移除成功提示
                setTimeout(() => {
                    successDiv.remove();
                }, 2000);
                
                return true;
            } else {
                console.warn('重新加载数据失败：获取到的非遗数据为空或无效');
                throw new Error('获取到的非遗数据为空或无效');
            }
        } catch (error) {
            console.error('重新加载非遗数据失败:', error);
            
            // 显示错误信息
            if (mapContainer) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'map-error-overlay';
                errorDiv.innerHTML = `
                    <div class="map-error-content">
                        <h3>数据重新加载失败</h3>
                        <p>${error.message || '未知错误'}</p>
                        <button onclick="window.MapCore.reloadData()">再次尝试</button>
                    </div>
                `;
                mapContainer.appendChild(errorDiv);
            }
            
            return false;
        }
    },
    
    /**
     * 添加所有标记到地图
     * @param {Array} data 非遗项目数据数组
     */
    /**
     * 添加所有标记到地图
     * @param {Array} data 非遗项目数据数组
     */
    addMarkers: function(data) {
        // 清除现有标记
        if (markers.length > 0) {
            markers.forEach(marker => {
                map.removeOverlay(marker);
            });
            markers = [];
        }
        
        // 添加新标记
        let validMarkersCount = 0;
        
        // 确保data是数组
        if (!Array.isArray(data)) {
            console.error('addMarkers: 传入的数据不是数组', data);
            return;
        }
        // console.log('添加标记到地图，数据项数：', data.length);
        
        // 添加项目标记到地图
        
        data.forEach(item => {
            // 确保项目有必要的数据
            if (!item || !item.id || !item.name) {
                console.warn('项目缺少ID或名称，跳过:', item);
                return;
            }
            
            // 确保经纬度存在且为有效数值
            if (item.lat && item.lng) {
                // 将经纬度转换为数值类型
                const lat = parseFloat(item.lat);
                const lng = parseFloat(item.lng);
                
                // 验证经纬度是否为有效数值
                if (!isNaN(lat) && !isNaN(lng)) {
                    const point = new window.BMap.Point(lng, lat);
                    
                    // 创建图标 - 为默认坐标的项目使用不同的图标
                    let iconUrl = '/static/images/marker.png'; // 标准图标路径
                    let iconSize = new window.BMap.Size(26, 26);
                    let imageSize = new window.BMap.Size(26, 26);
                    let anchor = new window.BMap.Size(13, 26);
                    
                    // 为默认坐标的项目使用不同的图标设置
                    if (item.isDefaultLocation) {
                        // 默认位置使用相同图标但尺寸更小
                        iconSize = new window.BMap.Size(20, 20);
                        imageSize = new window.BMap.Size(20, 20);
                        anchor = new window.BMap.Size(10, 20);
                    }
                    
                    // 创建图标对象
                    let icon = new window.BMap.Icon(
                        iconUrl,
                        iconSize,
                        {
                            imageSize: imageSize,
                            anchor: anchor
                        }
                    );
                    
                    // 创建标记
                    const marker = icon ? 
                        new window.BMap.Marker(point, { icon: icon }) : 
                        new window.BMap.Marker(point);
                    
                    // 保存项目数据到标记对象，用于点击时显示详情
                    marker.customData = item;
                    
                    // 创建标签
                    const label = new window.BMap.Label(item.name, {
                        offset: new window.BMap.Size(20, -10),
                        enableMassClear: true
                    });
                    
                    // 设置标签样式
                    label.setStyle({
                        display: 'none',  // 默认隐藏
                        color: '#333',
                        fontSize: '12px',
                        backgroundColor: 'rgba(255, 255, 255, 0.8)',
                        border: '1px solid #ccc',
                        borderRadius: '3px',
                        padding: '2px 5px'
                    });
                    
                    // 添加标签到标记
                    marker.setLabel(label);
                    
                    // 添加点击事件
                    marker.addEventListener('click', function() {
                        highlightMarker(this);
                        showHeritagePreview(item);
                    });
                    
                    // 添加鼠标悬停事件
                    marker.addEventListener('mouseover', function() {
                        if (!this.isHighlighted) {
                            const label = this.getLabel();
                            if (label) {
                                label.setStyle({
                                    display: 'block'
                                });
                            }
                        }
                    });
                    
                    // 添加鼠标离开事件
                    marker.addEventListener('mouseout', function() {
                        if (!this.isHighlighted) {
                            const label = this.getLabel();
                            if (label) {
                                label.setStyle({
                                    display: 'none'
                                });
                            }
                        }
                    });
                    
                    markers.push(marker);
                    map.addOverlay(marker);
                    validMarkersCount++;
                } else {
                    console.warn(`项目 ${item.id}:${item.name} 的经纬度无效:`, {lat, lng});
                }
            } else {
                console.warn(`项目 ${item.id}:${item.name} 缺少经纬度数据`);
            }
        });
        
        // 完成标记添加
        
        // 将所有标记添加到聚合管理器
        if (markerClusterer) {
            markerClusterer.clearMarkers();
            markerClusterer.addMarkers(markers);
        }
    },
    
    /**
     * 等待地图扩展库加载
     */
    waitForBMapLib: function() {
        return new Promise((resolve) => {
            // 检查必要的依赖是否已加载
            if (typeof MarkerClusterer !== 'undefined' && 
                typeof TextIconOverlay !== 'undefined') {
                resolve();
                return;
            }
            
            // 设置最大等待时间
            const maxWaitTime = 3000; // 3秒
            const startTime = Date.now();
            
            // 定期检查
            const checkInterval = setInterval(() => {
                if (typeof MarkerClusterer !== 'undefined' && 
                    typeof TextIconOverlay !== 'undefined') {
                    clearInterval(checkInterval);
                    resolve();
                    return;
                }
                
                // 超时处理
                if (Date.now() - startTime > maxWaitTime) {
                    clearInterval(checkInterval);
                    resolve(); // 即使超时也resolve，让流程继续
                }
            }, 200);
        });
    },
    
    /**
     * 添加地图控件
     */
    addMapControls: function() {
        // 添加缩放控件
        map.addControl(new window.BMap.NavigationControl());
        // 添加比例尺控件
        map.addControl(new window.BMap.ScaleControl());
        // 添加地图类型控件
        map.addControl(new window.BMap.MapTypeControl());
        // 启用滚轮缩放
        map.enableScrollWheelZoom(true);
    },
    
    /**
     * 添加陕西省边界
     */
    addShaanxiBoundary: function() {
        // 创建行政区域覆盖物
        const bdary = new window.BMap.Boundary();
        
        // 获取陕西省边界
        bdary.get('陕西省', function(rs) {
            try {
                if (!rs || !rs.boundaries || rs.boundaries.length === 0) {
                    return;
                }

                // 遍历所有边界
                for (let i = 0; i < rs.boundaries.length; i++) {
                    if (!rs.boundaries[i]) continue;
                    // 创建多边形覆盖物
                    const ply = new window.BMap.Polygon(rs.boundaries[i], {
                        strokeWeight: 2,
                        strokeColor: "#E83B36",
                        fillColor: "#FFD0CE",
                        fillOpacity: 0.1
                    });
                    // 添加覆盖物
                    map.addOverlay(ply);
                }
                
                // console.log('已添加陕西省边界到地图');
            } catch (error) {
                console.error('添加陕西省边界失败:', error.message);
            }
        });
    },
    
    /**
     * 刷新地图，确保所有标记可见
     */
    refreshMap: function() {
        // 强制刷新地图，确保所有标记可见
        if (map) {
            try {
                // 触发地图缩放事件，强制刷新
                const currentZoom = map.getZoom();
                map.setZoom(currentZoom - 1);
                setTimeout(() => {
                    map.setZoom(currentZoom);
                }, 100);
            } catch (error) {
                console.error('刷新地图失败:', error);
            }
        }
    },
    
    /**
     * 清除所有标记
     */
    clearMarkers: function() {
        // 清除现有标记
        if (markers.length > 0) {
            markers.forEach(marker => {
                map.removeOverlay(marker);
            });
            markers = [];
        }
        
        // 清除聚合管理器中的标记
        if (markerClusterer) {
            markerClusterer.clearMarkers();
        }
    },
    
    /**
     * 将标记添加到聚合管理器
     */
    addMarkersToClusterer: function() {
        if (markerClusterer && markers.length > 0) {
            markerClusterer.addMarkers(markers);
        }
    }
};

/**
 * 初始化搜索功能
 * @param {Array} data 非遗项目数据数组
 */
function initSearch(data) {
    const searchInput = document.getElementById('map-search-input');
    const searchBtn = document.getElementById('map-search-btn');
    
    if (!searchInput || !searchBtn) {
        console.error('搜索元素未找到');
        return;
    }
    
    // 搜索按钮点击事件
    searchBtn.addEventListener('click', function() {
        const keyword = searchInput.value.trim();
        if (keyword) {
            searchHeritageItems(keyword, data);
        }
    });
    
    // 输入框回车事件
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            const keyword = searchInput.value.trim();
            if (keyword) {
                searchHeritageItems(keyword, data);
            }
        }
    });
    
    // console.log('初始化搜索功能完成');
}

/**
 * 搜索非遗项目
 * @param {string} keyword 搜索关键词
 * @param {Array} data 非遗项目数据数组
 */
async function searchHeritageItems(keyword, data) {
    if (!keyword) {
        return [];
    }
    
    // console.log('搜索关键词:', keyword);
    
    try {
        // 使用API进行搜索
        const params = {
            search: keyword,
            page: 1,
            page_size: 100 // 获取足够多的结果以在地图上显示
        };
        
        const response = await window.API.heritage.getAllItems(params);
        
        if (!response || !response.results) {
            throw new Error('API响应格式不正确');
        }
        
        const results = response.results;
        
        // 更新地图标记
        if (typeof addMarkers === 'function') {
            addMarkers(results);
        }
        
        // 更新侧边栏
        if (typeof updateFilteredProjectList === 'function') {
            updateFilteredProjectList(results);
        }
        
        return results;
    } catch (error) {
        console.error('API搜索失败:', error);
        // 如果API搜索失败，回退到本地过滤
        if (data && Array.isArray(data)) {
            // console.log('回退到本地搜索');
            const results = data.filter(item => {
                return item.name.includes(keyword) || 
                       (item.description && item.description.includes(keyword)) ||
                       (item.category && item.category.includes(keyword)) ||
                       (item.region && item.region.includes(keyword));
            });
            
            // 更新地图标记
            if (typeof addMarkers === 'function') {
                addMarkers(results);
            }
            
            // 更新侧边栏
            if (typeof updateFilteredProjectList === 'function') {
                updateFilteredProjectList(results);
            }
            
            return results;
        }
        return [];
    }
}

/**
 * 添加所有标记到地图
 * @param {Array} data 非遗项目数据数组
 */
function addMarkers(data) {
    if (!data || !Array.isArray(data)) {
        console.error('标记数据无效');
        return;
    }
    
    // console.log('添加标记到地图，数据项数：', data.length);
    
    // 使用MapCore添加标记
    if (MapCore && typeof MapCore.addMarkers === 'function') {
        MapCore.addMarkers(data);
    } else {
        console.error('MapCore.addMarkers函数未定义');
    }
    return true;
}

/**
 * 从API加载非遗数据
 * @returns {Promise<Array>} 返回一个Promise，解析为非遗数据数组
 */
/**
 * 从API加载非遗数据
 * @returns {Promise<Array>} 返回包含有效坐标的非遗项目数据的Promise
 */
// 缓存API请求结果，避免重复请求
let heritageDataCache = null;
let heritageDataTimestamp = 0;
const CACHE_DURATION = 5 * 60 * 1000; // 缓存5分钟

/**
 * 从API加载非遗数据
 * @returns {Promise<Array>} 返回包含有效坐标的非遗项目数据的Promise
 */
async function loadHeritageData() {
    console.log('[loadHeritageData] Attempting to fetch heritage data from API...');
    try {
        if (window.API && window.API.heritage && typeof window.API.heritage.getAllItems === 'function') {
            const response = await window.API.heritage.getAllItems(); // getAllItems returns { count, results }
            // Assuming we need the results array
            const data = response.results;
            console.log('[loadHeritageData] Successfully fetched data:', data ? data.length + ' items' : 'null or empty');
            return data;
        } else {
            console.error('[loadHeritageData] window.API.heritage.getAllItems is not available.');
            throw new Error('window.API.heritage.getAllItems is not available.');
        }
    } catch (error) {
        console.error('[loadHeritageData] Error fetching heritage data:', error);
        // Propagate the error so it can be handled by the caller
        throw new Error(`获取非遗数据失败: ${error.message}`);
    }
}

/**
 * 初始化侧边栏
 * @param {Array} data 非遗项目数据数组
 */
function initSidebar(data) {
    // 更新项目列表
    if (typeof window.updateFilteredProjectList === 'function') {
        window.updateFilteredProjectList(data);
    } else if (typeof updateFilteredProjectList === 'function') {
        updateFilteredProjectList(data);
    } else {
        console.error('updateFilteredProjectList函数未定义');
    }
    
    // console.log('初始化侧边栏完成');
}

// 标记地图是否已初始化，避免重复初始化
let mapInitialized = false;

// 页面加载完成后初始化地图
document.addEventListener('DOMContentLoaded', function() {
    // console.log('地图页面加载完成，等待地图API加载...');
    
    // 如果地图已初始化，则不再重复初始化
    if (mapInitialized) {
        // console.log('地图已经初始化，跳过重复初始化');
        return;
    }
    
    // 等待一段时间让百度地图API有机会加载
    // 如果BMap已经定义，立即初始化；否则等待更长时间
    if (typeof window.BMap !== 'undefined') {
        console.log('Baidu Maps API already loaded. Initializing extensions and MapCore...');
        initMapWhenReady();
    } else {
        console.log('Baidu Maps API not yet loaded, waiting for it...');
        // 等待3秒让百度地图API有机会加载
        setTimeout(() => {
            if (typeof window.BMap !== 'undefined') {
                console.log('Baidu Maps API loaded after delay. Initializing extensions and MapCore...');
                initMapWhenReady();
            } else {
                console.warn('Baidu Maps API still not loaded after delay. This might be normal if API is loading asynchronously.');
                // 不显示错误，因为API可能还在加载中
                // 真正的错误会在API加载失败时由heritage-map.html中的错误处理显示
            }
        }, 3000);
    }
});

/**
 * 当地图API准备就绪时初始化地图
 */
function initMapWhenReady() {
    // 确保MapCore已定义
    if (typeof MapCore !== 'undefined' && typeof MapCore.init === 'function') {
        // 延迟一点执行初始化，确保DOM和其他资源已完全加载
        setTimeout(() => {
            if (mapInitialized) {
                // console.log('地图已经初始化，跳过重复初始化');
                return;
            }
            
            mapInitialized = true; // 标记为已初始化
            
            MapCore.init().then(result => {
                if (result !== false) {
                    // console.log('地图初始化成功');
                } else {
                    console.warn('地图初始化返回false，可能存在问题');
                    mapInitialized = false; // 初始化失败，重置标记
                }
            }).catch(err => {
                console.error('地图初始化过程中发生错误:', err);
                showMapError('地图初始化失败: ' + err.message);
                mapInitialized = false; // 初始化失败，重置标记
            });
        }, 100);
    } else {
        console.error('MapCore未定义或init方法不存在');
        showMapError('地图核心组件未正确加载，请刷新页面重试');
    }
}

// 将函数和对象暴露给全局作用域
window.showHeritagePreview = showHeritagePreview;
window.highlightMarker = highlightMarker; // 暴露highlightMarker到全局
window.markers = markers; // 暴露markers数组到全局
window.MapCore = MapCore; // 暴露MapCore到全局
function CustomTextOverlay(point, text, options) {
    window.BMap.Overlay.call(this);
    this._point = point;
    this._text = text;
    this._options = options || {};
    this._map = null;
    this._div = null;
}

// 初始化覆盖物
CustomTextOverlay.prototype.initialize = function(mapInstance) {
    this._map = mapInstance;
    this._div = document.createElement('div');
    // 使用绝对定位，具体位置由百度地图API处理
    this._div.innerHTML = this._text;
    this._div.className = 'custom-text-overlay';
    this._div.style.position = 'absolute';

    // 将div添加到地图的覆盖物容器中
    mapInstance.getPanes().labelPane.appendChild(this._div);

    return this._div;
}

// 绘制覆盖物
CustomTextOverlay.prototype.draw = function() {
    const pixel = this._map.pointToOverlayPixel(this._point);
    this._div.style.left = pixel.x + 'px';
    this._div.style.top = pixel.y + 'px';
};

// 移除覆盖物
CustomTextOverlay.prototype.remove = function() {
    if (this._div && this._div.parentNode) {
        this._div.parentNode.removeChild(this._div);
    }
    this._map = null;
    this._div = null;
};
