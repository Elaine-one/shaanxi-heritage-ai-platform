/**
 * 旅游规划进度管理器
 * 负责监控规划进度、更新进度条和处理完成状态
 */

class ProgressManager {
    /**
     * 构造函数
     * @param {TravelPlanningAgent} agent 旅游规划Agent实例
     */
    constructor(agent) {
        this.agent = agent;
        this.eventSource = null;
        this.simulationInterval = null;
        this.lastRealProgress = 0;
    }
    
    /**
     * 开始模拟进度（在发送请求前调用）
     */
    startSimulation() {
        if (this.simulationInterval) {
            clearInterval(this.simulationInterval);
        }
        
        let simProgress = this.lastRealProgress || 2;
        console.log('[模拟进度] 开始模拟，从', simProgress, '% 开始');
        
        this.simulationInterval = setInterval(() => {
            if (simProgress >= 99) {
                console.log('[模拟进度] 达到99%，停止模拟');
                this.stopSimulation();
                return;
            }
            
            simProgress += 1;
            console.log('[模拟进度] 更新到', simProgress, '%');
            this.updateProgressBar(simProgress);
            
            // 更新步骤列表（使用进度百分比判断）
            this.updateStepsByProgress(simProgress);
        }, 100); // 每100ms增加1%
    }
    
    /**
     * 根据进度百分比更新步骤列表
     */
    updateStepsByProgress(progress) {
        const stepsContainer = document.querySelector('.planning-steps');
        if (!stepsContainer) return;
        
        const steps = ['分析非遗项目', '获取天气信息', '生成AI建议', '路径规划计算', '生成路书', '完成'];
        
        // 根据进度百分比确定当前步骤索引
        let activeIndex = 0;
        if (progress >= 90) activeIndex = 5;
        else if (progress >= 70) activeIndex = 4;
        else if (progress >= 50) activeIndex = 3;
        else if (progress >= 30) activeIndex = 2;
        else if (progress >= 10) activeIndex = 1;
        else activeIndex = 0;
        
        // 只在步骤变化时更新DOM
        const currentActive = stepsContainer.querySelector('.active');
        const currentActiveIndex = currentActive ? Array.from(stepsContainer.children).indexOf(currentActive) : -1;
        
        if (currentActiveIndex !== activeIndex) {
            stepsContainer.innerHTML = '';
            steps.forEach((step, index) => {
                const stepElement = document.createElement('div');
                stepElement.className = 'step-item';
                
                if (index === activeIndex) {
                    stepElement.classList.add('active');
                } else if (index < activeIndex) {
                    stepElement.classList.add('completed');
                }
                
                stepElement.textContent = step;
                stepsContainer.appendChild(stepElement);
            });
        }
    }
    
    /**
     * 开始进度监控（使用 SSE）
     * @param {string} planId 规划ID
     */
    async startProgressMonitoring(planId) {
        if (this.eventSource) {
            this.eventSource.close();
        }
        
        try {
            const progressUrl = `${this.agent.apiBaseUrl.replace(/\/$/, '')}/progress-stream/${planId}`;
            console.log('[进度监控] 建立SSE连接:', progressUrl);
            
            this.eventSource = new EventSource(progressUrl);
            
            this.eventSource.onopen = async () => {
                console.log('[进度监控] SSE连接已建立');
                
                // 立即查询当前进度，避免错过已完成的进度
                try {
                    const currentData = await this.getCurrentProgress(planId);
                    if (currentData) {
                        console.log('[进度监控] 初始进度:', currentData.progress, '%');
                        this.lastRealProgress = currentData.progress;
                        this.updateProgressDisplay(currentData);
                        
                        // 如果已完成，停止模拟
                        if (currentData.progress >= 100) {
                            this.stopSimulation();
                        }
                    }
                } catch (error) {
                    console.error('[进度监控] 获取初始进度失败:', error);
                }
            };
            
            this.eventSource.onmessage = (event) => {
                const progressData = JSON.parse(event.data);
                console.log('[进度监控] 收到SSE更新:', progressData.progress, '% -', progressData.current_step);
                
                this.lastRealProgress = progressData.progress;
                this.updateProgressDisplay(progressData);
                
                // 收到真实进度，停止模拟
                this.stopSimulation();
                
                if (progressData.status === 'completed' && !this.agent.completionHandled) {
                    this.agent.completionHandled = true;
                    this.onPlanningCompleted();
                } else if (progressData.status === 'error' && !this.agent.completionHandled) {
                    this.agent.completionHandled = true;
                    this.onPlanningError(progressData.error_message);
                }
            };
            
            this.eventSource.onerror = (error) => {
                console.error('[进度监控] SSE错误:', error);
                this.eventSource.close();
                this.eventSource = null;
            };
            
        } catch (error) {
            console.error('[进度监控] SSE连接失败:', error);
        }
    }
    
