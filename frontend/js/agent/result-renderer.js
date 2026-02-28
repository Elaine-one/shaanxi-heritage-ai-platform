

/**
 * 旅游规划结果渲染器
 * 负责生成和渲染旅游规划结果的HTML内容
 * 包含：天气集成、行程节奏分析、未定义值处理
 */

class ResultRenderer {
    /**
     * 构造函数
     * @param {TravelPlanningAgent} agent 旅游规划Agent实例
     */
    constructor(agent) {
        this.agent = agent;
    }
    
    /**
     * 显示规划结果
     * @param {Object} planData 规划数据
     */
    displayPlanningResult(planData) {
        // 创建结果显示对话框
        const resultHtml = this.generateResultHTML(planData);
        
        // 显示结果对话框
        const dialogHtml = `
            <div id="planningResultDialog" class="modal-overlay">
                <div class="modal-content large">
                    <div class="modal-header">
                        <h3>旅游规划结果</h3>
                        <button class="modal-close" onclick="document.getElementById('planningResultDialog').remove();">&times;</button>
                    </div>
                    <div class="modal-body">
                        ${resultHtml}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" onclick="document.getElementById('planningResultDialog').remove();">关闭</button>
                        <button type="button" id="ai-edit-btn" class="btn btn-success ai-edit-btn-selector" onclick="travelAgent.editTravelPlan()">AI 对话修改</button>
                        <button type="button" id="exportPlanBtnResult" class="btn btn-primary" onclick="travelAgent.exportTravelPlan()">导出 PDF</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', dialogHtml);
        
        // 绑定建议栏标签页切换事件
        this.bindRecommendationTabs();
    }
    
    /**
     * 生成结果HTML
     * @param {Object} planData 规划数据
     * @returns {string} HTML字符串
     */
    generateResultHTML(planData) {
        let html = '';
        
        // 1. 基本信息
        if (planData.basic_info) {
            html += `
                <div class="result-section">
                    <h4>基本信息</h4>
                    <div class="info-grid">
                        <div class="info-item"><strong>标题:</strong> ${planData.basic_info.title || '非遗之旅'}</div>
                        <div class="info-item"><strong>时长:</strong> ${planData.basic_info.duration || '-'}</div>
                        <div class="info-item"><strong>出发地:</strong> ${planData.basic_info.departure || '未指定'}</div>
                        <div class="info-item"><strong>出行方式:</strong> ${planData.basic_info.travel_mode || '自驾'}</div>
                        <div class="info-item"><strong>团队人数:</strong> ${planData.basic_info.group_size || 1}人</div>
                        <div class="info-item"><strong>预算范围:</strong> ${planData.basic_info.budget_range || '中等'}</div>
                    </div>
                </div>
            `;
        }
        
        // 2. 行程安排
        if (planData.itinerary && planData.itinerary.length > 0) {
            html += `
                <div class="result-section">
                    <h4>每日行程</h4>
                    <div class="itinerary-container">
            `;
            
            planData.itinerary.forEach(dayPlan => {
                // 安全获取节奏标签，如果没有则默认为中等
                const pace = dayPlan.pace_label || '中等节奏';
                
                // 天气展示逻辑
                let weatherHtml = '';
                if (dayPlan.weather) {
                    const cond = dayPlan.weather.condition || '';
                    const temp = dayPlan.weather.temperature || '';
                    if (cond || temp) {
                        weatherHtml = `
                            <div class="day-weather-badge" style="background:#e3f2fd; color:#0277bd; padding:2px 8px; border-radius:12px; font-size:12px; display:inline-block; margin-left:10px; font-weight:normal;">
                                <i class="fas fa-cloud-sun"></i> ${cond} ${temp}
                            </div>
                        `;
                    }
                }

                html += `
                    <div class="day-plan">
                        <div class="day-header" style="display:flex; justify-content:space-between; align-items:center;">
                            <h5 style="margin:0;">第${dayPlan.day}天：${dayPlan.theme || '文化探索'} ${weatherHtml}</h5>
                            <span class="badge" style="background:#e0f7fa; color:#006064; padding:4px 8px; border-radius:4px; font-size:12px;">${pace}</span>
                        </div>
                        
                        <div class="day-items" style="margin-top:15px;">
                `;
                
                if (dayPlan.items && dayPlan.items.length > 0) {
                    dayPlan.items.forEach((item, index) => {
                        // 样式美化：左侧边框颜色区分
                        const duration = item.visit_duration ? `约${item.visit_duration}小时` : '时间自定';
                        html += `
                            <div class="heritage-item" style="padding:12px; border-left:4px solid #4caf50; background:#f9f9f9; margin-bottom:10px; border-radius:0 4px 4px 0;">
                                <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                                    <h6 style="margin:0; font-weight:bold; color:#333;">${index + 1}. ${item.name}</h6>
                                    <span style="font-size:12px; color:#666; background:#eee; padding:2px 6px; border-radius:4px;">${item.category || '非遗'}</span>
                                </div>
                                <p style="margin:0; font-size:13px; color:#666; display:flex; align-items:center; gap:15px;">
                                    <span><i class="fas fa-map-marker-alt text-danger"></i> ${item.region || '陕西'}</span>
                                    <span><i class="fas fa-clock text-primary"></i> ${duration}</span>
                                    ${item.travel_time_hours ? `<span><i class="fas fa-car text-secondary"></i> 车程约${item.travel_time_hours}小时</span>` : ''}
                                </p>
                            </div>
                        `;
                    });
                } else {
                    html += `<div class="text-muted p-2" style="font-style:italic; color:#999; text-align:center;">当天以自由活动为主，建议探索周边美食或休息调整。</div>`;
                }
                
                html += `
                        </div>
                    </div>
                `;
            });
            
            html += `
                    </div>
                </div>
            `;
        }
        
        // 3. 行程分析 (替代旧的时间统计)
        if (planData.pace_analysis) {
            const pace = planData.pace_analysis;
            const highlights = pace.highlights && pace.highlights.length > 0 ? pace.highlights.join('、') : '深度非遗文化体验';
            const relaxInfo = pace.relax_days && pace.relax_days.length > 0 ? `第 ${pace.relax_days.join(',')} 天行程较轻松，适合休整` : '行程充实，建议保持体力';
            
            html += `
                <div class="result-section">
                    <h4>行程亮点与节奏</h4>
                    <div style="display:flex; gap:15px; flex-wrap:wrap;">
                        <div class="info-card" style="flex:1; min-width:200px; background:#fff3e0; padding:15px; border-radius:8px; border:1px solid #ffe0b2;">
                            <strong style="color:#e65100; display:block; margin-bottom:8px;"><i class="fas fa-star"></i> 核心体验</strong>
                            <div style="font-size:14px; color:#333; line-height:1.6;">${highlights}</div>
                        </div>
                        <div class="info-card" style="flex:1; min-width:200px; background:#e8eaf6; padding:15px; border-radius:8px; border:1px solid #c5cae9;">
                            <strong style="color:#1a237e; display:block; margin-bottom:8px;"><i class="fas fa-chart-line"></i> 节奏概览</strong>
                            <div style="font-size:14px; color:#333; line-height:1.6;">${relaxInfo}</div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        // 4. 智能建议
        if (planData.recommendations) {
            html += `
                <div class="result-section">
                    <div class="recommendations-header">
                        <h4>智能出行建议</h4>
                        <div class="recommendations-tabs">
                            <button class="tab-btn active" data-tab="tips">💡 贴士</button>
                            <button class="tab-btn" data-tab="packing">🎒 装备</button>
                            <button class="tab-btn" data-tab="budget">💰 预算</button>
                        </div>
                    </div>
                    <div class="recommendations-content">
            `;
            
            // 实用提示
            const tips = planData.recommendations.travel_tips || [];
            html += `
                <div class="tab-content active" data-content="tips">
                    <ul class="custom-list">
                        ${tips.length > 0 ? tips.map(tip => `<li>${tip}</li>`).join('') : '<li>暂无特殊提示</li>'}
                    </ul>
                    ${this.generateAdditionalTips(planData)}
                </div>
            `;
            
            // 打包清单
            const packing = planData.recommendations.packing_list || [];
            html += `
                <div class="tab-content" data-content="packing">
                    <ul class="custom-list">
                        ${packing.length > 0 ? packing.map(item => `<li>${item}</li>`).join('') : '<li>常规出行装备即可</li>'}
                    </ul>
                    ${this.generateWeatherBasedPacking(planData)}
                </div>
            `;
            
            // 预算
            const budget = planData.recommendations.budget_estimate || {};
            html += `
                <div class="tab-content" data-content="budget">
                    ${budget.description ? `<p style="margin-bottom:10px;">${budget.description}</p>` : '<p class="text-muted">预算视具体消费习惯而定</p>'}
                    ${this.generateBudgetTips(planData)}
                </div>
            `;
            
            html += `</div></div>`;
        }
        
        return html;
    }
    
