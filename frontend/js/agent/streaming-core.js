/**
 * 流式通信核心模块
 * 提供独立的 SSE 流式请求处理，不依赖任何 UI 或业务逻辑
 */

class StreamingCore {
    constructor() {
        this.isStreaming = false;
        this.abortController = null;
    }

    /**
     * 发送流式请求
     * @param {string} url 请求 URL
     * @param {object} options 配置选项
     * @param {function} options.onChunk 收到数据块回调
     * @param {function} options.onComplete 完成回调
     * @param {function} options.onError 错误回调
     * @param {function} options.onStatus 状态变化回调
     * @param {AbortSignal} options.signal 中断信号
     * @returns {Promise<void>}
     */
    async stream(url, options = {}) {
        const {
            method = 'POST',
            headers = { 'Content-Type': 'application/json' },
            body = {},
            onChunk = () => {},
            onComplete = () => {},
            onError = () => {},
            onStatus = () => {},
            signal = null
        } = options;

        if (this.isStreaming) {
            console.warn('[StreamingCore] 已有流式请求正在进行');
            return;
        }

        this.isStreaming = true;
        this.abortController = signal || new AbortController();

        try {
            const response = await fetch(url, {
                method,
                headers,
                credentials: 'include',
                body: method !== 'GET' ? JSON.stringify(body) : undefined,
                signal: this.abortController.signal
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

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
                                onError(parsed.error);
                                return;
                            }

                            if (parsed.status) {
                                onStatus(parsed.status, parsed.content || '');
                            }

                            if (parsed.content) {
                                onChunk(parsed.content, parsed);
                            }

                            if (parsed.done) {
                                onStatus('done', '');
                            }
                        } catch (e) {
                            console.warn('[StreamingCore] 解析 SSE 数据失败:', e);
                        }
                    }
                }
            }

            this.isStreaming = false;
            onComplete();

        } catch (error) {
            this.isStreaming = false;
            if (error.name === 'AbortError') {
                console.log('[StreamingCore] 请求已被中断');
                onError('请求已被中断');
            } else {
                console.error('[StreamingCore] 流式请求失败:', error);
                onError(error.message);
            }
        }
    }

    /**
     * 停止流式请求
     */
    stop() {
        if (this.abortController) {
            this.abortController.abort();
        }
        this.isStreaming = false;
    }

    /**
     * 修复不完整的 Markdown 语法
     * @param {string} text 原始文本
     * @returns {string} 修复后的文本
     */
    static fixMarkdown(text) {
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
     * 渲染 Markdown 为 HTML
     * @param {string} text 原始 Markdown 文本
     * @returns {string} HTML
     */
    static renderMarkdown(text) {
        if (!text) return '';

        let html = text.replace(/\\n/g, '\n').replace(/\\"/g, '"');

        try {
            if (typeof window.marked !== 'undefined' && window.marked.parse) {
                html = window.marked.parse(html);
            } else if (typeof window.markdownit !== 'undefined') {
                const md = window.markdownit();
                html = md.render(html);
            } else {
                html = StreamingCore._simpleMarkdownRender(html);
            }
        } catch (e) {
            console.warn('[StreamingCore] Markdown渲染失败:', e);
            html = StreamingCore._simpleMarkdownRender(html);
        }

        return html;
    }

    /**
     * 简易 Markdown 渲染器（备用）
     */
    static _simpleMarkdownRender(text) {
        let html = text
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
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = StreamingCore;
} else {
    window.StreamingCore = StreamingCore;
}
