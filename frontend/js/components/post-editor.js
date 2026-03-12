/**
 * 帖子发布编辑器组件
 * 独立模块，提供丰富的发布功能
 */

class PostEditor {
    constructor(options = {}) {
        this.options = {
            mode: 'create',
            postId: null,
            onPostCreated: null,
            onPostUpdated: null,
            ...options
        };
        
        this.editor = null;
        this.selectedTags = [];
        this.availableTags = [];
        this.isSubmitting = false;
        this.modal = null;
        
        this.init();
    }
    
    async init() {
        await this.loadTags();
        this.createModal();
        this.bindEvents();
        this.initializeQuillEditor();
    }
    
    async loadTags() {
        try {
            const response = await forumAPI.getTags();
            this.availableTags = response.results || response;
        } catch (error) {
            console.error('加载标签失败:', error);
            this.availableTags = [];
        }
    }
    
    createModal() {
        const modalId = this.options.mode === 'create' ? 'postEditorModal' : 'editPostEditorModal';
        const existingModal = document.getElementById(modalId);
        
        if (existingModal) {
            existingModal.remove();
        }
        
        const modalHTML = `
            <div class="post-editor-modal" id="${modalId}">
                <div class="post-editor-overlay"></div>
                <div class="post-editor-container">
                    <div class="post-editor-header">
                        <div class="header-left">
                            <i class="fas fa-edit"></i>
                            <h2>${this.options.mode === 'create' ? '发布新帖' : '编辑帖子'}</h2>
                        </div>
                        <button class="close-btn" type="button">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    
                    <div class="post-editor-body">
                        <form id="postEditorForm" class="post-editor-form">
                            <div class="form-section">
                                <div class="section-title">
                                    <i class="fas fa-heading"></i>
                                    <span>帖子标题</span>
                                </div>
                                <div class="form-group">
                                    <input 
                                        type="text" 
                                        id="postTitle" 
                                        name="title" 
                                        class="form-input title-input"
                                        placeholder="请输入一个吸引人的标题..."
                                        maxlength="100"
                                        required
                                    >
                                    <div class="input-hint">
                                        <span class="char-counter"><span id="titleCount">0</span>/100</span>
                                        <span class="hint-text">建议20-50字，简洁明了</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="form-section">
                                <div class="section-title">
                                    <i class="fas fa-tags"></i>
                                    <span>选择标签</span>
                                    <span class="required-badge">必选</span>
                                </div>
                                <div class="form-group">
                                    <div class="tag-dropdown-container">
                                        <div class="tag-dropdown-header" id="tagDropdownHeader">
                                            <span class="placeholder">请选择标签（最多3个）</span>
                                            <i class="fas fa-chevron-down"></i>
                                        </div>
                                        <div class="tag-dropdown-menu" id="tagDropdownMenu">
                                            <div class="tag-search">
                                                <i class="fas fa-search"></i>
                                                <input type="text" id="tagSearchInput" placeholder="搜索标签...">
                                            </div>
                                            <div class="tag-options" id="tagOptions">
                                                ${this.renderTagOptions()}
                                            </div>
                                        </div>
                                    </div>
                                    <div class="selected-tags-container" id="selectedTagsContainer">
                                    </div>
                                    <div class="input-hint">
                                        <span class="hint-text">选择1-3个相关标签，帮助其他用户快速找到你的帖子</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="form-section">
                                <div class="section-title">
                                    <i class="fas fa-file-alt"></i>
                                    <span>帖子内容</span>
                                    <span class="required-badge">必填</span>
                                </div>
                                <div class="form-group">
                                    <div class="editor-wrapper">
                                        <div id="postContentEditor" class="quill-editor"></div>
                                    </div>
                                    <div class="input-hint">
                                        <span class="char-counter"><span id="contentCount">0</span>/5000</span>
                                        <span class="hint-text">支持富文本格式，至少10个字符</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="form-section optional-section">
                                <div class="section-header" id="optionalSectionHeader">
                                    <div class="section-title">
                                        <i class="fas fa-info-circle"></i>
                                        <span>发布须知</span>
                                    </div>
                                </div>
                                <div class="optional-content" id="optionalContent">
                                    <div class="info-list">
                                        <div class="info-item">
                                            <i class="fas fa-check-circle"></i>
                                            <span>发布后帖子将自动允许评论</span>
                                        </div>
                                        <div class="info-item">
                                            <i class="fas fa-check-circle"></i>
                                            <span>有新回复时系统会自动通知您</span>
                                        </div>
                                        <div class="info-item">
                                            <i class="fas fa-exclamation-triangle"></i>
                                            <span>请遵守社区规范，文明发言</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </form>
                    </div>
                    
                    <div class="post-editor-footer">
                        <div class="footer-left">
                            <button type="button" class="btn btn-secondary" id="saveDraftBtn">
                                <i class="fas fa-save"></i>
                                <span>保存草稿</span>
                            </button>
                        </div>
                        <div class="footer-right">
                            <button type="button" class="btn btn-outline" id="cancelBtn">
                                <span>取消</span>
                            </button>
                            <button type="submit" form="postEditorForm" class="btn btn-primary" id="submitBtn">
                                <i class="fas fa-paper-plane"></i>
                                <span>${this.options.mode === 'create' ? '发布帖子' : '保存修改'}</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.modal = document.getElementById(modalId);
    }
    
    renderTagOptions() {
        if (this.availableTags.length === 0) {
            return '<div class="no-tags">暂无可用标签</div>';
        }
        
        return this.availableTags.map(tag => `
            <div class="tag-option" data-tag-name="${tag.name}" data-tag-color="${tag.color || '#BC2E24'}">
                <div class="tag-checkbox">
                    <i class="fas fa-check"></i>
                </div>
                <div class="tag-info">
                    <span class="tag-name">${tag.name}</span>
                    ${tag.description ? `<span class="tag-description">${tag.description}</span>` : ''}
                </div>
                <div class="tag-color-indicator" style="background-color: ${tag.color || '#BC2E24'}"></div>
            </div>
        `).join('');
    }
    
    bindEvents() {
        const closeBtn = this.modal.querySelector('.close-btn');
        const overlay = this.modal.querySelector('.post-editor-overlay');
        const cancelBtn = this.modal.querySelector('#cancelBtn');
        const form = this.modal.querySelector('#postEditorForm');
        const tagDropdownHeader = this.modal.querySelector('#tagDropdownHeader');
        const tagSearchInput = this.modal.querySelector('#tagSearchInput');
        const optionalSectionHeader = this.modal.querySelector('#optionalSectionHeader');
        const saveDraftBtn = this.modal.querySelector('#saveDraftBtn');
        
        closeBtn.addEventListener('click', () => this.hide());
        overlay.addEventListener('click', () => this.hide());
        cancelBtn.addEventListener('click', () => this.hide());
        form.addEventListener('submit', (e) => this.handleSubmit(e));
        
        tagDropdownHeader.addEventListener('click', () => this.toggleTagDropdown());
        tagSearchInput.addEventListener('input', (e) => this.filterTags(e.target.value));
        optionalSectionHeader.addEventListener('click', () => this.toggleOptionalSection());
        saveDraftBtn.addEventListener('click', () => this.saveDraft());
        
        this.modal.querySelectorAll('.tag-option').forEach(option => {
            option.addEventListener('click', () => this.toggleTag(option));
        });
        
        const titleInput = this.modal.querySelector('#postTitle');
        titleInput.addEventListener('input', (e) => {
            this.modal.querySelector('#titleCount').textContent = e.target.value.length;
        });
        
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.tag-dropdown-container')) {
                this.closeTagDropdown();
            }
        });
    }
    
    initializeQuillEditor() {
        const initQuill = () => {
            if (typeof Quill !== 'undefined') {
                try {
                    this.editor = new Quill('#postContentEditor', {
                        theme: 'snow',
                        placeholder: '分享你的想法、经验或问题...\n\n提示：可以使用工具栏格式化文本，插入图片或链接',
                        modules: {
                            toolbar: [
                                [{ 'header': [1, 2, 3, false] }],
                                ['bold', 'italic', 'underline', 'strike'],
                                [{ 'color': [] }, { 'background': [] }],
                                [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                                [{ 'indent': '-1'}, { 'indent': '+1' }],
                                ['blockquote', 'code-block'],
                                ['link', 'image'],
                                [{ 'align': [] }],
                                ['clean']
                            ]
                        }
                    });
                    
                    this.editor.on('text-change', () => {
                        const length = this.editor.getLength() - 1;
                        this.modal.querySelector('#contentCount').textContent = length;
                    });
                    
                    console.log('Quill编辑器初始化成功');
                } catch (e) {
                    console.error('Quill初始化失败:', e);
                    this.fallbackToTextarea();
                }
            } else {
                console.warn('Quill未加载，重试中...');
                if (!this.quillRetryCount) this.quillRetryCount = 0;
                if (this.quillRetryCount < 10) {
                    this.quillRetryCount++;
                    setTimeout(initQuill, 500);
                } else {
                    console.error('Quill加载失败');
                    this.fallbackToTextarea();
                }
            }
        };
        
        initQuill();
    }
    
    fallbackToTextarea() {
        const editorDiv = this.modal.querySelector('#postContentEditor');
        if (editorDiv) {
            editorDiv.innerHTML = '<textarea class="fallback-textarea" placeholder="分享你的想法、经验或问题..."></textarea>';
            const textarea = editorDiv.querySelector('textarea');
            
            this.editor = {
                root: { innerHTML: '' },
                getLength: () => textarea.value.length + 1,
                getText: () => textarea.value,
                setContents: () => {
                    textarea.value = '';
                    this.editor.root.innerHTML = '';
                },
                on: (event, handler) => {
                    if (event === 'text-change') {
                        textarea.addEventListener('input', handler);
                    }
                }
            };
            
            textarea.addEventListener('input', (e) => {
                this.editor.root.innerHTML = e.target.value;
            });
        }
    }
    
    toggleTagDropdown() {
        const dropdown = this.modal.querySelector('#tagDropdownMenu');
        dropdown.classList.toggle('show');
    }
    
    closeTagDropdown() {
        const dropdown = this.modal.querySelector('#tagDropdownMenu');
        dropdown.classList.remove('show');
    }
    
    filterTags(query) {
        const options = this.modal.querySelectorAll('.tag-option');
        const lowerQuery = query.toLowerCase();
        
        options.forEach(option => {
            const tagName = option.dataset.tagName.toLowerCase();
            const isVisible = tagName.includes(lowerQuery);
            option.style.display = isVisible ? 'flex' : 'none';
        });
    }
    
    toggleTag(optionElement) {
        const tagName = optionElement.dataset.tagName;
        const tagColor = optionElement.dataset.tagColor;
        
        if (this.selectedTags.includes(tagName)) {
            this.selectedTags = this.selectedTags.filter(t => t !== tagName);
            optionElement.classList.remove('selected');
        } else {
            if (this.selectedTags.length >= 3) {
                this.showNotification('最多只能选择3个标签', 'warning');
                return;
            }
            this.selectedTags.push(tagName);
            optionElement.classList.add('selected');
        }
        
        this.updateSelectedTagsDisplay();
        this.updateTagDropdownHeader();
    }
    
    updateSelectedTagsDisplay() {
        const container = this.modal.querySelector('#selectedTagsContainer');
        
        if (this.selectedTags.length === 0) {
            container.innerHTML = '';
            return;
        }
        
        container.innerHTML = this.selectedTags.map(tagName => {
            const tag = this.availableTags.find(t => t.name === tagName);
            const color = tag?.color || '#BC2E24';
            return `
                <div class="selected-tag" style="border-color: ${color}; background-color: ${color}15;">
                    <span style="color: ${color}">${tagName}</span>
                    <button type="button" class="remove-tag" data-tag-name="${tagName}">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
        }).join('');
        
        container.querySelectorAll('.remove-tag').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tagName = e.currentTarget.dataset.tagName;
                const option = this.modal.querySelector(`.tag-option[data-tag-name="${tagName}"]`);
                if (option) {
                    this.toggleTag(option);
                }
            });
        });
    }
    
    updateTagDropdownHeader() {
        const header = this.modal.querySelector('#tagDropdownHeader');
        const placeholder = header.querySelector('.placeholder');
        
        if (this.selectedTags.length === 0) {
            placeholder.textContent = '请选择标签（最多3个）';
        } else {
            placeholder.textContent = `已选择 ${this.selectedTags.length} 个标签`;
        }
    }
    
    toggleOptionalSection() {
        const content = this.modal.querySelector('#optionalContent');
        const icon = this.modal.querySelector('#optionalSectionHeader .toggle-icon');
        
        content.classList.toggle('show');
        icon.classList.toggle('rotate');
    }
    
    async handleSubmit(e) {
        e.preventDefault();
        
        if (this.isSubmitting) return;
        
        const title = this.modal.querySelector('#postTitle').value.trim();
        const content = this.editor.root.innerHTML;
        const textContent = content.replace(/<[^>]*>/g, '').trim();
        
        if (!this.validateForm(title, textContent)) {
            return;
        }
        
        this.isSubmitting = true;
        this.setSubmitButtonState(true);
        
        try {
            const postData = {
                title,
                content,
                tag_names: this.selectedTags
            };
            
            let result;
            if (this.options.mode === 'create') {
                result = await forumAPI.createPost(postData);
                // 发布成功后清除草稿
                localStorage.removeItem('postDraft');
                this.showNotification('帖子发布成功！', 'success');
                if (this.options.onPostCreated) {
                    this.options.onPostCreated(result);
                }
            } else {
                result = await forumAPI.updatePost(this.options.postId, postData);
                this.showNotification('帖子更新成功！', 'success');
                if (this.options.onPostUpdated) {
                    this.options.onPostUpdated(result);
                }
            }
            
            this.hide();
        } catch (error) {
            console.error('提交失败:', error);
            this.showNotification('操作失败，请稍后重试', 'error');
        } finally {
            this.isSubmitting = false;
            this.setSubmitButtonState(false);
        }
    }
    
    validateForm(title, textContent) {
        if (!title) {
            this.showNotification('请输入帖子标题', 'error');
            return false;
        }
        
        if (title.length < 5) {
            this.showNotification('帖子标题至少需要5个字符', 'error');
            return false;
        }
        
        if (this.selectedTags.length === 0) {
            this.showNotification('请至少选择一个标签', 'error');
            return false;
        }
        
        if (textContent.length < 10) {
            this.showNotification('帖子内容至少需要10个字符', 'error');
            return false;
        }
        
        return true;
    }
    
    setSubmitButtonState(loading) {
        const submitBtn = this.modal.querySelector('#submitBtn');
        if (loading) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>提交中...</span>';
        } else {
            submitBtn.disabled = false;
            submitBtn.innerHTML = `<i class="fas fa-paper-plane"></i><span>${this.options.mode === 'create' ? '发布帖子' : '保存修改'}</span>`;
        }
    }
    
    saveDraft() {
        const title = this.modal.querySelector('#postTitle').value.trim();
        const content = this.editor.root.innerHTML;
        
        const draft = {
            title,
            content,
            tags: this.selectedTags,
            savedAt: new Date().toISOString()
        };
        
        localStorage.setItem('postDraft', JSON.stringify(draft));
        this.showNotification('草稿已保存', 'success');
    }
    
    loadDraft() {
        const draftStr = localStorage.getItem('postDraft');
        if (!draftStr) return;
        
        try {
            const draft = JSON.parse(draftStr);
            
            if (draft.title) {
                this.modal.querySelector('#postTitle').value = draft.title;
                this.modal.querySelector('#titleCount').textContent = draft.title.length;
            }
            
            if (draft.content && this.editor) {
                this.editor.root.innerHTML = draft.content;
            }
            
            if (draft.tags && draft.tags.length > 0) {
                draft.tags.forEach(tagName => {
                    const option = this.modal.querySelector(`.tag-option[data-tag-name="${tagName}"]`);
                    if (option) {
                        this.toggleTag(option);
                    }
                });
            }
            
            this.showNotification('草稿已加载', 'info');
        } catch (error) {
            console.error('加载草稿失败:', error);
        }
    }
    
    show() {
        if (this.modal) {
            this.modal.classList.add('show');
            document.body.style.overflow = 'hidden';
            
            if (this.options.mode === 'create') {
                this.loadDraft();
            }
        }
    }
    
    hide() {
        if (this.modal) {
            this.modal.classList.remove('show');
            document.body.style.overflow = '';
            this.reset();
        }
    }
    
    reset() {
        const form = this.modal.querySelector('#postEditorForm');
        form.reset();
        
        if (this.editor) {
            if (this.editor.setContents) {
                this.editor.setContents([]);
            }
            this.editor.root.innerHTML = '';
        }
        
        this.selectedTags = [];
        this.updateSelectedTagsDisplay();
        this.updateTagDropdownHeader();
        
        this.modal.querySelectorAll('.tag-option').forEach(option => {
            option.classList.remove('selected');
        });
        
        this.modal.querySelector('#titleCount').textContent = '0';
        this.modal.querySelector('#contentCount').textContent = '0';
    }
    
    showNotification(message, type = 'info') {
        if (typeof NotificationManager !== 'undefined') {
            NotificationManager[type](message);
        } else {
            alert(message);
        }
    }
    
    async setPostData(postId) {
        try {
            const post = await forumAPI.getPostDetail(postId);
            
            this.modal.querySelector('#postTitle').value = post.title;
            this.modal.querySelector('#titleCount').textContent = post.title.length;
            
            if (this.editor) {
                this.editor.root.innerHTML = post.content;
            }
            
            this.selectedTags = post.tags.map(tag => tag.name);
            this.updateSelectedTagsDisplay();
            this.updateTagDropdownHeader();
            
            this.selectedTags.forEach(tagName => {
                const option = this.modal.querySelector(`.tag-option[data-tag-name="${tagName}"]`);
                if (option) {
                    option.classList.add('selected');
                }
            });
            
            this.options.postId = postId;
        } catch (error) {
            console.error('加载帖子数据失败:', error);
            this.showNotification('无法加载帖子信息', 'error');
        }
    }
}

if (typeof window !== 'undefined') {
    window.PostEditor = PostEditor;
}
