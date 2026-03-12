/**
 * 地图工具栏模块
 * 提供交通、路线、定位、全屏等功能
 */

(function() {
    'use strict';
    
    /**
     * 添加工具栏样式
     */
    function addToolbarStyles() {
        if (document.getElementById('map-toolbar-styles')) {
            return;
        }
        
        const style = document.createElement('style');
        style.id = 'map-toolbar-styles';
        style.textContent = `
            .map-toolbar {
                position: absolute;
                right: 10px;
                bottom: 80px;
                display: flex;
                flex-direction: column;
                gap: 8px;
                background: rgba(255, 255, 255, 0.95);
                border-radius: 8px;
                padding: 8px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.15);
                border: 1px solid #ddd;
                z-index: 1000;
            }
            .toolbar-btn {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                width: 50px;
                height: 50px;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.3s ease;
                color: #666;
                font-size: 12px;
                background: transparent;
                border: none;
            }
            .toolbar-btn:hover {
                background: linear-gradient(135deg, #C1302E 0%, #E83B36 100%);
                color: white;
                transform: scale(1.05);
                box-shadow: 0 3px 10px rgba(193, 48, 46, 0.3);
            }
            .toolbar-btn i {
                font-size: 18px;
                margin-bottom: 2px;
            }
            .toolbar-btn span {
                font-size: 11px;
            }
            .toolbar-btn.active {
                background: linear-gradient(135deg, #C1302E 0%, #E83B36 100%);
                color: white;
            }
            .toolbar-btn:active {
                transform: scale(0.95);
            }
        `;
        document.head.appendChild(style);
    }
    
    /**
     * 显示提示消息
     * @param {string} message 消息内容
     */
    function showToast(message) {
        if (typeof window.showToast === 'function') {
            window.showToast(message);
            return;
        }
        
        let toast = document.getElementById('map-toolbar-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'map-toolbar-toast';
            toast.style.cssText = `
                position: fixed;
                bottom: 100px;
                right: 80px;
                background: rgba(0, 0, 0, 0.75);
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                z-index: 10000;
                opacity: 0;
                transition: opacity 0.3s;
                pointer-events: none;
            `;
            document.body.appendChild(toast);
        }
        
        toast.textContent = message;
        toast.style.opacity = '1';
        
        setTimeout(() => {
            toast.style.opacity = '0';
        }, 2000);
    }
    
    /**
     * 绑定工具栏事件
     * @param {HTMLElement} div 工具栏容器
     * @param {BMap.Map} mapInstance 地图实例
     */
    function bindToolbarEvents(div, mapInstance) {
        // 交通图层切换
        const trafficBtn = div.querySelector('#btn-traffic');
        let trafficLayer = null;
        
        trafficBtn.addEventListener('click', function() {
            this.classList.toggle('active');
            if (trafficLayer) {
                mapInstance.removeTileLayer(trafficLayer);
                trafficLayer = null;
                showToast('已关闭交通图层');
            } else {
                trafficLayer = new window.BMap.TrafficLayer();
                mapInstance.addTileLayer(trafficLayer);
                showToast('已开启交通图层');
            }
        });
        
        // 路线规划
        div.querySelector('#btn-transit').addEventListener('click', function() {
            const center = mapInstance.getCenter();
            const lng = center.lng.toFixed(6);
            const lat = center.lat.toFixed(6);
            window.open(`https://map.baidu.com/dir/,,${lat},${lng}`, '_blank');
            showToast('已打开路线规划页面');
        });
        
        // 定位功能
        div.querySelector('#btn-location').addEventListener('click', function() {
            if (navigator.geolocation) {
                showToast('正在定位...');
                navigator.geolocation.getCurrentPosition(
                    function(position) {
                        const point = new window.BMap.Point(
                            position.coords.longitude,
                            position.coords.latitude
                        );
                        
                        // 转换坐标（GPS坐标转百度坐标）
                        if (window.BMap.Convertor) {
                            const convertor = new window.BMap.Convertor();
                            convertor.translate([point], 1, 5, function(data) {
                                if (data.status === 0 && data.points.length > 0) {
                                    const baiduPoint = data.points[0];
                                    mapInstance.centerAndZoom(baiduPoint, 15);
                                    
                                    const marker = new window.BMap.Marker(baiduPoint);
                                    mapInstance.addOverlay(marker);
                                    marker.setAnimation(window.BMAP_ANIMATION_BOUNCE);
                                    setTimeout(() => marker.setAnimation(null), 2000);
                                    
                                    showToast('定位成功');
                                } else {
                                    mapInstance.centerAndZoom(point, 15);
                                    showToast('定位成功');
                                }
                            });
                        } else {
                            mapInstance.centerAndZoom(point, 15);
                            showToast('定位成功');
                        }
                    },
                    function(error) {
                        let errorMsg = '无法获取您的位置';
                        switch (error.code) {
                            case error.PERMISSION_DENIED:
                                errorMsg = '定位权限被拒绝，请在浏览器设置中允许定位';
                                break;
                            case error.POSITION_UNAVAILABLE:
                                errorMsg = '位置信息不可用';
                                break;
                            case error.TIMEOUT:
                                errorMsg = '定位请求超时';
                                break;
                        }
                        showToast(errorMsg);
                        console.error('定位失败:', error);
                    },
                    {
                        enableHighAccuracy: true,
                        timeout: 10000,
                        maximumAge: 0
                    }
                );
            } else {
                showToast('您的浏览器不支持定位功能');
            }
        });
        
        // 全屏功能
        const fullscreenBtn = div.querySelector('#btn-fullscreen');
        fullscreenBtn.addEventListener('click', function() {
            const mapContainer = document.getElementById('baidu-map');
            
            if (!document.fullscreenElement) {
                mapContainer.requestFullscreen().then(() => {
                    this.querySelector('i').classList.remove('fa-expand');
                    this.querySelector('i').classList.add('fa-compress');
                    this.querySelector('span').textContent = '退出';
                    showToast('已进入全屏模式');
                }).catch(err => {
                    console.warn('全屏请求失败:', err);
                    showToast('全屏请求失败');
                });
            } else {
                document.exitFullscreen().then(() => {
                    this.querySelector('i').classList.remove('fa-compress');
                    this.querySelector('i').classList.add('fa-expand');
                    this.querySelector('span').textContent = '全屏';
                    showToast('已退出全屏模式');
                }).catch(err => {
                    console.warn('退出全屏失败:', err);
                });
            }
        });
        
        // 监听全屏状态变化
        document.addEventListener('fullscreenchange', function() {
            const icon = fullscreenBtn.querySelector('i');
            const text = fullscreenBtn.querySelector('span');
            
            if (document.fullscreenElement) {
                icon.classList.remove('fa-expand');
                icon.classList.add('fa-compress');
                text.textContent = '退出';
            } else {
                icon.classList.remove('fa-compress');
                icon.classList.add('fa-expand');
                text.textContent = '全屏';
            }
        });
    }
    
    /**
     * 创建工具栏控件
     * @param {BMap.Map} mapInstance 地图实例
     */
    function createToolbar(mapInstance) {
        const div = document.createElement('div');
        div.className = 'map-toolbar';
        div.innerHTML = `
            <div class="toolbar-btn" id="btn-traffic" title="查看实时交通状况">
                <i class="fa fa-car"></i>
                <span>交通</span>
            </div>
            <div class="toolbar-btn" id="btn-transit" title="查询公交地铁路线">
                <i class="fa fa-subway"></i>
                <span>路线</span>
            </div>
            <div class="toolbar-btn" id="btn-location" title="定位到当前位置">
                <i class="fa fa-location-arrow"></i>
                <span>定位</span>
            </div>
            <div class="toolbar-btn" id="btn-fullscreen" title="全屏显示地图">
                <i class="fa fa-expand"></i>
                <span>全屏</span>
            </div>
        `;
        
        // 添加样式
        addToolbarStyles();
        
        // 绑定事件
        bindToolbarEvents(div, mapInstance);
        
        // 添加到地图容器
        mapInstance.getContainer().appendChild(div);
        
        return div;
    }
    
    /**
     * 添加控件提示
     */
    function addTooltips() {
        setTimeout(() => {
            const zoomControls = document.querySelectorAll('.BMap_stdMpZoom');
            zoomControls.forEach(ctrl => {
                ctrl.title = '缩放地图：滚轮或点击 +/- 按钮';
            });
            
            const mapTypeControls = document.querySelectorAll('.BMap_mapType');
            mapTypeControls.forEach(ctrl => {
                ctrl.title = '切换地图模式：地图/卫星/混合';
            });
            
            const panControls = document.querySelectorAll('.BMap_stdMpPan');
            panControls.forEach(ctrl => {
                ctrl.title = '拖拽移动地图';
            });
        }, 1000);
    }
    
    // 导出模块
    window.MapToolbar = {
        create: createToolbar,
        addTooltips: addTooltips
    };
    
})();
