/**
 * 悬浮AI助手组件
 * 支持状态持久化、展开/收缩动画、放大功能
 */
class FloatingAIAssistant {
    constructor() {
        this.STORAGE_KEY = 'floating_ai_assistant_state';
        this.isOpen = false;
        this.isExpanded = false;
        this.isMinimized = false;
        this.conversationHistory = [];
        this.currentMessage = '';
        this.isStreaming = false;
        this.sessionId = null;
        this.pendingRender = false;
        
        this.init();
    }
    
    init() {
        this.loadState();
        this.createUI();
        this.bindEvents();
        this.restoreUI();
    }
    
    createUI() {
        if (document.getElementById('floating-ai-assistant')) return;
        
        const container = document.createElement('div');
        container.id = 'floating-ai-assistant';
        container.innerHTML = this.getHTML();
        document.body.appendChild(container);
        
        this.addStyles();
    }
    
    getHTML() {
        const lastMessage = this.getLastMessagePreview();
        
        return `
            <div id="ai-float-btn" class="ai-float-btn" title="AI助手">
                <div class="btn-icon">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="btn-pulse"></div>
                ${this.conversationHistory.length > 0 ? `
                    <div class="btn-badge">
                        <i class="fas fa-comment"></i>
                    </div>
                ` : ''}
            </div>
            
            <div id="ai-float-panel" class="ai-float-panel ${this.isExpanded ? 'expanded' : ''}">
                <div class="panel-header">
                    <div class="header-left">
                        <div class="ai-avatar">
                            <i class="fas fa-robot"></i>
                        </div>
                        <div class="ai-info">
                            <div class="ai-name">陕西非遗助手</div>
                            <div class="ai-status">
                                <span class="status-dot"></span>
                                <span class="status-text">在线</span>
                            </div>
                        </div>
                    </div>
                    <div class="header-controls">
                        <button class="ctrl-btn" id="ai-expand-btn" title="放大">
                            <i class="fas fa-expand"></i>
                        </button>
                        <button class="ctrl-btn" id="ai-minimize-btn" title="最小化">
                            <i class="fas fa-minus"></i>
                        </button>
                        <button class="ctrl-btn close-btn" id="ai-close-btn" title="关闭">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
                
                <div class="panel-body">
                    <div class="chat-container" id="ai-chat-container">
                        ${this.renderConversationHistory()}
                    </div>
                    
                    <div class="typing-indicator" id="ai-typing-indicator" style="display: none;">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <span class="typing-text">正在思考...</span>
                    </div>
                </div>
                
                <div class="panel-footer">
                    <div class="input-wrapper">
                        <input type="text" id="ai-input" class="ai-input" placeholder="请输入您的问题..." autocomplete="off">
                        <button class="send-btn" id="ai-send-btn" type="button">
                            <i class="fas fa-paper-plane"></i>
                        </button>
                    </div>
                    <div class="quick-actions">
                        <button class="quick-btn" data-msg="推荐一条非遗旅游路线">推荐路线</button>
                        <button class="quick-btn" data-msg="查询天气">查天气</button>
                        <button class="quick-btn" data-msg="介绍陕西非遗">了解非遗</button>
                    </div>
                </div>
            </div>
            
            <div id="ai-minibar" class="ai-minibar" style="display: none;">
                <div class="minibar-avatar">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="minibar-content">
                    <div class="minibar-title">AI助手</div>
                    <div class="minibar-preview">${lastMessage}</div>
                </div>
                <button class="minibar-restore" id="ai-restore-btn">
                    <i class="fas fa-chevron-up"></i>
                </button>
            </div>
        `;
    }
    
