/**
 * 旅游规划Agent核心类
 * 负责与Agent API通信，处理核心业务逻辑
 */

class TravelPlanningAgent {
    /**
     * 构造函数
     */
    constructor() {
        this.apiBaseUrl = null; // 初始化为null，将在init中异步获取
        // 从localStorage恢复currentPlanId，确保页面刷新后仍能访问
        this.currentPlanId = localStorage.getItem('travelCurrentPlanId') || null;
        this.progressInterval = null;
        this.isPlanning = false;
        this.completionHandled = false; // 防止重复处理完成状态
        this.planResultCache = null; // 缓存规划结果
        this.isExporting = false; // 导出标志位，确保同一时间只能执行一次导出操作
        
        // 绑定事件处理器
        this.bindEvents();
        
        // 初始化API基础URL
        this.init();
        
        // 初始化进度管理器和结果渲染器
        this.progressManager = new ProgressManager(this);
        this.resultRenderer = new ResultRenderer(this);
    }
    
    /**
     * 初始化方法，用于异步获取API基础URL
     */
    async init() {
        try {
            this.apiBaseUrl = await this.getApiBaseUrl();
            console.log('旅游规划Agent初始化完成，API地址:', this.apiBaseUrl);
        } catch (error) {
            console.error('初始化API地址失败:', error);
            // 使用默认地址，匹配实际启动的Agent服务端口
            this.apiBaseUrl = 'http://localhost:8001/api/travel-plan';
        }
    }
    
