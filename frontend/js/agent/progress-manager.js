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
        this.progressInterval = null;
    }
    
    /**
     * 开始进度监控
     */
    startProgressMonitoring() {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
        }
        
        // 立即检查一次进度
        this.checkProgress();
        
        // 每2秒检查一次进度
        this.progressInterval = setInterval(() => {
            this.checkProgress();
        }, 2000);
    }
    
    /**
     * 检查规划进度
     */
    async checkProgress() {
        if (!this.agent.currentPlanId || this.agent.completionHandled) {
            return;
        }
        
        try {
            // 确保API地址已加载
            if (!this.agent.apiBaseUrl) {
                this.agent.apiBaseUrl = await this.agent.getApiBaseUrl();
            }
            
            // 构建请求头，Agent服务是独立的FastAPI应用，不需要CSRF token
            const headers = {};
            
            const response = await fetch(`${this.agent.apiBaseUrl.replace(/\/$/, '')}/progress/${this.agent.currentPlanId}`, {
                headers: headers,
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const progressData = await response.json();
            
            // 更新进度显示
            this.updateProgressDisplay(progressData);
            
            // 检查是否完成（防止重复处理）
            if (progressData.status === 'completed' && !this.agent.completionHandled) {
                this.agent.completionHandled = true;
                this.onPlanningCompleted();
            } else if (progressData.status === 'error' && !this.agent.completionHandled) {
                this.agent.completionHandled = true;
                this.onPlanningError(progressData.error_message);
            }
            
        } catch (error) {
            // 增加调试信息，帮助了解进度检查失败的原因
            console.error('检查规划进度失败:', error);
            console.error('请求URL:', `${this.agent.apiBaseUrl.replace(/\/$/, '')}/progress/${this.agent.currentPlanId}`);
            console.error('当前planId:', this.agent.currentPlanId);
            console.error('当前API地址:', this.agent.apiBaseUrl);
            // 不中断进度监控，继续尝试
        }
    }
    
    /**
     * 更新进度显示
     * @param {Object} progressData 进度数据
     */
    updateProgressDisplay(progressData) {
        // 更新进度条
        const progressBar = document.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.style.width = `${progressData.progress}%`;
            progressBar.textContent = `${progressData.progress}%`;
        }
        
        // 更新当前步骤
        const currentStepElement = document.querySelector('.current-step');
        if (currentStepElement) {
            currentStepElement.textContent = progressData.current_step;
        }
        
        // 更新步骤列表
        const stepsContainer = document.querySelector('.planning-steps');
        if (stepsContainer && progressData.steps) {
            stepsContainer.innerHTML = '';
            progressData.steps.forEach((step, index) => {
                const stepElement = document.createElement('div');
                stepElement.className = 'step-item';
                
                if (step === progressData.current_step) {
                    stepElement.classList.add('active');
                } else if (index < progressData.steps.indexOf(progressData.current_step)) {
                    stepElement.classList.add('completed');
                }
                
                stepElement.textContent = step;
                stepsContainer.appendChild(stepElement);
            });
        }
    }
    
    /**
     * 规划完成处理
     */
    async onPlanningCompleted() {
        // 立即停止进度监控，防止竞态条件
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
        
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
        // 停止进度监控
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
        
        this.agent.isPlanning = false;
        this.agent.completionHandled = true; // 确保不会重复处理
        this.agent.updateUIForPlanning(false);
        
        this.agent.showMessage(`规划失败: ${errorMessage}`, 'error');
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
}

// 导出ProgressManager类，供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ProgressManager;
} else {
    window.ProgressManager = ProgressManager;
}