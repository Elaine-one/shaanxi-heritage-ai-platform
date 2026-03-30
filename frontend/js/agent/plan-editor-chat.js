/**
 * Plan Editor Chat Module
 * 处理消息发送、渲染、Markdown处理
 * 复用 StreamingCore 提供流式能力
 */

class PlanEditorChat {
    constructor(editor) {
        this.editor = editor;
        this.streamingCore = new StreamingCore();
        this.currentAiReply = null;
        this.aiMessageContainer = null;
        this.halfAiMessageContainer = null;
    }

    async sendMessage() {
        if (this.editor.isSending) return;

        const input = document.getElementById('chat-input');
        const sendBtn = document.getElementById('send-message-btn');
        const message = input.value.trim();

        if (!message) return;

        input.value = '';
        
        this.editor.chatHistory.push({ type: 'user', content: message, timestamp: new Date() });
        this.editor.saveState();

        this.editor.isSending = true;
        sendBtn.disabled = true;
        const originalBtnText = sendBtn.innerHTML;
        sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        const messageId = `ai-msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        
        this.currentAiReply = {
            messageId: messageId,
            content: '',
            isThinking: true
        };

        this._appendUserMessage(message);
        this._appendAiMessagePlaceholder(messageId);

        try {
            if (!this.editor.sessionId) await this.editor.api.initializeChatSession();

            const apiUrl = await this.editor.api.getApiBaseUrl();
            const url = `${apiUrl}/chat-stream`;

            let fullMessage = '';
            let pendingRender = false;

            const renderMessage = () => {
                if (this.currentAiReply) {
                    this.currentAiReply.content = fullMessage;
                    this.currentAiReply.isThinking = false;
                }
                this._updateAiMessageContent(fullMessage);
                pendingRender = false;
            };

            await this.streamingCore.stream(url, {
                method: 'POST',
                body: { message, session_id: this.editor.sessionId },
                onChunk: (content) => {
                    fullMessage += content;
                    if (!pendingRender) {
                        pendingRender = true;
                        requestAnimationFrame(() => renderMessage());
                    }
                },
                onStatus: (status, statusContent) => {
                },
                onComplete: () => {
                    if (pendingRender) renderMessage();
                    this.editor.chatHistory.push({ type: 'ai', content: fullMessage, timestamp: new Date() });
                    this.editor.saveState();
                    this.currentAiReply = null;
                    this.aiMessageContainer = null;
                    this.halfAiMessageContainer = null;
                    if (this.editor.isHalfExpanded) {
                        this.syncChatToHalf();
                    }
                },
                onError: (errorMsg) => {
                    this._updateAiMessageContent(`错误: ${errorMsg}`);
                    this.editor.chatHistory.push({ type: 'ai', content: `错误: ${errorMsg}`, timestamp: new Date() });
                    this.editor.saveState();
                    this.currentAiReply = null;
                    this.aiMessageContainer = null;
                    this.halfAiMessageContainer = null;
                }
            });

        } catch (error) {
            console.error('发送消息失败:', error);
            let errorMessage = '网络请求失败，请稍后重试。';

            if (error.name === 'TypeError' && error.message && error.message.includes('fetch')) {
                errorMessage = '网络连接失败，请检查网络连接。';
            } else if (error.message && error.message.includes('Failed to fetch')) {
                errorMessage = '网络连接失败，请检查网络连接。';
            } else if (error.message && error.message.includes('HTTP')) {
                errorMessage = `服务器错误: ${error.message}`;
            } else if (error.message) {
                errorMessage = `请求失败: ${error.message}`;
            }

            this._updateAiMessageContent(errorMessage);
            this.editor.chatHistory.push({ type: 'ai', content: errorMessage, timestamp: new Date() });
            this.editor.saveState();
            this.currentAiReply = null;
            this.aiMessageContainer = null;
            this.halfAiMessageContainer = null;
        } finally {
            this.editor.isSending = false;
            sendBtn.disabled = false;
            sendBtn.innerHTML = originalBtnText;
            const inputEl = document.getElementById('chat-input');
            if (inputEl) inputEl.focus();
        }
    }

    async sendHalfMessage() {
        if (this.editor.isSending) return;

        const input = document.getElementById('half-chat-input');
        const sendBtn = document.getElementById('half-send-btn');
        const message = input.value.trim();

        if (!message) return;

        input.value = '';
        
        this.editor.chatHistory.push({ type: 'user', content: message, timestamp: new Date() });
        this.editor.saveState();

        this.editor.isSending = true;
        sendBtn.disabled = true;
        const originalBtnHTML = sendBtn.innerHTML;
        sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        const messageId = `ai-msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        
        this.currentAiReply = {
            messageId: messageId,
            content: '',
            isThinking: true
        };

        this._appendHalfUserMessage(message);
        this._appendHalfAiMessagePlaceholder(messageId);

        try {
            if (!this.editor.sessionId) await this.editor.api.initializeChatSession();

            const apiUrl = await this.editor.api.getApiBaseUrl();
            const url = `${apiUrl}/chat-stream`;

            let fullMessage = '';
            let pendingRender = false;

            const renderHalfMessage = () => {
                if (this.currentAiReply) {
                    this.currentAiReply.content = fullMessage;
                    this.currentAiReply.isThinking = false;
                }
                this._updateHalfAiMessageContent(fullMessage);
                pendingRender = false;
            };

            await this.streamingCore.stream(url, {
                method: 'POST',
                body: { message, session_id: this.editor.sessionId },
                onChunk: (content) => {
                    fullMessage += content;
                    if (!pendingRender) {
                        pendingRender = true;
                        requestAnimationFrame(() => renderHalfMessage());
                    }
                },
                onStatus: (status, statusContent) => {
                },
                onComplete: () => {
                    if (pendingRender) renderHalfMessage();
                    this.editor.chatHistory.push({ type: 'ai', content: fullMessage, timestamp: new Date() });
                    this.editor.saveState();
                    this.currentAiReply = null;
                    this.aiMessageContainer = null;
                    this.halfAiMessageContainer = null;
                    this.syncChatToFull();
                },
                onError: (errorMsg) => {
                    this._updateHalfAiMessageContent(`错误: ${errorMsg}`);
                    this.editor.chatHistory.push({ type: 'ai', content: `错误: ${errorMsg}`, timestamp: new Date() });
                    this.editor.saveState();
                    this.currentAiReply = null;
                    this.aiMessageContainer = null;
                    this.halfAiMessageContainer = null;
                }
            });

        } catch (error) {
            console.error('发送消息失败:', error);
            this._updateHalfAiMessageContent('网络请求失败，请稍后重试。');
            this.editor.chatHistory.push({ type: 'ai', content: '网络请求失败，请稍后重试。', timestamp: new Date() });
            this.editor.saveState();
            this.currentAiReply = null;
            this.aiMessageContainer = null;
            this.halfAiMessageContainer = null;
        } finally {
            this.editor.isSending = false;
            sendBtn.disabled = false;
            sendBtn.innerHTML = originalBtnHTML;
        }
    }

