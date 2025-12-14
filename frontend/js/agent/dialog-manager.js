/**
 * 对话框管理器模块
 * 负责规划配置对话框的创建和关闭
 */

class DialogManager {
    /**
     * 显示规划配置对话框
     * @returns {Promise<Object|null>} 配置对象或null（用户取消）
     */
    // 静态标志位，确保同一时间只能创建一个规划配置对话框
    static planningDialogOpen = false;
    
    static async showPlanningConfigDialog() {
        // 1. 首先检查是否已经存在对话框，如果存在则直接返回，避免重复创建
        if (DialogManager.planningDialogOpen) {
            console.warn('规划配置对话框已存在，避免重复创建');
            // 尝试找到并聚焦到现有对话框
            const existingDialog = document.querySelector('.modal-overlay');
            if (existingDialog) {
                existingDialog.style.zIndex = '1051'; // 确保在最上层
            }
            return Promise.resolve(null);
        }
        
        // 2. 设置标志位，表示正在创建对话框
        DialogManager.planningDialogOpen = true;
        
        // 3. 删除所有现有对话框
        const existingDialogs = document.querySelectorAll('.modal-overlay');
        existingDialogs.forEach(dialog => {
            try {
                dialog.parentNode.removeChild(dialog);
            } catch (e) {
                console.warn('删除现有对话框时出错:', e);
            }
        });
        
        return new Promise((resolve) => {
            // 直接使用局部变量存储resolve函数，避免全局污染
            let dialogResolve = resolve;
            let dialogElement = null;
            
            // 4. 创建一个唯一的对话框ID，确保不会与其他对话框冲突
            const dialogId = 'planningConfigDialog_' + Date.now();
            
            // 5. 使用DOM操作创建对话框元素，确保完全控制生命周期
            const createDialog = () => {
                // 创建对话框容器
                const dialogContainer = document.createElement('div');
                dialogContainer.id = dialogId;
                dialogContainer.className = 'modal-overlay';
                
                // 创建对话框内容
                const contentHtml = `
                    <div class="modal-content medium">
                        <div class="modal-header">
                            <h3><i class="fas fa-map-marked-alt"></i> 旅游规划配置</h3>
                            <button class="modal-close">&times;</button>
                        </div>
                        <div class="modal-body">
                            <div class="config-intro">
                                <div class="intro-card">
                                    <i class="fas fa-info-circle"></i>
                                    <p>请填写以下信息，我们将为您量身定制专属的非遗文化旅游规划方案</p>
                                </div>
                            </div>
                            <form id="planningConfigForm">
                                <div class="form-group">
                                    <label for="travelDays"><i class="fas fa-calendar-alt"></i> 旅游天数:</label>
                                    <select id="travelDays">
                                        <option value="1">1天</option>
                                        <option value="2">2天</option>
                                        <option value="3" selected>3天</option>
                                        <option value="4">4天</option>
                                        <option value="5">5天</option>
                                        <option value="7">7天</option>
                                        <option value="10">10天</option>
                                        <option value="14">14天</option>
                                    </select>
                                </div>
                                
                                <div class="form-divider"></div>
                                
                                <div class="form-group">
                                    <label for="departureLocation"><i class="fas fa-map-marker-alt"></i> 出发地:</label>
                                    <input type="text" id="departureLocation" placeholder="请输入出发城市，如：西安市">
                                </div>
                                
                                <div class="form-group">
                                    <label for="travelMode"><i class="fas fa-car"></i> 出行方式:</label>
                                    <select id="travelMode">
                                        <option value="自驾" selected>🚗 自驾</option>
                                        <option value="公共交通">🚌 公共交通</option>
                                        <option value="跟团">👥 跟团</option>
                                        <option value="自由行">🎒 自由行</option>
                                    </select>
                                </div>
                                
                                <div class="form-divider"></div>
                                
                                <div class="form-group">
                                    <label for="budgetRange"><i class="fas fa-wallet"></i> 预算范围:</label>
                                    <select id="budgetRange">
                                        <option value="经济">💰 经济型 (500-1000元/天)</option>
                                        <option value="中等" selected>💳 中等 (1000-2000元/天)</option>
                                        <option value="高端">💎 高端 (2000-5000元/天)</option>
                                        <option value="豪华">👑 豪华 (5000元以上/天)</option>
                                    </select>
                                </div>
                                
                                <div class="form-group">
                                    <label for="groupSize"><i class="fas fa-users"></i> 团队人数:</label>
                                    <input type="number" id="groupSize" min="1" max="50" value="2">
                                </div>
                                
                                <div class="form-divider"></div>
                                
                                <div class="form-group">
                                    <label for="specialRequirements"><i class="fas fa-clipboard-list"></i> 特殊要求:</label>
                                    <textarea id="specialRequirements" placeholder="如：无障碍设施、素食需求、儿童友好、摄影爱好、文化深度游等" rows="4"></textarea>
                                </div>
                                
                                <div class="form-tips">
                                    <div class="tip-item">
                                        <i class="fas fa-lightbulb"></i>
                                        <span>建议选择3-7天的行程，能更好地体验非遗文化魅力</span>
                                    </div>
                                    <div class="tip-item">
                                        <i class="fas fa-clock"></i>
                                        <span>规划生成需要2-3分钟，请耐心等待</span>
                                    </div>
                                    <div class="tip-item">
                                        <i class="fas fa-star"></i>
                                        <span>我们会根据天气、交通等因素优化您的行程</span>
                                    </div>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" id="cancelBtn">取消</button>
                                <button type="button" class="btn btn-primary" id="startBtn">开始规划</button>
                            </div>
                    </div>
                `;
                
                dialogContainer.innerHTML = contentHtml;
                return dialogContainer;
            };
            
            // 4. 创建并显示对话框
            dialogElement = createDialog();
            document.body.appendChild(dialogElement);
            console.log('已创建新对话框，ID:', dialogId);
            
            // 5. 立即添加事件监听器，确保能捕获所有事件
            const modalContent = dialogElement.querySelector('.modal-content');
            const closeBtn = dialogElement.querySelector('.modal-close');
            const cancelBtn = dialogElement.querySelector('#cancelBtn');
            const startBtn = dialogElement.querySelector('#startBtn');
            
            // 6. 关闭对话框的通用函数
            const closeDialog = (value) => {
                console.log('closeDialog函数被调用，value:', value);
                
                try {
                    // 6.1 首先调用resolve函数，确保规划流程继续执行
                    if (dialogResolve) {
                        dialogResolve(value);
                        dialogResolve = null;
                        console.log('resolve函数已调用，返回值:', value);
                    } else {
                        console.warn('resolve函数已不存在');
                    }
                    
                    // 6.2 然后立即从DOM中删除对话框，不依赖任何条件
                    if (dialogElement && dialogElement.parentNode) {
                        dialogElement.parentNode.removeChild(dialogElement);
                        console.log('对话框已从DOM中删除');
                    } else {
                        console.warn('尝试删除对话框，但对话框已不存在');
                    }
                    
                    // 6.3 然后强制删除所有相关元素，确保没有残留
                    const remainingDialog = document.getElementById(dialogId);
                    if (remainingDialog) {
                        remainingDialog.parentNode.removeChild(remainingDialog);
                        console.log('已删除残留的对话框元素');
                    }
                    
                    // 6.4 清理所有引用
                    dialogElement = null;
                    window.planningConfigDialog = null;
                    console.log('已清理所有对话框引用');
                    
                    // 6.5 重置标志位，允许创建新对话框
                    DialogManager.planningDialogOpen = false;
                    console.log('已重置规划对话框标志位，允许创建新对话框');
                    
                    // 6.5 强制浏览器重排和重绘，确保对话框能立即从屏幕上消失
                    setTimeout(() => {
                        console.log('强制浏览器重排和重绘');
                        window.dispatchEvent(new Event('resize'));
                        // 额外添加一个布局刷新
                        document.body.offsetHeight; // 触发重排
                    }, 0);
                    
                } catch (error) {
                    console.error('closeDialog函数执行出错:', error);
                }
            };
            
            // 7. 表单提交处理函数
            const handleSubmit = () => {
                console.log('handleSubmit函数被调用');
                
                try {
                    // 从对话框中查找所有表单字段
                    const travelDaysElement = modalContent.querySelector('#travelDays');
                    const departureElement = modalContent.querySelector('#departureLocation');
                    const travelModeElement = modalContent.querySelector('#travelMode');
                    const budgetRangeElement = modalContent.querySelector('#budgetRange');
                    const groupSizeElement = modalContent.querySelector('#groupSize');
                    const specialRequirementsElement = modalContent.querySelector('#specialRequirements');
                    
                    // 安全获取表单字段值
                    const travelDays = travelDaysElement ? travelDaysElement.value : '';
                    const departureLocation = departureElement ? departureElement.value : '';
                    const travelMode = travelModeElement ? travelModeElement.value : '';
                    const budgetRange = budgetRangeElement ? budgetRangeElement.value : '';
                    const groupSize = groupSizeElement ? groupSizeElement.value : '';
                    const specialRequirements = specialRequirementsElement ? specialRequirementsElement.value : '';
                    
                    // 安全调用trim()方法，防止departureLocation为undefined
                    const departureLocationTrimmed = departureLocation ? departureLocation.trim() : '';
                    
                    // 检查必填字段
                    let isValid = true;
                    let errorMessage = '';
                    
                    if (!travelDays) {
                        isValid = false;
                        errorMessage = '请选择旅游天数';
                    } else if (!departureLocationTrimmed) {
                        isValid = false;
                        errorMessage = '请输入出发地';
                    } else if (!groupSize || isNaN(groupSize) || parseInt(groupSize) < 1 || parseInt(groupSize) > 50) {
                        isValid = false;
                        errorMessage = '请输入有效的团队人数（1-50人）';
                    }
                    
                    console.log('表单验证结果:', isValid, '错误信息:', errorMessage);
                    
                    if (isValid) {
                        const config = {
                            travelDays: parseInt(travelDays),
                            departureLocation: departureLocationTrimmed,
                            travelMode: travelMode,
                            budgetRange: budgetRange,
                            groupSize: parseInt(groupSize),
                            specialRequirements: specialRequirements ? specialRequirements.trim().split('\n').filter(req => req.trim()) : []
                        };
                        
                        console.log('表单验证通过，配置:', config);
                        
                        // 直接调用closeDialog函数，关闭对话框并返回配置
                        closeDialog(config);
                    } else {
                        // 显示错误信息
                        alert(errorMessage);
                    }
                } catch (error) {
                    console.error('handleSubmit函数执行出错:', error);
                    // 显示错误信息
                    alert('表单提交出错，请重试');
                }
            };
            
            // 8. 绑定事件监听器
            closeBtn.addEventListener('click', () => closeDialog(null));
            cancelBtn.addEventListener('click', () => closeDialog(null));
            startBtn.addEventListener('click', handleSubmit);
            
            // 9. 防止事件冒泡
            dialogElement.addEventListener('click', (e) => {
                e.stopPropagation();
            });
            
            // 10. 添加ESC键关闭对话框
            const handleEscKey = (e) => {
                if (e.key === 'Escape') {
                    closeDialog(null);
                    document.removeEventListener('keydown', handleEscKey);
                }
            };
            document.addEventListener('keydown', handleEscKey);
            
            // 11. 确保在对话框删除前清理事件监听器
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === 'childList') {
                        for (const removedNode of mutation.removedNodes) {
                            if (removedNode === dialogElement) {
                                document.removeEventListener('keydown', handleEscKey);
                                observer.disconnect();
                                console.log('对话框已被移除，事件监听器已清理');
                            }
                        }
                    }
                });
            });
            
            observer.observe(document.body, { childList: true });
        });
    }
}

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DialogManager;
} else if (typeof window !== 'undefined') {
    window.DialogManager = DialogManager;
}