    /**
     * 获取API基础URL
     * 支持多种方式获取：
     * 1. 从localStorage读取用户配置
     * 2. 从后端API获取Agent服务地址
     * 3. 使用当前页面的主机和端口
     * 4. 默认使用localhost:8001
     */
    async getApiBaseUrl() {
        let apiUrl = '';
        
        // 1. 检查localStorage中的自定义配置
        const customApiUrl = localStorage.getItem('travel_agent_api_url');
        if (customApiUrl && customApiUrl.trim()) {
            try {
                const url = new URL(customApiUrl.trim());
                apiUrl = `${url.origin}/api/travel-plan`;
            } catch (e) {
                console.warn('自定义API URL格式错误，使用默认配置');
            }
        }
        
        // 2. 从后端API获取Agent服务地址
        if (!apiUrl) {
            try {
                const response = await fetch('/api/agent-service-url/');
                if (response.ok) {
                    const data = await response.json();
                    if (data.status === 'success' && data.url) {
                        // 确保URL是完整的
                        let agentUrl = data.url;
                        if (!agentUrl.startsWith('http://') && !agentUrl.startsWith('https://')) {
                            // 如果不是完整URL，使用当前页面的协议和主机
                            const currentOrigin = window.location.origin;
                            agentUrl = `${currentOrigin}/${agentUrl.replace(/^\//, '')}`;
                        }
                        // 确保URL不以斜杠结尾
                        agentUrl = agentUrl.replace(/\/$/, '');
                        // 确保URL不包含双斜杠（除了协议部分）
                        const protocolIndex = agentUrl.indexOf('://');
                        if (protocolIndex !== -1) {
                            const protocol = agentUrl.substring(0, protocolIndex + 3);
                            const rest = agentUrl.substring(protocolIndex + 3).replace(/\/+\//g, '/');
                            agentUrl = protocol + rest;
                        }
                        apiUrl = `${agentUrl}/api/travel-plan`;
                    }
                }
            } catch (e) {
                console.warn('无法从后端API获取Agent服务地址，使用备选方案');
            }
        }
        
        // 3. 使用当前页面的主机和端口
        if (!apiUrl) {
            try {
                const currentUrl = new URL(window.location.href);
                apiUrl = `http://${currentUrl.hostname}:8001/api/travel-plan`;
            } catch (e) {
                console.warn('无法解析当前页面URL，使用备选方案');
            }
        }
        
        // 4. 检查环境变量配置
        if (!apiUrl) {
            const envApiUrl = window.TRAVEL_AGENT_API_URL || process.env.TRAVEL_AGENT_API_URL;
            if (envApiUrl) {
                try {
                    const url = new URL(envApiUrl);
                    apiUrl = `${url.origin}/api/travel-plan`;
                } catch (envError) {
                    console.warn('环境变量API URL格式错误');
                }
            }
        }
        
        // 5. 尝试使用当前页面的origin
        if (!apiUrl) {
            try {
                const currentOrigin = window.location.origin;
                if (currentOrigin && currentOrigin !== 'null') {
                    apiUrl = `${currentOrigin}/api/travel-plan`;
                }
            } catch (originError) {
                console.warn('无法获取当前页面origin');
            }
        }
        
        // 6. 最终备选方案
        if (!apiUrl) {
            apiUrl = 'http://localhost:8001/api/travel-plan';
        }
        
        // 确保URL格式正确
        // 移除开头的斜杠
        if (apiUrl.startsWith('/')) {
            apiUrl = apiUrl.substring(1);
        }
        
        // 确保URL不包含双斜杠（除了协议部分）
        const protocolIndex = apiUrl.indexOf('://');
        if (protocolIndex !== -1) {
            const protocol = apiUrl.substring(0, protocolIndex + 3);
            const rest = apiUrl.substring(protocolIndex + 3).replace(/\/+\//g, '/');
            apiUrl = protocol + rest;
        }
        
        console.log('最终API URL:', apiUrl);
        return apiUrl;
    }
    
    /**
     * 绑定事件处理器
     */
    bindEvents() {
        // 旅游规划按钮事件
        const planButton = document.getElementById('planTravelBtn');
        if (planButton) {
            planButton.addEventListener('click', () => this.startTravelPlanning());
        }
        
        // 取消规划按钮事件
        const cancelButton = document.getElementById('cancelPlanBtn');
        if (cancelButton) {
            cancelButton.addEventListener('click', () => this.cancelTravelPlanning());
        }
    }
    
    /**
     * 开始旅游规划
     */
    async startTravelPlanning() {
        try {
            // 确保API地址已加载
            if (!this.apiBaseUrl) {
                this.apiBaseUrl = await this.getApiBaseUrl();
            }
            
            // 检查是否已在规划中
            if (this.isPlanning) {
                this.showMessage('正在规划中，请稍候...', 'warning');
                return;
            }
            
            // 获取选中的非遗项目
            const selectedItems = this.getSelectedItems();
            if (selectedItems.length === 0) {
                this.showMessage('请先选择要游览的非遗项目', 'error');
                return;
            }
            
            if (selectedItems.length > 20) {
                this.showMessage('选择的项目过多，最多支持20个项目', 'error');
                return;
            }
            
            // 显示规划配置对话框
            const planningConfig = await DialogManager.showPlanningConfigDialog();
            if (!planningConfig) {
                return; // 用户取消
            }
            
            // 开始规划，重置所有相关状态标志
            this.isPlanning = true;
            this.completionHandled = false;
            this.planResultCache = null;
            // 清除当前planId，确保使用新生成的planId
            this.currentPlanId = null;
            localStorage.removeItem('travelCurrentPlanId');
            this.updateUIForPlanning(true);
            
            // 构建请求参数
            const requestData = {
                heritage_ids: selectedItems.map(item => parseInt(item.id)),
                user_id: this.getCurrentUserId().toString(), // 转换为字符串类型，API期望字符串格式
                travel_days: planningConfig.travelDays,
                departure_location: planningConfig.departureLocation,
                travel_mode: planningConfig.travelMode,
                budget_range: planningConfig.budgetRange,
                group_size: planningConfig.groupSize,
                special_requirements: planningConfig.specialRequirements
            };
            
            console.log('发送旅游规划请求:', requestData);
            
            // 发送规划请求
            const requestUrl = `${this.apiBaseUrl.replace(/\/$/, '')}/create`;
            console.log('发送POST请求到:', requestUrl);
            console.log('请求数据:', requestData);
            
            try {
                // 增加浏览器网络请求的详细日志
                console.log('准备发送请求，检查URL是否可达:', requestUrl);
                
                // 尝试使用简单的GET请求测试连接
                const healthUrl = requestUrl.replace('/api/travel-plan/create', '/health');
                const testResponse = await fetch(healthUrl, {
                    method: 'GET',
                    mode: 'cors',
                    credentials: 'include'
                });
                
                console.log('健康检查请求成功，状态码:', testResponse.status);
                
                // 构建请求头
                const headers = {
                    'Content-Type': 'application/json'
                };
                
                // 发送实际的POST请求，Agent服务是独立的FastAPI应用，不需要CSRF token
                const response = await fetch(requestUrl, {
                    method: 'POST',
                    headers: headers,
                    body: JSON.stringify(requestData),
                    mode: 'cors',
                    credentials: 'include'
                });
                
                console.log('收到响应，状态码:', response.status);
                
                if (!response.ok) {
                    const errorText = await response.text();
                    console.error('请求失败，响应内容:', errorText);
                    throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`);
                }
                
                const result = await response.json();
                console.log('响应数据:', result);
                
                if (result.success) {
                    this.currentPlanId = result.plan_id;
                    // 将planId保存到localStorage，确保页面刷新后仍能访问
                    localStorage.setItem('travelCurrentPlanId', this.currentPlanId);
                    this.showMessage(`规划任务已启动，预计需要${result.data.estimated_time}`, 'success');
                    
                    // 开始监控进度
                    this.progressManager.startProgressMonitoring();
                } else {
                    console.error('创建规划失败，错误信息:', result.message);
                    throw new Error(result.message || '创建规划失败');
                }
            } catch (fetchError) {
                console.error('请求发送失败:', fetchError);
                console.error('错误类型:', fetchError.type);
                console.error('错误信息:', fetchError.message);
                console.error('错误堆栈:', fetchError.stack);
                
                // 添加更详细的错误分析
                if (fetchError instanceof TypeError && fetchError.message === 'Failed to fetch') {
                    console.error('错误分析: 可能是网络连接问题、跨域问题或服务器未响应');
                    console.error('请检查:', 
                        '1. agent服务是否正在8001端口运行',
                        '2. 网络连接是否正常',
                        '3. 浏览器控制台是否有跨域错误',
                        '4. agent服务的CORS配置是否正确'
                    );
                }
                
                throw fetchError;
            }
            
        } catch (error) {
            this.handleError(error, '开始旅游规划时发生错误');
            this.isPlanning = false;
            this.updateUIForPlanning(false);
            // 确保currentPlanId仍然存在，以便后续导出和编辑
            console.log('开始旅游规划时发生错误，但保留currentPlanId:', this.currentPlanId);
        }
    }
    
    /**
     * 获取选中的非遗项目
     * @returns {Array} 选中的项目数组
     */
    getSelectedItems() {
        // 实现获取选中项目的逻辑
        const selectedItems = [];
        const checkboxes = document.querySelectorAll('.select-checkbox:checked');
        
        checkboxes.forEach(checkbox => {
            const favoriteItem = checkbox.closest('.favorite-item');
            if (favoriteItem) {
                const itemId = favoriteItem.getAttribute('data-id');
                const itemName = favoriteItem.getAttribute('data-name');
                const itemRegion = favoriteItem.getAttribute('data-region') || '';
                
                if (itemId) {
                    selectedItems.push({
                        id: itemId,
                        name: itemName,
                        region: itemRegion
                    });
                }
            }
        });
        
        return selectedItems;
    }
    
    /**
     * 获取当前用户ID
     * @returns {number} 用户ID
     */
    getCurrentUserId() {
        // 从localStorage获取用户ID，实际项目中可能需要从认证系统获取
        return parseInt(localStorage.getItem('userId') || '1');
    }
    
    /**
     * 显示消息
     * @param {string} message 消息内容
     * @param {string} type 消息类型：success, error, warning, info
     */
    showMessage(message, type = 'info') {
        // 实现消息显示逻辑
        console.log(`${type}: ${message}`);
        
        // 创建右上角浮动通知
        const messageElement = document.createElement('div');
        messageElement.className = `notification notification-${type}`;
        messageElement.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            z-index: 10000;
            animation: slideInRight 0.3s ease-out, fadeOut 0.3s ease-in 2.7s forwards;
            max-width: 350px;
            word-wrap: break-word;
            background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : type === 'warning' ? '#f59e0b' : '#3b82f6'};
        `;
        
        // 添加图标
        const icon = type === 'success' ? '✓' : type === 'error' ? '✗' : type === 'warning' ? '⚠' : 'ℹ';
        messageElement.innerHTML = `
            <span style="margin-right: 8px; font-weight: bold;">${icon}</span>
            ${message}
        `;
        
        // 添加动画样式
        const styleElement = document.getElementById('notification-styles');
        if (!styleElement) {
            const styles = document.createElement('style');
            styles.id = 'notification-styles';
            styles.textContent = `
                @keyframes slideInRight {
                    from {
                        transform: translateX(100%);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }
                @keyframes fadeOut {
                    from {
                        opacity: 1;
                    }
                    to {
                        opacity: 0;
                        transform: translateX(100%);
                    }
                }
            `;
            document.head.appendChild(styles);
        }
        
        // 添加到页面
        document.body.appendChild(messageElement);
        
        // 3秒后自动移除消息
        setTimeout(() => {
            if (messageElement.parentNode) {
                messageElement.parentNode.removeChild(messageElement);
            }
        }, 3000);
    }
    
    /**
     * 更新UI为规划中状态
     * @param {boolean} isPlanning 是否正在规划
     */
    updateUIForPlanning(isPlanning) {
        // 实现UI更新逻辑，比如显示/隐藏进度条，禁用/启用按钮等
        console.log('更新UI状态:', isPlanning ? '规划中' : '未规划');
        
        // 显示/隐藏整个规划进度区域
        const planningProgress = document.getElementById('planning-progress');
        if (planningProgress) {
            planningProgress.style.display = isPlanning ? 'block' : 'none';
        }
        
        // 显示/隐藏进度条容器
        const progressBarContainer = document.querySelector('.progress-bar-container');
        if (progressBarContainer) {
            progressBarContainer.style.display = isPlanning ? 'block' : 'none';
        }
        
        const planButton = document.getElementById('planTravelBtn');
        if (planButton) {
            planButton.disabled = isPlanning;
        }
    }
    
    /**
     * 处理错误
     * @param {Error} error 错误对象
     * @param {string} context 错误上下文
     */
    handleError(error, context) {
        console.error(`${context}:`, error);
        this.showMessage(`${context}: ${error.message}`, 'error');
    }
    
    /**
     * 导出旅游规划
     */
    async exportTravelPlan() {
        // 保存所有导出按钮的原始状态，声明在try块之外，确保finally块能访问到
        let originalButtonStates = [];
        
        try {
            // 防止同时执行多个导出操作
            if (this.isExporting) {
                console.warn('正在执行导出操作，请勿重复点击');
                this.showMessage('正在导出规划，请稍候...', 'info');
                return;
            }
            
            // 设置导出标志位
            this.isExporting = true;
            
            // 确保API地址已加载
            if (!this.apiBaseUrl) {
                this.apiBaseUrl = await this.getApiBaseUrl();
            }
            
            // 保存所有导出按钮的原始状态
            const exportButtons = document.querySelectorAll('[onclick*="exportTravelPlan"]');
            
            // 更新所有导出按钮状态为"导出中"
            exportButtons.forEach(button => {
                // 保存原始状态
                originalButtonStates.push({
                    button: button,
                    originalText: button.innerHTML,
                    originalDisabled: button.disabled
                });
                
                // 更新按钮状态
                button.disabled = true;
                button.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16" style="margin-right: 8px; animation: spin 1s linear infinite;">
                        <path d="M8 16a7 7 0 1 0 0-14 7 7 0 0 0 0 14zm0 1a8 8 0 1 1 0-16 8 8 0 0 1 0 16z"/>
                        <path d="M7 8a1 1 0 0 1 2 0V5.5a.5.5 0 0 1 1 0V8a2 2 0 1 1-4 0V5.5a.5.5 0 0 1 1 0V8z"/>
                    </svg>导出中...
                `;
            });
            
            // 显示导出进度
            this.showMessage('正在导出规划，请稍候...', 'info');
            
            // 调用导出API，支持两种导出方式
            let exportUrl;
            let requestBody;
            
            // 检查是否有可导出的数据
            if (!this.currentPlanId && !this.planResultCache) {
                this.showMessage('没有可导出的规划', 'error');
                this.isExporting = false;
                return;
            }
            
            // 优先使用旅游规划的导出端点（如果有plan_id）
            if (this.currentPlanId) {
                exportUrl = `${this.apiBaseUrl.replace(/\/$/, '')}/export/${this.currentPlanId}`;
                requestBody = { format: 'pdf' };
            } else if (this.planResultCache) {
                // 如果没有plan_id但有缓存的规划结果，使用AI聊天导出端点
                exportUrl = `${this.apiBaseUrl.replace('/api/travel-plan', '/api/agent/export_plan_pdf')}`;
                requestBody = {
                    complete_plan_data: this.planResultCache,
                    title: this.planResultCache?.title || '我的旅游规划',
                    destination: this.planResultCache?.destination,
                    duration: this.planResultCache?.duration,
                    weather_info: this.planResultCache?.weather_info
                };
            }
            
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 120000); // 设置120秒超时，适应更丰富的AI内容生成
            
            try {
                const response = await fetch(exportUrl, {
                    method: 'POST',
                    mode: 'cors',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(requestBody),
                    signal: controller.signal // 添加超时控制
                });
                
                clearTimeout(timeoutId); // 清除超时计时器
                
                if (!response.ok) {
                    let errorMessage = `导出失败: ${response.status} ${response.statusText}`;
                    try {
                        // 尝试获取后端返回的详细错误信息
                        const errorData = await response.json();
                        if (errorData.detail) {
                            errorMessage = `导出失败: ${errorData.detail}`;
                        }
                    } catch (e) {
                        // 如果无法解析JSON，使用默认错误信息
                    }
                    throw new Error(errorMessage);
                }
                
                // 获取响应头中的文件名
                const contentDisposition = response.headers.get('Content-Disposition');
                let filename;
                if (contentDisposition) {
                    const match = contentDisposition.match(/filename="?([^"]+)"?/);
                    if (match && match[1]) {
                        filename = match[1];
                    }
                }
                
                // 如果没有从响应头获取到文件名，使用默认文件名
                if (!filename) {
                    const destination = this.planResultCache?.destination || '旅游规划';
                    const planId = this.currentPlanId || Date.now();
                    filename = `${destination}_${planId}.pdf`;
                }
                
                // 直接处理响应为文件流
                const blob = await response.blob();
                
                // 验证blob大小，确保不是空文件
                if (blob.size === 0) {
                    throw new Error('导出的PDF文件为空');
                }
                
                // 创建下载链接
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                
                // 触发下载
                a.click();
                
                // 清理资源
                setTimeout(() => {
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                }, 100);
                
                // 显示成功消息
                this.showMessage('规划导出成功！', 'success');
            } catch (error) {
                clearTimeout(timeoutId); // 清除超时计时器
                if (error.name === 'AbortError') {
                    throw new Error('导出请求超时，请稍后重试');
                }
                throw error;
            }
        } catch (error) {
            this.handleError(error, '导出旅游规划时发生错误');
        } finally {
            // 重置导出标志位，允许后续导出操作
            this.isExporting = false;
            
            // 恢复所有导出按钮的原始状态
            if (originalButtonStates) {
                originalButtonStates.forEach(({ button, originalText, originalDisabled }) => {
                    button.innerHTML = originalText;
                    button.disabled = originalDisabled;
                });
            }
        }
    }
    
    /**
     * 编辑旅游规划
     */
    async editTravelPlan() {
        try {
            // 确保API地址已加载
            if (!this.apiBaseUrl) {
                this.apiBaseUrl = await this.getApiBaseUrl();
            }
            
            if (!this.currentPlanId) {
                this.showMessage('没有可编辑的规划', 'error');
                return;
            }
            
            // 获取规划结果
            let planData;
            if (this.planResultCache) {
                planData = this.planResultCache;
            } else {
                planData = await this.getPlanningResult();
                this.planResultCache = planData;
            }
            
            if (!planData) {
                this.showMessage('无法获取规划数据', 'error');
                return;
            }
            
            // 显示编辑界面，这里可以调用plan-editor.js中的方法
            if (typeof window.openPlanEditor === 'function') {
                // 只传递planData一个参数，因为openPlanEditor函数只接收一个参数
                window.openPlanEditor(planData);
                
                // 关闭旅游规划结果模态框
                const planningResultDialog = document.getElementById('planningResultDialog');
                if (planningResultDialog) {
                    planningResultDialog.remove();
                }
            } else {
                this.showMessage('规划编辑器未加载', 'error');
            }
        } catch (error) {
            this.handleError(error, '编辑旅游规划时发生错误');
        }
    }
    
    /**
     * 取消旅游规划
     */
    async cancelTravelPlanning() {
        try {
            if (!this.currentPlanId || !this.isPlanning) {
                return;
            }
            
            // 确保API地址已加载
            if (!this.apiBaseUrl) {
                this.apiBaseUrl = await this.getApiBaseUrl();
            }
            
            // 调用取消API
            const cancelUrl = `${this.apiBaseUrl.replace(/\/$/, '')}/cancel/${this.currentPlanId}`;
            const response = await fetch(cancelUrl, {
                method: 'POST',
                mode: 'cors',
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error(`取消失败: ${response.status} ${response.statusText}`);
            }
            
            // 停止进度监控
            this.progressManager.stopProgressMonitoring();
            
            // 重置状态
            this.isPlanning = false;
            this.completionHandled = true;
            this.updateUIForPlanning(false);
            
            this.showMessage('规划已取消', 'success');
        } catch (error) {
            this.handleError(error, '取消旅游规划时发生错误');
        }
    }
    
    /**
     * 停止进度监控
     */
    stopProgressMonitoring() {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
    }
    
    /**
     * 获取规划结果
     * @returns {Promise<Object|null>} 规划结果
     */
    async getPlanningResult() {
        if (!this.currentPlanId) {
            return null;
        }
        
        try {
            // 确保API地址已加载
            if (!this.apiBaseUrl) {
                this.apiBaseUrl = await this.getApiBaseUrl();
            }
            
            // 构建请求头，Agent服务是独立的FastAPI应用，不需要CSRF token
            const headers = {};
            
            const response = await fetch(`${this.apiBaseUrl.replace(/\/$/, '')}/result/${this.currentPlanId}`, {
                headers: headers,
                credentials: 'include'
            });
            
            if (!response.ok) {
                if (response.status === 404) {
                    // 规划结果不存在，可能是因为规划还未完成或已过期
                    console.warn(`规划结果不存在: ${this.currentPlanId}`);
                    return null;
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                return result.data;
            } else {
                throw new Error(result.message || '获取结果失败');
            }
            
        } catch (error) {
            console.error('获取规划结果失败:', error);
            throw error;
        }
    }
    
    /**
     * 显示规划结果
     * @param {Object} planData 规划数据
     */
    displayPlanningResult(planData) {
        this.resultRenderer.displayPlanningResult(planData);
    }
}

// 导出TravelPlanningAgent类，供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TravelPlanningAgent;
} else if (typeof window !== 'undefined') {
    window.TravelPlanningAgent = TravelPlanningAgent;
}
