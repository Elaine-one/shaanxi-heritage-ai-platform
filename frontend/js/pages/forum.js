// 论坛页面JavaScript逻辑

class ForumManager {
    constructor() {
        this.currentPage = 1;
        this.currentSort = 'latest_reply';
        this.currentTag = '';
        this.currentSearch = '';
        this.isLoading = false;
        this.hasMorePosts = true;
        this.postEditor = null;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.initializeEditor();
        this.loadPosts();
        this.loadSidebarData();
        this.updateUserIcon();
        this.initScrollToTop();
    }
    
    bindEvents() {
        // 排序选项卡
        document.querySelectorAll('.sort-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.handleSortChange(e.target.dataset.sort);
            });
        });
        
        // 标签筛选
        document.getElementById('tagFilter').addEventListener('change', (e) => {
            this.handleTagFilter(e.target.value);
        });
        
        // 搜索
        document.getElementById('searchInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleSearch(e.target.value);
            }
        });
        
        document.querySelector('.search-btn').addEventListener('click', () => {
            const searchInput = document.getElementById('searchInput');
            this.handleSearch(searchInput.value);
        });
        
        // 发布新帖按钮
        document.getElementById('newPostBtn').addEventListener('click', () => {
            this.showNewPostModal();
        });
        
        // 加载更多
        document.getElementById('loadMoreBtn').addEventListener('click', () => {
            this.loadMorePosts();
        });
        
        // 模态框事件
        this.bindModalEvents();
        
        // 热门标签点击
        document.querySelectorAll('.sidebar .tag').forEach(tag => {
            tag.addEventListener('click', (e) => {
                this.handleTagFilter(e.target.dataset.tag);
            });
        });
    }
    
    bindModalEvents() {
        // 新帖模态框
        const newPostModal = document.getElementById('newPostModal');
        const closeModal = document.getElementById('closeModal');
        const cancelPost = document.getElementById('cancelPost');
        const newPostForm = document.getElementById('newPostForm');
        
        closeModal.addEventListener('click', () => {
            this.hideNewPostModal();
        });
        
        cancelPost.addEventListener('click', () => {
            this.hideNewPostModal();
        });
        
        newPostModal.addEventListener('click', (e) => {
            if (e.target === newPostModal) {
                this.hideNewPostModal();
            }
        });
        
        newPostForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleNewPostSubmit();
        });
        
        // 登录模态框
        const loginModal = document.getElementById('loginModal');
        const closeLoginModal = document.getElementById('closeLoginModal');
        const cancelLogin = document.getElementById('cancelLogin');
        
        closeLoginModal.addEventListener('click', () => {
            this.hideLoginModal();
        });
        
        cancelLogin.addEventListener('click', () => {
            this.hideLoginModal();
        });
        
        loginModal.addEventListener('click', (e) => {
            if (e.target === loginModal) {
                this.hideLoginModal();
            }
        });
        
        // 编辑帖子模态框
        const editPostModal = document.getElementById('editPostModal');
        const closeEditModal = document.getElementById('closeEditModal');
        const cancelEditPost = document.getElementById('cancelEditPost');
        const editPostForm = document.getElementById('editPostForm');
        
        closeEditModal.addEventListener('click', () => {
            this.hideEditPostModal();
        });
        
        cancelEditPost.addEventListener('click', () => {
            this.hideEditPostModal();
        });
        
        editPostModal.addEventListener('click', (e) => {
            if (e.target === editPostModal) {
                this.hideEditPostModal();
            }
        });
        
        editPostForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleEditPostSubmit();
        });
        
        // 字符计数
        document.getElementById('postTitle').addEventListener('input', (e) => {
            this.updateCharCount('titleCount', e.target.value.length);
        });
        
        document.getElementById('editPostTitle').addEventListener('input', (e) => {
            this.updateCharCount('editTitleCount', e.target.value.length);
        });
    }
    
    initializeEditor() {
        // 初始化Quill富文本编辑器
        if (typeof Quill !== 'undefined') {
            this.postEditor = new Quill('#postEditor', {
                theme: 'snow',
                placeholder: '请输入帖子内容...',
                modules: {
                    toolbar: [
                        [{ 'header': [1, 2, 3, false] }],
                        ['bold', 'italic', 'underline', 'strike'],
                        [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                        ['blockquote', 'code-block'],
                        ['link', 'image'],
                        ['clean']
                    ]
                }
            });
            
            // 监听内容变化
            this.postEditor.on('text-change', () => {
                const length = this.postEditor.getLength() - 1; // 减去末尾的换行符
                this.updateCharCount('contentCount', length);
            });
        }
    }
    
    async loadPosts(reset = false) {
        if (this.isLoading) return;
        
        this.isLoading = true;
        
        try {
            const params = {
                sort: this.currentSort,
                tag: this.currentTag,
                search: this.currentSearch,
                page: reset ? 1 : this.currentPage,
                page_size: 10
            };
            
            const response = await forumAPI.getPosts(params);
            
            if (reset) {
                this.currentPage = 1;
                this.renderPosts(response.results, true);
            } else {
                this.renderPosts(response.results, false);
            }
            
            this.hasMorePosts = !!response.next;
            this.updatePaginationInfo(response);
            
        } catch (error) {
            console.error('加载帖子失败:', error);
            this.showError('加载帖子失败，请稍后重试');
        } finally {
            this.isLoading = false;
            this.hideLoadingSkeleton();
        }
    }
    
    renderPosts(posts, reset = false) {
        const postList = document.getElementById('postList');
        
        if (reset) {
            postList.innerHTML = '';
        }
        
        posts.forEach(post => {
            const postElement = this.createPostElement(post);
            postList.appendChild(postElement);
        });
        
        // 更新加载更多按钮状态
        const loadMoreBtn = document.getElementById('loadMoreBtn');
        loadMoreBtn.style.display = this.hasMorePosts ? 'block' : 'none';
    }
    
    createPostElement(post) {
        const postDiv = document.createElement('div');
        postDiv.className = 'post-item';
        postDiv.dataset.postId = post.id;
        
        // 状态标识
        let statusBadges = '';
        if (post.is_pinned) statusBadges += '<span class="status-badge status-pinned">置顶</span>';
        if (post.is_featured) statusBadges += '<span class="status-badge status-featured">精华</span>';
        if (post.is_hot) statusBadges += '<span class="status-badge status-hot">热帖</span>';
        if (post.has_new_reply) statusBadges += '<span class="status-badge status-new-reply">新回复</span>';
        
        // 标签
        const tags = post.tags.map(tag => 
            `<a href="#" class="post-tag" data-tag="${JSON.stringify(tag)}">${tag.name}</a>`
        ).join('');
        
        // 最后回复信息
        const lastReply = post.last_reply ? 
            `<div class="last-reply">
                最后回复：<a href="#" class="last-reply-author">${post.last_reply.author}</a>
                <span class="post-time">${this.formatRelativeTime(post.last_reply.created_at)}</span>
            </div>` : '';
        
        // 快速操作按钮（仅作者或管理员可见）
        // 注意：这里暂时不显示操作按钮，将在异步检查后添加
        const actions = '';
        
        postDiv.innerHTML = `
            <div class="post-status">${statusBadges}</div>
            <div class="post-avatar" onclick="window.location.href='/pages/profile.html?user=${post.author.id || ''}'">
                ${post.author.avatar ? 
                    `<img src="${post.author.avatar}" alt="${post.author.username}">` :
                    post.author.username.charAt(0).toUpperCase()
                }
            </div>
            <div class="post-content">
                <a href="/pages/forum-post.html?id=${post.id || ''}" class="post-title" target="_blank">
                    ${post.title}
                </a>
                <div class="post-meta">
                    <a href="/pages/profile.html?user=${post.author.id || ''}" class="post-author">${post.author.username}</a>
                    <span class="post-time">${this.formatDateTime(post.created_at)}</span>
                    <button class="follow-btn hidden" data-user-id="${post.author.id || ''}">关注</button>
                </div>
                ${lastReply}
                <div class="post-stats">
                    <div class="stat-item">
                        <i class="fas fa-comment"></i>
                        <span>${post.comment_count}</span>
                    </div>
                    <div class="stat-item">
                        <i class="fas fa-eye"></i>
                        <span>${post.view_count}</span>
                    </div>
                    <div class="stat-item">
                        <i class="fas fa-heart"></i>
                        <span>${post.like_count}</span>
                    </div>
                </div>
                <div class="post-tags">${tags}</div>
            </div>
            ${actions}
        `;
        
        // 绑定标签点击事件
        postDiv.querySelectorAll('.post-tag').forEach(tagEl => {
            tagEl.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleTagFilter(e.target.dataset.tag);
            });
        });
        
        // 异步检查当前用户状态并显示关注按钮
        this.isLoggedIn().then(isLoggedIn => {
            if (isLoggedIn) {
                const currentUser = JSON.parse(localStorage.getItem('user'));
                const followBtn = postDiv.querySelector('.follow-btn');
                
                // 只有当帖子作者不是当前用户时才显示关注按钮
                if (currentUser && currentUser.id !== post.author.id) {
                    followBtn.style.display = 'inline-block';
                    
                    // 检查是否已关注
                    this.checkFollowStatus(post.author.id).then(isFollowing => {
                        followBtn.textContent = isFollowing ? '已关注' : '关注';
                        followBtn.classList.toggle('following', isFollowing);
                    });
                    
                    // 绑定关注按钮事件
                    followBtn.addEventListener('click', (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        this.toggleFollow(post.author.id, followBtn);
                    });
                }
            }
        });
        
        // 异步检查权限并添加操作按钮
        this.canEditPost(post).then(canEdit => {
            if (canEdit) {
                const actionsDiv = document.createElement('div');
                actionsDiv.className = 'post-actions';
                actionsDiv.innerHTML = `
                    <button class="action-btn edit-btn" data-post-id="${post.id}">编辑</button>
                    <button class="action-btn delete-btn" data-post-id="${post.id}">删除</button>
                `;
                
                postDiv.appendChild(actionsDiv);
                
                // 绑定操作按钮事件
                actionsDiv.querySelector('.edit-btn').addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.editPost(post.id);
                });
                
                actionsDiv.querySelector('.delete-btn').addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.deletePost(post.id);
                });
            }
        }).catch(error => {
            console.error('检查编辑权限失败:', error);
        });
        
        return postDiv;
    }
    
    async loadSidebarData() {
        try {
            // 加载活跃用户
            const activeUsers = await forumAPI.getActiveUsers();
            this.renderActiveUsers(activeUsers);
            
            // 加载公告（如果有API）
            // const announcements = await forumAPI.getAnnouncements();
            // this.renderAnnouncements(announcements);
            
        } catch (error) {
            console.error('加载侧边栏数据失败:', error);
        }
    }
    
    renderActiveUsers(users) {
        const container = document.getElementById('activeUsers');
        if (!container || !users.length) return;
        
        container.innerHTML = users.slice(0, 10).map((user, index) => `
            <div class="ranking-item">
                <div class="ranking-number ${index < 3 ? 'top-3' : ''}">${index + 1}</div>
                <div class="ranking-avatar">
                    ${user.avatar ? 
                        `<img src="${user.avatar}" alt="${user.username}">` :
                        user.username.charAt(0).toUpperCase()
                    }
                </div>
            </div>
        `).join('');
    }
    
    handleSortChange(sort) {
        // 更新选中状态
        document.querySelectorAll('.sort-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.sort === sort);
        });
        
        this.currentSort = sort;
        this.loadPosts(true);
    }
    
    handleTagFilter(tag) {
        // 更新筛选器选中状态
        const tagFilter = document.getElementById('tagFilter');
        tagFilter.value = tag;
        
        this.currentTag = tag;
        this.loadPosts(true);
    }
    
    handleSearch(query) {
        this.currentSearch = query.trim();
        this.loadPosts(true);
    }
    
    loadMorePosts() {
        if (!this.hasMorePosts || this.isLoading) return;
        
        this.currentPage++;
        this.loadPosts(false);
    }
    
    async showNewPostModal() {
        // 检查登录状态
        if (!(await this.isLoggedIn())) {
            this.showLoginModal();
            return;
        }
        
        const modal = document.getElementById('newPostModal');
        modal.classList.add('show');
        
        // 重置表单
        document.getElementById('newPostForm').reset();
        if (this.postEditor) {
            this.postEditor.setContents([]);
        }
        this.updateCharCount('titleCount', 0);
        this.updateCharCount('contentCount', 0);
    }
    
    hideNewPostModal() {
        const modal = document.getElementById('newPostModal');
        modal.classList.remove('show');
    }
    
    showLoginModal() {
        const modal = document.getElementById('loginModal');
        modal.classList.add('show');
    }
    
    hideLoginModal() {
        const modal = document.getElementById('loginModal');
        modal.classList.remove('show');
    }
    
    hideEditPostModal() {
        document.getElementById('editPostModal').style.display = 'none';
        // 清空表单
        document.getElementById('editPostForm').reset();
        if (this.editPostEditor) {
            this.editPostEditor.setContents([]);
        }
        this.currentEditPostId = null;
    }
    
    async handleNewPostSubmit() {
        // 首先检查登录状态
        const isLoggedIn = await this.isLoggedIn();
        if (!isLoggedIn) {
            this.showError('请先登录后再发布帖子');
            this.showLoginModal();
            return;
        }
        
        const form = document.getElementById('newPostForm');
        const formData = new FormData(form);
        
        const title = formData.get('title').trim();
        const tags = Array.from(document.getElementById('postTags').selectedOptions)
            .map(option => option.value)
            .slice(0, 3); // 最多3个标签
        
        if (!title) {
            this.showError('请输入帖子标题');
            return;
        }
        
        if (title.length < 5) {
            this.showError('帖子标题至少需要5个字符');
            return;
        }
        
        if (!this.postEditor || this.postEditor.getLength() <= 1) {
            this.showError('请输入帖子内容');
            return;
        }
        
        const content = this.postEditor.root.innerHTML;
        const textContent = content.replace(/<[^>]*>/g, '').trim();
        if (textContent.length < 10) {
            this.showError('帖子内容至少需要10个字符（不包括HTML标签）');
            return;
        }
        
        try {
            // 确保获取CSRF token
            try {
                await fetch('/api/auth/csrf/');
                console.log('CSRF token endpoint called for post creation.');
            } catch (csrfError) {
                console.warn('Failed to fetch CSRF token, proceeding with existing cookie if any:', csrfError);
            }
            
            const postData = {
                title,
                content,
                tag_names: tags
            };
            
            console.log('发送的帖子数据:', postData);
            console.log('标题长度:', title.length);
            console.log('内容长度:', content.length);
            console.log('标签数量:', tags.length);
            
            const newPost = await forumAPI.createPost(postData);
            
            this.hideNewPostModal();
            this.showSuccess('帖子发布成功！');
            
            // 重新加载帖子列表
            this.loadPosts(true);
            
        } catch (error) {
            console.error('发布帖子失败:', error);
            if (error.status === 403) {
                this.showError('权限不足，请确保您已登录');
            } else {
                this.showError('发布失败，请稍后重试');
            }
        }
    }
    
    async handleEditPostSubmit() {
        if (!this.currentEditPostId) {
            this.showError('无效的帖子ID');
            return;
        }
        
        const title = document.getElementById('editPostTitle').value.trim();
        const tags = Array.from(document.getElementById('editPostTags').selectedOptions)
            .map(option => option.value)
            .slice(0, 3);
        
        if (!title) {
            this.showError('请输入帖子标题');
            return;
        }
        
        if (title.length < 5) {
            this.showError('帖子标题至少需要5个字符');
            return;
        }
        
        if (!this.editPostEditor || this.editPostEditor.getLength() <= 1) {
            this.showError('请输入帖子内容');
            return;
        }
        
        const content = this.editPostEditor.root.innerHTML;
        const textContent = content.replace(/<[^>]*>/g, '').trim();
        if (textContent.length < 10) {
            this.showError('帖子内容至少需要10个字符（不包括HTML标签）');
            return;
        }
        
        try {
            const postData = {
                title,
                content,
                tag_names: tags
            };
            
            await forumAPI.updatePost(this.currentEditPostId, postData);
            
            this.hideEditPostModal();
            this.showSuccess('帖子更新成功！');
            
            // 重新加载帖子列表
            this.loadPosts(true);
            
        } catch (error) {
            console.error('更新帖子失败:', error);
            if (error.status === 403) {
                this.showError('权限不足，无法编辑此帖子');
            } else {
                this.showError('更新失败，请稍后重试');
            }
        }
    }
    
    async editPost(postId) {
        try {
            // 获取帖子详情
            const post = await forumAPI.getPostDetail(postId);
            
            // 填充编辑表单
            document.getElementById('editPostTitle').value = post.title;
            
            // 初始化编辑器
            if (!this.editPostEditor) {
                this.editPostEditor = new Quill('#editPostContent', {
                    theme: 'snow',
                    modules: {
                        toolbar: [
                            [{ 'header': [1, 2, 3, false] }],
                            ['bold', 'italic', 'underline', 'strike'],
                            [{ 'color': [] }, { 'background': [] }],
                            [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                            ['blockquote', 'code-block'],
                            ['link', 'image'],
                            ['clean']
                        ]
                    },
                    placeholder: '请输入帖子内容...'
                });
            }
            
            // 设置编辑器内容
            this.editPostEditor.root.innerHTML = post.content;
            
            // 设置标签
            const tagSelect = document.getElementById('editPostTags');
            Array.from(tagSelect.options).forEach(option => {
                option.selected = post.tags.includes(option.value);
            });
            
            // 保存当前编辑的帖子ID
            this.currentEditPostId = postId;
            
            // 显示编辑模态框
            document.getElementById('editPostModal').style.display = 'flex';
            
        } catch (error) {
            console.error('获取帖子详情失败:', error);
            this.showError('无法加载帖子信息，请稍后重试');
        }
    }
    
    async deletePost(postId) {
        if (!confirm('确定要删除这个帖子吗？此操作不可撤销。')) {
            return;
        }
        
        try {
            await forumAPI.deletePost(postId);
            this.showSuccess('帖子删除成功');
            
            // 从列表中移除
            const postElement = document.querySelector(`[data-post-id="${postId}"]`);
            if (postElement) {
                postElement.remove();
            }
            
        } catch (error) {
            console.error('删除帖子失败:', error);
            this.showError('删除失败，请稍后重试');
        }
    }
    
    updateCharCount(elementId, count) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = count;
        }
    }
    
    updatePaginationInfo(response) {
        const info = document.getElementById('paginationInfo');
        if (info && response.count) {
            const start = (this.currentPage - 1) * 10 + 1;
            const end = Math.min(this.currentPage * 10, response.count);
            info.textContent = `显示 ${start}-${end} 条，共 ${response.count} 条`;
        }
    }
    
    hideLoadingSkeleton() {
        const skeleton = document.querySelector('.loading-skeleton');
        if (skeleton) {
            skeleton.style.display = 'none';
        }
    }
    
    initScrollToTop() {
        const backToTopBtn = document.getElementById('backToTop');
        
        window.addEventListener('scroll', () => {
            if (window.pageYOffset > 300) {
                backToTopBtn.classList.add('show');
            } else {
                backToTopBtn.classList.remove('show');
            }
        });
        
        backToTopBtn.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
    
    // 工具方法
    /**
     * 检查用户是否已登录（使用后端session验证）
     */
    async isLoggedIn() {
        try {
            // 使用全局的checkLoginStatus函数
            return await window.checkLoginStatus();
        } catch (error) {
            console.error('[forum.js] Error checking login status:', error);
            return false;
        }
    }
    
    async canEditPost(post) {
        try {
            const user = await window.checkBackendAuth();
            if (!user) return false;
            return user.id === post.author.id || user.is_staff;
        } catch (error) {
            console.error('[forum.js] Error checking edit permission:', error);
            return false;
        }
    }
    
    formatDateTime(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    formatRelativeTime(dateString) {
        const now = new Date();
        const date = new Date(dateString);
        const diff = now - date;
        
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);
        
        if (minutes < 1) return '刚刚';
        if (minutes < 60) return `${minutes}分钟前`;
        if (hours < 24) return `${hours}小时前`;
        if (days < 7) return `${days}天前`;
        
        return this.formatDateTime(dateString);
    }
    
    // 使用全局api-utils中的showErrorMessage函数
    showError(message) {
        if (window.apiUtils && window.apiUtils.showErrorMessage) {
            window.apiUtils.showErrorMessage('错误: ' + message);
        } else {
            alert('错误: ' + message);
        }
    }
    
    showSuccess(message) {
        // 简单的成功提示，可以替换为更好的UI组件
        alert('成功: ' + message);
    }
    
    async updateUserIcon() {
        // 使用auth.js中定义的全局updateUserIcon函数
        if (typeof window.updateUserIcon === 'function') {
            await window.updateUserIcon();
        }
    }
    
    async checkFollowStatus(userId) {
        try {
            const response = await fetch(`/api/forum/users/${userId}/follow-status/`, {
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include' // 使用session认证，不再依赖localStorage中的access_token
            });
            
            if (response.ok) {
                const data = await response.json();
                return data.is_following;
            }
            return false;
        } catch (error) {
            console.error('检查关注状态失败:', error);
            return false;
        }
    }
    
    async toggleFollow(userId, button) {
        if (!await this.isLoggedIn()) {
            this.showLoginModal();
            return;
        }
        
        // 防止重复点击
        if (button.disabled) {
            return;
        }
        
        try {
            const isCurrentlyFollowing = button.classList.contains('following');
            const originalText = button.textContent;
            
            // 设置加载状态
            button.disabled = true;
            button.textContent = '处理中...';
            button.style.opacity = '0.7';
            
            const result = await ForumAPI.toggleUserFollow(userId);
            
            // 更新按钮状态
            button.textContent = result.is_following ? '已关注' : '关注';
            button.classList.toggle('following', result.is_following);
            
            // 显示成功通知
            this.showSuccess(
                result.is_following ? '关注成功！' : '取消关注成功！'
            );

        } catch (error) {
            console.error('关注操作失败:', error);
            // 恢复原始状态
            button.textContent = button.classList.contains('following') ? '已关注' : '关注';
            this.showError('操作失败，请稍后重试');
        } finally {
            button.disabled = false;
            button.style.opacity = '1';
        }
    }
    
    getCSRFToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return '';
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    new ForumManager();
});