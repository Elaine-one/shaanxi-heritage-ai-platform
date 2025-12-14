// 用户创作页面JavaScript

class UserCreation {
    constructor() {
        this.currentPage = 1;
        this.pageSize = 10;
        this.currentSort = 'latest';
        this.currentCategory = 'all';
        this.creations = [];
        this.isLoading = false;
        this.hasMore = true;
        
        this.init();
    }

    async init() {
        // 等待checkLoginStatus函数可用
        let isLoggedIn = false;
        try {
            // 使用异步的checkLoginStatus函数
            if (typeof window.checkLoginStatus === 'function') {
                isLoggedIn = await window.checkLoginStatus();
            }
        } catch (error) {
            console.warn('检查登录状态失败:', error);
            isLoggedIn = false;
        }
        
        // 初始化事件监听器（无论是否登录都需要）
        this.initEventListeners();
        
        // 初始化统计数据实时更新（只在init中调用一次，避免重复创建定时器）
        this.initStatsUpdate();
        
        if (!isLoggedIn) {
            this.showLoginRequired();
            return;
        }

        // 加载统计数据
        await this.loadStatistics();
        
        // 加载用户个人统计数据（如果是创作者中心页面）
        if (window.location.pathname.includes('creation-center')) {
            await this.loadUserStatistics();
        }
        
        // 加载初始数据
        await this.loadCreations();
        
        // 加载热门标签
        await this.loadTrendingTags();
        
        // 加载非遗项目列表
        await this.loadHeritageList();
    }

