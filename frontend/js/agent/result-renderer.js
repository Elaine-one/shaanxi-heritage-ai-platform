/**
 * 旅游规划结果渲染器
 * 负责生成和渲染旅游规划结果的HTML内容
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
                        <button type="button" class="btn btn-success" onclick="travelAgent.editTravelPlan()">编辑规划</button>
                        <button type="button" class="btn btn-primary" onclick="travelAgent.exportTravelPlan()">导出规划</button>
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
        
        // 基本信息
        if (planData.basic_info) {
            html += `
                <div class="result-section">
                    <h4>基本信息</h4>
                    <div class="info-grid">
                        <div class="info-item"><strong>标题:</strong> ${planData.basic_info.title}</div>
                        <div class="info-item"><strong>时长:</strong> ${planData.basic_info.duration}</div>
                        <div class="info-item"><strong>出发地:</strong> ${planData.basic_info.departure}</div>
                        <div class="info-item"><strong>出行方式:</strong> ${planData.basic_info.travel_mode}</div>
                        <div class="info-item"><strong>团队人数:</strong> ${planData.basic_info.group_size}人</div>
                        <div class="info-item"><strong>预算范围:</strong> ${planData.basic_info.budget_range}</div>
                    </div>
                </div>
            `;
        }
        
        // 行程安排
        if (planData.itinerary && planData.itinerary.length > 0) {
            html += `
                <div class="result-section">
                    <h4>行程安排</h4>
                    <div class="itinerary-container">
            `;
            
            planData.itinerary.forEach(dayPlan => {
                const totalTime = dayPlan.total_time || (dayPlan.estimated_duration + dayPlan.travel_time);
                const efficiency = dayPlan.efficiency || Math.round((dayPlan.estimated_duration / totalTime) * 100);
                const difficulty = dayPlan.difficulty_level || '中等';
                const itemsCount = dayPlan.items ? dayPlan.items.length : 0;
                
                html += `
                    <div class="day-plan">
                        <div class="day-header">
                            <h5>第${dayPlan.day}天 ${dayPlan.date ? `(${dayPlan.date})` : ''}</h5>
                            <div class="day-info">
                                <span>🕐 总时长: ${totalTime}小时</span>
                                <span>🎯 游览: ${dayPlan.estimated_duration}小时</span>
                                <span>🚗 交通: ${dayPlan.travel_time}小时</span>
                                <span>📊 效率: ${efficiency}%</span>
                                <span>⚡ 难度: ${difficulty}</span>
                                <span>📍 景点: ${itemsCount}个</span>
                            </div>
                        </div>
                        
                        <div class="day-items">
                `;
                
                if (dayPlan.items && dayPlan.items.length > 0) {
                    dayPlan.items.forEach((item, index) => {
                        const startTime = item.start_time || `${9 + index * 2}:00`;
                        const endTime = item.end_time || `${11 + index * 2}:00`;
                        const difficulty = item.difficulty || '中等';
                        const highlight = item.is_highlight ? '⭐ ' : '';
                        
                        html += `
                            <div class="heritage-item">
                                <h6>${highlight}${item.name}</h6>
                                <div class="time-info">${startTime} - ${endTime}</div>
                                <p><strong>类别:</strong> ${item.category || item.type || '未分类'}</p>
                                <p><strong>地区:</strong> ${item.region}</p>
                                <p><strong>难度等级:</strong> ${difficulty}</p>
                                <p><strong>游览时长:</strong> ${item.visit_duration || item.duration || 2}小时</p>
                                ${item.travel_time ? `<p><strong>到达时间:</strong> ${item.travel_time}分钟</p>` : ''}
                                ${item.description ? `<p><strong>介绍:</strong> ${item.description}</p>` : ''}
                                ${item.special_notes ? `<p><strong>特别提示:</strong> ${item.special_notes}</p>` : ''}
                            </div>
                        `;
                    });
                }
                
                // 天气信息
                if (dayPlan.weather) {
                    html += `
                        <div class="weather-info">
                            <h6>天气信息</h6>
                            <p><strong>天气:</strong> ${dayPlan.weather.condition}</p>
                            <p><strong>温度:</strong> ${dayPlan.weather.temperature}</p>
                            <p><strong>适宜性:</strong> ${dayPlan.weather.suitability}</p>
                        </div>
                    `;
                }
                
                // 建议
                if (dayPlan.recommendations && dayPlan.recommendations.length > 0) {
                    html += `
                        <div class="recommendations">
                            <h6>当日建议</h6>
                            <ul>
                                ${dayPlan.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                            </ul>
                        </div>
                    `;
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
        
        // 时间统计信息
        if (planData.time_analysis) {
            html += `
                <div class="result-section">
                    <h4>时间分析</h4>
                    <div class="info-grid">
                        <div class="info-item">
                            <strong>总游览时间</strong>
                            ${planData.time_analysis.total_visit_hours}小时
                        </div>
                        <div class="info-item">
                            <strong>总交通时间</strong>
                            ${planData.time_analysis.total_travel_hours}小时
                        </div>
                        <div class="info-item">
                            <strong>平均每日时长</strong>
                            ${planData.time_analysis.average_hours_per_day}小时
                        </div>
                        <div class="info-item">
                            <strong>行程效率</strong>
                            ${planData.time_analysis.efficiency_score}%
                        </div>
                    </div>
                    ${planData.time_analysis.recommendations && planData.time_analysis.recommendations.length > 0 ? `
                        <div class="recommendations">
                            <h6>时间优化建议</h6>
                            <ul>
                                ${planData.time_analysis.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            `;
        }
        
        // 建议和提示
        if (planData.recommendations) {
            html += `
                <div class="result-section">
                    <div class="recommendations-header">
                        <h4>智能旅游建议</h4>
                        <div class="recommendations-tabs">
                            <button class="tab-btn active" data-tab="tips">💡 实用提示</button>
                            <button class="tab-btn" data-tab="packing">🎒 打包清单</button>
                            <button class="tab-btn" data-tab="budget">💰 预算规划</button>
                            <button class="tab-btn" data-tab="safety">🛡️ 安全须知</button>
                        </div>
                    </div>
                    <div class="recommendations-content">
            `;
            
            // 实用提示标签页
            if (planData.recommendations.travel_tips && planData.recommendations.travel_tips.length > 0) {
                html += `
                    <div class="tab-content active" data-content="tips">
                        <div class="tips-section">
                            <h5>🎯 旅游提示</h5>
                            <ul>
                                ${planData.recommendations.travel_tips.map(tip => `<li>${tip}</li>`).join('')}
                            </ul>
                        </div>
                        ${this.generateAdditionalTips(planData)}
                    </div>
                `;
            }
            
            // 打包清单标签页
            if (planData.recommendations.packing_list && planData.recommendations.packing_list.length > 0) {
                html += `
                    <div class="tab-content" data-content="packing">
                        <div class="packing-section">
                            <h5>🧳 必备物品</h5>
                            <div class="packing-categories">
                                ${this.generatePackingCategories(planData.recommendations.packing_list)}
                            </div>
                        </div>
                        ${this.generateWeatherBasedPacking(planData)}
                    </div>
                `;
            }
            
            // 预算规划标签页
            if (planData.recommendations.budget_estimate) {
                const budget = planData.recommendations.budget_estimate;
                html += `
                    <div class="tab-content" data-content="budget">
                        <div class="budget-section">
                            <h5>💰 预算估算</h5>
                            <div class="budget-overview">
                                ${budget.total ? `<div class="budget-item total"><span>总预算</span><strong>${budget.total}</strong></div>` : ''}
                                ${budget.per_person ? `<div class="budget-item per-person"><span>人均费用</span><strong>${budget.per_person}</strong></div>` : ''}
                            </div>
                            ${budget.breakdown ? `
                                <div class="budget-breakdown">
                                    <h6>📊 费用明细</h6>
                                    <div class="breakdown-grid">
                                        ${Object.entries(budget.breakdown).map(([key, value]) => 
                                            `<div class="breakdown-item">
                                                <span class="category">${key}</span>
                                                <span class="amount">${value}</span>
                                            </div>`
                                        ).join('')}
                                    </div>
                                </div>
                            ` : ''}
                            ${budget.description ? `<div class="budget-note"><em>💡 ${budget.description}</em></div>` : ''}
                            ${this.generateBudgetTips(planData)}
                        </div>
                    </div>
                `;
            }
            
            // 安全须知标签页
            html += `
                <div class="tab-content" data-content="safety">
                    <div class="safety-section">
                        <h5>🛡️ 安全须知</h5>
                        ${this.generateSafetyTips(planData)}
                    </div>
                </div>
            `;
            
            html += `
                    </div>
                </div>
            `;
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
                tips.push('🛏️ 长途旅行建议选择舒适的住宿，保证充足睡眠');
            }
            if (days <= 2) {
                tips.push('⏰ 行程紧凑，建议提前规划路线，合理安排时间');
                tips.push('🚗 短途旅行可考虑包车或租车，提高出行效率');
            }
            if (days >= 3 && days <= 4) {
                tips.push('📋 中等行程建议预留半天自由活动时间，体验当地生活');
            }
        }
        
        // 基于季节和天气的建议
        if (planData.weather_info) {
            const avgTemp = planData.weather_info.average_temperature;
            const weatherCondition = planData.weather_info.condition || '';
            
            if (avgTemp < 10) {
                tips.push('🧥 气温较低，注意保暖，建议携带厚外套和暖宝宝');
                tips.push('🧤 低温天气建议准备手套、围巾等保暖用品');
            } else if (avgTemp > 30) {
                tips.push('☀️ 气温较高，注意防暑降温，多补充水分');
                tips.push('🧴 高温天气建议携带防晒霜、遮阳帽等防晒用品');
            } else if (avgTemp >= 15 && avgTemp <= 25) {
                tips.push('🌤️ 气温适宜，是户外活动的好时机');
            }
            
            if (weatherCondition.includes('雨')) {
                tips.push('☔ 预报有雨，建议携带雨具，选择室内备选活动');
            }
        }
        
        // 基于非遗项目类型的专业建议
        if (planData.itinerary) {
            const allItems = planData.itinerary.flatMap(day => day.items || []);
            const itemTypes = allItems.map(item => item.type || '').join(' ');
            
            if (itemTypes.includes('手工艺') || itemTypes.includes('工艺')) {
                tips.push('🎨 参与手工艺体验时，建议穿着不怕弄脏的衣物');
                tips.push('📸 手工艺制作过程值得记录，可拍摄制作步骤');
            }
            
            if (itemTypes.includes('表演') || itemTypes.includes('戏曲')) {
                tips.push('🎭 观看表演时，请遵守现场秩序，关闭手机闪光灯');
                tips.push('📱 部分表演可能禁止拍摄，请注意现场提示');
            }
        }
        
        if (tips.length > 0) {
            return `
                <div class="tips-section">
                    <h5>💡 智能建议</h5>
                    <ul>
                        ${tips.map(tip => `<li>${tip}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        return '';
    }
    
    /**
     * 生成打包清单分类
     * @param {Array} packingList 打包清单
     * @returns {string} HTML字符串
     */
    generatePackingCategories(packingList) {
        // 简单分类处理，实际项目中可能需要更复杂的分类逻辑
        const categories = {
            '衣物': [],
            '个人用品': [],
            '电子设备': [],
            '其他': []
        };
        
        packingList.forEach(item => {
            if (item.includes('衣') || item.includes('裤') || item.includes('鞋') || item.includes('帽')) {
                categories['衣物'].push(item);
            } else if (item.includes('手机') || item.includes('充电器') || item.includes('相机') || item.includes('电脑')) {
                categories['电子设备'].push(item);
            } else if (item.includes('牙刷') || item.includes('牙膏') || item.includes('毛巾') || item.includes('洗发水')) {
                categories['个人用品'].push(item);
            } else {
                categories['其他'].push(item);
            }
        });
        
        let html = '';
        
        Object.entries(categories).forEach(([category, items]) => {
            if (items.length > 0) {
                html += `
                    <div class="packing-category">
                        <h6>${category}</h6>
                        <ul>
                            ${items.map(item => `<li>${item}</li>`).join('')}
                        </ul>
                    </div>
                `;
            }
        });
        
        return html;
    }
    
    /**
     * 生成基于天气的打包建议
     * @param {Object} planData 规划数据
     * @returns {string} HTML字符串
     */
    generateWeatherBasedPacking(planData) {
        if (!planData.weather_info) {
            return '';
        }
        
        const weather = planData.weather_info;
        const avgTemp = weather.average_temperature;
        const condition = weather.condition || '';
        
        let tips = [];
        
        if (avgTemp < 10) {
            tips.push('🧥 厚外套、毛衣、保暖内衣');
            tips.push('🧤 手套、围巾、帽子');
            tips.push('🧦 厚袜子');
        } else if (avgTemp > 30) {
            tips.push('👕 轻薄透气的衣物');
            tips.push('🕶️ 太阳镜、遮阳帽');
            tips.push('🧴 防晒霜、防晒喷雾');
        } else {
            tips.push('👖 舒适的长袖和短袖衣物');
            tips.push('🧥 轻薄外套（早晚温差大）');
        }
        
        if (condition.includes('雨')) {
            tips.push('☂️ 雨伞或雨衣');
            tips.push('👟 防水鞋');
        }
        
        if (tips.length > 0) {
            return `
                <div class="weather-packing">
                    <h5>🌤️ 天气适配建议</h5>
                    <ul>
                        ${tips.map(tip => `<li>${tip}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        return '';
    }
    
    /**
     * 生成预算建议
     * @param {Object} planData 规划数据
     * @returns {string} HTML字符串
     */
    generateBudgetTips(planData) {
        const tips = [];
        
        // 基于行程天数的预算建议
        if (planData.itinerary && planData.itinerary.length > 0) {
            const days = planData.itinerary.length;
            if (days >= 7) {
                tips.push('💸 长途旅行建议提前预订住宿和交通，可节省费用');
                tips.push('🏨 考虑选择含早餐的住宿，可减少餐饮支出');
            }
            if (days <= 3) {
                tips.push('🎫 短途旅行可考虑购买景点套票，更划算');
                tips.push('🍽️ 尝试当地特色小吃，性价比高且能体验当地文化');
            }
        }
        
        // 基于出行方式的预算建议
        if (planData.basic_info && planData.basic_info.travel_mode) {
            const travelMode = planData.basic_info.travel_mode;
            if (travelMode === '自驾') {
                tips.push('⛽ 提前查询加油站位置和油价，规划加油点');
                tips.push('🅿️ 了解景点停车费用，考虑购买停车优惠');
            } else if (travelMode === '公共交通') {
                tips.push('🚌 考虑购买当地交通卡，享受优惠折扣');
                tips.push('📱 下载当地交通APP，方便查询路线和票价');
            }
        }
        
        if (tips.length > 0) {
            return `
                <div class="budget-tips">
                    <h6>💡 预算建议</h6>
                    <ul>
                        ${tips.map(tip => `<li>${tip}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        return '';
    }
    
    /**
     * 生成安全须知
     * @param {Object} planData 规划数据
     * @returns {string} HTML字符串
     */
    generateSafetyTips(planData) {
        const baseTips = [
            '🔒 保管好个人财物，贵重物品随身携带',
            '📱 保持手机电量充足，携带充电宝',
            '📞 保存当地紧急联系方式',
            '🗺️ 提前下载离线地图，避免迷路',
            '🚨 遇到紧急情况，及时报警或寻求帮助',
            '🍽️ 注意饮食卫生，选择正规餐厅',
            '💧 随身携带饮用水，保持水分补充',
            '🌞 注意防晒，避免长时间暴露在阳光下'
        ];
        
        let additionalTips = [];
        
        // 基于天气的安全建议
        if (planData.weather_info) {
            const condition = planData.weather_info.condition || '';
            if (condition.includes('雨')) {
                additionalTips.push('☔ 雨天路滑，注意行走安全');
                additionalTips.push('⚡ 雷雨天气，避免在户外活动');
            }
        }
        
        // 基于地形的安全建议
        if (planData.itinerary) {
            const allItems = planData.itinerary.flatMap(day => day.items || []);
            const hasMountain = allItems.some(item => item.region.includes('山') || item.name.includes('山'));
            if (hasMountain) {
                additionalTips.push('⛰️ 山区游览注意防滑，穿舒适的登山鞋');
                additionalTips.push('🌲 遵守景区规定，不要进入未开发区域');
            }
        }
        
        const allTips = [...baseTips, ...additionalTips];
        
        return `
            <ul>
                ${allTips.map(tip => `<li>${tip}</li>`).join('')}
            </ul>
        `;
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