    renderConversationHistory() {
        if (this.conversationHistory.length === 0) {
            return `
                <div class="welcome-message">
                    <div class="welcome-icon">
                        <i class="fas fa-hands-helping"></i>
                    </div>
                    <h4>您好！我是陕西非遗助手</h4>
                    <p>我可以帮您：</p>
                    <ul>
                        <li><i class="fas fa-route"></i> 规划非遗旅游路线</li>
                        <li><i class="fas fa-cloud-sun"></i> 查询目的地天气</li>
                        <li><i class="fas fa-info-circle"></i> 介绍非遗项目</li>
                        <li><i class="fas fa-map-marker-alt"></i> 推荐周边景点</li>
                    </ul>
                </div>
            `;
        }
        
        return this.conversationHistory.map(msg => `
            <div class="chat-message ${msg.role === 'user' ? 'user-message' : 'ai-message'}">
                <div class="message-avatar">
                    <i class="fas fa-${msg.role === 'user' ? 'user' : 'robot'}"></i>
                </div>
                <div class="message-content">${this.renderMarkdown(msg.content)}</div>
            </div>
        `).join('');
    }
    
    getLastMessagePreview() {
        if (this.conversationHistory.length === 0) {
            return '点击开始对话';
        }
        const lastMsg = this.conversationHistory[this.conversationHistory.length - 1];
        const preview = lastMsg.content.substring(0, 30);
        return preview + (lastMsg.content.length > 30 ? '...' : '');
    }
    