    _appendUserMessage(content) {
        const chatHistory = document.getElementById('chat-history');
        if (!chatHistory) return;
        
        const html = `
            <div class="chat-message user-message">
                <div class="message-avatar"><i class="fas fa-user"></i></div>
                <div class="message-content">${content}</div>
            </div>
        `;
        chatHistory.insertAdjacentHTML('beforeend', html);
        this.scrollToBottom();
    }

    _appendAiMessagePlaceholder(messageId) {
        const chatHistory = document.getElementById('chat-history');
        if (!chatHistory) return;
        
        const html = `
            <div class="chat-message ai-message">
                <div class="message-avatar"><i class="fas fa-robot"></i></div>
                <div class="message-content" id="${messageId}">
                    <div class="thinking-indicator">
                        <i class="fas fa-spinner fa-spin"></i> 正在思考...
                    </div>
                </div>
            </div>
        `;
        chatHistory.insertAdjacentHTML('beforeend', html);
        this.aiMessageContainer = document.getElementById(messageId);
        this.scrollToBottom();
    }

    _updateAiMessageContent(content) {
        if (!this.aiMessageContainer) return;
        
        if (content) {
            const safeMessage = StreamingCore.fixMarkdown(content);
            const htmlContent = StreamingCore.renderMarkdown(safeMessage);
            this.aiMessageContainer.innerHTML = htmlContent;
        } else {
            this.aiMessageContainer.innerHTML = `
                <div class="thinking-indicator">
                    <i class="fas fa-spinner fa-spin"></i> 正在思考...
                </div>
            `;
        }
        this.scrollToBottom();
    }

