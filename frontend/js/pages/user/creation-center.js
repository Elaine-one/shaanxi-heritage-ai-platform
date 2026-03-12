// 创作中心页面JavaScript

class CreationCenter {
    constructor() {
        this.currentUser = null;
        this.currentTab = 'my-creations';
        this.creations = [];
        this.viewHistory = [];
        this.favorites = [];
        
        this.init();
    }

    async init() {
        // 检查登录状态
        const isLoggedIn = await window.checkLoginStatus();
        if (!isLoggedIn) {
            this.redirectToLogin();
            return;
        }

        // 获取当前用户信息 - 使用checkBackendAuth确保获取最新信息
        const userData = await window.checkBackendAuth(true);
        if (!userData) {
            this.redirectToLogin();
            return;
        }
        this.currentUser = userData;
        
        // 初始化数据数组
        this.likedCreations = [];

        // 初始化事件监听器
        this.initEventListeners();
        
        // 加载用户数据
        await this.loadUserData();
        
        // 加载创作数据
        await this.loadCreations();
        
        // 加载浏览历史
        await this.loadViewHistory();
        
        // 加载收藏数据
        await this.loadFavorites();
        
        // 初始化图表
        this.initCharts();
        
        // 初始化自动更新
        this.initAutoUpdate();
    }

