/**
 * Plan Editor API Module
 * 处理API通信、会话管理、导出功能
 */

class PlanEditorAPI {
    constructor(editor) {
        this.editor = editor;
        this.apiUrls = {};
        this.isExporting = false;
        this._applyBtnWasEnabled = false;
        this._pendingExportData = null;
        this._exportStartTime = null;
    }

    async getApiBaseUrl(apiType = 'agent') {
        if (this.apiUrls[apiType]) {
            return this.apiUrls[apiType];
        }
        
        const apiUrl = `/api/agent/api/${apiType}`;
        console.log(`使用代理API URL (${apiType}):`, apiUrl);
        this.apiUrls[apiType] = apiUrl;
        return apiUrl;
    }

    async initializeChatSession() {
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
            const data = await res.json();
            if (data.success) {
                this.editor.sessionId = data.session_id;
                this.editor.ui.enableApplyButton();
            }
        } catch (e) {
            console.error('初始化会话失败:', e);
        }
    }

    async applyChanges() {
        this.editor.chat.addChatMessage('ai', '✅ 修改已应用。现在您可以导出包含这些修改的PDF路书了。', true);
        setTimeout(() => this.editor.ui.showExportOptions(), 1000);
    }

    _setExportingState(isExporting) {
        this.isExporting = isExporting;
        
        const exportBtn = document.getElementById('export-pdf-btn');
        const applyBtn = document.getElementById('apply-changes-btn');
        
        if (exportBtn) {
            exportBtn.disabled = isExporting;
            if (isExporting) {
                exportBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> 正在生成PDF...';
            } else {
                exportBtn.innerHTML = '<i class="fas fa-file-pdf me-2"></i> 导出包含修改的 PDF';
            }
        }
        
        if (applyBtn) {
            if (isExporting) {
                this._applyBtnWasEnabled = !applyBtn.disabled;
                applyBtn.disabled = true;
            } else {
                applyBtn.disabled = !this._applyBtnWasEnabled;
            }
        }
        
        this._saveExportState();
    }

    _saveExportState() {
        try {
            const state = {
                isExporting: this.isExporting,
                pendingExportData: this._pendingExportData,
                exportStartTime: this._exportStartTime,
                sessionId: this.editor.sessionId
            };
            localStorage.setItem('plan_editor_export_state', JSON.stringify(state));
        } catch (e) {
            console.warn('保存导出状态失败:', e);
        }
    }

    _clearExportState() {
        try {
            localStorage.removeItem('plan_editor_export_state');
            this._pendingExportData = null;
            this._exportStartTime = null;
        } catch (e) {
            console.warn('清除导出状态失败:', e);
        }
    }

    _loadExportState() {
        try {
            const saved = localStorage.getItem('plan_editor_export_state');
            if (saved) {
                const state = JSON.parse(saved);
                
                if (state.isExporting && state.exportStartTime) {
                    const elapsed = Date.now() - state.exportStartTime;
                    if (elapsed > 600000) {
                        this._clearExportState();
                        return null;
                    }
                    return state;
                }
            }
        } catch (e) {
            console.warn('加载导出状态失败:', e);
        }
        return null;
    }

    checkPendingExport() {
        const pendingState = this._loadExportState();
        if (pendingState && pendingState.isExporting) {
            this._pendingExportData = pendingState.pendingExportData;
            this.editor.sessionId = pendingState.sessionId;
            
            this.editor.chat.addChatMessage('ai', '⚠️ 检测到上次有未完成的导出任务。后端可能仍在处理中，您可以等待片刻后重新尝试导出。', false);
            this.editor.ui.showExportOptions();
            this._clearExportState();
            return true;
        }
        return false;
    }

    async exportPlanWithWeather() {
        if (this.isExporting) return;
        
        this._setExportingState(true);
        this.editor.chat.addChatMessage('ai', '正在为您生成深度定制路书，请稍候...', true);
        
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 300000);
        
        try {
            const apiUrl = await this.getApiBaseUrl('agent');
            const formattedHistory = this.editor.chatHistory.map(msg => ({
                role: msg.type === 'user' ? 'user' : 'assistant',
                content: msg.content
            }));

            const requestBody = {
                complete_plan_data: {
                    ...this.editor.currentPlan,
                    conversation_history: formattedHistory
                },
                title: this.editor.currentPlan?.title,
                destination: this.editor.currentPlan?.destination,
                duration: this.editor.currentPlan?.duration,
                session_id: this.editor.sessionId
            };
            
            this._pendingExportData = requestBody;
            this._exportStartTime = Date.now();
            this._saveExportState();

            const response = await fetch(`${apiUrl}/export_plan_pdf`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(requestBody),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `导出失败 (${response.status})`);
            }
            
            const blob = await response.blob();
            
            if (blob.size < 1000) {
                throw new Error('生成的PDF文件太小，可能内容为空');
            }
            
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `定制路书_${Date.now()}.pdf`;
            document.body.appendChild(a);
            a.click();
            setTimeout(() => window.URL.revokeObjectURL(url), 100);

            this.editor.chat.addChatMessage('ai', `✅ 导出成功！`, true);
            this._clearExportState();

        } catch (e) {
            clearTimeout(timeoutId);
            console.error('PDF导出错误:', e);
            
            let errorMsg = '❌ 导出失败，请重试。';
            if (e.name === 'AbortError') {
                errorMsg = '❌ 导出超时（5分钟），请稍后重试。';
            } else if (e.message && e.message.includes('Failed to fetch')) {
                errorMsg = '⚠️ 导出请求已发送，但连接中断。后端可能仍在处理中，请稍后返回查看或重新导出。';
            } else if (e.message) {
                errorMsg = `❌ 导出失败: ${e.message}`;
            }
            
            this.editor.chat.addChatMessage('ai', errorMsg, true);
        } finally {
            this._setExportingState(false);
        }
    }
}

window.PlanEditorAPI = PlanEditorAPI;
