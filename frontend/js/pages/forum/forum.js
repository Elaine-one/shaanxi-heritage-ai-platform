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
        this.editPostEditor = null;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadPosts();
        this.loadSidebarData();
        this.loadTags();
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
        
        // 热门标签点击
        document.querySelectorAll('.sidebar .tag').forEach(tag => {
            tag.addEventListener('click', (e) => {
                this.handleTagFilter(e.target.dataset.tag);
            });
        });
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
        
        // 显示关注按钮并绑定事件
        const followBtn = postDiv.querySelector('.follow-btn');
        
        // 检查当前用户状态
        this.isLoggedIn().then(isLoggedIn => {
            // 只有当帖子作者不是当前用户时才显示关注按钮
            if (isLoggedIn) {
                const userStr = localStorage.getItem('user');
                if (userStr) {
                    try {
                        const currentUser = JSON.parse(userStr);
                        const currentUserId = currentUser.id || currentUser.userId;
                        
                        if (currentUserId && String(currentUserId) === String(post.author.id)) {
                            followBtn.style.display = 'none';
                        } else {
                            followBtn.style.display = 'inline-block';
                            
                            this.checkFollowStatus(post.author.id).then(isFollowing => {
                                followBtn.textContent = isFollowing ? '已关注' : '关注';
                                followBtn.classList.toggle('following', isFollowing);
                            });
                        }
                    } catch (e) {
                        console.error('解析用户信息失败:', e);
                        followBtn.style.display = 'inline-block';
                    }
                } else {
                    followBtn.style.display = 'inline-block';
                }
            } else {
                followBtn.style.display = 'inline-block';
                followBtn.textContent = '关注';
                followBtn.classList.remove('following');
            }
            
            // 绑定关注按钮事件
            followBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.toggleFollow(post.author.id, followBtn);
            });
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
            
            // 加载公告
            const announcements = await forumAPI.getAnnouncements();
            this.renderAnnouncements(announcements);
            
            // 加载热门标签
            const hotTags = await forumAPI.getHotTags();
            this.renderHotTags(hotTags);
            
            // 加载版规
            const rules = await forumAPI.getRules();
            this.renderRules(rules);
            
        } catch (error) {
            console.error('加载侧边栏数据失败:', error);
        }
    }
    
    renderAnnouncements(announcements) {
        const container = document.getElementById('announcementList');
        if (!container) return;
        
        if (!announcements || announcements.length === 0) {
            container.innerHTML = '<p class="no-data">暂无公告</p>';
            return;
        }
        
        container.innerHTML = announcements.map(item => `
            <div class="announcement-item">
                <a href="${item.link || '#'}">${item.title}</a>
                <span class="announcement-date">${this.formatDate(item.publish_date)}</span>
            </div>
        `).join('');
    }
    
    renderHotTags(tags) {
        const container = document.getElementById('hotTagsList');
        if (!container) return;
        
        if (!tags || tags.length === 0) {
            container.innerHTML = '<p class="no-data">暂无标签</p>';
            return;
        }
        
        container.innerHTML = tags.map(tag => `
            <a href="#" class="tag-item" data-tag="${tag.name}" style="background-color: ${tag.color}20; border-color: ${tag.color};">
                ${tag.name}
            </a>
        `).join('');
        
        // 绑定标签点击事件
        container.querySelectorAll('.tag-item').forEach(tagEl => {
            tagEl.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleTagFilter(e.target.dataset.tag);
            });
        });
    }
    
    renderRules(rules) {
        const container = document.getElementById('rulesList');
        if (!container) return;
        
        if (!rules || rules.length === 0) {
            container.innerHTML = '<li>暂无版规</li>';
            return;
        }
        
        container.innerHTML = rules.map(rule => `
            <li>${rule.content}</li>
        `).join('');
    }
    
    formatDate(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return `${date.getFullYear()}/${String(date.getMonth() + 1).padStart(2, '0')}/${String(date.getDate()).padStart(2, '0')}`;
    }
    
    async loadTags() {
        try {
            const response = await forumAPI.getTags();
            this.renderTagFilter(response.results || response);
        } catch (error) {
            console.error('加载标签失败:', error);
        }
    }
    
    renderTagFilter(tags) {
        const tagFilter = document.getElementById('tagFilter');
        if (!tagFilter) return;
        
        if (!tags || tags.length === 0) {
            return;
        }
        
        // 保留"全部标签"选项
        const allOption = tagFilter.querySelector('option[value=""]');
        tagFilter.innerHTML = '';
        if (allOption) {
            tagFilter.appendChild(allOption);
        } else {
            tagFilter.innerHTML = '<option value="">全部标签</option>';
        }
        
        // 添加从数据库加载的标签
        tags.forEach(tag => {
            const option = document.createElement('option');
            option.value = tag.name;
            option.textContent = tag.name;
            tagFilter.appendChild(option);
        });
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
        
        // 初始化发布编辑器
        if (!this.postEditor) {
            this.postEditor = new PostEditor({
                mode: 'create',
                onPostCreated: () => {
                    this.loadPosts(true);
                }
            });
        }
        
        this.postEditor.show();
    }
    
    showLoginModal() {
        if (typeof LoginModal !== 'undefined') {
            LoginModal.show({
                title: '需要登录',
                message: '您需要登录后才能发布帖子或进行其他操作',
                autoRedirect: true
            });
        } else {
            console.warn('LoginModal not available');
        }
    }
    
    async editPost(postId) {
        try {
            // 初始化编辑编辑器
            if (!this.editPostEditor) {
                this.editPostEditor = new PostEditor({
                    mode: 'edit',
                    onPostUpdated: () => {
                        this.loadPosts(true);
                    }
                });
            }
            
            await this.editPostEditor.setPostData(postId);
            this.editPostEditor.show();
            
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
    
    showError(message) {
        if (typeof NotificationManager !== 'undefined') {
            NotificationManager.error(message);
        } else if (window.apiUtils && window.apiUtils.showErrorMessage) {
            window.apiUtils.showErrorMessage('错误: ' + message);
        } else {
            alert('错误: ' + message);
        }
    }
    
    showSuccess(message) {
        if (typeof NotificationManager !== 'undefined') {
            NotificationManager.success(message);
        } else {
            alert('成功: ' + message);
        }
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
    
    async togglePostLike(postId, likeElement) {
        if (!await this.isLoggedIn()) {
            this.showLoginModal();
            return;
        }
        
        // 防止重复点击
        if (likeElement.classList.contains('processing')) {
            return;
        }
        
        const likeCountSpan = likeElement.querySelector('.like-count');
        const isCurrentlyLiked = likeElement.classList.contains('liked');
        
        try {
            // 设置处理状态
            likeElement.classList.add('processing');
            likeElement.style.opacity = '0.7';
            
            // 调用API
            const result = await forumAPI.togglePostLike(postId);
            
            // 更新UI
            likeElement.classList.toggle('liked', result.is_liked);
            if (likeCountSpan) {
                likeCountSpan.textContent = result.like_count;
            }
            
            // 显示成功通知
            this.showSuccess(result.is_liked ? '点赞成功！' : '取消点赞成功！');
            
        } catch (error) {
            console.error('点赞操作失败:', error);
            this.showError('操作失败，请稍后重试');
        } finally {
            likeElement.classList.remove('processing');
            likeElement.style.opacity = '1';
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