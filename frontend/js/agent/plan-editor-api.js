/**
 * Plan Editor API Module
 * 处理API通信、会话管理、导出功能
 */

class PlanEditorAPI {
    constructor(editor) {
        this.editor = editor;
        this.apiUrls = {};
        this.isExporting = false;
        this._currentTaskId = null;
        this._sessionInitializing = false;
    }

    async getApiBaseUrl(apiType = 'agent') {
        if (this.apiUrls[apiType]) {
            return this.apiUrls[apiType];
        }
        const apiUrl = `/api/agent/api/${apiType}`;
        this.apiUrls[apiType] = apiUrl;
        return apiUrl;
    }

    async initializeChatSession() {
        if (this._sessionInitializing) {
            console.warn('会话正在初始化中，忽略重复调用');
            return;
        }
        this._sessionInitializing = true;

        let planData = this.editor.currentPlan || {};
        if (!planData.plan_id) planData.plan_id = `chat_${Date.now()}`;
        try {
            const apiUrl = await this.getApiBaseUrl();
            const res = await fetch(`${apiUrl}/start_edit_session`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ plan_data: planData })
            });

            if (!res.ok) {
                const contentType = res.headers.get('content-type') || '';
                if (contentType.includes('application/json')) {
                    const errData = await res.json();
                    throw new Error(errData.detail || `HTTP ${res.status}`);
                } else {
                    const textPreview = await res.text().then(t => t.substring(0, 200));
                    throw new Error(`服务端返回非JSON响应 (${res.status})`);
                }
            }

            const data = await res.json();
            if (data.success) {
                this.editor.sessionId = data.session_id;
                this.editor.ui.enableApplyButton();
            } else {
                throw new Error(data.message || '初始化失败');
            }
        } catch (e) {
            console.error('初始化会话失败:', e);
            this.editor._initializing = false;
            this.editor.isEditing = false;
            throw new Error('会话初始化失败: ' + (e.message || e));
        } finally {
            this._sessionInitializing = false;
        }
    }

    async applyChanges() {
        this.editor.chat.addChatMessage('ai', '✅ 修改已应用。现在您可以导出包含这些修改的PDF路书了。', true);
        this.editor.ui.showExportButton();
    }

    _setExportBtnText(text, isLoading = false) {
        const exportBtn = document.getElementById('export-pdf-btn');
        if (!exportBtn) return;
        if (isLoading) {
            exportBtn.innerHTML = `<i class="fas fa-spinner fa-spin me-2"></i> ${text}`;
        } else {
            exportBtn.innerHTML = `<i class="fas fa-file-pdf me-2"></i> ${text}`;
        }
    }

    _setExportingState(isExporting) {
        this.isExporting = isExporting;

        const exportBtn = document.getElementById('export-pdf-btn');
        const applyBtn = document.getElementById('apply-changes-btn');
        const sendBtn = document.getElementById('send-message-btn');
        const halfSendBtn = document.getElementById('half-send-btn');

        if (exportBtn) {
            exportBtn.disabled = isExporting;
            if (isExporting) {
                exportBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> 正在生成PDF...';
            } else {
                exportBtn.innerHTML = '<i class="fas fa-file-pdf me-2"></i> 导出包含修改的 PDF';
            }
        }

        if (applyBtn) applyBtn.disabled = isExporting;
        if (sendBtn) sendBtn.disabled = isExporting;
        if (halfSendBtn) halfSendBtn.disabled = isExporting;

        this.editor.saveState();
    }

    async checkPendingExport() {
        if (!this.editor.sessionId) return false;

        try {
            const apiUrl = await this.getApiBaseUrl('agent');
            const res = await fetch(`${apiUrl}/session_export_status?session_id=${this.editor.sessionId}`, {
                credentials: 'include'
            });

            if (!res.ok) return false;

            const data = await res.json();

            if (data.has_task && data.status && data.status !== 'failed' && data.status !== 'cancelled') {
                this._currentTaskId = data.task_id;

                if (data.status === 'completed') {
                    return { completed: true, apiUrl, taskInfo: data };
                }

                this._setExportingState(true);
                this._setExportBtnText('AI生成中，预计2-5分钟...', true);
                try {
                    await this._pollPdfStatus(apiUrl, data.task_id);
                } catch (e) {
                    this.editor.chat.addChatMessage('ai', `⚠️ PDF导出失败: ${e.message}`, true);
                    this._setExportBtnText(`导出失败: ${e.message}`);
                    setTimeout(() => this._setExportBtnText('导出包含修改的 PDF'), 3000);
                } finally {
                    this._setExportingState(false);
                    this._currentTaskId = null;
                }
                return true;
            }
        } catch (e) {
            console.warn('查询导出状态失败:', e);
        }

        return false;
    }

    _handleExportCompleted(apiUrl, taskInfo) {
        const filename = taskInfo.filename || '定制路书.pdf';
        const downloadUrl = `${apiUrl}/download_pdf/${taskInfo.task_id}`;
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();

        this.editor.chat.addChatMessage('ai', '✅ PDF导出成功！文件已自动下载。', true);
        this._setExportBtnText('导出包含修改的 PDF');
        this._setExportingState(false);
        this._currentTaskId = null;
    }

    async exportPlanWithWeather() {
        if (this.isExporting) return;

        this._setExportingState(true);
        this._setExportBtnText('正在提交...', true);

        try {
            const apiUrl = await this.getApiBaseUrl('agent');

            const response = await fetch(`${apiUrl}/export_pdf`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    session_id: this.editor.sessionId
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `提交失败 (${response.status})`);
            }

            const data = await response.json();
            if (!data.success || !data.message) {
                throw new Error(data.message || '提交导出任务失败');
            }

            this._currentTaskId = data.message;
            this._setExportBtnText('AI生成中，预计2-5分钟...', true);

            await this._pollPdfStatus(apiUrl, this._currentTaskId);

        } catch (e) {
            console.error('PDF导出错误:', e);
            this._setExportBtnText(`导出失败: ${e.message}`);
            setTimeout(() => this._setExportBtnText('导出包含修改的 PDF'), 3000);
        } finally {
            this._setExportingState(false);
            this._currentTaskId = null;
        }
    }

    async _pollPdfStatus(apiUrl, taskId) {
        const MAX_POLL_TIME = 10 * 60 * 1000;
        const FAST_INTERVAL = 3000;
        const SLOW_INTERVAL = 8000;
        const FAST_PHASE_DURATION = 30000;
        const startTime = Date.now();
        let lastProgress = 0;
        let isFirstCheck = true;

        while (Date.now() - startTime < MAX_POLL_TIME) {
            if (!isFirstCheck) {
                const elapsed = Date.now() - startTime;
                const interval = elapsed < FAST_PHASE_DURATION ? FAST_INTERVAL : SLOW_INTERVAL;
                await new Promise(r => setTimeout(r, interval));
            }
            isFirstCheck = false;

            try {
                const res = await fetch(`${apiUrl}/export_pdf_status?task_id=${taskId}`, {
                    credentials: 'include'
                });

                if (!res.ok) continue;

                const data = await res.json();
                const taskInfo = data.changes || {};
                const status = data.status || taskInfo.status || 'unknown';
                const progress = taskInfo.progress || 0;

                if (progress > lastProgress) {
                    lastProgress = progress;
                    const progressText = progress >= 100 ? '生成完成！' : `生成中 ${progress}%`;
                    this._setExportBtnText(progressText, true);
                }

                if (status === 'completed') {
                    const filename = taskInfo.filename || '定制路书.pdf';
                    const downloadUrl = `${apiUrl}/download_pdf/${taskId}`;
                    const a = document.createElement('a');
                    a.href = downloadUrl;
                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                    a.remove();

                    this.editor.chat.addChatMessage('ai', '✅ PDF导出成功！文件已自动下载。', true);
                    this._setExportBtnText('导出包含修改的 PDF');
                    return;
                }

                if (status === 'failed') {
                    throw new Error(taskInfo.error || 'PDF生成失败');
                }

            } catch (e) {
                if (e.message && !e.message.includes('fetch')) {
                    throw e;
                }
            }
        }

        throw new Error('导出超时（10分钟），请稍后重试');
    }

    async cleanup() {
        const sessionId = this.editor.sessionId;
        this._currentTaskId = null;
        this.isExporting = false;

        if (!sessionId) return;

        try {
            const apiUrl = await this.getApiBaseUrl('agent');
            await fetch(`${apiUrl}/end_edit_session`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ session_id: sessionId })
            });
        } catch (e) {
            console.warn('通知后端结束会话失败:', e);
        }
    }
}

window.PlanEditorAPI = PlanEditorAPI;
