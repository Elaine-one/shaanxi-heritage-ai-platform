/**
 * 流式对话管理器
 * 支持真正的 SSE 流式输出，支持状态反馈和不完整 Markdown 处理
 */

class StreamingChatManager {
    constructor() {
        this.eventSource = null;
        this.currentMessage = '';
        this.isStreaming = false;
        this.pendingRender = false;
        this.statusCallback = null;
    }

    /**
     * 发送流式消息
     * @param {string} message 用户消息
     * @param {string} sessionId 会话ID
     * @param {function} onChunk 收到文本块时的回调
     * @param {function} onComplete 完成时的回调
     * @param {function} onError 错误时的回调
     * @param {function} onStatus 状态变化时的回调（可选）
     */
    async sendStreamMessage(message, sessionId, onChunk, onComplete, onError, onStatus = null) {
        if (this.isStreaming) {
            console.warn('已有流式请求正在进行');
            return;
        }

        this.isStreaming = true;
        this.currentMessage = '';
        this.statusCallback = onStatus;

        try {
            const apiUrl = await this.getApiBaseUrl();
            const url = `${apiUrl}/agent/chat-stream`;

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify({
                    message: message,
                    session_id: sessionId
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            let buffer = '';
            let pendingRender = false;

            const renderMessage = () => {
                const safeMessage = this._fixIncompleteMarkdown(this.currentMessage);
                const html = marked.parse(safeMessage);
                onChunk(this.currentMessage, html);
                pendingRender = false;
            };

            while (true) {
                const { done, value } = await reader.read();

                if (done) {
                    break;
                }

                buffer += decoder.decode(value, { stream: true });

                const lines = buffer.split('\n');
                buffer = lines.pop();

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        try {
                            const parsed = JSON.parse(data);
                            
                            if (parsed.error) {
                                onError(parsed.error);
                                return;
                            }

                            if (parsed.status === 'thinking') {
                                if (this.statusCallback) {
                                    this.statusCallback('thinking', parsed.content || '正在思考...');
                                }
                            } else if (parsed.content) {
                                this.currentMessage += parsed.content;
                                
                                if (!pendingRender) {
                                    pendingRender = true;
                                    requestAnimationFrame(() => {
                                        renderMessage();
                                    });
                                }
                            } else if (parsed.done) {
                                if (this.statusCallback) {
                                    this.statusCallback('done', '');
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

            this.isStreaming = false;
            onComplete(this.currentMessage);

        } catch (error) {
            this.isStreaming = false;
            console.error('流式请求失败:', error);
            onError(error.message);
        }
    }

    /**
     * 修复不完整的 Markdown 语法
     * @param {string} text 原始文本
     * @returns {string} 修复后的文本
     */
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

    /**
     * 停止流式请求
     */
    stopStreaming() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
        this.isStreaming = false;
    }

    /**
     * 获取 API 基础地址
     */
    async getApiBaseUrl() {
        try {
            const response = await fetch('/api/agent/url');
            const data = await response.json();
            return data.url;
        } catch (error) {
            console.error('获取 API 地址失败:', error);
            return '/api/agent';
        }
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = StreamingChatManager;
} else {
    window.StreamingChatManager = StreamingChatManager;
}
