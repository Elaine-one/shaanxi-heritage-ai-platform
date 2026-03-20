/**
 * 旅游规划编辑器 - AI对话式编辑功能
 * 模块化重构版本
 * 
 * 模块结构:
 * - plan-editor.css: 所有样式
 * - plan-editor-ui.js: UI创建、拖拽、状态切换
 * - plan-editor-chat.js: 消息发送、渲染、Markdown
 * - plan-editor-api.js: API通信、会话管理
 * - plan-editor.js: 主入口、状态管理
 */

class PlanEditor {
    constructor() {
        this.STORAGE_KEY = 'plan_editor_state';
        this.STORAGE_VERSION = '2.1';
        this.sessionId = null;
        this.currentPlan = null;
        this.chatHistory = [];
        this.isEditing = false;
        this.isSending = false;
        this.renderThrottleTimer = null;
        this.isMinimized = false;
        this.isHalfExpanded = false;
        this.isMenuOpen = false;
        this.hintTimer = null;
        this.currentHintIndex = 0;
        this.hints = [
            { icon: 'fa-comment-dots', text: '点击继续规划您的旅行' },
            { icon: 'fa-lightbulb', text: '需要调整行程？随时告诉我' },
            { icon: 'fa-route', text: '点击查看智能规划建议' },
            { icon: 'fa-star', text: '有问题？让我来帮您' },
            { icon: 'fa-magic', text: '一键生成个性化路线' }
        ];
        
        this.init();
    }

    init() {
        try {
            this.loadState();
            
            this.ui = new PlanEditorUI(this);
            this.chat = new PlanEditorChat(this);
            this.api = new PlanEditorAPI(this);
            
            this.ui.bindEvents();
            
            window.addEventListener('beforeunload', () => {
                this.saveState();
            });
            
            if (this.chatHistory.length > 0 || this.isMinimized || this.isHalfExpanded || this.isEditing) {
                this.ui.createEditorUI();
                this.ui.restoreFromSavedState();
                
                this.api.checkPendingExport();
            }
            console.log('PlanEditor 初始化成功');
        } catch (e) {
            console.error('PlanEditor 初始化失败:', e);
            this.chatHistory = [];
            this.isMinimized = false;
            this.isHalfExpanded = false;
            this.isEditing = false;
            localStorage.removeItem(this.STORAGE_KEY);
        }
    }
    
    saveState() {
        const state = {
            version: this.STORAGE_VERSION,
            sessionId: this.sessionId,
            currentPlan: this.currentPlan,
            chatHistory: this.chatHistory.slice(-50),
            isMinimized: this.isMinimized,
            isHalfExpanded: this.isHalfExpanded,
            isEditing: this.isEditing,
            savedAt: Date.now()
        };
        
        try {
            localStorage.setItem(this.STORAGE_KEY, JSON.stringify(state));
        } catch (e) {
            console.warn('保存状态失败:', e);
        }
    }
    
    loadState() {
        try {
            const saved = localStorage.getItem(this.STORAGE_KEY);
            if (saved) {
                const state = JSON.parse(saved);
                
                if (state.version !== this.STORAGE_VERSION) {
                    console.log('计划编辑器状态版本不匹配，清除旧数据');
                    localStorage.removeItem(this.STORAGE_KEY);
                    return;
                }
                
                const hoursSinceSaved = (Date.now() - (state.savedAt || 0)) / (1000 * 60 * 60);
                if (hoursSinceSaved > 24) {
                    localStorage.removeItem(this.STORAGE_KEY);
                    return;
                }
                
                this.sessionId = state.sessionId || null;
                this.currentPlan = state.currentPlan || null;
                this.chatHistory = state.chatHistory || [];
                this.isMinimized = state.isMinimized || false;
                this.isHalfExpanded = state.isHalfExpanded || false;
                this.isEditing = state.isEditing || false;
            }
        } catch (e) {
            console.warn('加载状态失败，清除损坏的数据:', e);
            localStorage.removeItem(this.STORAGE_KEY);
        }
    }

    startEditing(planData) {
        this.currentPlan = planData;
        this.isEditing = true;
        this.chatHistory = [];
        
        this.ui.createEditorUI();
        
        this.ui.showEditor();
        this.ui.enableApplyButton();
        
        const welcome = "您好！我是您的专属旅行规划师。\n\n如果您对当前的行程安排有任何调整想法（比如想更轻松一点、想增加某个景点、或者想调整预算），请直接告诉我，我会为您重新定制。";
        this.chat.addChatMessage('ai', welcome, true);
        
        this.api.initializeChatSession();
    }
}

try {
    window.planEditor = new PlanEditor();
    console.log('plan-editor.js 加载完成，window.planEditor 已初始化');
} catch (e) {
    console.error('plan-editor.js 初始化失败:', e);
    window.planEditor = null;
}

window.openPlanEditor = function(planData) {
    if (!window.planEditor) {
        console.error('PlanEditor 未初始化，尝试重新创建');
        try {
            window.planEditor = new PlanEditor();
        } catch (e) {
            console.error('重新创建 PlanEditor 失败:', e);
            alert('编辑器加载失败，请刷新页面重试');
            return;
        }
    }
    window.planEditor.startEditing(planData);
};