    _appendHalfUserMessage(content) {
        const halfChatArea = document.getElementById('half-chat-area');
        if (!halfChatArea) return;
        
        const html = `
            <div class="half-message user-half">
                <div class="half-avatar user"><i class="fas fa-user"></i></div>
                <div class="half-content user">${content}</div>
            </div>
        `;
        halfChatArea.insertAdjacentHTML('beforeend', html);
        halfChatArea.scrollTop = halfChatArea.scrollHeight;
    }

    _appendHalfAiMessagePlaceholder(messageId) {
        const halfChatArea = document.getElementById('half-chat-area');
        if (!halfChatArea) return;
        
        const html = `
            <div class="half-message ai-half">
                <div class="half-avatar ai"><i class="fas fa-robot"></i></div>
                <div class="half-content ai" id="${messageId}">
                    <div class="half-thinking-indicator">
                        <i class="fas fa-spinner fa-spin"></i> 思考中...
                    </div>
                </div>
            </div>
        `;
        halfChatArea.insertAdjacentHTML('beforeend', html);
        this.halfAiMessageContainer = document.getElementById(messageId);
        halfChatArea.scrollTop = halfChatArea.scrollHeight;
    }

    _updateHalfAiMessageContent(content) {
        if (!this.halfAiMessageContainer) return;
        
        if (content) {
            const safeMessage = StreamingCore.fixMarkdown(content);
            const htmlContent = StreamingCore.renderMarkdown(safeMessage);
            this.halfAiMessageContainer.innerHTML = htmlContent;
        } else {
            this.halfAiMessageContainer.innerHTML = `
                <div class="half-thinking-indicator">
                    <i class="fas fa-spinner fa-spin"></i> 思考中...
                </div>
            `;
        }
        const halfChatArea = document.getElementById('half-chat-area');
        if (halfChatArea) {
            halfChatArea.scrollTop = halfChatArea.scrollHeight;
        }
    }

    renderChatWithPending() {
        const chatContainer = document.getElementById('chat-history');
        if (!chatContainer) return;
        
        const wasExporting = this.editor.api.isExporting;
        const hadExportBtn = document.getElementById('export-pdf-btn') !== null;
        
        chatContainer.innerHTML = '';
        
        this.editor.chatHistory.forEach(msg => {
            const isUser = msg.type === 'user';
            const icon = isUser ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
            const displayContent = isUser ? msg.content : this.renderMarkdown(msg.content);
            
            const html = `
                <div class="chat-message ${isUser ? 'user-message' : 'ai-message'}">
                    <div class="message-avatar">${icon}</div>
                    <div class="message-content">${displayContent}</div>
                </div>
            `;
            chatContainer.insertAdjacentHTML('beforeend', html);
        });
        
        if (this.currentAiReply) {
            const icon = '<i class="fas fa-robot"></i>';
            let displayContent;
            
            if (this.currentAiReply.isThinking) {
                displayContent = `
                    <div class="thinking-indicator">
                        <i class="fas fa-spinner fa-spin"></i> 正在思考...
                    </div>
                `;
            } else if (this.currentAiReply.content) {
                displayContent = this.renderMarkdown(this.currentAiReply.content);
            } else {
                displayContent = `
                    <div class="thinking-indicator">
                        <i class="fas fa-spinner fa-spin"></i> 正在思考...
                    </div>
                `;
            }
            
            const html = `
                <div class="chat-message ai-message">
                    <div class="message-avatar">${icon}</div>
                    <div class="message-content" id="${this.currentAiReply.messageId}">${displayContent}</div>
                </div>
            `;
            chatContainer.insertAdjacentHTML('beforeend', html);
            this.aiMessageContainer = document.getElementById(this.currentAiReply.messageId);
        }
        
        if (hadExportBtn) {
            this.editor.ui.showExportOptions();
        }
        
        if (wasExporting) {
            this.editor.api._setExportingState(true);
        }
        
        this.scrollToBottom();
    }