    addStyles() {
        if (document.getElementById('floating-ai-styles')) return;
        
        const style = document.createElement('style');
        style.id = 'floating-ai-styles';
        style.textContent = `
            #floating-ai-assistant {
                position: fixed;
                z-index: 9999;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            }
            
            .ai-float-btn {
                position: fixed;
                bottom: 30px;
                right: 30px;
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: linear-gradient(135deg, #c13030 0%, #8c2e2e 100%);
                box-shadow: 0 4px 20px rgba(193, 48, 48, 0.4);
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                z-index: 10000;
            }
            
            .ai-float-btn:hover {
                transform: scale(1.1);
                box-shadow: 0 6px 30px rgba(193, 48, 48, 0.5);
            }
            
            .ai-float-btn .btn-icon {
                color: white;
                font-size: 24px;
                z-index: 1;
            }
            
            .ai-float-btn .btn-pulse {
                position: absolute;
                width: 100%;
                height: 100%;
                border-radius: 50%;
                background: rgba(193, 48, 48, 0.3);
                animation: pulse 2s infinite;
            }
            
            .ai-float-btn .btn-badge {
                position: absolute;
                top: -5px;
                right: -5px;
                width: 20px;
                height: 20px;
                background: #f8e3a3;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 10px;
                color: #8c2e2e;
            }
            
            @keyframes pulse {
                0% { transform: scale(1); opacity: 1; }
                50% { transform: scale(1.3); opacity: 0; }
                100% { transform: scale(1); opacity: 0; }
            }
            
            .ai-float-panel {
                position: fixed;
                bottom: 100px;
                right: 30px;
                width: 380px;
                height: 520px;
                background: white;
                border-radius: 16px;
                box-shadow: 0 10px 50px rgba(0, 0, 0, 0.15);
                display: none;
                flex-direction: column;
                overflow: hidden;
                transform-origin: bottom right;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            }
            
            .ai-float-panel.open {
                display: flex;
                animation: slideUp 0.3s ease;
            }
            
            .ai-float-panel.expanded {
                width: 500px;
                height: 700px;
                bottom: 20px;
                right: 20px;
            }
            
            @keyframes slideUp {
                from { opacity: 0; transform: translateY(20px) scale(0.95); }
                to { opacity: 1; transform: translateY(0) scale(1); }
            }
            
            .panel-header {
                padding: 16px 20px;
                background: linear-gradient(135deg, #c13030 0%, #8c2e2e 100%);
                color: white;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-shrink: 0;
            }
            
            .header-left {
                display: flex;
                align-items: center;
                gap: 12px;
            }
            
            .ai-avatar {
                width: 40px;
                height: 40px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
            }
            
            .ai-info .ai-name {
                font-weight: 600;
                font-size: 16px;
            }
            
            .ai-info .ai-status {
                display: flex;
                align-items: center;
                gap: 6px;
                font-size: 12px;
                opacity: 0.9;
            }
            
            .status-dot {
                width: 8px;
                height: 8px;
                background: #4ade80;
                border-radius: 50%;
                animation: blink 2s infinite;
            }
            
            @keyframes blink {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            
            .header-controls {
                display: flex;
                gap: 8px;
            }
            
            .ctrl-btn {
                width: 32px;
                height: 32px;
                border: none;
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border-radius: 8px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: background 0.2s;
            }
            
            .ctrl-btn:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            
            .ctrl-btn.close-btn:hover {
                background: rgba(220, 38, 38, 0.5);
            }
            
            .panel-body {
                flex: 1;
                overflow: hidden;
                display: flex;
                flex-direction: column;
                background: #f8f9fa;
            }
            
            .chat-container {
                flex: 1;
                overflow-y: auto;
                padding: 16px;
                scroll-behavior: smooth;
            }
            
            .chat-container::-webkit-scrollbar {
                width: 6px;
            }
            
            .chat-container::-webkit-scrollbar-thumb {
                background: #ddd;
                border-radius: 3px;
            }
            
            .welcome-message {
                text-align: center;
                padding: 30px 20px;
                color: #666;
            }
            
            .welcome-message .welcome-icon {
                width: 60px;
                height: 60px;
                margin: 0 auto 16px;
                background: linear-gradient(135deg, #f8e3a3 0%, #d4b96a 100%);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                color: #8c2e2e;
            }
            
            .welcome-message h4 {
                color: #333;
                margin-bottom: 12px;
            }
            
            .welcome-message ul {
                list-style: none;
                text-align: left;
                margin-top: 16px;
            }
            
            .welcome-message li {
                padding: 8px 0;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .welcome-message li i {
                color: #c13030;
                width: 20px;
            }
            
            .chat-message {
                display: flex;
                gap: 10px;
                margin-bottom: 16px;
                animation: fadeIn 0.3s ease;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .chat-message.user-message {
                flex-direction: row-reverse;
            }
            
            .message-avatar {
                width: 36px;
                height: 36px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
                font-size: 14px;
            }
            
            .ai-message .message-avatar {
                background: linear-gradient(135deg, #c13030 0%, #8c2e2e 100%);
                color: white;
            }
            
            .user-message .message-avatar {
                background: linear-gradient(135deg, #f8e3a3 0%, #d4b96a 100%);
                color: #8c2e2e;
            }
            
            .message-content {
                max-width: 80%;
                padding: 12px 16px;
                border-radius: 16px;
                line-height: 1.6;
                font-size: 14px;
            }
            
            .ai-message .message-content {
                background: white;
                border-bottom-left-radius: 4px;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            }
            
            .user-message .message-content {
                background: linear-gradient(135deg, #c13030 0%, #8c2e2e 100%);
                color: white;
                border-bottom-right-radius: 4px;
            }
            
            .typing-indicator {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 12px 16px;
                background: white;
                margin: 0 16px 16px;
                border-radius: 16px;
                border-bottom-left-radius: 4px;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                width: fit-content;
            }
            
            .typing-dot {
                width: 8px;
                height: 8px;
                background: #c13030;
                border-radius: 50%;
                animation: typingBounce 1.4s infinite ease-in-out;
            }
            
            .typing-dot:nth-child(1) { animation-delay: 0s; }
            .typing-dot:nth-child(2) { animation-delay: 0.2s; }
            .typing-dot:nth-child(3) { animation-delay: 0.4s; }
            
            @keyframes typingBounce {
                0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
                40% { transform: scale(1); opacity: 1; }
            }
            
            .typing-text {
                color: #888;
                font-size: 13px;
            }
            
            .panel-footer {
                padding: 12px 16px;
                background: white;
                border-top: 1px solid #eee;
                flex-shrink: 0;
            }
            
            .input-wrapper {
                display: flex;
                gap: 8px;
                background: #f5f5f5;
                border-radius: 24px;
                padding: 4px;
            }
            
            .ai-input {
                flex: 1;
                border: none;
                background: transparent;
                padding: 10px 16px;
                font-size: 14px;
                outline: none;
            }
            
            .send-btn {
                width: 40px;
                height: 40px;
                border: none;
                background: linear-gradient(135deg, #c13030 0%, #8c2e2e 100%);
                color: white;
                border-radius: 50%;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: transform 0.2s;
            }
            
            .send-btn:hover {
                transform: scale(1.05);
            }
            
            .send-btn:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            
            .quick-actions {
                display: flex;
                gap: 8px;
                margin-top: 10px;
                flex-wrap: wrap;
            }
            
            .quick-btn {
                padding: 6px 12px;
                border: 1px solid #e0e0e0;
                background: white;
                border-radius: 16px;
                font-size: 12px;
                color: #666;
                cursor: pointer;
                transition: all 0.2s;
            }
            
            .quick-btn:hover {
                border-color: #c13030;
                color: #c13030;
                background: #fff5f5;
            }
            
            .ai-minibar {
                position: fixed;
                bottom: 30px;
                right: 100px;
                background: white;
                border-radius: 30px;
                padding: 8px 16px;
                display: flex;
                align-items: center;
                gap: 12px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
                cursor: pointer;
                transition: all 0.3s;
                z-index: 9998;
            }
            
            .ai-minibar:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 25px rgba(0, 0, 0, 0.15);
            }
            
            .minibar-avatar {
                width: 36px;
                height: 36px;
                background: linear-gradient(135deg, #c13030 0%, #8c2e2e 100%);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 14px;
            }
            
            .minibar-content {
                max-width: 200px;
            }
            
            .minibar-title {
                font-weight: 600;
                font-size: 13px;
                color: #333;
            }
            
            .minibar-preview {
                font-size: 12px;
                color: #888;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            
            .minibar-restore {
                width: 28px;
                height: 28px;
                border: none;
                background: #f5f5f5;
                border-radius: 50%;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #666;
                transition: all 0.2s;
            }
            
            .minibar-restore:hover {
                background: #c13030;
                color: white;
            }
            
            .status-indicator {
                color: #888;
                font-style: italic;
                margin-bottom: 8px;
                padding: 8px 12px;
                background: #f8f9fa;
                border-radius: 8px;
                font-size: 13px;
            }
            
            .status-indicator i {
                margin-right: 6px;
            }
            
            @media (max-width: 480px) {
                .ai-float-panel {
                    width: 100%;
                    height: 100%;
                    bottom: 0;
                    right: 0;
                    border-radius: 0;
                }
                
                .ai-float-panel.expanded {
                    width: 100%;
                    height: 100%;
                }
                
                .ai-float-btn {
                    bottom: 20px;
                    right: 20px;
                    width: 50px;
                    height: 50px;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    bindEvents() {
        document.addEventListener('click', (e) => {
            if (e.target.closest('#ai-float-btn')) {
                this.togglePanel();
            } else if (e.target.closest('#ai-close-btn')) {
                this.closePanel();
            } else if (e.target.closest('#ai-minimize-btn')) {
                this.minimizePanel();
            } else if (e.target.closest('#ai-expand-btn')) {
                this.toggleExpand();
            } else if (e.target.closest('#ai-restore-btn') || e.target.closest('.ai-minibar')) {
                this.restorePanel();
            } else if (e.target.closest('#ai-send-btn')) {
                this.sendMessage();
            } else if (e.target.closest('.quick-btn')) {
                const btn = e.target.closest('.quick-btn');
                const msg = btn.dataset.msg;
                document.getElementById('ai-input').value = msg;
                this.sendMessage();
            }
        });
        
        document.addEventListener('keydown', (e) => {
            if (e.target.id === 'ai-input' && e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        window.addEventListener('beforeunload', () => {
            this.saveState();
        });
    }
    
    togglePanel() {
        const panel = document.getElementById('ai-float-panel');
        const btn = document.getElementById('ai-float-btn');
        
        if (this.isOpen) {
            this.closePanel();
        } else {
            panel.classList.add('open');
            btn.style.display = 'none';
            this.isOpen = true;
            this.scrollToBottom();
            document.getElementById('ai-input').focus();
        }
    }
    
    closePanel() {
        const panel = document.getElementById('ai-float-panel');
        const btn = document.getElementById('ai-float-btn');
        const minibar = document.getElementById('ai-minibar');
        
        panel.classList.remove('open');
        btn.style.display = 'flex';
        minibar.style.display = 'none';
        this.isOpen = false;
        this.isMinimized = false;
        this.saveState();
    }
    
    minimizePanel() {
        const panel = document.getElementById('ai-float-panel');
        const minibar = document.getElementById('ai-minibar');
        
        panel.classList.remove('open');
        minibar.style.display = 'flex';
        this.isMinimized = true;
        this.updateMinibarPreview();
    }
    
    restorePanel() {
        const panel = document.getElementById('ai-float-panel');
        const minibar = document.getElementById('ai-minibar');
        
        panel.classList.add('open');
        minibar.style.display = 'none';
        this.isMinimized = false;
        this.scrollToBottom();
    }
    
    toggleExpand() {
        const panel = document.getElementById('ai-float-panel');
        const expandBtn = document.getElementById('ai-expand-btn');
        
        this.isExpanded = !this.isExpanded;
        panel.classList.toggle('expanded', this.isExpanded);
        expandBtn.innerHTML = this.isExpanded 
            ? '<i class="fas fa-compress"></i>' 
            : '<i class="fas fa-expand"></i>';
        
        this.saveState();
    }
    
    async sendMessage() {
        const input = document.getElementById('ai-input');
        const sendBtn = document.getElementById('ai-send-btn');
        const message = input.value.trim();
        
        if (!message || this.isStreaming) return;
        
        input.value = '';
        this.addMessage('user', message);
        
        this.isStreaming = true;
        sendBtn.disabled = true;
        this.showTypingIndicator();
        
        try {
            const apiUrl = await this.getApiBaseUrl();
            const response = await fetch(`${apiUrl}/agent/chat-stream`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let fullMessage = '';
            let pendingRender = false;
            
            const messageId = this.createAIMessageElement();
            
            const renderMessage = () => {
                const safeMessage = this._fixIncompleteMarkdown(fullMessage);
                const html = this.renderMarkdown(safeMessage);
                document.getElementById(messageId).innerHTML = html;
                this.scrollToBottom();
                pendingRender = false;
            };
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop();
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        try {
                            const parsed = JSON.parse(data);
                            
                            if (parsed.error) {
                                this.hideTypingIndicator();
                                this.updateMessageContent(messageId, `错误: ${parsed.error}`);
                                return;
                            }
                            
                            if (parsed.status === 'thinking') {
                                this.updateTypingText(parsed.content || '正在思考...');
                            } else if (parsed.content) {
                                if (this.isTypingVisible()) {
                                    this.hideTypingIndicator();
                                }
                                fullMessage += parsed.content;
                                
                                if (!pendingRender) {
                                    pendingRender = true;
                                    requestAnimationFrame(renderMessage);
                                }
                            }
                        } catch (e) {
                            console.error('解析错误:', e);
                        }
                    }
                }
            }
            
            if (pendingRender) {
                renderMessage();
            }
            
            this.conversationHistory.push({ role: 'assistant', content: fullMessage });
            this.saveState();
            this.updateMinibarPreview();
            
        } catch (error) {
            console.error('发送失败:', error);
            this.hideTypingIndicator();
            this.addMessage('assistant', '抱歉，网络连接出现问题，请稍后重试。');
        } finally {
            this.isStreaming = false;
            sendBtn.disabled = false;
            input.focus();
        }
    }
    
    addMessage(role, content) {
        this.conversationHistory.push({ role, content, timestamp: Date.now() });
        this.saveState();
        
        const container = document.getElementById('ai-chat-container');
        const isUser = role === 'user';
        
        const html = `
            <div class="chat-message ${isUser ? 'user-message' : 'ai-message'}">
                <div class="message-avatar">
                    <i class="fas fa-${isUser ? 'user' : 'robot'}"></i>
                </div>
                <div class="message-content">${isUser ? content : this.renderMarkdown(content)}</div>
            </div>
        `;
        
        container.insertAdjacentHTML('beforeend', html);
        this.scrollToBottom();
        this.updateMinibarPreview();
    }
    
    createAIMessageElement() {
        const container = document.getElementById('ai-chat-container');
        const messageId = `msg-${Date.now()}`;
        
        const html = `
            <div class="chat-message ai-message">
                <div class="message-avatar">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="message-content" id="${messageId}"></div>
            </div>
        `;
        
        container.insertAdjacentHTML('beforeend', html);
        this.scrollToBottom();
        return messageId;
    }
    
    updateMessageContent(messageId, content) {
        const el = document.getElementById(messageId);
        if (el) {
            el.innerHTML = this.renderMarkdown(content);
        }
    }
    
    showTypingIndicator() {
        const indicator = document.getElementById('ai-typing-indicator');
        if (indicator) {
            indicator.style.display = 'flex';
            this.scrollToBottom();
        }
    }
    
    hideTypingIndicator() {
        const indicator = document.getElementById('ai-typing-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }
    
    isTypingVisible() {
        const indicator = document.getElementById('ai-typing-indicator');
        return indicator && indicator.style.display !== 'none';
    }
    
    updateTypingText(text) {
        const textEl = document.querySelector('.typing-text');
        if (textEl) {
            textEl.textContent = text;
        }
    }
    
    scrollToBottom() {
        const container = document.getElementById('ai-chat-container');
        if (container) {
            container.scrollTop = container.scrollHeight;
        }
    }
    
    updateMinibarPreview() {
        const preview = document.querySelector('.minibar-preview');
        if (preview) {
            preview.textContent = this.getLastMessagePreview();
        }
    }
    
    renderMarkdown(text) {
        if (!text) return '';
        
        if (typeof window.marked !== 'undefined' && window.marked.parse) {
            return window.marked.parse(text);
        }
        
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');
    }
    
    _fixIncompleteMarkdown(text) {
        if (!text) return '';
        
        let fixed = text;
        
        const boldCount = (fixed.match(/\*\*/g) || []).length;
        if (boldCount % 2 !== 0) {
            fixed += '**';
        }
        
        const codeBlockMatches = fixed.match(/```/g);
        if (codeBlockMatches && codeBlockMatches.length % 2 !== 0) {
            fixed += '\n```';
        }
        