    /**
     * 获取当前进度（立即查询）
     */
    async getCurrentProgress(planId) {
        try {
            const progressUrl = `${this.agent.apiBaseUrl.replace(/\/$/, '')}/progress/${planId}`;
            const response = await fetch(progressUrl, { credentials: 'include' });
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('[进度监控] 获取当前进度失败:', error);
        }
        return null;
    }
    
    /**
     * 停止模拟进度
     */
    stopSimulation() {
        console.log('[停止模拟] 开始停止模拟，simulationInterval:', this.simulationInterval);
        if (this.simulationInterval) {
            clearInterval(this.simulationInterval);
            this.simulationInterval = null;
            console.log('[停止模拟] 模拟已停止');
        } else {
            console.log('[停止模拟] 没有正在运行的模拟');
        }
    }
    
    /**
     * 停止进度监控
     */
    stopProgressMonitoring() {
        console.log('[停止监控] 开始停止进度监控');
        this.stopSimulation();
        
        if (this.eventSource) {
            console.log('[停止监控] 关闭SSE连接');
            this.eventSource.close();
            this.eventSource = null;
        }
        console.log('[停止监控] 进度监控已完全停止');
    }
    
    /**
     * 更新进度显示（带平滑动画）
     * @param {Object} progressData 进度数据
     */
    updateProgressDisplay(progressData) {
        console.log('[更新进度] progress:', progressData.progress, '%, step:', progressData.current_step);
        
        const newProgress = progressData.progress;
        this.lastRealProgress = newProgress;
        
        // 收到真实进度，停止模拟
        this.stopSimulation();
        
        // 立即更新到真实进度
        this.updateProgressBar(newProgress);
        
        // 更新当前步骤文本
        const currentStepElement = document.querySelector('.current-step');
        if (currentStepElement) {
            currentStepElement.textContent = progressData.current_step;
        }
        
        // 更新步骤列表（使用进度百分比判断）
        this.updateStepsByProgress(newProgress);
    }
    
    /**
     * 更新进度条 DOM
     */
    updateProgressBar(progress) {
        const progressBar = document.querySelector('.progress-bar');
        if (progressBar) {
            const roundedProgress = Math.round(progress);
            progressBar.style.width = `${roundedProgress}%`;
            progressBar.textContent = `${roundedProgress}%`;
        }
    }
    
    /**
     * 规划完成处理
     */
    async onPlanningCompleted() {
        this.stopProgressMonitoring();
        
        this.agent.isPlanning = false;
        this.agent.updateUIForPlanning(false);
        
        this.agent.showMessage('旅游规划完成！', 'success');
        
        // 获取规划结果（使用缓存机制）
        try {
            if (!this.agent.planResultCache) {
                this.agent.planResultCache = await this.agent.getPlanningResult();
            }
            if (this.agent.planResultCache) {
                this.agent.displayPlanningResult(this.agent.planResultCache);
            }
        } catch (error) {
            this.agent.showMessage('规划完成，但获取结果失败', 'warning');
        }
    }
    
    /**
     * 规划错误处理
     * @param {string} errorMessage 错误消息
     */
    onPlanningError(errorMessage) {
        this.stopProgressMonitoring();
        
        this.agent.isPlanning = false;
        this.agent.completionHandled = true;
        this.agent.updateUIForPlanning(false);
        
        this.agent.showMessage(`规划失败: ${errorMessage}`, 'error');
    }
}

// 导出ProgressManager类，供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ProgressManager;
} else {
    window.ProgressManager = ProgressManager;
}