    renderHalfWithPending() {
        const halfChatArea = document.getElementById('half-chat-area');
        if (!halfChatArea) return;
        
        halfChatArea.innerHTML = '';
        
        this.editor.chatHistory.forEach(msg => {
            const isUser = msg.type === 'user';
            const icon = isUser ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
            const displayContent = isUser ? msg.content : this.renderMarkdown(msg.content);
            
            const html = `
                <div class="half-message ${isUser ? 'user-half' : 'ai-half'}">
                    <div class="half-avatar ${isUser ? 'user' : 'ai'}">${icon}</div>
                    <div class="half-content ${isUser ? 'user' : 'ai'}">${displayContent}</div>
                </div>
            `;
            halfChatArea.insertAdjacentHTML('beforeend', html);
        });
        
        if (this.currentAiReply) {
            const icon = '<i class="fas fa-robot"></i>';
            let displayContent;
            
            if (this.currentAiReply.isThinking) {
                displayContent = `
                    <div class="half-thinking-indicator">
                        <i class="fas fa-spinner fa-spin"></i> 思考中...
                    </div>
                `;
            } else if (this.currentAiReply.content) {
                displayContent = this.renderMarkdown(this.currentAiReply.content);
            } else {
                displayContent = `
                    <div class="half-thinking-indicator">
                        <i class="fas fa-spinner fa-spin"></i> 思考中...
                    </div>
                `;
            }
            
            const html = `
                <div class="half-message ai-half">
                    <div class="half-avatar ai">${icon}</div>
                    <div class="half-content ai" id="${this.currentAiReply.messageId}">${displayContent}</div>
                </div>
            `;
            halfChatArea.insertAdjacentHTML('beforeend', html);
            this.halfAiMessageContainer = document.getElementById(this.currentAiReply.messageId);
        }
        
        halfChatArea.scrollTop = halfChatArea.scrollHeight;
    }

    async addChatMessage(type, content, typingEffect = false) {
        const chatHistory = document.getElementById('chat-history');
        if (!chatHistory) return;
        
        this.editor.chatHistory.push({ type, content, timestamp: new Date() });
        this.editor.saveState();

        const messageId = `${type}-msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const isUser = type === 'user';
        const icon = isUser ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
        
        let displayContent = isUser ? content : this.renderMarkdown(content);
        if (typingEffect) displayContent = '';

        const html = `
            <div class="chat-message ${isUser ? 'user-message' : 'ai-message'}">
                <div class="message-avatar">${icon}</div>
                <div class="message-content" id="${messageId}">${displayContent}</div>
            </div>
        `;
        
        chatHistory.insertAdjacentHTML('beforeend', html);
        this.scrollToBottom();
        if (this.editor.isHalfExpanded) {
            this.syncChatToHalf();
        }

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

    syncChatToFull() {
        this.renderChatWithPending();
    }

    syncChatToHalf() {
        this.renderHalfWithPending();
    }

    renderMarkdown(text) {
        return StreamingCore.renderMarkdown(text);
    }

    scrollToBottom() {
        const area = document.querySelector('.chat-scroll-area');
        if (area) {
            area.scrollTop = area.scrollHeight;
        }
    }
}

window.PlanEditorChat = PlanEditorChat;