    initEventListeners() {
        // 标签页切换
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // 创作状态筛选
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.filterCreations(e.target.dataset.status);
            });
        });

        // 清空浏览历史
        document.getElementById('clearHistoryBtn').addEventListener('click', () => {
            this.clearViewHistory();
        });

        // 导出数据
        document.getElementById('exportDataBtn').addEventListener('click', () => {
            this.exportData();
        });

        // 删除账户
        document.getElementById('deleteAccountBtn').addEventListener('click', () => {
            this.deleteAccount();
        });

        // 统计时间范围切换
        document.getElementById('analyticsRange').addEventListener('change', (e) => {
            this.updateAnalytics(e.target.value);
        });

        // 设置保存
        document.getElementById('autoSaveDraft').addEventListener('change', (e) => {
            this.saveSetting('autoSaveDraft', e.target.checked);
        });

        document.getElementById('emailNotifications').addEventListener('change', (e) => {
            this.saveSetting('emailNotifications', e.target.checked);
        });

        document.getElementById('defaultVisibility').addEventListener('change', (e) => {
            this.saveSetting('defaultVisibility', e.target.value);
        });
    }
    
    // 加载用户点赞的创作
    async loadLikedCreations() {
        try {
            // 使用正确的API端点获取点赞数据
            const response = await fetch('/api/creation-likes/');
            if (response.ok) {
                const data = await response.json();
                // 确保likedCreations是数组
                this.likedCreations = Array.isArray(data) ? data : (data.results || []);
                this.renderLikedCreations();
            } else {
                console.error('加载点赞创作失败，HTTP状态:', response.status);
            }
        } catch (error) {
            console.error('加载点赞创作失败:', error);
        }
    }
    
    // 渲染用户点赞的创作
    renderLikedCreations() {
        const container = document.getElementById('likedList');
        
        if (this.likedCreations.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-heart"></i>
                    <h3>暂无点赞内容</h3>
                    <p>去发现并点赞您喜欢的创作吧！</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.likedCreations.map(item => {
            const creation = item.creation || item;
            return `
            <div class="liked-item" data-id="${creation.id}">
                <div class="liked-preview">
                    ${this.renderMedia(creation)}
                </div>
                <div class="liked-info">
                    <h4 class="liked-title">${creation.title}</h4>
                    <p class="liked-author">作者：${creation.user?.display_name || creation.author?.display_name || '未知作者'}</p>
                    <div class="liked-meta">
                        <span class="liked-date">点赞时间：${this.formatDate(item.created_at || creation.updated_at)}</span>
                        <span class="liked-views"><i class="fas fa-eye"></i> ${creation.view_count || 0}</span>
                        <span class="liked-likes"><i class="fas fa-heart"></i> ${creation.like_count || 0}</span>
                    </div>
                </div>
                <div class="liked-actions">
                    <button class="action-btn view" onclick="creationCenter.viewCreation(${creation.id})"><i class="fas fa-eye"></i> 查看</button>
                </div>
            </div>
            `;
        }).join('');
    }

    async loadUserData() {
        try {
            // 更新用户信息显示
            const avatarElement = document.getElementById('userAvatar');
            const displayNameElement = document.getElementById('userDisplayName');
            const bioElement = document.getElementById('userBio');
            
            if (avatarElement) {
                // 尝试从API获取完整用户信息（包含头像）
                let userData = null;
                try {
                    // 使用user-profile-api.js中的getUserProfile方法获取完整用户信息
                    if (window.API && window.API.userProfile) {
                        userData = await window.API.userProfile.getUserProfile();
                        console.log('从user-profile-api获取的用户信息:', userData);
                    } else {
                        // 如果API不可用，尝试从checkBackendAuth获取
                        userData = await window.checkBackendAuth(true);
                        console.log('从checkBackendAuth获取的用户信息:', userData);
                    }
                } catch (error) {
                    console.error('获取用户信息失败:', error);
                    userData = this.currentUser;
                    console.log('使用this.currentUser:', userData);
                }
                
                // 处理头像显示
                let avatarUrl = null;
                
                // 优先从profile获取头像
                if (userData.profile && userData.profile.avatar) {
                    avatarUrl = userData.profile.avatar;
                } else if (userData.avatar) {
                    // 尝试使用当前用户对象中的头像
                    avatarUrl = userData.avatar;
                }
                
                console.log('处理前的头像URL:', avatarUrl);
                
                if (avatarUrl) {
                    // 直接使用获取到的头像URL，不需要再添加域名
                    // 因为从API获取的应该是完整的URL或可以直接使用的相对URL
                    avatarElement.src = avatarUrl;
                } else {
                    // 没有头像，显示默认头像
                    avatarElement.src = '../static/common/default-avatar.png';
                }
                
                // 添加错误处理，确保在头像加载失败时显示默认头像
                avatarElement.onerror = function() {
                    console.error('头像加载失败，使用默认头像');
                    this.src = '../static/common/default-avatar.png';
                };
            }
            
            if (displayNameElement) {
                // 优先使用profile.display_name，然后是username
                const displayName = this.currentUser.profile?.display_name || this.currentUser.username || this.currentUser.name || '用户';
                displayNameElement.textContent = displayName;
            }
            
            if (bioElement) {
                bioElement.textContent = this.currentUser.profile?.bio || this.currentUser.bio || this.currentUser.description || '管理您的创作内容和数据';
            }

            // 加载统计数据，添加错误处理
            try {
                await this.loadUserStats();
            } catch (error) {
                console.error('加载用户统计数据失败:', error);
                // 统计数据加载失败时，从创作列表计算
                this.calculateStatsFromCreations();
            }
            
        } catch (error) {
            console.error('加载用户数据失败:', error);
            // 出错时显示默认头像
            const avatarElement = document.getElementById('userAvatar');
            if (avatarElement) {
                avatarElement.src = '../static/common/default-avatar.png';
            }
            // 出错时从创作列表计算统计数据
            this.calculateStatsFromCreations();
        }
    }

    async loadUserStats() {
        try {
            // 从创作列表计算统计数据，避免重复的API请求
            this.calculateStatsFromCreations();
        } catch (error) {
            console.error('计算用户统计数据失败:', error);
        }
    }

    updateStatsDisplay(stats) {
        // 更新统计数据显示，添加更健壮的默认值处理
        document.getElementById('totalCreations').textContent = stats.total_creations || stats.total || 0;
        document.getElementById('totalViews').textContent = stats.total_views || stats.views || 0;
        document.getElementById('totalLikes').textContent = stats.total_likes || stats.likes || 0;
        document.getElementById('totalFans').textContent = stats.total_fans || stats.fans || 0;
    }
    
    // 渲染媒体内容
    renderMedia(creation) {
        // 处理媒体URL，确保正确的路径格式
        const processMediaUrl = (url) => {
            if (!url) return null;
            if (url.startsWith('http')) return url;
            if (url.startsWith('/media/')) return url;
            if (url.startsWith('media/')) return `/${url}`;
            return `/media/${url}`;
        };
        
        console.log('渲染媒体:', creation);
        
        // 检查创作数据是否有媒体URL
        let mediaUrl = null;
        let posterUrl = null;
        
        // 统一处理不同类型的媒体URL
        if (creation.type === 'video') {
            mediaUrl = processMediaUrl(creation.video_url) || processMediaUrl(creation.url);
            posterUrl = processMediaUrl(creation.thumbnail) || processMediaUrl(creation.image_url) || processMediaUrl(creation.cover);
        } else if (creation.type === 'photo') {
            mediaUrl = processMediaUrl(creation.image_url) || processMediaUrl(creation.url);
        }
        
        switch (creation.type) {
            case 'video':
                return `
                    <div style="position: relative; width: 100%; height: 100%; background: #000; display: flex; align-items: center; justify-content: center;">
                        ${mediaUrl ? `
                            <video style="width: 100%; height: 100%; object-fit: cover;" poster="${posterUrl || ''}" preload="metadata">
                                <source src="${mediaUrl}" type="video/mp4">
                                <source src="${mediaUrl}" type="video/webm">
                                您的浏览器不支持视频播放
                            </video>
                        ` : `
                            <div style="color: white; text-align: center;">
                                <i class="fas fa-video" style="font-size: 3rem; margin-bottom: 10px;"></i>
                                <div>视频文件缺失</div>
                            </div>
                        `}
                    </div>
                `;
            case 'photo':
                return `
                    <div style="position: relative; width: 100%; height: 100%; background: #f0f0f0; display: flex; align-items: center; justify-content: center;">
                        ${mediaUrl ? `
                            <img src="${mediaUrl}" 
                                 alt="${creation.title || '创作图片'}" 
                                 style="width: 100%; height: 100%; object-fit: cover;">
                        ` : `
                            <div style="color: #666; text-align: center;">
                                <i class="fas fa-image" style="font-size: 3rem; margin-bottom: 10px;"></i>
                                <div>图片文件缺失</div>
                            </div>
                        `}
                    </div>
                `;
            case 'music':
                return `
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); height: 100%; display: flex; align-items: center; justify-content: center; flex-direction: column;">
                        <i class="fas fa-music" style="font-size: 3rem; color: white; margin-bottom: 10px;"></i>
                        <div style="color: white; font-size: 14px;">音频作品</div>
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
    
    // 从创作列表中计算统计数据
    calculateStatsFromCreations() {
        // 计算创作数量
        const totalCreations = this.creations.length || 0;
        
        // 计算总浏览量和总点赞数
        const statsFromCreations = this.creations.reduce((acc, creation) => {
            acc.views += creation.view_count || 0;
            acc.likes += creation.like_count || 0;
            return acc;
        }, { views: 0, likes: 0 });
        
        // 更新显示
        document.getElementById('totalCreations').textContent = totalCreations;
        document.getElementById('totalViews').textContent = statsFromCreations.views;
        document.getElementById('totalLikes').textContent = statsFromCreations.likes;
        // 粉丝数无法从创作列表计算，保持原有值或设为0
        const fansElement = document.getElementById('totalFans');
        if (fansElement && fansElement.textContent === '0') {
            fansElement.textContent = 0;
        }
    }

    async loadCreations() {
        try {
            const response = await fetch('/api/creations/my_creations/');
            if (response.ok) {
                const data = await response.json();
                // 确保creations是数组
                this.creations = Array.isArray(data) ? data : (data.results || []);
                this.renderCreations();
                // 加载成功后计算统计数据
                this.calculateStatsFromCreations();
            } else {
                console.error('加载创作列表失败，HTTP状态:', response.status);
                // 即使API请求失败，也确保渲染现有的创作数据
                if (this.creations.length > 0) {
                    this.renderCreations();
                }
            }
        } catch (error) {
            console.error('加载创作列表失败:', error);
            // 出错时使用现有的创作数据
            if (this.creations.length > 0) {
                this.renderCreations();
                this.calculateStatsFromCreations();
            }
        }
    }

    async loadViewHistory() {
        try {
            const response = await fetch('/api/creations/view_history/');
            if (response.ok) {
                const data = await response.json();
                // 确保viewHistory是数组
                this.viewHistory = Array.isArray(data) ? data : (data.results || []);
                this.renderViewHistory();
            }
        } catch (error) {
            console.error('加载浏览历史失败:', error);
        }
    }

    async loadFavorites() {
        try {
            const response = await fetch('/api/creation-favorites/');
            if (response.ok) {
                const data = await response.json();
                // 确保favorites是数组
                this.favorites = Array.isArray(data) ? data : (data.results || []);
                this.renderFavorites();
            }
        } catch (error) {
            console.error('加载收藏列表失败:', error);
        }
    }

    renderCreations() {
        const container = document.getElementById('myCreationsList');
        
        if (this.creations.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-video"></i>
                    <h3>暂无创作内容</h3>
                    <p>开始您的第一个创作吧！</p>
                    <button class="create-btn" onclick="window.location.href='user-creation.html'">
                        发布创作
                    </button>
                </div>
            `;
            return;
        }

        container.innerHTML = this.creations.map(creation => `
            <div class="creation-item" data-id="${creation.id}">
                <div class="creation-preview">
                    ${this.renderMedia(creation)}
                    <div class="creation-status ${creation.status}">${this.getStatusLabel(creation.status)}</div>
                </div>
                <div class="creation-info">
                    <h4 class="creation-title">${creation.title}</h4>
                    <p class="creation-description">${creation.description}</p>
                    <div class="creation-meta">
                        <span class="creation-date">${this.formatDate(creation.created_at)}</span>
                        <span class="creation-views"><i class="fas fa-eye"></i> ${creation.view_count || 0}</span>
                        <span class="creation-likes"><i class="fas fa-heart"></i> ${creation.like_count || 0}</span>
                    </div>
                    <div class="creation-actions">
                        <button class="action-btn edit" onclick="creationCenter.editCreation(${creation.id})">
                            <i class="fas fa-edit"></i> 编辑
                        </button>
                        <button class="action-btn delete" onclick="creationCenter.deleteCreation(${creation.id})">
                            <i class="fas fa-trash"></i> 删除
                        </button>
                        <button class="action-btn view" onclick="creationCenter.viewCreation(${creation.id})">
                            <i class="fas fa-external-link-alt"></i> 查看
                        </button>
                        <button class="action-btn comments" onclick="creationCenter.viewComments(${creation.id})">
                            <i class="fas fa-comments"></i> 评论
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    renderViewHistory() {
        const container = document.getElementById('historyList');
        
        if (this.viewHistory.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-history"></i>
                    <h3>暂无浏览历史</h3>
                    <p>开始浏览其他用户的创作吧！</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.viewHistory.map(item => `
            <div class="history-item">
                <div class="history-preview">
                    ${this.renderMedia(item.creation)}
                </div>
                <div class="history-info">
                    <h4 class="history-title">${item.creation.title}</h4>
                    <p class="history-author">作者：${item.creation.author.display_name}</p>
                    <div class="history-meta">
                        <span class="history-date">浏览时间：${this.formatDate(item.viewed_at)}</span>
                        <span class="history-duration">浏览时长：${this.formatDuration(item.view_duration)}</span>
                    </div>
                </div>
                <div class="history-actions">
                    <button class="action-btn view" onclick="creationCenter.viewCreation(${item.creation.id})"><i class="fas fa-eye"></i> 再次查看</button>
                </div>
            </div>
        `).join('');
    }

    renderFavorites() {
        const container = document.getElementById('favoritesList');
        
        if (this.favorites.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-heart"></i>
                    <h3>暂无收藏内容</h3>
                    <p>发现并收藏您喜欢的创作吧！</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.favorites.filter(favorite => favorite && favorite.creation).map(favorite => {
            // 安全获取作者名称
            let authorName = '未知作者';
            if (favorite.creation.author && favorite.creation.author.display_name) {
                authorName = favorite.creation.author.display_name;
            } else if (favorite.creation.user && favorite.creation.user.display_name) {
                authorName = favorite.creation.user.display_name;
            } else if (favorite.creation.author && favorite.creation.author.username) {
                authorName = favorite.creation.author.username;
            } else if (favorite.creation.user && favorite.creation.user.username) {
                authorName = favorite.creation.user.username;
            }
            
            return `
                <div class="favorite-item">
                    <div class="favorite-preview">
                        ${this.renderMedia(favorite.creation)}
                    </div>
                    <div class="favorite-info">
                        <h4 class="favorite-title">${favorite.creation.title || '无标题'}</h4>
                        <p class="favorite-author">作者：${authorName}</p>
                        <div class="favorite-meta">
                            <span class="favorite-date">收藏时间：${this.formatDate(favorite.created_at)}</span>
                            <span class="favorite-views"><i class="fas fa-eye"></i> ${favorite.creation.view_count || 0}</span>
                            <span class="favorite-likes"><i class="fas fa-heart"></i> ${favorite.creation.like_count || 0}</span>
                        </div>
                    </div>
                    <div class="favorite-actions">
                        <button class="action-btn view" onclick="creationCenter.viewCreation(${favorite.creation.id})"><i class="fas fa-eye"></i> 查看</button>
                        <button class="action-btn unfavorite" onclick="creationCenter.unfavorite(${favorite.id})"><i class="fas fa-heart-broken"></i> 取消收藏</button>
                    </div>
                </div>
            `;
        }).join('');
    }

    switchTab(tabName) {
        // 更新标签按钮状态
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // 更新内容区域
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(tabName).classList.add('active');

        this.currentTab = tabName;

        // 加载对应数据
        switch (tabName) {
            case 'my-creations':
                this.loadCreations();
                break;
            case 'view-history':
                this.loadViewHistory();
                break;
            case 'favorites':
                this.loadFavorites();
                break;
            case 'liked':
                this.loadLikedCreations();
                break;
            case 'analytics':
                this.updateAnalytics(document.getElementById('analyticsRange').value);
                break;
        }
    }

    filterCreations(status) {
        // 更新筛选按钮状态
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-status="${status}"]`).classList.add('active');

        // 根据状态筛选创作
        let filteredCreations = this.creations;
        if (status !== 'all') {
            filteredCreations = this.creations.filter(creation => creation.status === status);
        }

        // 重新渲染创作列表
        this.renderFilteredCreations(filteredCreations);
    }

    renderFilteredCreations(creations) {
        const container = document.getElementById('myCreationsList');
        
        if (creations.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-search"></i>
                    <h3>暂无符合条件的创作</h3>
                    <p>尝试调整筛选条件或发布新的创作</p>
                </div>
            `;
            return;
        }

        // 使用相同的渲染逻辑，但只显示筛选后的创作
        container.innerHTML = creations.map(creation => `
            <div class="creation-item" data-id="${creation.id}">
                <div class="creation-preview">
                    <img src="${creation.thumbnail || '../static/common/default-thumbnail.png'}" 
                         alt="${creation.title}"
                         onerror="this.src='../static/common/default-thumbnail.png'">
                    <div class="creation-status ${creation.status}">${this.getStatusLabel(creation.status)}</div>
                </div>
                <div class="creation-info">
                    <h4 class="creation-title">${creation.title}</h4>
                    <p class="creation-description">${creation.description}</p>
                    <div class="creation-meta">
                        <span class="creation-date">${this.formatDate(creation.created_at)}</span>
                        <span class="creation-views"><i class="fas fa-eye"></i> ${creation.view_count || 0}</span>
                        <span class="creation-likes"><i class="fas fa-heart"></i> ${creation.like_count || 0}</span>
                    </div>
                    <div class="creation-actions">
                        <button class="action-btn edit" onclick="creationCenter.editCreation(${creation.id})">
                            <i class="fas fa-edit"></i> 编辑
                        </button>
                        <button class="action-btn delete" onclick="creationCenter.deleteCreation(${creation.id})">
                            <i class="fas fa-trash"></i> 删除
                        </button>
                        <button class="action-btn view" onclick="creationCenter.viewCreation(${creation.id})">
                            <i class="fas fa-external-link-alt"></i> 查看
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    initCharts() {
        // 初始化图表容器
        this.viewsChart = new Chart(document.getElementById('viewsChart'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: '浏览数',
                    data: [],
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });

        this.typeChart = new Chart(document.getElementById('typeChart'), {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1']
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    async updateAnalytics(range) {
        try {
            const response = await fetch(`/api/analytics/?range=${range}`);
            if (response.ok) {
                const analytics = await response.json();
                this.updateCharts(analytics);
                this.updateAnalyticsStats(analytics);
            }
        } catch (error) {
            console.error('加载统计数据失败:', error);
        }
    }

    updateCharts(analytics) {
        // 更新浏览趋势图表
        this.viewsChart.data.labels = analytics.views.labels;
        this.viewsChart.data.datasets[0].data = analytics.views.data;
        this.viewsChart.update();

        // 更新创作类型分布图表
        this.typeChart.data.labels = analytics.types.labels;
        this.typeChart.data.datasets[0].data = analytics.types.data;
        this.typeChart.update();
    }

    updateAnalyticsStats(analytics) {
        // 更新热门创作
        const topCreationsContainer = document.getElementById('topCreations');
        topCreationsContainer.innerHTML = analytics.top_creations.map(creation => `
            <div class="top-creation-item">
                <span class="creation-title">${creation.title}</span>
                <span class="creation-stats">${creation.views} 浏览</span>
            </div>
        `).join('');

        // 更新互动统计
        const interactionStatsContainer = document.getElementById('interactionStats');
        interactionStatsContainer.innerHTML = `
            <div class="interaction-item">
                <span>总点赞数</span>
                <span class="stat-value">${analytics.interactions.likes}</span>
            </div>
            <div class="interaction-item">
                <span>总评论数</span>
                <span class="stat-value">${analytics.interactions.comments}</span>
            </div>
            <div class="interaction-item">
                <span>总分享数</span>
                <span class="stat-value">${analytics.interactions.shares}</span>
            </div>
        `;
    }

    // 工具方法
    getStatusLabel(status) {
        const statusLabels = {
            'published': '已发布',
            'draft': '草稿',
            'reviewing': '审核中',
            'rejected': '已拒绝'
        };
        return statusLabels[status] || status;
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('zh-CN') + ' ' + date.toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    formatDuration(seconds) {
        if (!seconds) return '0秒';
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        
        if (minutes > 0) {
            return `${minutes}分${remainingSeconds}秒`;
        }
        return `${remainingSeconds}秒`;
    }

    redirectToLogin() {
        window.location.href = 'login.html';
    }

    // 操作方法
    editCreation(creationId) {
        // 跳转到编辑页面或打开编辑模态框
        window.location.href = `user-creation.html?edit=${creationId}`;
    }

    async deleteCreation(creationId) {
        if (!confirm('确定要删除这个创作吗？此操作不可恢复。')) {
            return;
        }

        try {
            const response = await fetch(`/api/creations/${creationId}/`, {
                method: 'DELETE'
            });

            if (response.ok) {
                // 从列表中移除
                this.creations = this.creations.filter(creation => creation.id !== creationId);
                this.renderCreations();
                if (typeof NotificationManager !== 'undefined') {
                    NotificationManager.success('创作删除成功');
                } else {
                    alert('创作删除成功');
                }
            } else {
                throw new Error('删除失败');
            }
        } catch (error) {
            console.error('删除创作失败:', error);
            if (typeof NotificationManager !== 'undefined') {
                NotificationManager.error('删除失败，请稍后重试');
            } else {
                alert('删除失败，请稍后重试');
            }
        }
    }

    async viewComments(creationId) {
        try {
            const response = await fetch(`/api/creation-comments/?creation_id=${creationId}`);
            if (response.ok) {
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
                
                this.showCommentsModal(comments, creationId);
            } else {
                throw new Error('获取评论失败');
            }
        } catch (error) {
            console.error('获取评论失败:', error);
            if (typeof NotificationManager !== 'undefined') {
                NotificationManager.error('获取评论失败，请稍后重试');
            } else {
                alert('获取评论失败，请稍后重试');
            }
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
                        color: #666;
                    ">&times;</button>
                </div>
                <div id="commentsList" style="margin-bottom: 20px;">
                    ${comments.length > 0 ? comments.map(comment => `
                        <div class="comment-item" style="
                            border-bottom: 1px solid #eee;
                            padding: 15px 0;
                            display: flex;
                            justify-content: space-between;
                            align-items: start;
                        ">
                            <div style="flex: 1;">
                                <div style="font-weight: bold; color: #333; margin-bottom: 5px;">
                                    ${comment.user.username}
                                </div>
                                <div style="color: #666; margin-bottom: 5px;">
                                    ${comment.content}
                                </div>
                                <div style="font-size: 12px; color: #999;">
                                    ${new Date(comment.created_at).toLocaleString('zh-CN')}
                                    ${comment.like_count > 0 ? ` | 👍 ${comment.like_count}` : ''}
                                </div>
                            </div>
                            <button class="delete-comment-btn" data-comment-id="${comment.id}" style="
                                background: #dc3545;
                                color: white;
                                border: none;
                                padding: 5px 10px;
                                border-radius: 4px;
                                cursor: pointer;
                                font-size: 12px;
                            ">删除</button>
                        </div>
                    `).join('') : '<p style="text-align: center; color: #999;">暂无评论</p>'}
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // 添加事件监听器
        modal.querySelector('#closeComments').addEventListener('click', () => {
            document.body.removeChild(modal);
        });

        // 删除评论按钮事件
        modal.querySelectorAll('.delete-comment-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const commentId = e.target.dataset.commentId;
                if (confirm('确定要删除这条评论吗？')) {
                    await this.deleteComment(commentId, creationId);
                    document.body.removeChild(modal);
                }
            });
        });

        // 点击模态框外部关闭
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                document.body.removeChild(modal);
            }
        });
    }

    async deleteComment(commentId, creationId) {
        try {
            // 获取CSRF令牌
            const csrfToken = await (async () => {
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
            })();
            
            const response = await fetch(`/api/creation-comments/${commentId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': csrfToken
                }
            });

            if (response.ok) {
                // 重新加载评论列表
                await this.viewComments(creationId);
                if (typeof NotificationManager !== 'undefined') {
                    NotificationManager.success('评论删除成功');
                } else {
                    alert('评论删除成功');
                }
            } else {
                const errorData = await response.json();
                throw new Error(errorData.error || '删除评论失败');
            }
        } catch (error) {
            console.error('删除评论失败:', error);
            if (typeof NotificationManager !== 'undefined') {
                NotificationManager.error('删除评论失败，请稍后重试');
            } else {
                alert('删除评论失败，请稍后重试');
            }
        }
    }

    viewCreation(creationId) {
        // 跳转到用户创作页面，而不是创作详情页面
        window.location.href = `user-creation.html`;
    }

    async clearViewHistory() {
        if (!confirm('确定要清空浏览历史吗？此操作不可恢复。')) {
            return;
        }

        try {
            const response = await fetch('/api/view-history/', {
                method: 'DELETE'
            });

            if (response.ok) {
                this.viewHistory = [];
                this.renderViewHistory();
                if (typeof NotificationManager !== 'undefined') {
                    NotificationManager.success('浏览历史已清空');
                } else {
                    alert('浏览历史已清空');
                }
            } else {
                throw new Error('清空失败');
            }
        } catch (error) {
            console.error('清空浏览历史失败:', error);
            if (typeof NotificationManager !== 'undefined') {
                NotificationManager.error('清空失败，请稍后重试');
            } else {
                alert('清空失败，请稍后重试');
            }
        }
    }

    async unfavorite(favoriteId) {
        try {
            console.log('取消收藏，favoriteId:', favoriteId);
            
            // 获取CSRF token
            const csrfToken = window.getCsrfToken ? window.getCsrfToken() : 
                             document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                             document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
            
            if (!csrfToken) {
                console.error('CSRF token未找到');
                throw new Error('CSRF token缺失');
            }
            
            const response = await fetch(`/api/creation-favorites/${favoriteId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': csrfToken
                }
            });

            if (response.ok) {
                // 从列表中移除
                this.favorites = this.favorites.filter(favorite => favorite.id !== favoriteId);
                this.renderFavorites();
                if (typeof NotificationManager !== 'undefined') {
                    NotificationManager.success('取消收藏成功');
                }
            } else {
                console.error("取消收藏失败: " + response.status + " " + response.statusText);
                const errorText = await response.text();
                console.error("取消收藏失败响应: " + errorText);
                throw new Error('取消收藏失败');
            }
        } catch (error) {
            console.error('取消收藏失败:', error);
            if (typeof NotificationManager !== 'undefined') {
                NotificationManager.error('取消收藏失败，请稍后重试');
            } else {
                alert('取消收藏失败，请稍后重试');
            }
        }
    }

    async exportData() {
        try {
            const response = await fetch('/api/export-data/');
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `创作数据_${new Date().toISOString().split('T')[0]}.zip`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            }
        } catch (error) {
            console.error('导出数据失败:', error);
            if (typeof NotificationManager !== 'undefined') {
                NotificationManager.error('导出数据失败，请稍后重试');
            } else {
                alert('导出数据失败，请稍后重试');
            }
        }
    }

    async deleteAccount() {
        if (!confirm('确定要删除创作账户吗？这将永久删除您的所有创作数据，此操作不可恢复。')) {
            return;
        }

        try {
            const response = await fetch('/api/delete-account/', {
                method: 'DELETE'
            });

            if (response.ok) {
                if (typeof NotificationManager !== 'undefined') {
                    NotificationManager.success('创作账户已删除');
                } else {
                    alert('创作账户已删除');
                }
                this.redirectToLogin();
            } else {
                throw new Error('删除账户失败');
            }
        } catch (error) {
            console.error('删除账户失败:', error);
            if (typeof NotificationManager !== 'undefined') {
                NotificationManager.error('删除账户失败，请稍后重试');
            } else {
                alert('删除账户失败，请稍后重试');
            }
        }
    }

    async saveSetting(key, value) {
        try {
            await fetch('/api/settings/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ [key]: value })
            });
        } catch (error) {
            console.error('保存设置失败:', error);
        }
    }
    
    // 初始化自动更新
    initAutoUpdate() {
        // 设置30秒自动更新一次数据
        this.autoUpdateInterval = setInterval(async () => {
            await this.updateAllData();
        }, 30000);
    }
    
    // 批量更新所有数据
    async updateAllData() {
        try {
            // 使用Promise.allSettled替代Promise.all，确保所有请求都完成，即使部分失败
            await Promise.allSettled([
                this.loadUserData(),
                this.loadCreations(),
                this.loadViewHistory(),
                this.loadFavorites(),
                this.loadLikedCreations()
            ]);
            
            // 确保无论API请求是否成功，都计算并显示统计数据
            this.calculateStatsFromCreations();
            
            // 更新图表，添加错误处理
            try {
                this.updateAnalytics(document.getElementById('analyticsRange').value || '7d');
            } catch (error) {
                console.error('更新图表失败:', error);
            }
        } catch (error) {
            console.error('自动更新数据失败:', error);
            // 出错时也确保计算统计数据
            this.calculateStatsFromCreations();
        }
    }
    
    // 刷新所有数据（对外暴露的方法，用于外部调用）
    async refreshAllData() {
        console.log('刷新创作者中心所有数据');
        await this.updateAllData();
    }
    
    // 清理资源
    cleanup() {
        if (this.autoUpdateInterval) {
            clearInterval(this.autoUpdateInterval);
        }
        
        // 清理图表实例
        if (this.viewsChart) {
            this.viewsChart.destroy();
        }
        if (this.typeChart) {
            this.typeChart.destroy();
        }
    }
    
    // 在页面卸载时清理资源
    beforeUnload() {
        this.cleanup();
    }
}

// 全局实例
let creationCenter;

document.addEventListener('DOMContentLoaded', () => {
    creationCenter = new CreationCenter();
    window.creationCenter = creationCenter;
});