    /**
     * 生成额外的旅游提示
     * @param {Object} planData 规划数据
     * @returns {string} HTML字符串
     */
    generateAdditionalTips(planData) {
        const tips = [];
        
        // 基于天数的建议
        if (planData.itinerary && planData.itinerary.length > 0) {
            const days = planData.itinerary.length;
            if (days >= 5) {
                tips.push('🗓️ 行程较长，建议安排1-2天的休息时间，避免过度疲劳');
            }
            if (days <= 2) {
                tips.push('⏰ 行程紧凑，建议提前规划路线，合理安排时间');
            }
        }
        
        if (tips.length > 0) {
            return `
                <div style="margin-top:15px; padding-top:10px; border-top:1px dashed #eee;">
                    <strong style="font-size:13px; color:#666;">更多建议：</strong>
                    <ul class="custom-list" style="margin-top:5px;">
                        ${tips.map(tip => `<li>${tip}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        return '';
    }
    
    /**
     * 生成打包清单分类
     */
    generatePackingCategories(packingList) {
        return '';
    }
    
    /**
     * 生成基于天气的打包建议
     * @param {Object} planData 规划数据
     * @returns {string} HTML字符串
     */
    generateWeatherBasedPacking(planData) {
        if (!planData.weather_info) return '';
        
        // 尝试从 summary 获取天气描述
        let condition = '';
        // 兼容不同的天气数据结构
        const summary = planData.weather_info.summary || {};
        const summaryStr = JSON.stringify(summary);
        
        let tips = [];
        if (summaryStr.includes('雨')) {
            tips.push('☔ 预报有雨，建议携带雨具，选择室内备选活动');
        }
        if (summaryStr.includes('冷') || summaryStr.includes('低温')) {
             tips.push('🧥 气温较低，请备好防寒衣物');
        }
        if (summaryStr.includes('热') || summaryStr.includes('高温')) {
             tips.push('☀️ 紫外线较强，请注意防晒');
        }
        
        if (tips.length > 0) {
            return `
                <div style="margin-top:15px; padding:10px; background:#e3f2fd; border-radius:4px;">
                    <strong style="color:#0277bd; font-size:13px;"><i class="fas fa-cloud-showers-heavy"></i> 天气特别提醒</strong>
                    <ul class="custom-list" style="margin-bottom:0;">
                        ${tips.map(tip => `<li>${tip}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        return '';
    }
    
    /**
     * 生成预算建议
     */
    generateBudgetTips(planData) {
        // 如果后端没有返回详细的预算 breakdown，这里就不显示额外的了
        return '';
    }
    
    /**
     * 生成安全须知
     */
    generateSafetyTips(planData) {
        return '';
    }
    
    /**
     * 绑定建议栏标签页切换事件
     */
    bindRecommendationTabs() {
        const tabs = document.querySelectorAll('.recommendations-tabs .tab-btn');
        const tabContents = document.querySelectorAll('.recommendations-content .tab-content');
        
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                // 移除所有活动状态
                tabs.forEach(t => t.classList.remove('active'));
                tabContents.forEach(content => content.classList.remove('active'));
                
                // 添加当前活动状态
                tab.classList.add('active');
                const targetTab = tab.getAttribute('data-tab');
                const targetContent = document.querySelector(`.tab-content[data-content="${targetTab}"]`);
                if (targetContent) {
                    targetContent.classList.add('active');
                }
            });
        });
    }
}

// 导出ResultRenderer类，供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ResultRenderer;
} else {
    window.ResultRenderer = ResultRenderer;
}