        return fixed;
    }
    
    async getApiBaseUrl() {
        try {
            const response = await fetch('/api/agent/url');
            const data = await response.json();
            return data.url;
        } catch (error) {
            return '/api/agent';
        }
    }
    
    saveState() {
        const state = {
            isOpen: this.isOpen,
            isExpanded: this.isExpanded,
            isMinimized: this.isMinimized,
            conversationHistory: this.conversationHistory.slice(-50),
            sessionId: this.sessionId,
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
                this.conversationHistory = state.conversationHistory || [];
                this.sessionId = state.sessionId || `session_${Date.now()}`;
                this.isExpanded = state.isExpanded || false;
                
                const savedAt = state.savedAt || 0;
                const hoursSinceSaved = (Date.now() - savedAt) / (1000 * 60 * 60);
                if (hoursSinceSaved > 24) {
                    this.conversationHistory = [];
                    this.sessionId = `session_${Date.now()}`;
                }
            } else {
                this.sessionId = `session_${Date.now()}`;
            }
        } catch (e) {
            console.warn('加载状态失败:', e);
            this.sessionId = `session_${Date.now()}`;
        }
    }
    
    restoreUI() {
        if (this.conversationHistory.length > 0) {
            this.updateMinibarPreview();
        }
    }
    
    clearHistory() {
        this.conversationHistory = [];
        this.sessionId = `session_${Date.now()}`;
        this.saveState();
        
        const container = document.getElementById('ai-chat-container');
        if (container) {
            container.innerHTML = this.renderConversationHistory();
        }
    }
}

let floatingAIInstance = null;

function initFloatingAI() {
    if (!floatingAIInstance) {
        floatingAIInstance = new FloatingAIAssistant();
    }
    return floatingAIInstance;
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initFloatingAI);
} else {
    initFloatingAI();
}

window.FloatingAIAssistant = FloatingAIAssistant;
