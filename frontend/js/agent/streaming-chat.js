/**
 * 流式对话管理器
 * 支持真正的 SSE 流式输出
 */

class StreamingChatManager {
    constructor() {
        this.eventSource = null;
        this.currentMessage = '';
        this.isStreaming = false;
        this.pendingRender = false;
    }

    /**
     * 发送流式消息
     * @param {string} message 用户消息
     * @param {string} sessionId 会话ID
     * @param {function} onChunk 收到文本块时的回调
     * @param {function} onComplete 完成时的回调
     * @param {function} onError 错误时的回调
     */
    async sendStreamMessage(message, sessionId, onChunk, onComplete, onError) {
        if (this.isStreaming) {
            console.warn('已有流式请求正在进行');
            return;
        }

        this.isStreaming = true;
        this.currentMessage = '';

        try {
            // 构建请求 URL
            const apiUrl = await this.getApiBaseUrl();
            const url = `${apiUrl}/agent/chat-stream`;

            // 使用 fetch 发送 POST 请求
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

            // 读取流式响应
            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            let buffer = '';
            let pendingRender = false;

            const renderMessage = () => {
                const html = marked.parse(this.currentMessage);
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

                            if (parsed.content) {
                                this.currentMessage += parsed.content;
                                
                                if (!pendingRender) {
                                    pendingRender = true;
                                    requestAnimationFrame(() => {
                                        renderMessage();
                                    });
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

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = StreamingChatManager;
} else {
    window.StreamingChatManager = StreamingChatManager;
}
