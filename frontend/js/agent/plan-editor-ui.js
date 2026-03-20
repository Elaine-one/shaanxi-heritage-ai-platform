/**
 * Plan Editor UI Module
 * 处理UI创建、拖拽功能、状态切换
 */

class PlanEditorUI {
    constructor(editor) {
        this.editor = editor;
        this.eventsBound = false;
        this.minibarDragged = false;
    }

    createEditorUI() {
        if (document.getElementById('plan-editor-modal')) return;

        const editorHTML = `
            <div id="plan-editor-modal" class="plan-editor-modal">
                <div id="plan-editor-header" class="editor-header">
                    <div class="header-title"><i class="fas fa-map-marked-alt me-2"></i>旅行规划助手</div>
                    <div class="header-controls">
                        <button type="button" class="ctrl-btn" id="half-expand-btn" title="半展开">
                            <i class="fas fa-window-restore"></i>
                        </button>
                        <button type="button" class="ctrl-btn" id="minimize-btn" title="最小化">
                            <i class="fas fa-minus"></i>
                        </button>
                        <button type="button" class="ctrl-btn" id="zoom-out-btn" title="缩小">
                            <i class="fas fa-search-minus"></i>
                        </button>
                        <button type="button" class="ctrl-btn" id="zoom-in-btn" title="放大">
                            <i class="fas fa-search-plus"></i>
                        </button>
                        <button type="button" class="close-btn" id="plan-editor-close" title="关闭">
                            <i class="fas fa-times"></i>
                        </button>
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
            <div id="plan-editor-half" class="plan-editor-half" style="display: none;">
                <div class="half-header">
                    <div class="half-title">
                        <div class="half-icon">
                            <i class="fas fa-map-marked-alt"></i>
                        </div>
                        <span>规划助手</span>
                    </div>
                    <div class="half-controls">
                        <button type="button" class="half-ctrl-btn" id="half-to-full" title="全展开">
                            <i class="fas fa-expand"></i>
                        </button>
                        <button type="button" class="half-ctrl-btn" id="half-to-mini" title="最小化">
                            <i class="fas fa-minus"></i>
                        </button>
                        <button type="button" class="half-close-btn" id="half-close" title="关闭">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
                <div class="half-body">
                    <div class="half-chat-area" id="half-chat-area">
                    </div>
                </div>
                <div class="half-input-area">
                    <div class="half-input-wrapper">
                        <input type="text" id="half-chat-input" class="half-chat-input" placeholder="输入消息..." autocomplete="off">
                        <button class="half-send-btn" id="half-send-btn" type="button">
                            <i class="fas fa-paper-plane"></i>
                        </button>
                    </div>
                </div>
            </div>
            <div id="plan-editor-minibar" class="plan-editor-minibar" style="display: none;">
                <div class="minibar-main-btn" id="minibar-main-btn">
                    <div class="minibar-robot">
                        <i class="fas fa-map-marked-alt"></i>
                    </div>
                    <span class="minibar-pulse"></span>
                </div>
                <div class="minibar-menu" id="minibar-menu">
                    <button type="button" class="minibar-menu-item" id="minibar-half-btn" title="半展开">
                        <i class="fas fa-window-restore"></i>
                        <span>半展开</span>
                    </button>
                    <button type="button" class="minibar-menu-item" id="restore-btn" title="全展开">
                        <i class="fas fa-expand"></i>
                        <span>全展开</span>
                    </button>
                    <button type="button" class="minibar-menu-item close" id="minibar-close-btn" title="关闭">
                        <i class="fas fa-times"></i>
                        <span>关闭</span>
                    </button>
                </div>
                <div class="minibar-hints-container" id="minibar-hints-container"></div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', editorHTML);
        this.initDragAndDrop();
    }

    bindEvents() {
        if (this.eventsBound) return;
        this.eventsBound = true;
        
        this.minibarDragged = false;
        
        document.addEventListener('click', (e) => {
            const target = e.target;
            if (target.closest('#send-message-btn')) this.editor.chat.sendMessage();
            if (target.closest('#half-send-btn')) this.editor.chat.sendHalfMessage();
            if (target.closest('#apply-changes-btn')) this.editor.api.applyChanges();
            if (target.closest('#plan-editor-close') || target.closest('#plan-editor-close-btn')) this.hideEditor();
            if (target.closest('#half-close')) this.hideEditor();
            if (target.closest('#zoom-in-btn')) this.zoomIn();
            if (target.closest('#zoom-out-btn')) this.zoomOut();
            if (target.closest('#minimize-btn')) this.minimize();
            if (target.closest('#half-expand-btn')) this.halfExpand();
            if (target.closest('#half-to-full') || target.closest('#restore-btn')) this.restore();
            if (target.closest('#half-to-mini')) this.minimize();
            if (target.closest('#minibar-close-btn')) this.hideEditor();
            if (target.closest('#minibar-half-btn')) this.halfExpand();
            
            if (target.closest('#minibar-main-btn')) {
                if (!this.minibarDragged) {
                    this.toggleMenu();
                }
                this.minibarDragged = false;
            }
            
            if (!target.closest('#plan-editor-minibar')) {
                this.closeMenu();
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.target.id === 'chat-input' && e.key === 'Enter') {
                e.preventDefault();
                this.editor.chat.sendMessage();
            }
            if (e.target.id === 'half-chat-input' && e.key === 'Enter') {
                e.preventDefault();
                this.editor.chat.sendHalfMessage();
            }
            if (e.key === 'Escape') {
                const modal = document.getElementById('plan-editor-modal');
                const half = document.getElementById('plan-editor-half');
                if (modal && modal.style.display !== 'none') this.hideEditor();
                else if (half && half.style.display !== 'none') this.minimize();
            }
        });
    }

    toggleMenu() {
        const menu = document.getElementById('minibar-menu');
        const minibar = document.getElementById('plan-editor-minibar');
        const mainBtn = document.getElementById('minibar-main-btn');
        
        if (menu && minibar && mainBtn) {
            const isShowing = menu.classList.contains('show');
            
            if (!isShowing) {
                menu.classList.remove('slide-left', 'slide-right');
                
                const btnRect = mainBtn.getBoundingClientRect();
                const screenWidth = window.innerWidth;
                const menuWidth = 230;
                
                const spaceOnLeft = btnRect.left;
                const spaceOnRight = screenWidth - btnRect.right;
                
                let direction;
                if (spaceOnRight >= menuWidth) {
                    direction = 'right';
                    menu.classList.add('slide-right');
                } else if (spaceOnLeft >= menuWidth) {
                    direction = 'left';
                    menu.classList.add('slide-left');
                } else if (spaceOnRight >= spaceOnLeft) {
                    direction = 'right';
                    menu.classList.add('slide-right');
                } else {
                    direction = 'left';
                    menu.classList.add('slide-left');
                }
                
                const bottomPos = window.innerHeight - btnRect.bottom + 24;
                menu.style.bottom = `${bottomPos}px`;
                
                if (direction === 'right') {
                    menu.style.left = `${btnRect.right + 8}px`;
                    menu.style.right = 'auto';
                } else {
                    menu.style.right = `${window.innerWidth - btnRect.left + 8}px`;
                    menu.style.left = 'auto';
                }
            }
            
            menu.classList.toggle('show');
            this.editor.isMenuOpen = menu.classList.contains('show');
        }
    }

    closeMenu() {
        const menu = document.getElementById('minibar-menu');
        if (menu) {
            menu.classList.remove('show');
            this.editor.isMenuOpen = false;
        }
    }

    startHints() {
        this.stopHints();
        this.showHint();
        this.editor.hintTimer = setInterval(() => {
            this.showHint();
        }, 4000);
    }

    stopHints() {
        if (this.editor.hintTimer) {
            clearInterval(this.editor.hintTimer);
            this.editor.hintTimer = null;
        }
        this.hideHint();
    }

    showHint() {
        const container = document.getElementById('minibar-hints-container');
        if (!container || !this.editor.isMinimized) return;

        this.hideHint();

        const hint = this.editor.hints[this.editor.currentHintIndex];
        this.editor.currentHintIndex = (this.editor.currentHintIndex + 1) % this.editor.hints.length;

        const hintEl = document.createElement('div');
        hintEl.className = 'minibar-hint';
        hintEl.id = 'current-minibar-hint';
        hintEl.innerHTML = `<i class="fas ${hint.icon}"></i>${hint.text}`;
        
        const randomOffset = (Math.random() - 0.5) * 40;
        hintEl.style.right = `${randomOffset}px`;
        
        container.appendChild(hintEl);
        
        requestAnimationFrame(() => {
            hintEl.classList.add('show');
        });

        setTimeout(() => {
            this.hideHint();
        }, 3000);
    }

    hideHint() {
        const hintEl = document.getElementById('current-minibar-hint');
        if (hintEl) {
            hintEl.classList.remove('show');
            setTimeout(() => {
                if (hintEl.parentNode) {
                    hintEl.parentNode.removeChild(hintEl);
                }
            }, 400);
        }
    }

    showEditor() {
        this.createEditorUI();
        const modal = document.getElementById('plan-editor-modal');
        const minibar = document.getElementById('plan-editor-minibar');
        const half = document.getElementById('plan-editor-half');
        modal.style.display = 'flex';
        if (minibar) minibar.style.display = 'none';
        if (half) half.style.display = 'none';
        this.editor.isMinimized = false;
        this.editor.isHalfExpanded = false;
        this.editor.saveState();
        this.editor.chat.syncChatToFull();
        requestAnimationFrame(() => {
            modal.style.opacity = '1';
        });
        setTimeout(() => document.getElementById('chat-input').focus(), 100);
    }

    hideEditor() {
        const modal = document.getElementById('plan-editor-modal');
        const minibar = document.getElementById('plan-editor-minibar');
        const half = document.getElementById('plan-editor-half');
        if (modal) modal.style.display = 'none';
        if (minibar) minibar.style.display = 'none';
        if (half) half.style.display = 'none';
        
        this.editor.chatHistory = [];
        this.editor.sessionId = null;
        this.editor.currentPlan = null;
        this.editor.isEditing = false;
        this.editor.isMinimized = false;
        this.editor.isHalfExpanded = false;
        
        localStorage.removeItem(this.editor.STORAGE_KEY);
        
        const chatHistory = document.getElementById('chat-history');
        if (chatHistory) chatHistory.innerHTML = '';
        
        const halfChatArea = document.getElementById('half-chat-area');
        if (halfChatArea) halfChatArea.innerHTML = '';
    }

    zoomIn() {
        const modal = document.getElementById('plan-editor-modal');
        if (modal) {
            const maxWidth = Math.min(1000, window.innerWidth * 0.95);
            const maxHeight = Math.min(800, window.innerHeight * 0.95);
            modal.style.width = `${maxWidth}px`;
            modal.style.height = `${maxHeight}px`;
        }
    }

    zoomOut() {
        const modal = document.getElementById('plan-editor-modal');
        if (modal) {
            modal.style.width = '800px';
            modal.style.height = '650px';
        }
    }

    minimize() {
        const modal = document.getElementById('plan-editor-modal');
        const minibar = document.getElementById('plan-editor-minibar');
        const half = document.getElementById('plan-editor-half');
        if (modal && minibar) {
            modal.style.display = 'none';
            if (half) half.style.display = 'none';
            minibar.style.display = 'flex';
            this.editor.isMinimized = true;
            this.editor.isHalfExpanded = false;
            this.editor.isMenuOpen = false;
            this.closeMenu();
            this.editor.saveState();
            this.startHints();
        }
    }

    halfExpand() {
        const modal = document.getElementById('plan-editor-modal');
        const minibar = document.getElementById('plan-editor-minibar');
        const half = document.getElementById('plan-editor-half');
        if (half) {
            if (modal) modal.style.display = 'none';
            if (minibar) minibar.style.display = 'none';
            half.style.display = 'flex';
            this.editor.isMinimized = false;
            this.editor.isHalfExpanded = true;
            this.editor.isMenuOpen = false;
            this.closeMenu();
            this.stopHints();
            this.editor.saveState();
            this.editor.chat.syncChatToHalf();
        }
    }

    restore() {
        const modal = document.getElementById('plan-editor-modal');
        const minibar = document.getElementById('plan-editor-minibar');
        const half = document.getElementById('plan-editor-half');
        if (modal && minibar) {
            modal.style.display = 'flex';
            minibar.style.display = 'none';
            if (half) half.style.display = 'none';
            this.editor.isMinimized = false;
            this.editor.isHalfExpanded = false;
            this.editor.isMenuOpen = false;
            this.closeMenu();
            this.stopHints();
            this.editor.saveState();
            this.editor.chat.syncChatToFull();
            setTimeout(() => {
                const input = document.getElementById('chat-input');
                if (input) input.focus();
            }, 100);
        }
    }

    restoreFromSavedState() {
        const modal = document.getElementById('plan-editor-modal');
        const minibar = document.getElementById('plan-editor-minibar');
        const halfExpanded = document.getElementById('plan-editor-half');
        
        if (this.editor.chatHistory.length === 0) {
            if (this.editor.isEditing) {
                this.enableApplyButton();
            }
            return;
        }
        
        if (this.editor.isHalfExpanded) {
            if (modal) modal.style.display = 'none';
            if (minibar) minibar.style.display = 'none';
            if (halfExpanded) halfExpanded.style.display = 'flex';
            this.editor.chat.syncChatToHalf();
        } else if (this.editor.isMinimized) {
            if (modal) modal.style.display = 'none';
            if (halfExpanded) halfExpanded.style.display = 'none';
            if (minibar) minibar.style.display = 'flex';
        } else {
            if (minibar) minibar.style.display = 'none';
            if (halfExpanded) halfExpanded.style.display = 'none';
            if (modal) modal.style.display = 'flex';
            this.editor.chat.syncChatToFull();
        }
        
        if (this.editor.isEditing) {
            this.enableApplyButton();
        }
    }

    initDragAndDrop() {
        const modal = document.getElementById('plan-editor-modal');
        const header = document.getElementById('plan-editor-header');
        const halfHeader = document.querySelector('.half-header');
        
        if (modal && header) {
            this.makeDraggable(modal, header);
        }
        
        const half = document.getElementById('plan-editor-half');
        if (half && halfHeader) {
            this.makeDraggable(half, halfHeader);
        }
        
        const minibar = document.getElementById('plan-editor-minibar');
        const minibarBtn = document.getElementById('minibar-main-btn');
        if (minibar && minibarBtn) {
            this.makeMinibarDraggable(minibar, minibarBtn);
        }
    }

    makeMinibarDraggable(element, handle) {
        let isDragging = false;
        let hasMoved = false;
        let startX, startY, initialLeft, initialTop;
        
        handle.addEventListener('mousedown', (e) => {
            isDragging = true;
            hasMoved = false;
            startX = e.clientX;
            startY = e.clientY;
            
            const rect = element.getBoundingClientRect();
            initialLeft = rect.left;
            initialTop = rect.top;
            
            element.style.right = 'auto';
            element.style.bottom = 'auto';
            element.style.left = rect.left + 'px';
            element.style.top = rect.top + 'px';
            
            element.style.transition = 'none';
            e.preventDefault();
        });
        
        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            
            const dx = e.clientX - startX;
            const dy = e.clientY - startY;
            
            if (Math.abs(dx) > 5 || Math.abs(dy) > 5) {
                hasMoved = true;
                this.minibarDragged = true;
            }
            
            element.style.left = `${initialLeft + dx}px`;
            element.style.top = `${initialTop + dy}px`;
        });
        
        document.addEventListener('mouseup', () => {
            if (isDragging) {
                isDragging = false;
                element.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
                
                if (hasMoved) {
                    this.closeMenu();
                }
            }
        });
    }

    makeDraggable(element, handle) {
        let isDragging = false, startX, startY, initialLeft, initialTop;
        
        handle.addEventListener('mousedown', (e) => {
            if(e.target.closest('button')) return;
            isDragging = true;
            startX = e.clientX;
            startY = e.clientY;
            
            const rect = element.getBoundingClientRect();
            
            element.style.transform = 'none';
            element.style.left = rect.left + 'px';
            element.style.top = rect.top + 'px';
            
            initialLeft = rect.left;
            initialTop = rect.top;
            
            element.style.transition = 'none';
        });
        
        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            const dx = e.clientX - startX;
            const dy = e.clientY - startY;
            element.style.left = `${initialLeft + dx}px`;
            element.style.top = `${initialTop + dy}px`;
        });
        
        document.addEventListener('mouseup', () => {
            if (isDragging) {
                isDragging = false;
                element.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
            }
        });
    }

    enableApplyButton() {
        const btn = document.getElementById('apply-changes-btn');
        if (btn) btn.disabled = false;
    }

    showExportOptions() {
        const exportOptionsHtml = `
            <div class="export-options-container">
                <button type="button" id="export-pdf-btn" class="btn btn-primary w-100" onclick="planEditor.api.exportPlanWithWeather()">
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
        this.editor.chat.scrollToBottom();
    }
}

window.PlanEditorUI = PlanEditorUI;
