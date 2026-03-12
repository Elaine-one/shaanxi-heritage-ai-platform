/**
 * 旅游规划编辑器 - AI对话式编辑功能
 * 优化：AI打字时自动跟随滚动、丝滑缩放动画、Markdown实时渲染、对话历史透传
 */

class PlanEditor {
    constructor() {
        this.sessionId = null;
        this.currentPlan = null;
        this.chatHistory = [];
        this.isEditing = false;
        this.eventsBound = false;
        this.isSending = false;
        this.renderThrottleTimer = null;
        this.isMinimized = false;
        this.apiUrls = {}; // API URL缓存
        this.init();
    }

    async getApiBaseUrl(apiType = 'agent') {
        // 检查缓存
        if (this.apiUrls[apiType]) {
            return this.apiUrls[apiType];
        }
        
        // 获取 API 服务地址
        const apiUrl = `/api/agent/api/${apiType}`;
        console.log(`使用代理API URL (${apiType}):`, apiUrl);
        this.apiUrls[apiType] = apiUrl;
        return apiUrl;
    }

    init() {
        this.bindEvents();
    }

    createEditorUI() {
        if (document.getElementById('plan-editor-modal')) return;
        this.addStyles();

        const editorHTML = `
            <div id="plan-editor-modal" class="plan-editor-modal">
                <div id="plan-editor-header" class="editor-header">
                    <div class="header-title"><i class="fas fa-robot me-2"></i>AI 智能规划师</div>
                    <div class="header-controls">
                        <button type="button" class="ctrl-btn" id="minimize-btn" title="最小化">−</button>
                        <button type="button" class="ctrl-btn" id="zoom-out-btn" title="缩小">-</button>
                        <button type="button" class="ctrl-btn" id="zoom-in-btn" title="放大">+</button>
                        <button type="button" class="close-btn" id="plan-editor-close" title="关闭">&times;</button>
                    </div>
                </div>
                <div class="editor-body">
                    <div class="chat-scroll-area">
                        <div id="chat-history" class="chat-container"></div>
                    </div>
                    <div class="input-area">
                        <div class="input-wrapper">
                            <input type="text" id="chat-input" class="chat-input" placeholder="请输入修改建议，如：'去掉爬山，换成博物馆'..." autocomplete="off">
                            <button class="send-btn" id="send-message-btn" type="button">发送 <i class="fas fa-paper-plane ms-1"></i></button>
                        </div>
                    </div>
                </div>
                <div class="editor-footer">
                    <button type="button" class="footer-btn btn-secondary" id="plan-editor-close-btn">关闭</button>
                    <button type="button" class="footer-btn btn-success" id="apply-changes-btn" disabled><i class="fas fa-check me-1"></i> 应用修改</button>
                </div>
            </div>
            <div id="plan-editor-minibar" class="plan-editor-minibar" style="display: none;">
                <div class="minibar-icon"><i class="fas fa-robot"></i></div>
                <div class="minibar-title">AI 智能规划师</div>
                <div class="minibar-controls">
                    <button type="button" class="minibar-btn" id="restore-btn" title="恢复">□</button>
                    <button type="button" class="minibar-btn close" id="minibar-close-btn" title="关闭">&times;</button>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', editorHTML);
        this.initDragAndDrop();
    }

    addStyles() {
        if (document.getElementById('plan-editor-inline-styles')) return;
        const style = document.createElement('style');
        style.id = 'plan-editor-inline-styles';
        style.textContent = `
            .plan-editor-modal {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                width: 800px;
                height: 650px;
                max-width: 95vw;
                max-height: 95vh;
                background: #fff;
                border-radius: 12px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.25);
                z-index: 10000;
                display: flex;
                flex-direction: column;
                overflow: hidden;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
                /* 关键：添加过渡效果实现丝滑缩放 */
                transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1), height 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            }

            .editor-header {
                padding: 15px 20px;
                background: linear-gradient(135deg, #dc3545, #c82333);
                color: white;
                display: flex;
                justify-content: space-between;
                align-items: center;
                cursor: move;
                flex-shrink: 0;
            }

            .header-controls { display: flex; gap: 8px; align-items: center; }
            .ctrl-btn {
                background: rgba(255,255,255,0.2); border: none; color: white;
                width: 28px; height: 28px; border-radius: 4px; cursor: pointer;
                display: flex; align-items: center; justify-content: center;
                font-size: 16px; transition: background 0.2s;
            }
            .ctrl-btn:hover { background: rgba(255,255,255,0.3); }
            .close-btn { background: none; border: none; color: white; font-size: 24px; cursor: pointer; margin-left: 10px; }

            .editor-body { flex: 1; display: flex; flex-direction: column; overflow: hidden; background-color: #f8f9fa; }
            
            /* 聊天区域 */
            .chat-scroll-area {
                flex: 1;
                overflow-y: auto;
                padding: 20px;
                scroll-behavior: smooth; /* 平滑滚动 */
            }

            .input-area { padding: 15px 20px; background: white; border-top: 1px solid #eee; flex-shrink: 0; }
            .input-wrapper { display: flex; box-shadow: 0 2px 10px rgba(0,0,0,0.05); border-radius: 25px; overflow: hidden; border: 1px solid #ddd; }
            .chat-input { flex: 1; border: none; padding: 12px 20px; outline: none; font-size: 15px; }
            
            .send-btn {
                border: none; background: linear-gradient(135deg, #007bff, #0056b3);
                color: white; padding: 0 25px; font-weight: 600; cursor: pointer;
                display: flex; align-items: center; justify-content: center;
                transition: opacity 0.2s;
            }
            .send-btn:hover { opacity: 0.9; }

            .editor-footer {
                padding: 12px 20px; background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 50%, #ffffff 100%);
                display: flex; justify-content: flex-end; gap: 10px; flex-shrink: 0;
            }
            .footer-btn {
                padding: 8px 20px; border-radius: 20px; border: none; cursor: pointer;
                font-weight: 500; display: flex; align-items: center; justify-content: center;
                transition: all 0.3s ease;
            }
            .footer-btn:active { transform: scale(0.98); }
            .footer-btn.btn-secondary { 
                background: linear-gradient(135deg, #7A8A9A 0%, #5A6A7A 100%); 
                color: white; 
                box-shadow: 0 2px 8px rgba(122, 138, 154, 0.3);
            }
            .footer-btn.btn-secondary:hover { 
                background: linear-gradient(135deg, #6A7A8A 0%, #4A5A6A 100%);
                transform: translateY(-1px);
            }
            .footer-btn.btn-success { 
                background: linear-gradient(135deg, #5AAC7F 0%, #3D8B6A 100%); 
                color: white;
                box-shadow: 0 2px 8px rgba(90, 172, 127, 0.3);
            }
            .footer-btn.btn-success:hover { 
                background: linear-gradient(135deg, #4A9A6A 0%, #2D7A5A 100%);
                transform: translateY(-1px);
            }
            .footer-btn.btn-success:disabled { background: #ccc; cursor: not-allowed; opacity: 0.7; transform: none; }

            .chat-message { margin-bottom: 15px; display: flex; align-items: flex-start; animation: fadeIn 0.3s ease; }
            .chat-message.user-message { flex-direction: row-reverse; }
            
            .message-avatar {
                width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
                color: white; font-size: 18px; flex-shrink: 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .ai-message .message-avatar { background: linear-gradient(135deg, #6c757d, #495057); margin-right: 12px; }
            .user-message .message-avatar { background: linear-gradient(135deg, #007bff, #0056b3); margin-left: 12px; }

            .message-content {
                max-width: 80%; padding: 12px 16px; border-radius: 12px; line-height: 1.6;
                font-size: 15px; word-wrap: break-word; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            }
            .ai-message .message-content { background: white; border-top-left-radius: 2px; }
            .user-message .message-content { background: linear-gradient(135deg, #007bff, #0056b3); color: white; border-top-right-radius: 2px; }

            .message-content p { margin: 0 0 8px 0; }
            .message-content p:last-child { margin-bottom: 0; }
            .message-content h3, .message-content h4 { margin: 10px 0 5px; font-weight: bold; }
            .message-content ul { margin: 5px 0 10px 20px; padding: 0; }
            
            .export-options-container button { width: 100%; padding: 10px; border-radius: 8px; margin-top: 5px; }

            @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
            @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
            .typing-cursor { display: inline-block; width: 2px; height: 1em; background: currentColor; margin-left: 2px; animation: blink 1s infinite; vertical-align: middle; }
            
            /* 最小化栏样式 */
            .plan-editor-minibar {
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: linear-gradient(135deg, #C1302E 0%, #8B0000 100%);
                color: white;
                padding: 12px 20px;
                border-radius: 30px;
                display: flex;
                align-items: center;
                gap: 12px;
                box-shadow: 0 4px 20px rgba(193, 48, 46, 0.4);
                z-index: 10001;
                cursor: pointer;
                transition: all 0.3s ease;
                animation: slideInRight 0.3s ease;
            }
            .plan-editor-minibar:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 25px rgba(193, 48, 46, 0.5);
            }
            .minibar-icon {
                width: 36px;
                height: 36px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
            }
            .minibar-title {
                font-weight: 600;
                font-size: 14px;
            }
            .minibar-controls {
                display: flex;
                gap: 8px;
            }
            .minibar-btn {
                background: rgba(255, 255, 255, 0.2);
                border: none;
                color: white;
                width: 28px;
                height: 28px;
                border-radius: 50%;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 14px;
                transition: background 0.2s;
            }
            .minibar-btn:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            .minibar-btn.close:hover {
                background: rgba(255, 0, 0, 0.5);
            }
            @keyframes slideInRight {
                from { opacity: 0; transform: translateX(100px); }
                to { opacity: 1; transform: translateX(0); }
            }
        `;
        document.head.appendChild(style);
    }

    bindEvents() {
        if (this.eventsBound) return;
        this.eventsBound = true;
        
        document.addEventListener('click', (e) => {
            const target = e.target;
            if (target.closest('#send-message-btn')) this.sendMessage();
            if (target.closest('#apply-changes-btn')) this.applyChanges();
            if (target.closest('#plan-editor-close') || target.closest('#plan-editor-close-btn')) this.hideEditor();
            if (target.closest('#zoom-in-btn')) this.zoomIn();
            if (target.closest('#zoom-out-btn')) this.zoomOut();
            if (target.closest('#minimize-btn')) this.minimize();
            if (target.closest('#restore-btn')) this.restore();
            if (target.closest('#minibar-close-btn')) this.hideEditor();
            if (target.closest('.plan-editor-minibar') && !target.closest('button')) this.restore();
        });

        document.addEventListener('keydown', (e) => {
            if (e.target.id === 'chat-input' && e.key === 'Enter') {
                e.preventDefault(); // 防止默认行为，确保立即响应
                this.sendMessage();
            }
            if (e.key === 'Escape') {
                const modal = document.getElementById('plan-editor-modal');
                if (modal && modal.style.display !== 'none') this.hideEditor();
            }
        });
    }

    startEditing(planData) {
        this.currentPlan = planData;
        this.isEditing = true;
        this.chatHistory = [];
        
        // 确保编辑器UI已创建
        this.createEditorUI();
        
        // 清空之前的对话记录UI
        const chatContainer = document.getElementById('chat-history');
        if (chatContainer) {
            chatContainer.innerHTML = '';
        }
        
        this.showEditor();
        this.enableApplyButton(); 
        
        const welcome = "您好！我是您的专属旅行规划师。\n\n如果您对当前的行程安排有任何调整想法（比如想更轻松一点、想增加某个景点、或者想调整预算），请直接告诉我，我会为您重新定制。";
        this.addChatMessage('ai', welcome, true);
        
        this.initializeChatSession();
    }

    showEditor() {
        this.createEditorUI();
        const modal = document.getElementById('plan-editor-modal');
        const minibar = document.getElementById('plan-editor-minibar');
        modal.style.display = 'flex';
        if (minibar) minibar.style.display = 'none';
        this.isMinimized = false;
        // 确保显示时触发一次布局计算，避免动画异常
        requestAnimationFrame(() => {
            modal.style.opacity = '1';
        });
        setTimeout(() => document.getElementById('chat-input').focus(), 100);
    }
    
    hideEditor() {
        const modal = document.getElementById('plan-editor-modal');
        const minibar = document.getElementById('plan-editor-minibar');
        if (modal) modal.style.display = 'none';
        if (minibar) minibar.style.display = 'none';
        this.isMinimized = false;
    }

    /**
     * 丝滑放大
     * 利用 CSS transition 实现动画
     */
    zoomIn() {
        const modal = document.getElementById('plan-editor-modal');
        if (modal) {
            // 限制最大尺寸
            const maxWidth = Math.min(1000, window.innerWidth * 0.95);
            const maxHeight = Math.min(800, window.innerHeight * 0.95);
            modal.style.width = `${maxWidth}px`;
            modal.style.height = `${maxHeight}px`;
        }
    }
    
    /**
     * 丝滑缩小
     */
    zoomOut() {
        const modal = document.getElementById('plan-editor-modal');
        if (modal) {
            modal.style.width = '800px';
            modal.style.height = '650px';
        }
    }
    
    /**
     * 最小化到右下角
     */
    minimize() {
        const modal = document.getElementById('plan-editor-modal');
        const minibar = document.getElementById('plan-editor-minibar');
        if (modal && minibar) {
            modal.style.display = 'none';
            minibar.style.display = 'flex';
            this.isMinimized = true;
        }
    }
    
    /**
     * 从最小化恢复
     */
    restore() {
        const modal = document.getElementById('plan-editor-modal');
        const minibar = document.getElementById('plan-editor-minibar');
        if (modal && minibar) {
            modal.style.display = 'flex';
            minibar.style.display = 'none';
            this.isMinimized = false;
            // 恢复后聚焦输入框
            setTimeout(() => {
                const input = document.getElementById('chat-input');
                if (input) input.focus();
            }, 100);
        }
    }

    initDragAndDrop() {
        const modal = document.getElementById('plan-editor-modal');
        const header = document.getElementById('plan-editor-header');
        let isDragging = false, startX, startY, initialLeft, initialTop;
        
        header.addEventListener('mousedown', (e) => {
            if(e.target.closest('button')) return; // 防止点击按钮触发拖拽
            isDragging = true;
            startX = e.clientX;
            startY = e.clientY;
            
            // 获取计算后的样式值
            const style = window.getComputedStyle(modal);
            const rect = modal.getBoundingClientRect();
            
            // 移除 transform，改为绝对定位，防止拖拽时的计算冲突
            modal.style.transform = 'none';
            modal.style.left = rect.left + 'px';
            modal.style.top = rect.top + 'px';
            
            initialLeft = rect.left;
            initialTop = rect.top;
            
            // 拖拽时暂时禁用过渡动画，防止延迟感
            modal.style.transition = 'none';
        });
        
        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            const dx = e.clientX - startX;
            const dy = e.clientY - startY;
            modal.style.left = `${initialLeft + dx}px`;
            modal.style.top = `${initialTop + dy}px`;
        });
        
        document.addEventListener('mouseup', () => {
            if (isDragging) {
                isDragging = false;
                // 拖拽结束后恢复过渡动画
                modal.style.transition = 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1), height 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
            }
        });
    }

    async sendMessage() {
        if (this.isSending) return;

        const input = document.getElementById('chat-input');
        const sendBtn = document.getElementById('send-message-btn');
        const message = input.value.trim();
        
        if (!message) return;
        
        input.value = '';
        this.addChatMessage('user', message, false);
        
        this.isSending = true;
        sendBtn.disabled = true;
        const originalBtnText = sendBtn.innerHTML;
        sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        
        // 显示"思考中"状态
        const loadingId = this.showLoading();
        
        try {
            if (!this.sessionId) await this.initializeChatSession();

            const apiUrl = await this.getApiBaseUrl();
            
            // 使用流式接口
            const response = await fetch(`${apiUrl}/chat-stream`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ 
                    message: message,
                    session_id: this.sessionId 
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            // 创建消息容器
            const messageId = `msg-${Date.now()}`;
            const chatHistory = document.getElementById('chat-history');
            const html = `
                <div class="chat-message ai-message">
                    <div class="message-avatar"><i class="fas fa-robot"></i></div>
                    <div class="message-content" id="${messageId}"></div>
                </div>
            `;
            chatHistory.insertAdjacentHTML('beforeend', html);

            // 移除"思考中"状态（因为已经开始接收数据）
            this.hideLoading(loadingId);

            // 读取流式响应
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let fullMessage = '';
            let isDone = false;
            let pendingRender = false;

            const renderMessage = () => {
                let html;
                try {
                    if (typeof window.marked !== 'undefined' && window.marked.parse) {
                        html = window.marked.parse(fullMessage);
                    } else if (typeof window.markdownit !== 'undefined') {
                        const md = window.markdownit();
                        html = md.render(fullMessage);
                    } else {
                        html = fullMessage.replace(/\n/g, '<br>');
                    }
                } catch (e) {
                    console.warn('Markdown渲染失败:', e);
                    html = fullMessage.replace(/\n/g, '<br>');
                }
                document.getElementById(messageId).innerHTML = html;
                this.scrollToBottom();
                pendingRender = false;
            };

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                // 解码数据
                buffer += decoder.decode(value, { stream: true });

                // 处理 SSE 数据
                const lines = buffer.split('\n');
                buffer = lines.pop();

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        try {
                            const parsed = JSON.parse(data);
                            
                            if (parsed.error) {
                                this.addChatMessage('ai', `错误: ${parsed.error}`, false);
                                return;
                            }

                            if (parsed.content) {
                                fullMessage += parsed.content;
                                
                                if (!pendingRender) {
                                    pendingRender = true;
                                    requestAnimationFrame(() => {
                                        renderMessage();
                                    });
                                }
                            }
                            
                            if (parsed.done) {
                                isDone = true;
                            }
                            
                            if (parsed.metadata) {
                                // 处理元数据
                                if (parsed.metadata.changes_made && parsed.metadata.updated_plan) {
                                    this.currentPlan = parsed.metadata.updated_plan;
                                }
                            }
                        } catch (e) {
                            console.error('解析 SSE 数据失败:', e);
                        }
                    }
                }
            }

            if (pendingRender) {
                renderMessage();
            }

            console.log('流式输出完成，总长度:', fullMessage.length);

        } catch (error) {
            console.error('发送消息失败:', error);
            
            // 更详细的错误信息
            let errorMessage = '网络请求失败，请稍后重试。';
            
            if (error.name === 'TypeError') {
                errorMessage = '请求参数错误，请检查输入内容。';
            } else if (error.message && error.message.includes('Failed to fetch')) {
                errorMessage = '网络连接失败，请检查网络连接。';
            } else if (error.message && error.message.includes('HTTP')) {
                errorMessage = `服务器错误: ${error.message}`;
            } else if (error.message) {
                errorMessage = `请求失败: ${error.message}`;
            }
            
            this.addChatMessage('ai', errorMessage, false);
        } finally {
            this.isSending = false;
            sendBtn.disabled = false;
            sendBtn.innerHTML = originalBtnText;
            input.focus();
        }
    }

    async addChatMessage(type, content, typingEffect = false) {
        const chatHistory = document.getElementById('chat-history');
        if (!chatHistory) return;
        
        this.chatHistory.push({ type, content, timestamp: new Date() });

        const messageId = `msg-${Date.now()}`;
        const isUser = type === 'user';
        const icon = isUser ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
        
        // 如果是用户消息，直接显示；如果是AI消息且开启打字机，先显示空容器
        let displayContent = isUser ? content : this.renderMarkdown(content);
        // 如果开启打字机效果，初始内容为空（光标后续动态添加）
        if (typingEffect) displayContent = '';

        const html = `
            <div class="chat-message ${isUser ? 'user-message' : 'ai-message'}">
                <div class="message-avatar">${icon}</div>
                <div class="message-content" id="${messageId}">${displayContent}</div>
            </div>
        `;
        
        chatHistory.insertAdjacentHTML('beforeend', html);
        this.scrollToBottom();

        if (typingEffect && !isUser) {
            const container = document.getElementById(messageId);
            const fullHtml = this.renderMarkdown(content);
            
            const cursor = document.createElement('span');
            cursor.className = 'typing-cursor';
            container.appendChild(cursor);
            
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = fullHtml;
            
            const steps = [];
            
            function buildSteps(node) {
                if (node.nodeType === Node.TEXT_NODE) {
                    steps.push({ type: 'text', content: node.textContent });
                } else if (node.nodeType === Node.ELEMENT_NODE) {
                    steps.push({ type: 'elementStart', tagName: node.tagName, attributes: node.attributes });
                    node.childNodes.forEach(child => buildSteps(child));
                    steps.push({ type: 'elementEnd' });
                }
            }
            
            tempDiv.childNodes.forEach(child => buildSteps(child));
            
            let stepIndex = 0;
            let charIndex = 0;
            let currentStep = null;
            const parentStack = [container];
            const charInterval = 15;
            let isCompleted = false;
            let backgroundTimer = null;
            
            const processStep = () => {
                if (cursor.parentNode) cursor.parentNode.removeChild(cursor);
                
                if (!currentStep && stepIndex < steps.length) {
                    currentStep = steps[stepIndex];
                    stepIndex++;
                    charIndex = 0;
                }
                
                if (currentStep) {
                    const parent = parentStack[parentStack.length - 1];
                    
                    if (currentStep.type === 'elementStart') {
                        const el = document.createElement(currentStep.tagName);
                        Array.from(currentStep.attributes).forEach(attr => {
                            el.setAttribute(attr.name, attr.value);
                        });
                        parent.appendChild(el);
                        parentStack.push(el);
                        currentStep = null;
                    } else if (currentStep.type === 'elementEnd') {
                        parentStack.pop();
                        currentStep = null;
                    } else if (currentStep.type === 'text') {
                        if (charIndex < currentStep.content.length) {
                            const char = currentStep.content[charIndex];
                            parent.appendChild(document.createTextNode(char));
                            charIndex++;
                        } else {
                            currentStep = null;
                        }
                    }
                }
                
                const activeParent = parentStack[parentStack.length - 1];
                activeParent.appendChild(cursor);
                
                this.scrollToBottom();
                
                if (stepIndex >= steps.length && !currentStep) {
                    isCompleted = true;
                    cursor.remove();
                    container.innerHTML = fullHtml;
                    this.scrollToBottom();
                    return true;
                }
                return false;
            };
            
            const runAnimation = () => {
                if (isCompleted) return;
                
                if (document.hidden) {
                    backgroundTimer = setInterval(() => {
                        if (isCompleted || !document.hidden) {
                            clearInterval(backgroundTimer);
                            backgroundTimer = null;
                            if (!isCompleted) {
                                requestAnimationFrame(runAnimation);
                            }
                            return;
                        }
                        isCompleted = processStep();
                    }, charInterval);
                } else {
                    const animate = (currentTime) => {
                        if (isCompleted) return;
                        
                        if (document.hidden) {
                            runAnimation();
                            return;
                        }
                        
                        processStep();
                        
                        if (!isCompleted) {
                            setTimeout(() => requestAnimationFrame(animate), charInterval);
                        }
                    };
                    requestAnimationFrame(animate);
                }
            };
            
            return new Promise(resolve => {
                runAnimation();
                
                const checkComplete = setInterval(() => {
                    if (isCompleted) {
                        clearInterval(checkComplete);
                        if (backgroundTimer) {
                            clearInterval(backgroundTimer);
                        }
                        resolve();
                    }
                }, 50);
            });
        }
    }

    renderMarkdown(text) {
        if (!text) return '';
        
        // 预处理：解决 JSON 转义问题
        let html = text.replace(/\\n/g, '\n').replace(/\\"/g, '"');
        
        html = html
            .replace(/^### (.*$)/gm, '<h4>$1</h4>')
            .replace(/^## (.*$)/gm, '<h3>$1</h3>')
            .replace(/^# (.*$)/gm, '<h2>$1</h2>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/^- (.*?)(\n|$)/gm, '<li>$1</li>'); // 列表修复
            
        if (html.includes('<li>')) {
            html = html.replace(/((?:<li>.*<\/li>\n?)+)/g, '<ul>$1</ul>');
        }

        html = html.replace(/\n/g, '<br>');
        return html;
    }

    showLoading() {
        const id = `loading-${Date.now()}`;
        const html = `
            <div id="${id}" class="chat-message ai-message">
                <div class="message-avatar"><i class="fas fa-robot"></i></div>
                <div class="message-content" style="padding: 10px 15px;">
                    <i class="fas fa-circle-notch fa-spin text-secondary"></i> 思考中...
                </div>
            </div>
        `;
        document.getElementById('chat-history').insertAdjacentHTML('beforeend', html);
        this.scrollToBottom();
        return id;
    }

    hideLoading(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    scrollToBottom() {
        const area = document.querySelector('.chat-scroll-area');
        if (area) {
            area.scrollTop = area.scrollHeight;
        }
    }

    showExportOptions() {
        const exportOptionsHtml = `
            <div class="export-options-container">
                <button type="button" class="btn btn-primary w-100" onclick="planEditor.exportPlanWithWeather()">
                    <i class="fas fa-file-pdf me-2"></i> 导出包含修改的 PDF
                </button>
            </div>
        `;
        const chatHistory = document.getElementById('chat-history');
        const html = `
            <div class="chat-message ai-message">
                <div class="message-avatar"><i class="fas fa-robot"></i></div>
                <div class="message-content">${exportOptionsHtml}</div>
            </div>
        `;
        chatHistory.insertAdjacentHTML('beforeend', html);
        this.scrollToBottom();
    }

    async exportPlanWithWeather() {
        this.addChatMessage('ai', '正在为您生成深度定制路书，请稍候...', true);
        
        try {
            const apiUrl = await this.getApiBaseUrl('agent');
            // 将聊天记录转换为后端需要的格式
            const formattedHistory = this.chatHistory.map(msg => ({
                role: msg.type === 'user' ? 'user' : 'assistant',
                content: msg.content
            }));

            // 构建请求体，包含规划数据和对话历史
            const requestBody = {
                complete_plan_data: {
                    ...this.currentPlan,
                    conversation_history: formattedHistory // 关键：传递对话历史
                },
                title: this.currentPlan?.title,
                destination: this.currentPlan?.destination,
                duration: this.currentPlan?.duration,
                session_id: this.sessionId
            };

            const response = await fetch(`${apiUrl}/export_plan_pdf`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) throw new Error('Export failed');
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
                a.href = url;
                a.download = `定制路书_${Date.now()}.pdf`;
                document.body.appendChild(a);
                a.click();
                setTimeout(() => window.URL.revokeObjectURL(url), 100);

                this.addChatMessage('ai', `✅ 导出成功！`, true);

            } catch (e) {
            console.error(e);
            this.addChatMessage('ai', '❌ 导出失败，请重试。', true);
        }
    }

    async initializeChatSession() {
        let planData = this.currentPlan || {};
        if (!planData.plan_id) planData.plan_id = `chat_${Date.now()}`;
        try {
            const apiUrl = await this.getApiBaseUrl();
            const res = await fetch(`${apiUrl}/start_edit_session`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ plan_data: planData })
            });
            const data = await res.json();
            if (data.success) {
                this.sessionId = data.session_id;
                this.enableApplyButton();
            }
        } catch (e) {}
    }

    enableApplyButton() {
        const btn = document.getElementById('apply-changes-btn');
        if (btn) btn.disabled = false;
    }

    async applyChanges() {
        this.addChatMessage('ai', '✅ 修改已应用。现在您可以导出包含这些修改的PDF路书了。', true);
        setTimeout(() => this.showExportOptions(), 1000);
    }
}

window.planEditor = new PlanEditor();
window.openPlanEditor = function(planData) {
    window.planEditor.startEditing(planData);
};