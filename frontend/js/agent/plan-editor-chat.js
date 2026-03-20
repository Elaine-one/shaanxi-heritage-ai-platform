/**
 * Plan Editor Chat Module
 * 处理消息发送、渲染、Markdown处理
 */

class PlanEditorChat {
    constructor(editor) {
        this.editor = editor;
    }

    async sendMessage() {
        if (this.editor.isSending) return;

        const input = document.getElementById('chat-input');
        const sendBtn = document.getElementById('send-message-btn');
        const message = input.value.trim();
        
        if (!message) return;
        
        input.value = '';
        this.addChatMessage('user', message, false);
        
        this.editor.isSending = true;
        sendBtn.disabled = true;
        const originalBtnText = sendBtn.innerHTML;
        sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        
        const loadingId = this.showLoading();
        
        try {
            if (!this.editor.sessionId) await this.editor.api.initializeChatSession();

            const apiUrl = await this.editor.api.getApiBaseUrl();
            
            const response = await fetch(`${apiUrl}/chat-stream`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ 
                    message: message,
                    session_id: this.editor.sessionId 
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const messageId = `msg-${Date.now()}`;
            const chatHistory = document.getElementById('chat-history');
            const html = `
                <div class="chat-message ai-message">
                    <div class="message-avatar"><i class="fas fa-robot"></i></div>
                    <div class="message-content" id="${messageId}"></div>
                </div>
            `;
            chatHistory.insertAdjacentHTML('beforeend', html);

            this.hideLoading(loadingId);

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let fullMessage = '';
            let pendingRender = false;
            let statusIndicator = null;

            const renderMessage = () => {
                if (statusIndicator) {
                    statusIndicator.remove();
                    statusIndicator = null;
                }
                
                const safeMessage = this._fixIncompleteMarkdown(fullMessage);
                let html;
                try {
                    if (typeof window.marked !== 'undefined' && window.marked.parse) {
                        html = window.marked.parse(safeMessage);
                    } else if (typeof window.markdownit !== 'undefined') {
                        const md = window.markdownit();
                        html = md.render(safeMessage);
                    } else {
                        html = safeMessage.replace(/\n/g, '<br>');
                    }
                } catch (e) {
                    console.warn('Markdown渲染失败:', e);
                    html = safeMessage.replace(/\n/g, '<br>');
                }
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
                                this.addChatMessage('ai', `错误: ${parsed.error}`, false);
                                return;
                            }

                            if (parsed.status === 'thinking') {
                                this._updateStatusIndicator(messageId, parsed.content || '正在思考...');
                            } else if (parsed.content) {
                                fullMessage += parsed.content;
                                
                                if (!pendingRender) {
                                    pendingRender = true;
                                    requestAnimationFrame(() => {
                                        renderMessage();
                                    });
                                }
                            }
                            
                            if (parsed.metadata) {
                                if (parsed.metadata.changes_made && parsed.metadata.updated_plan) {
                                    this.editor.currentPlan = parsed.metadata.updated_plan;
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

            this.editor.chatHistory.push({ type: 'ai', content: fullMessage, timestamp: new Date() });
            this.editor.saveState();
            
            this.syncChatToFull();
            if (this.editor.isHalfExpanded) {
                this.syncChatToHalf();
            }

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
            
            this.editor.chatHistory.push({ type: 'ai', content: errorMessage, timestamp: new Date() });
            this.editor.saveState();
            this.syncChatToFull();
            if (this.editor.isHalfExpanded) {
                this.syncChatToHalf();
            }
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
        this.syncChatToHalf();
        this.editor.saveState();
        
        this.editor.isSending = true;
        sendBtn.disabled = true;
        const originalBtnHTML = sendBtn.innerHTML;
        sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        
        const thinkingId = `half-thinking-${Date.now()}`;
        const halfChatArea = document.getElementById('half-chat-area');
        const thinkingHtml = `
            <div class="half-message ai-half" id="${thinkingId}">
                <div class="half-avatar ai"><i class="fas fa-robot"></i></div>
                <div class="half-content ai" style="color: #888; font-style: italic;">
                    <i class="fas fa-spinner fa-spin"></i> 思考中...
                </div>
            </div>
        `;
        halfChatArea.insertAdjacentHTML('beforeend', thinkingHtml);
        halfChatArea.scrollTop = halfChatArea.scrollHeight;
        
        try {
            if (!this.editor.sessionId) await this.editor.api.initializeChatSession();

            const apiUrl = await this.editor.api.getApiBaseUrl();
            
            const response = await fetch(`${apiUrl}/chat-stream`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ 
                    message: message,
                    session_id: this.editor.sessionId 
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let fullMessage = '';
            let hasRealContent = false;
            let messageId = null;

            const renderHalfMessage = () => {
                const thinkingEl = document.getElementById(thinkingId);
                if (thinkingEl) thinkingEl.remove();
                
                if (!messageId) {
                    messageId = `half-msg-${Date.now()}`;
                    const msgHtml = `
                        <div class="half-message ai-half" id="${messageId}">
                            <div class="half-avatar ai"><i class="fas fa-robot"></i></div>
                            <div class="half-content ai"></div>
                        </div>
                    `;
                    halfChatArea.insertAdjacentHTML('beforeend', msgHtml);
                }
                
                const msgEl = document.getElementById(messageId);
                if (msgEl) {
                    const contentEl = msgEl.querySelector('.half-content');
                    if (contentEl) {
                        contentEl.innerHTML = this.renderMarkdown(fullMessage);
                    }
                }
                halfChatArea.scrollTop = halfChatArea.scrollHeight;
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
                                const thinkingEl = document.getElementById(thinkingId);
                                if (thinkingEl) thinkingEl.remove();
                                this.editor.chatHistory.push({ type: 'ai', content: `错误: ${parsed.error}`, timestamp: new Date() });
                                this.syncChatToHalf();
                                return;
                            }

                            if (parsed.status === 'thinking') {
                                const thinkingEl = document.getElementById(thinkingId);
                                if (thinkingEl) {
                                    const contentEl = thinkingEl.querySelector('.half-content');
                                    if (contentEl) {
                                        contentEl.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${parsed.content || '思考中...'}`;
                                    }
                                }
                            } else if (parsed.content) {
                                fullMessage += parsed.content;
                                hasRealContent = true;
                                renderHalfMessage();
                            }
                            
                            if (parsed.metadata) {
                                if (parsed.metadata.changes_made && parsed.metadata.updated_plan) {
                                    this.editor.currentPlan = parsed.metadata.updated_plan;
                                }
                            }
                        } catch (e) {
                            console.error('解析 SSE 数据失败:', e);
                        }
                    }
                }
            }

            if (fullMessage) {
                this.editor.chatHistory.push({ type: 'ai', content: fullMessage, timestamp: new Date() });
                this.editor.saveState();
            }

        } catch (error) {
            console.error('发送消息失败:', error);
            const thinkingEl = document.getElementById(thinkingId);
            if (thinkingEl) thinkingEl.remove();
            this.editor.chatHistory.push({ type: 'ai', content: '网络请求失败，请稍后重试。', timestamp: new Date() });
            this.syncChatToHalf();
        } finally {
            this.editor.isSending = false;
            sendBtn.disabled = false;
            sendBtn.innerHTML = originalBtnHTML;
        }
    }

    async addChatMessage(type, content, typingEffect = false) {
        const chatHistory = document.getElementById('chat-history');
        if (!chatHistory) return;
        
        this.editor.chatHistory.push({ type, content, timestamp: new Date() });
        this.editor.saveState();

        const messageId = `msg-${Date.now()}`;
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
        
        if (hadExportBtn) {
            this.editor.ui.showExportOptions();
        }
        
        if (wasExporting) {
            this.editor.api._setExportingState(true);
        }
        
        this.scrollToBottom();
    }

    syncChatToHalf() {
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
        
        halfChatArea.scrollTop = halfChatArea.scrollHeight;
    }

    renderMarkdown(text) {
        if (!text) return '';
        
        let html = text.replace(/\\n/g, '\n').replace(/\\"/g, '"');
        
        html = html
            .replace(/^### (.*$)/gm, '<h4>$1</h4>')
            .replace(/^## (.*$)/gm, '<h3>$1</h3>')
            .replace(/^# (.*$)/gm, '<h2>$1</h2>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/^- (.*?)(\n|$)/gm, '<li>$1</li>');
            
        if (html.includes('<li>')) {
            html = html.replace(/((?:<li>.*<\/li>\n?)+)/g, '<ul>$1</ul>');
        }

        html = html.replace(/\n/g, '<br>');
        return html;
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
        
        const codeMatches = fixed.match(/(?<!`)`(?!`)/g);
        if (codeMatches && codeMatches.length % 2 !== 0) {
            fixed += '`';
        }
        
        const italicMatches = fixed.match(/(?<!\*)\*(?!\*)/g);
        if (italicMatches && italicMatches.length % 2 !== 0) {
            fixed += '*';
        }
        
        return fixed;
    }

    _updateStatusIndicator(messageId, statusText) {
        const container = document.getElementById(messageId);
        if (!container) return;
        
        let statusEl = container.querySelector('.status-indicator');
        if (!statusEl) {
            statusEl = document.createElement('div');
            statusEl.className = 'status-indicator';
            statusEl.style.cssText = 'color: #888; font-style: italic; margin-bottom: 8px;';
            container.insertBefore(statusEl, container.firstChild);
        }
        
        statusEl.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${statusText}`;
    }

    showLoading() {
        const id = `loading-${Date.now()}`;
        const html = `
            <div id="${id}" class="chat-message ai-message">
                <div class="message-avatar"><i class="fas fa-robot"></i></div>
                <div class="message-content" style="padding: 10px 15px;">
                    <i class="fas fa-circle-notch fa-spin" style="color: #8B0000;"></i> 思考中...
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
}

window.PlanEditorChat = PlanEditorChat;