    initEventListeners() {
        // 防止重复绑定事件监听器
        if (this.eventListenersBound) {
            console.log('事件监听器已经绑定，跳过');
            return;
        }
        this.eventListenersBound = true;
        
        // 发布创作按钮
        document.getElementById('createBtn').addEventListener('click', async () => {
            const isLoggedIn = await window.checkLoginStatus();
            if (!isLoggedIn) {
                this.showLoginPrompt('发布创作');
                return;
            }
            this.openCreationModal();
        });

        // 创作者中心按钮
        document.getElementById('creatorCenterBtn').addEventListener('click', async () => {
            const isLoggedIn = await window.checkLoginStatus();
            if (!isLoggedIn) {
                this.showLoginPrompt('访问创作者中心');
                return;
            }
            this.openCreatorCenter();
        });

        // 模态框关闭按钮
        document.getElementById('closeModal').addEventListener('click', () => {
            this.closeCreationModal();
        });

        // 取消按钮
        document.getElementById('cancelBtn').addEventListener('click', () => {
            this.closeCreationModal();
        });

        // 提交按钮
        document.getElementById('submitBtn').addEventListener('click', () => {
            this.submitCreation();
        });

        // 文件上传预览
        document.getElementById('creationFile').addEventListener('change', (e) => {
            this.previewFile(e.target.files[0]);
        });

        // 标签输入
        document.getElementById('tagInput').addEventListener('input', (e) => {
            this.handleTagInput(e.target.value);
        });

        // 排序按钮
        document.querySelectorAll('.sort-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.handleSortChange(e.target.dataset.sort);
            });
        });

        // 分类按钮
        document.querySelectorAll('.category-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.handleCategoryChange(e.target.dataset.category);
            });
        });

        // 加载更多按钮
        document.getElementById('loadMoreBtn').addEventListener('click', () => {
            this.loadMoreCreations();
        });

        // 点击模态框外部关闭
        document.getElementById('creationModal').addEventListener('click', (e) => {
            if (e.target.id === 'creationModal') {
                this.closeCreationModal();
            }
        });
    }

    async loadCreations() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoadingSkeleton();

        try {
            // 构建查询参数
            let queryParams = new URLSearchParams({
                page: this.currentPage,
                size: this.pageSize,
                sort: this.currentSort,
                category: this.currentCategory,
                status: 'published'
            });
            
            // 添加标签筛选
            if (this.currentTag) {
                queryParams.append('tag', this.currentTag);
            }
            
            // 加载创作内容
            const response = await fetch(`/api/creations/?${queryParams.toString()}`);
            
            if (!response.ok) {
                throw new Error('加载创作内容失败');
            }

            const data = await response.json();
            let creations = data.results || [];
            
            // 如果用户已登录，获取用户的点赞状态
            if (await window.checkLoginStatus()) {
                try {
                    // 使用正确的API端点获取用户的点赞记录
                    const likesResponse = await fetch('/api/creation-likes/');
                    if (likesResponse.ok) {
                        const likedCreations = await likesResponse.json();
                        const likedIds = new Set();
                        
                        // 处理返回的数据格式，兼容多种可能的结构
                        const likesData = Array.isArray(likedCreations) ? likedCreations : (likedCreations.results || []);
                        likesData.forEach(item => {
                            // 从点赞记录中获取创作ID
                            const creationId = item.creation?.id || item.creation_id;
                            if (creationId) {
                                likedIds.add(creationId);
                            }
                        });
                        
                        // 将点赞状态合并到创作数据中
                        if (likedIds.size > 0) {
                            creations = creations.map(creation => ({
                                ...creation,
                                is_liked: likedIds.has(creation.id),
                                liked: likedIds.has(creation.id)
                            }));
                        }
                    }
                } catch (error) {
                    console.error('获取点赞状态失败:', error);
                    // 即使获取点赞状态失败，也继续渲染创作列表
                }
            }
            
            if (this.currentPage === 1) {
                this.creations = creations;
            } else {
                this.creations = [...this.creations, ...creations];
            }
            
            this.hasMore = data.next !== null;
            this.renderCreations();
            
        } catch (error) {
            console.error('加载创作内容失败:', error);
            this.showError('加载创作内容失败，请稍后重试');
        } finally {
            this.isLoading = false;
            this.hideLoadingSkeleton();
        }
    }

    async loadMoreCreations() {
        if (this.isLoading || !this.hasMore) return;
        
        this.currentPage++;
        await this.loadCreations();
    }

    async loadTrendingTags() {
        // 限制热门标签的请求频率，避免频繁请求
        if (this.lastTagsRequest && Date.now() - this.lastTagsRequest < 60000) {
            console.log('热门标签请求过于频繁，跳过本次请求');
            return;
        }
        
        this.lastTagsRequest = Date.now();
        
        try {
            const response = await fetch('/api/creations/trending_tags/');
            
            if (response.ok) {
                const tags = await response.json();
                this.renderTrendingTags(tags);
            }
        } catch (error) {
            console.error('加载热门标签失败:', error);
        }
    }

    async loadHeritageList() {
        try {
            // 使用heritageAPI.getAllItems获取非遗项目列表
            const response = await window.heritageAPI.getAllItems();
            const heritageList = response.results || [];
            this.renderHeritageSelect(heritageList);
        } catch (error) {
            console.error('加载非遗项目列表失败:', error);
        }
    }

    async loadStatistics() {
        try {
            // 加载创作统计数据
            const response = await fetch('/api/creations/statistics/');
            
            if (response.ok) {
                const stats = await response.json();
                this.renderStatistics(stats);
            }
        } catch (error) {
            console.error('加载统计数据失败:', error);
            // 设置默认值
            this.renderStatistics({ total: 0, today: 0 });
        }
    }

    async loadUserStatistics() {
        console.log('loadUserStatistics方法已禁用，避免大量重复请求');
        // 直接返回，不发送任何API请求
        return;
    }

    renderStatistics(stats) {
        console.log('更新统计数据:', stats);
        
        const totalElement = document.getElementById('totalCreations');
        const todayElement = document.getElementById('todayCreations');
        const viewsElement = document.getElementById('totalViews');
        const likesElement = document.getElementById('totalLikes');
        
        if (totalElement) {
            totalElement.textContent = stats.total || stats.total_creations || 0;
        }
        
        if (todayElement) {
            todayElement.textContent = stats.today || 0;
        }
        
        if (viewsElement) {
            viewsElement.textContent = stats.total_views || stats.views || 0;
        }
        
        if (likesElement) {
            likesElement.textContent = stats.total_likes || stats.likes || 0;
        }
        
        // 确保创作卡片中的统计数据也得到更新
        this.creations.forEach(creation => {
            const viewsEl = document.querySelector(`.stat-views[data-id="${creation.id}"]`);
            const likesEl = document.querySelector(`.stat-likes[data-id="${creation.id}"]`);
            const commentsEl = document.querySelector(`.stat-comments[data-id="${creation.id}"]`);
            
            if (viewsEl) {
                viewsEl.textContent = creation.view_count || 0;
            }
            if (likesEl) {
                likesEl.textContent = creation.like_count || 0;
            }
            if (commentsEl) {
                commentsEl.textContent = creation.comment_count || 0;
            }
        });
    }

    renderUserStatistics(userStats) {
        // 这里可以添加用户个人统计数据的渲染逻辑
        // 如果有专门的个人统计显示区域
        console.log('用户个人统计数据:', userStats);
    }

    renderCreations() {
        const container = document.getElementById('creationList');
        
        if (this.creations.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-video"></i>
                    <h3>暂无创作内容</h3>
                    <p>成为第一个分享非遗创作的用户吧！</p>
                    <button class="create-btn" onclick="userCreation.handleEmptyStateCreate()">
                        发布创作
                    </button>
                </div>
            `;
            return;
        }

        // 获取当前用户信息
        const currentUser = window.getCurrentUser ? window.getCurrentUser() : null;

        container.innerHTML = this.creations.map(creation => {
            // 检查是否有管理权限（管理员或作者本人）
            const canManage = currentUser && (currentUser.is_staff || (creation.user && creation.user.id === currentUser.id));
            
            return `
            <div class="creation-card" data-id="${creation.id}">
                <div class="creation-media">
                    ${this.renderMedia(creation)}
                    <div class="creation-type-badge">${this.getTypeLabel(creation.type)}</div>
                    ${canManage ? `<div class="creation-manage-badge" style="position: absolute; top: 10px; right: 10px; background: rgba(0,0,0,0.7); color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">
                        ${currentUser.is_staff ? '管理员' : '我的创作'}
                    </div>` : ''}
                </div>
                <div class="creation-content">
                    <h3 class="creation-title">${creation.title}</h3>
                    <p class="creation-description">${creation.description}</p>
                    
                    <div class="creation-meta">
                        <div class="creation-user">
                            <img src="${creation.user && creation.user.avatar ? creation.user.avatar : '../static/common/default-avatar.png'}" 
                                 alt="${creation.user && creation.user.display_name ? creation.user.display_name : creation.user ? creation.user.username : '用户'}" 
                                 class="user-avatar"
                                 onerror="this.src='../static/common/default-avatar.png'">
                            <div class="user-info">
                                <h4>${creation.user && creation.user.display_name ? creation.user.display_name : creation.user ? creation.user.username : '用户'}</h4>
                                <span>${this.formatDate(creation.created_at)}</span>
                            </div>
                        </div>
                        <div class="creation-stats">
                            <div class="stat">
                                <i class="fas fa-eye"></i>
                                <span class="stat-views" data-id="${creation.id}">${creation.view_count || 0}</span>
                            </div>
                            <div class="stat">
                                <i class="fas fa-heart"></i>
                                <span class="stat-likes" data-id="${creation.id}">${creation.like_count || 0}</span>
                            </div>
                            <div class="stat">
                                <i class="fas fa-comment"></i>
                                <span class="stat-comments" data-id="${creation.id}">${creation.comment_count || 0}</span>
                            </div>
                        </div>
                    </div>
                    
                    ${creation.tags && creation.tags.length > 0 ? `
                        <div class="creation-tags">
                            ${creation.tags.map(tag => `<span class="creation-tag" onclick="userCreation.filterByTag('${tag.name}')">#${tag.name}</span>`).join('')}
                        </div>
                    ` : ''}
                    
                    <div class="creation-actions">
                        <button class="action-btn like ${creation.is_liked || creation.liked || false ? 'active' : ''}" 
                                onclick="userCreation.handleLike(${creation.id})">
                            <i class="fas fa-heart"></i>
                            ${creation.is_liked || creation.liked || false ? '已点赞' : '点赞'}
                        </button>
                        <button class="action-btn" onclick="userCreation.handleComment(${creation.id})">
                            <i class="fas fa-comment"></i>
                            评论
                        </button>
                        <button class="action-btn" onclick="userCreation.handleShare(${creation.id})">
                            <i class="fas fa-share"></i>
                            分享
                        </button>
                        ${canManage ? `
                        <button class="action-btn manage-btn" onclick="userCreation.handleManage(${creation.id})" style="background: #ff6b6b;">
                            <i class="fas fa-cog"></i>
                            管理
                        </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `}).join('');
        
        // 初始化视口监控
        this.initViewportMonitoring();
    }

    renderMedia(creation) {
        // 处理媒体URL，确保正确的路径格式
        const processMediaUrl = (url) => {
            if (!url) return null;
            if (url.startsWith('http')) return url;
            if (url.startsWith('/media/')) return url;
            if (url.startsWith('media/')) return `/${url}`;
            return `/media/${url}`;
        };
        
        switch (creation.type) {
            case 'video':
                const videoUrl = processMediaUrl(creation.video_url);
                const posterUrl = processMediaUrl(creation.thumbnail) || processMediaUrl(creation.image_url);
                return `
                    <video class="creation-video" controls poster="${posterUrl || '/static/common/default-video.jpg'}" style="width: 100%; height: 100%; object-fit: cover;">
                        <source src="${videoUrl}" type="video/mp4">
                        <source src="${videoUrl}" type="video/webm">
                        您的浏览器不支持视频播放
                    </video>
                `;
            case 'photo':
                const imageUrl = processMediaUrl(creation.image_url);
                return `
                    <img class="creation-image" src="${imageUrl || '/static/common/default-image.jpg'}" 
                         alt="${creation.title || '创作图片'}" 
                         style="width: 100%; height: 100%; object-fit: cover;"
                         onerror="this.src='/static/common/default-image.jpg'">
                `;
            case 'music':
                const audioUrl = processMediaUrl(creation.audio_url);
                return `
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); height: 100%; display: flex; align-items: center; justify-content: center; flex-direction: column;">
                        <i class="fas fa-music" style="font-size: 3rem; color: white; margin-bottom: 10px;"></i>
                        ${audioUrl ? `<audio controls style="width: 90%;"><source src="${audioUrl}" type="audio/mpeg">您的浏览器不支持音频播放</audio>` : ''}
                    </div>
                `;
            default:
                return `
                    <div style="background: #f8f9fa; height: 100%; display: flex; align-items: center; justify-content: center;">
                        <i class="fas fa-file-alt" style="font-size: 3rem; color: #666;"></i>
                    </div>
                `;
        }
    }

    renderTrendingTags(tags) {
        const container = document.getElementById('trendingTags');
        // 只显示前5个热门标签
        const topTags = tags.slice(0, 5);
        container.innerHTML = topTags.map(tag => `
            <span class="tag" onclick="userCreation.filterByTag('${tag.name}')">#${tag.name}</span>
        `).join('');
    }

    renderHeritageSelect(heritageList) {
        const select = document.getElementById('heritageSelect');
        select.innerHTML = '<option value="">请选择关联的非遗项目</option>' + 
            heritageList.map(heritage => `
                <option value="${heritage.id}">${heritage.name}</option>
            `).join('');
    }

    openCreationModal() {
        // 检查用户是否已登录
        if (!window.checkLoginStatus()) {
            this.showLoginPrompt('发布创作');
            return;
        }
        
        document.getElementById('creationModal').style.display = 'block';
        this.resetModalForm();
    }

    closeCreationModal() {
        document.getElementById('creationModal').style.display = 'none';
        this.resetModalForm();
    }

    openCreatorCenter() {
        // 检查用户是否已登录
        if (!window.checkLoginStatus()) {
            this.showLoginPrompt('访问创作者中心');
            return;
        }
        
        // 跳转到创作者中心页面
        window.location.href = 'creation-center.html';
    }

    async handleEmptyStateCreate() {
        // 检查用户是否已登录
        if (!window.checkLoginStatus()) {
            this.showLoginPrompt('发布创作');
            return;
        }
        this.openCreationModal();
    }

    resetModalForm() {
        document.getElementById('creationTitle').value = '';
        document.getElementById('creationContent').value = '';
        document.getElementById('creationFile').value = '';
        document.getElementById('fileName').textContent = '未选择文件';
        document.getElementById('filePreview').innerHTML = '';
        document.getElementById('selectedTags').innerHTML = '';
        document.getElementById('heritageSelect').value = '';
    }

    previewFile(file) {
        if (!file) return;

        const fileName = document.getElementById('fileName');
        const preview = document.getElementById('filePreview');
        
        fileName.textContent = file.name;
        preview.innerHTML = '';

        // 添加文件验证提示
        let validationMessage = '';
        
        // 文件大小验证（50MB限制）
        const maxSize = 50 * 1024 * 1024; // 50MB
        if (file.size > maxSize) {
            validationMessage = '<div style="color: red;">❌ 文件大小超过50MB限制</div>';
        }
        
        // 文件类型验证
        const allowedTypes = {
            'video': ['video/mp4', 'video/avi', 'video/quicktime'],
            'photo': ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'],
            'music': ['audio/mpeg', 'audio/wav']
        };
        
        let fileType = 'article';
        if (file.type.startsWith('video/')) {
            fileType = 'video';
        } else if (file.type.startsWith('image/')) {
            fileType = 'photo';
        } else if (file.type.startsWith('audio/')) {
            fileType = 'music';
        }
        
        if (fileType !== 'article' && allowedTypes[fileType]) {
            if (!allowedTypes[fileType].includes(file.type)) {
                const supportedFormats = allowedTypes[fileType].map(t => t.split('/')[1]).join(', ');
                validationMessage += `<div style="color: red;">❌ 不支持的格式。${this.getTypeLabel(fileType)}类型支持: ${supportedFormats}</div>`;
            } else {
                validationMessage += `<div style="color: green;">✅ 文件格式验证通过</div>`;
            }
        }
        
        // 显示文件信息
        const fileSize = (file.size / (1024 * 1024)).toFixed(2);
        const fileInfo = `<div style="margin-bottom: 10px;">
            <strong>文件信息:</strong><br>
            名称: ${file.name}<br>
            大小: ${fileSize}MB<br>
            类型: ${file.type}
            ${validationMessage}
        </div>`;
        
        preview.innerHTML = fileInfo;

        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (e) => {
                preview.innerHTML = fileInfo + `<img src="${e.target.result}" alt="预览" style="max-width: 100%; max-height: 300px;">`;
            };
            reader.readAsDataURL(file);
        } else if (file.type.startsWith('video/')) {
            const reader = new FileReader();
            reader.onload = (e) => {
                preview.innerHTML = fileInfo + `
                    <video controls style="width: 100%; max-height: 300px;">
                        <source src="${e.target.result}" type="${file.type}">
                        您的浏览器不支持视频播放
                    </video>
                `;
            };
            reader.readAsDataURL(file);
        }
    }

    handleTagInput(value) {
        // 实现标签建议功能
        const suggestedTags = document.getElementById('suggestedTags');
        
        if (value.length > 1) {
            // 这里可以调用API获取标签建议
            suggestedTags.style.display = 'block';
            suggestedTags.innerHTML = `
                <div class="suggested-tag" onclick="userCreation.addTag('${value}')">添加 "${value}"</div>
            `;
        } else {
            suggestedTags.style.display = 'none';
        }
    }

    addTag(tagName) {
        const selectedTags = document.getElementById('selectedTags');
        const tagInput = document.getElementById('tagInput');
        
        if (!tagName.trim()) return;
        
        selectedTags.innerHTML += `
            <span class="selected-tag">
                ${tagName}
                <span class="remove-tag" onclick="this.parentElement.remove()">×</span>
            </span>
        `;
        
        tagInput.value = '';
        document.getElementById('suggestedTags').style.display = 'none';
    }

    async submitCreation() {
        const title = document.getElementById('creationTitle').value.trim();
        const content = document.getElementById('creationContent').value.trim();
        const file = document.getElementById('creationFile').files[0];
        const heritageId = document.getElementById('heritageSelect').value;
        
        // 根据文件类型自动识别创作类型
        let type = 'article'; // 默认为文章
        if (file) {
            const fileType = file.type;
            if (fileType.startsWith('video/')) {
                type = 'video';
            } else if (fileType.startsWith('image/')) {
                type = 'photo';
            } else if (fileType.startsWith('audio/')) {
                type = 'music';
            }
        }
        
        // 获取选中的标签
        const selectedTags = Array.from(document.querySelectorAll('.selected-tag'))
            .map(tag => tag.textContent.replace('×', '').trim());

        // 验证表单
        if (!title || title.length < 5 || title.length > 50) {
            this.showError('标题长度应在5-50字之间');
            return;
        }

        if (!content) {
            this.showError('请填写创作内容');
            return;
        }

        // 文件大小验证（50MB限制）
        if (file) {
            const maxSize = 50 * 1024 * 1024; // 50MB
            if (file.size > maxSize) {
                this.showError('文件大小不能超过50MB');
                return;
            }
            
            // 文件类型验证
            const allowedTypes = {
                'video': ['video/mp4', 'video/avi', 'video/quicktime'],
                'photo': ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'],
                'music': ['audio/mpeg', 'audio/wav']
            };
            
            let fileType = 'article';
            if (file.type.startsWith('video/')) {
                fileType = 'video';
            } else if (file.type.startsWith('image/')) {
                fileType = 'photo';
            } else if (file.type.startsWith('audio/')) {
                fileType = 'music';
            }
            
            if (fileType !== 'article' && allowedTypes[fileType]) {
                if (!allowedTypes[fileType].includes(file.type)) {
                    this.showError(`不支持的文件格式。${this.getTypeLabel(fileType)}类型支持: ${allowedTypes[fileType].map(t => t.split('/')[1]).join(', ')}`);
                    return;
                }
            }
        }

        try {
            // 获取CSRF token
            const csrfToken = await this.getCSRFToken();
            if (!csrfToken) {
                throw new Error('无法获取安全令牌，请刷新页面重试');
            }

            const formData = new FormData();
            formData.append('title', title);
            formData.append('description', content);
            formData.append('type', type);
            formData.append('tags', JSON.stringify(selectedTags));
            
            if (heritageId) {
                formData.append('heritage_id', heritageId);
            }
            
            if (file) {
                formData.append('media_file', file);
            }

            const response = await fetch('/api/creations/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrfToken
                }
            });

            if (response.ok) {
                this.showSuccess('创作发布成功！');
                this.closeCreationModal();
                this.refreshCreations();
                // 重新加载统计数据
                await this.loadStatistics();
                
                // 通知创作者中心更新数据（如果当前在创作者中心页面）
                if (window.location.pathname.includes('creation-center')) {
                    console.log('当前在创作者中心页面，通知更新数据');
                    // 如果creationCenter实例存在，调用其refresh方法
                    if (window.creationCenter) {
                        window.creationCenter.refreshAllData();
                    }
                }
            } else {
                const error = await response.json();
                throw new Error(error.message || '发布失败');
            }

        } catch (error) {
            console.error('发布创作失败:', error);
            this.showError('发布失败：' + error.message);
        }
    }

    async handleLike(creationId) {
        // 检查用户是否已登录
        if (!window.checkLoginStatus()) {
            this.showLoginPrompt('点赞');
            return;
        }
        
        try {
            // 获取CSRF token
            const csrfToken = await this.getCSRFToken();
            if (!csrfToken) {
                console.error('无法获取安全令牌，点赞失败');
                this.showError('无法获取安全令牌，请刷新页面后重试');
                return;
            }

            console.log('发送点赞请求，creationId:', creationId, 'CSRF Token:', csrfToken);

            const response = await fetch(`/api/creation-likes/toggle/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ creation_id: creationId })
            });

            console.log('点赞响应状态:', response.status);

            if (response.ok) {
                const result = await response.json();
                console.log('点赞成功，结果:', result);
                
                // 更新UI显示
                    const card = document.querySelector(`[data-id="${creationId}"]`);
                    if (card) {
                        const likeBtn = card.querySelector('.action-btn.like');
                        const likeCount = card.querySelector('.stat-likes');
                        
                        if (likeBtn) {
                            likeBtn.classList.toggle('active', result.liked);
                            likeBtn.innerHTML = `<i class="fas fa-heart"></i> ${result.liked ? '已点赞' : '点赞'}`;
                        }
                        
                        // 更新点赞数
                        if (likeCount) {
                            likeCount.textContent = result.like_count || 0;
                        }
                    }
                    
                    // 更新本地创作数据
                    const creationIndex = this.creations.findIndex(c => c.id === creationId);
                    if (creationIndex !== -1) {
                        this.creations[creationIndex].is_liked = result.liked;
                        this.creations[creationIndex].liked = result.liked;
                        this.creations[creationIndex].like_count = result.like_count;
                    }
                this.showSuccess(result.message || (result.liked ? '点赞成功' : '取消点赞成功'));
                // 重新加载统计数据
                await this.loadStatistics();
                
                // 通知创作者中心更新数据（如果当前在创作者中心页面）
                if (window.location.pathname.includes('creation-center')) {
                    console.log('当前在创作者中心页面，通知更新数据');
                    // 如果creationCenter实例存在，调用其refresh方法
                    if (window.creationCenter) {
                        window.creationCenter.refreshAllData();
                    }
                }
            } else {
                const errorText = await response.text();
                console.error('点赞失败响应:', errorText);
                let errorMessage = '点赞失败';
                try {
                    const errorData = JSON.parse(errorText);
                    errorMessage = errorData.error || errorData.message || '点赞失败';
                } catch (e) {
                    errorMessage = `点赞失败 (${response.status})`;
                }
                this.showError(errorMessage);
            }
        } catch (error) {
            console.error('点赞失败:', error);
            this.showError('点赞失败，请检查网络连接后重试');
        }
    }

    async handleComment(creationId) {
        // 检查用户是否已登录
        if (!window.checkLoginStatus()) {
            this.showLoginPrompt('评论');
            return;
        }
        
        try {
            // 获取该创作的评论列表
            const response = await fetch(`/api/creation-comments/?creation_id=${creationId}`);
            if (!response.ok) {
                throw new Error('获取评论失败');
            }
            const data = await response.json();
            
            // 检查返回的数据格式，确保是数组
            let comments = [];
            if (Array.isArray(data)) {
                comments = data;
            } else if (data && Array.isArray(data.results)) {
                // 如果返回的是分页格式，提取results数组
                comments = data.results;
            } else if (data && data.comments && Array.isArray(data.comments)) {
                // 如果返回的是包含comments字段的对象
                comments = data.comments;
            } else {
                console.warn('评论API返回未知格式:', data);
                comments = [];
            }
            
            // 显示评论管理模态框
            this.showCommentsModal(comments, creationId);
        } catch (error) {
            console.error('获取评论失败:', error);
            this.showError('获取评论失败，请稍后重试');
        }
    }

    showCommentsModal(comments, creationId) {
        // 创建评论管理模态框
        const modal = document.createElement('div');
        modal.className = 'comments-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        `;
        
        const currentUser = window.getCurrentUser ? window.getCurrentUser() : null;
        
        modal.innerHTML = `
            <div class="comments-modal-content" style="
                background: white;
                padding: 30px;
                border-radius: 15px;
                max-width: 600px;
                width: 90%;
                max-height: 80vh;
                overflow-y: auto;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h3 style="margin: 0; color: #333;">评论管理</h3>
                    <button id="closeComments" style="
                        background: none;
                        border: none;
                        font-size: 24px;
                        cursor: pointer;
                        color: #999;
                    ">&times;</button>
                </div>
                
                <div id="commentsList" style="margin-bottom: 20px;">
                    ${comments.length === 0 ? 
                        '<p style="text-align: center; color: #999; padding: 20px;">暂无评论</p>' :
                        comments.map(comment => `
                            <div class="comment-item" style="
                                padding: 15px;
                                border: 1px solid #eee;
                                border-radius: 8px;
                                margin-bottom: 10px;
                                position: relative;
                            ">
                                <div style="display: flex; justify-content: space-between; align-items: start;">
                                    <div style="flex: 1;">
                                        <div style="display: flex; align-items: center; margin-bottom: 8px;">
                                            <strong style="color: #333; margin-right: 10px;">${comment.user.username}</strong>
                                            <span style="color: #999; font-size: 12px;">${this.formatDate(comment.created_at)}</span>
                                        </div>
                                        <p style="margin: 0; color: #666; line-height: 1.5;">${comment.content}</p>
                                    </div>
                                    ${(currentUser && (currentUser.id === comment.user.id || currentUser.is_staff)) ? 
                                        `<button class="delete-comment-btn" data-comment-id="${comment.id}" style="
                                            background: #ff4757;
                                            color: white;
                                            border: none;
                                            padding: 5px 10px;
                                            border-radius: 4px;
                                            cursor: pointer;
                                            font-size: 12px;
                                        ">删除</button>` : ''
                                    }
                                </div>
                            </div>
                        `).join('')
                    }
                </div>
                
                <div style="border-top: 1px solid #eee; padding-top: 20px;">
                    <h4 style="margin-bottom: 15px; color: #333;">发表评论</h4>
                    <textarea id="newCommentContent" placeholder="请输入您的评论..." style="
                        width: 100%;
                        min-height: 80px;
                        padding: 12px;
                        border: 2px solid #e0e0e0;
                        border-radius: 8px;
                        font-size: 14px;
                        resize: vertical;
                        margin-bottom: 15px;
                    "></textarea>
                    <div style="display: flex; gap: 10px; justify-content: flex-end;">
                        <button id="cancelNewComment" style="
                            padding: 8px 16px;
                            background: #f8f9fa;
                            color: #666;
                            border: 1px solid #ddd;
                            border-radius: 6px;
                            cursor: pointer;
                        ">取消</button>
                        <button id="submitNewComment" style="
                            padding: 8px 16px;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                            border: none;
                            border-radius: 6px;
                            cursor: pointer;
                        ">发布评论</button>
                    </div>
                </div>
            </div>
        `;
        
        // 添加事件监听器
        modal.querySelector('#closeComments').addEventListener('click', () => {
            document.body.removeChild(modal);
        });
        
        modal.querySelector('#cancelNewComment').addEventListener('click', () => {
            document.body.removeChild(modal);
        });
        
        modal.querySelector('#submitNewComment').addEventListener('click', async () => {
            const content = modal.querySelector('#newCommentContent').value.trim();
            if (!content) {
                this.showError('请输入评论内容');
                return;
            }
            
            try {
                const csrfToken = await this.getCSRFToken();
                const currentUser = window.getCurrentUser ? window.getCurrentUser() : null;
                if (!currentUser) {
                    this.showError('请先登录');
                    return;
                }
                
                const response = await fetch('/api/creation-comments/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({
                        creation_id: creationId,
                        user_id: currentUser.id,
                        content: content
                    })
                });
                
                if (response.ok) {
                    this.showSuccess('评论发布成功！');
                    document.body.removeChild(modal);
                    // 更新评论数
                    const card = document.querySelector(`[data-id="${creationId}"]`);
                    if (card) {
                        const commentCount = card.querySelector('.stat i.fa-comment + span');
                        if (commentCount) {
                            const currentCount = parseInt(commentCount.textContent) || 0;
                            commentCount.textContent = currentCount + 1;
                        }
                    }
                    // 重新加载统计数据
                    await this.loadStatistics();
                } else {
                    const error = await response.json();
                    this.showError(error.error || '评论发布失败');
                }
            } catch (error) {
                console.error('评论发布失败:', error);
                this.showError('评论发布失败，请稍后重试');
            }
        });
        
        // 删除评论按钮事件
        modal.querySelectorAll('.delete-comment-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const commentId = e.target.dataset.commentId;
                if (confirm('确定要删除这条评论吗？')) {
                    await this.deleteComment(commentId, creationId, modal);
                }
            });
        });
        
        // 点击模态框外部关闭
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                document.body.removeChild(modal);
            }
        });
        
        document.body.appendChild(modal);
        modal.querySelector('#newCommentContent').focus();
    }

    async deleteComment(commentId, creationId, modal) {
        try {
            const csrfToken = await this.getCSRFToken();
            const response = await fetch(`/api/creation-comments/${commentId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': csrfToken
                }
            });

            if (response.ok) {
                this.showSuccess('评论删除成功！');
                // 重新加载评论列表
                try {
                    const reloadResponse = await fetch(`/api/creation-comments/?creation_id=${creationId}`);
                    if (reloadResponse.ok) {
                        const comments = await reloadResponse.json();
                        // 重新渲染评论列表
                        const commentsList = modal.querySelector('#commentsList');
                        const currentUser = window.getCurrentUser ? window.getCurrentUser() : null;
                        
                        commentsList.innerHTML = comments.length === 0 ? 
                            '<p style="text-align: center; color: #999; padding: 20px;">暂无评论</p>' :
                            comments.map(comment => `
                                <div class="comment-item" style="
                                    padding: 15px;
                                    border: 1px solid #eee;
                                    border-radius: 8px;
                                    margin-bottom: 10px;
                                    position: relative;
                                ">
                                    <div style="display: flex; justify-content: space-between; align-items: start;">
                                        <div style="flex: 1;">
                                            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                                                <strong style="color: #333; margin-right: 10px;">${comment.user.username}</strong>
                                                <span style="color: #999; font-size: 12px;">${this.formatDate(comment.created_at)}</span>
                                            </div>
                                            <p style="margin: 0; color: #666; line-height: 1.5;">${comment.content}</p>
                                        </div>
                                        ${(currentUser && (currentUser.id === comment.user.id || currentUser.is_staff)) ? 
                                            `<button class="delete-comment-btn" data-comment-id="${comment.id}" style="
                                                background: #ff4757;
                                                color: white;
                                                border: none;
                                                padding: 5px 10px;
                                                border-radius: 4px;
                                                cursor: pointer;
                                                font-size: 12px;
                                            ">删除</button>` : ''
                                        }
                                    </div>
                                </div>
                            `).join('');
                        
                        // 重新绑定删除按钮事件
                        commentsList.querySelectorAll('.delete-comment-btn').forEach(btn => {
                            btn.addEventListener('click', async (e) => {
                                const commentId = e.target.dataset.commentId;
                                if (confirm('确定要删除这条评论吗？')) {
                                    await this.deleteComment(commentId, creationId, modal);
                                }
                            });
                        });
                    }
                } catch (reloadError) {
                    console.error('重新加载评论失败:', reloadError);
                }
                
                // 更新评论数
                const card = document.querySelector(`[data-id="${creationId}"]`);
                if (card) {
                    const commentCount = card.querySelector('.stat i.fa-comment + span');
                    if (commentCount) {
                        const currentCount = parseInt(commentCount.textContent) || 0;
                        commentCount.textContent = Math.max(0, currentCount - 1);
                    }
                }
                
                // 重新加载统计数据
                await this.loadStatistics();
            } else {
                const error = await response.json();
                this.showError(error.error || '删除评论失败');
            }
        } catch (error) {
            console.error('删除评论失败:', error);
            this.showError('删除评论失败，请稍后重试');
        }
    }

    handleShare(creationId) {
        // 实现分享功能
        if (navigator.share) {
            navigator.share({
                title: '非遗创作分享',
                text: '看看这个有趣的非遗创作！',
                url: window.location.href
            });
        } else {
            // 复制链接到剪贴板
            navigator.clipboard.writeText(window.location.href).then(() => {
                this.showSuccess('链接已复制到剪贴板');
            });
        }
    }

    async handleManage(creationId) {
        // 获取当前用户信息
        const currentUser = window.getCurrentUser ? window.getCurrentUser() : null;
        if (!currentUser) {
            this.showError('请先登录');
            return;
        }

        // 获取创作详情
        try {
            const response = await fetch(`/api/creations/${creationId}/`);
            if (!response.ok) {
                throw new Error('获取创作详情失败');
            }
            const creation = await response.json();
            
            // 检查权限
            const canManage = currentUser.is_staff || (creation.user && creation.user.id === currentUser.id);
            if (!canManage) {
                this.showError('没有管理权限');
                return;
            }

            // 显示管理菜单
            this.showManageMenu(creation, currentUser);
        } catch (error) {
            console.error('获取创作详情失败:', error);
            this.showError('获取创作详情失败');
        }
    }

    showManageMenu(creation, currentUser) {
        // 创建管理菜单模态框
        const modal = document.createElement('div');
        modal.className = 'manage-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        `;

        const isAdmin = currentUser.is_staff;
        const isAuthor = creation.user && creation.user.id === currentUser.id;

        modal.innerHTML = `
            <div class="manage-modal-content" style="
                background: white;
                padding: 30px;
                border-radius: 15px;
                max-width: 400px;
                width: 90%;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h3 style="margin: 0; color: #333;">创作管理</h3>
                    <button id="closeManage" style="
                        background: none;
                        border: none;
                        font-size: 24px;
                        cursor: pointer;
                        color: #999;
                    ">&times;</button>
                </div>

                <div style="margin-bottom: 20px;">
                    <h4 style="margin: 0 0 10px 0; color: #666;">${creation.title}</h4>
                    <p style="margin: 0; color: #999; font-size: 14px;">
                        作者: ${creation.user.display_name || creation.user.username}
                    </p>
                </div>

                <div style="display: flex; flex-direction: column; gap: 10px;">
                    ${isAuthor ? `
                        <button class="manage-btn" onclick="userCreation.editCreation(${creation.id})" style="
                            background: #4CAF50;
                            color: white;
                            border: none;
                            padding: 12px;
                            border-radius: 8px;
                            cursor: pointer;
                            font-size: 14px;
                            display: flex;
                            align-items: center;
                            gap: 8px;
                        ">
                            <i class="fas fa-edit"></i>
                            编辑创作
                        </button>
                    ` : ''}

                    ${isAdmin ? `
                        <button class="manage-btn" onclick="userCreation.toggleFeatured(${creation.id}, ${creation.is_featured})" style="
                            background: ${creation.is_featured ? '#ff9800' : '#2196F3'};
                            color: white;
                            border: none;
                            padding: 12px;
                            border-radius: 8px;
                            cursor: pointer;
                            font-size: 14px;
                            display: flex;
                            align-items: center;
                            gap: 8px;
                        ">
                            <i class="fas fa-star"></i>
                            ${creation.is_featured ? '取消精选' : '设为精选'}
                        </button>

                        <button class="manage-btn" onclick="userCreation.toggleRecommended(${creation.id}, ${creation.is_recommended})" style="
                            background: ${creation.is_recommended ? '#9C27B0' : '#673AB7'};
                            color: white;
                            border: none;
                            padding: 12px;
                            border-radius: 8px;
                            cursor: pointer;
                            font-size: 14px;
                            display: flex;
                            align-items: center;
                            gap: 8px;
                        ">
                            <i class="fas fa-thumbs-up"></i>
                            ${creation.is_recommended ? '取消推荐' : '设为推荐'}
                        </button>
                    ` : ''}

                    <button class="manage-btn" onclick="userCreation.deleteCreation(${creation.id})" style="
                        background: #f44336;
                        color: white;
                        border: none;
                        padding: 12px;
                        border-radius: 8px;
                        cursor: pointer;
                        font-size: 14px;
                        display: flex;
                        align-items: center;
                        gap: 8px;
                    ">
                        <i class="fas fa-trash"></i>
                        删除创作
                    </button>
                </div>
            </div>
        `;

        // 绑定关闭事件
        modal.querySelector('#closeManage').addEventListener('click', () => {
            document.body.removeChild(modal);
        });

        // 点击外部关闭
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                document.body.removeChild(modal);
            }
        });

        document.body.appendChild(modal);
    }

    async editCreation(creationId) {
        // 编辑创作功能
        this.showSuccess('编辑功能开发中...');
    }

    async toggleFeatured(creationId, isFeatured) {
        try {
            const csrfToken = await this.getCSRFToken();
            const response = await fetch(`/api/creations/${creationId}/${isFeatured ? 'unfeature' : 'feature'}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken
                }
            });

            if (response.ok) {
                this.showSuccess(isFeatured ? '已取消精选' : '已设为精选');
                this.refreshCreations();
                document.querySelector('.manage-modal').remove();
            } else {
                const error = await response.json();
                this.showError(error.error || '操作失败');
            }
        } catch (error) {
            console.error('操作失败:', error);
            this.showError('操作失败，请稍后重试');
        }
    }

    async toggleRecommended(creationId, isRecommended) {
        try {
            const csrfToken = await this.getCSRFToken();
            const response = await fetch(`/api/creations/${creationId}/${isRecommended ? 'unrecommend' : 'recommend'}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken
                }
            });

            if (response.ok) {
                this.showSuccess(isRecommended ? '已取消推荐' : '已设为推荐');
                this.refreshCreations();
                document.querySelector('.manage-modal').remove();
            } else {
                const error = await response.json();
                this.showError(error.error || '操作失败');
            }
        } catch (error) {
            console.error('操作失败:', error);
            this.showError('操作失败，请稍后重试');
        }
    }

    async deleteCreation(creationId) {
        if (confirm('确定要删除这个创作吗？此操作不可恢复。')) {
            try {
                const csrfToken = await this.getCSRFToken();
                const response = await fetch(`/api/creations/${creationId}/`, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': csrfToken
                    }
                });

                if (response.ok) {
                    this.showSuccess('创作已删除');
                    this.refreshCreations();
                    document.querySelector('.manage-modal').remove();
                } else {
                    const error = await response.json();
                    this.showError(error.error || '删除失败');
                }
            } catch (error) {
                console.error('删除失败:', error);
                this.showError('删除失败，请稍后重试');
            }
        }
    }

    handleSortChange(sort) {
        this.currentSort = sort;
        this.currentPage = 1;
        
        // 更新按钮状态
        document.querySelectorAll('.sort-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-sort="${sort}"]`).classList.add('active');
        
        this.loadCreations();
    }

    handleCategoryChange(category) {
        this.currentCategory = category;
        this.currentPage = 1;
        
        // 更新按钮状态
        document.querySelectorAll('.category-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-category="${category}"]`).classList.add('active');
        
        this.loadCreations();
    }

    filterByTag(tag) {
        // 实现按标签筛选
        this.currentTag = tag;
        this.currentPage = 1;
        
        // 更新标签状态
        document.querySelectorAll('.creation-tag').forEach(tagEl => {
            tagEl.classList.remove('active');
        });
        
        // 加载筛选后的创作
        this.loadCreations();
    }
    
    initStatsUpdate() {
        // 禁用自动统计更新，避免大量重复请求导致服务器崩溃
        // 移除定时器，改为手动更新
        if (this.statsUpdateInterval) {
            clearInterval(this.statsUpdateInterval);
            this.statsUpdateInterval = null;
        }
        
        if (this.tagsUpdateInterval) {
            clearInterval(this.tagsUpdateInterval);
            this.tagsUpdateInterval = null;
        }
        
        console.log('自动统计更新已禁用，避免大量重复请求');
    }
    
    async updateStats() {
        // 禁用自动统计更新，避免大量重复请求导致服务器崩溃
        console.log('updateStats方法已禁用，避免大量重复请求');
        // 直接返回，不发送任何API请求
        return;
    }
    
    initViewportMonitoring() {
        // 初始化视口监控，使用IntersectionObserver API
        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                const creationCard = entry.target;
                const mediaEl = creationCard.querySelector('.creation-media');
                
                if (entry.isIntersecting) {
                    // 元素进入视口，开始加载或播放
                    this.startMedia(mediaEl);
                } else {
                    // 元素离开视口，停止加载或播放
                    this.stopMedia(mediaEl);
                }
            });
        }, {
            root: null, // 使用视口作为根元素
            rootMargin: '0px', // 没有边距
            threshold: 0.1 // 当元素10%进入视口时触发
        });
        
        // 观察所有创作卡片
        document.querySelectorAll('.creation-card').forEach(card => {
            this.observer.observe(card);
        });
    }
    
    startMedia(mediaEl) {
        // 开始媒体加载或播放
        const video = mediaEl.querySelector('video');
        const audio = mediaEl.querySelector('audio');
        const img = mediaEl.querySelector('img[data-src]');
        
        // 加载图片
        if (img) {
            img.src = img.dataset.src;
            img.removeAttribute('data-src');
        }
        
        // 播放视频
        if (video && video.paused) {
            // 可以根据需求决定是否自动播放
            // video.play().catch(err => console.error('自动播放失败:', err));
        }
        
        // 播放音频
        if (audio && audio.paused) {
            // 音频一般不自动播放
        }
    }
    
    stopMedia(mediaEl) {
        // 停止媒体加载或播放
        const video = mediaEl.querySelector('video');
        const audio = mediaEl.querySelector('audio');
        
        // 暂停视频
        if (video && !video.paused) {
            video.pause();
        }
        
        // 暂停音频
        if (audio && !audio.paused) {
            audio.pause();
        }
        
        // 对于未加载的图片，可以停止加载
        // 但对于已加载的图片，我们不做处理
    }
    
    // 清理资源
    cleanup() {
        if (this.statsUpdateInterval) {
            clearInterval(this.statsUpdateInterval);
        }
        
        if (this.tagsUpdateInterval) {
            clearInterval(this.tagsUpdateInterval);
        }
        
        if (this.observer) {
            this.observer.disconnect();
        }
    }

    refreshCreations() {
        this.currentPage = 1;
        this.loadCreations();
    }

    showLoadingSkeleton() {
        const container = document.getElementById('creationList');
        container.innerHTML = `
            <div class="loading-skeleton">
                <div class="skeleton-creation">
                    <div class="skeleton-video"></div>
                    <div class="skeleton-content">
                        <div class="skeleton-title"></div>
                        <div class="skeleton-user"></div>
                        <div class="skeleton-stats"></div>
                    </div>
                </div>
                <div class="skeleton-creation">
                    <div class="skeleton-video"></div>
                    <div class="skeleton-content">
                        <div class="skeleton-title"></div>
                        <div class="skeleton-user"></div>
                        <div class="skeleton-stats"></div>
                    </div>
                </div>
            </div>
        `;
    }

    hideLoadingSkeleton() {
        // 骨架屏会在renderCreations中被替换
    }

    showLoginRequired() {
        const container = document.getElementById('creationList');
        container.innerHTML = `
            <div class="login-required">
                <div class="login-icon">
                    <i class="fas fa-user-lock"></i>
                </div>
                <h2>请先登录</h2>
                <p>登录后即可发布创作和访问创作者中心</p>
                <div class="login-actions">
                    <button class="login-btn" onclick="window.location.href='login.html'">
                        <i class="fas fa-sign-in-alt"></i>
                        立即登录
                    </button>
                    <button class="register-btn" onclick="window.location.href='register.html'">
                        <i class="fas fa-user-plus"></i>
                        注册账号
                    </button>
                </div>
            </div>
        `;
        
        // 保持发布按钮可用，让点击事件能够触发登录提示
        document.getElementById('createBtn').disabled = false;
    }

    showLoginPrompt(action) {
        // 创建登录提示模态框
        const modal = document.createElement('div');
        modal.className = 'login-prompt-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        `;
        
        modal.innerHTML = `
            <div class="login-prompt-content" style="
                background: white;
                padding: 30px;
                border-radius: 15px;
                text-align: center;
                max-width: 400px;
                width: 90%;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            ">
                <div class="prompt-icon" style="
                    font-size: 3rem;
                    color: #667eea;
                    margin-bottom: 20px;
                ">
                    <i class="fas fa-user-lock"></i>
                </div>
                <h3 style="margin-bottom: 10px; color: #333;">请先登录</h3>
                <p style="color: #666; margin-bottom: 25px;">登录后即可${action}</p>
                <div class="prompt-actions" style="display: flex; gap: 15px; justify-content: center;">
                    <button class="prompt-login-btn" style="
                        padding: 12px 25px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        border: none;
                        border-radius: 8px;
                        cursor: pointer;
                        font-weight: 600;
                    ">
                        <i class="fas fa-sign-in-alt"></i>
                        立即登录
                    </button>
                    <button class="prompt-cancel-btn" style="
                        padding: 12px 25px;
                        background: #f8f9fa;
                        color: #666;
                        border: 1px solid #ddd;
                        border-radius: 8px;
                        cursor: pointer;
                        font-weight: 600;
                    ">
                        取消
                    </button>
                </div>
            </div>
        `;
        
        // 添加事件监听器
        modal.querySelector('.prompt-login-btn').addEventListener('click', () => {
            window.location.href = 'login.html';
        });
        
        modal.querySelector('.prompt-cancel-btn').addEventListener('click', () => {
            document.body.removeChild(modal);
        });
        
        // 点击模态框外部关闭
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                document.body.removeChild(modal);
            }
        });
        
        document.body.appendChild(modal);
    }

    showError(message) {
        // 简单的错误提示实现
        alert(message);
    }

    showSuccess(message) {
        // 简单的成功提示实现
        alert(message);
    }

    getTypeLabel(type) {
        const labels = {
            'video': '视频',
            'photo': '图片',
            'article': '文章',
            'music': '音乐'
        };
        return labels[type] || '创作';
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;
        
        const minute = 60 * 1000;
        const hour = 60 * minute;
        const day = 24 * hour;
        
        if (diff < hour) {
            return Math.floor(diff / minute) + '分钟前';
        } else if (diff < day) {
            return Math.floor(diff / hour) + '小时前';
        } else if (diff < 7 * day) {
            return Math.floor(diff / day) + '天前';
        } else {
            return date.toLocaleDateString('zh-CN');
        }
    }

    async getCSRFToken() {
        // 首先尝试从DOM获取CSRF token
        const domToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (domToken) {
            return domToken;
        }
        
        // 如果DOM中没有，通过API获取CSRF token
        try {
            const response = await fetch('/api/auth/csrf/');
            if (response.ok) {
                const data = await response.json();
                return data.csrfToken || '';
            }
        } catch (error) {
            console.error('获取CSRF token失败:', error);
        }
        
        return '';
    }
}

// 全局实例
let userCreation;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    userCreation = new UserCreation();
});