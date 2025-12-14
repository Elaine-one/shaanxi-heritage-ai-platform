// 个人中心页面脚本
document.addEventListener('DOMContentLoaded', function() {
    // 获取DOM元素
    const userAvatar = document.getElementById('user-avatar');
    const username = document.getElementById('username');
    const userEmail = document.getElementById('user-email');
    const logoutBtn = document.getElementById('logout-btn');
    const favoritesContainer = document.getElementById('favorites-container');
    const historyContainer = document.getElementById('history-container');
    const followingContainer = document.getElementById('following-container');
    const followersContainer = document.getElementById('followers-container');
    const favoritesCount = document.getElementById('favorites-count');
    const visitsCount = document.getElementById('visits-count');
    const commentsCount = document.getElementById('comments-count');
    const followingTotal = document.getElementById('following-total');
    const followersTotal = document.getElementById('followers-total');
    const menuItems = document.querySelectorAll('.profile-menu li[data-section]');
    const contentSections = document.querySelectorAll('.content-section');
    const favoritesSort = document.getElementById('favorites-sort');
    const saveSettingsBtn = document.getElementById('save-settings-btn');
    const displayNameInput = document.getElementById('display-name');
    const userBioInput = document.getElementById('user-bio');
    const uploadAvatarBtn = document.getElementById('upload-avatar-btn');
    const defaultAvatarBtn = document.getElementById('default-avatar-btn');
    const settingsAvatar = document.getElementById('settings-avatar');
    // 多选相关元素
    const multiSelectBtn = document.getElementById('multi-select-btn');
    const multiSelectActions = document.getElementById('multi-select-actions');
    const cancelMultiSelectBtn = document.getElementById('cancel-multi-select-btn');
    const travelPlanBtn = document.getElementById('planTravelBtn');
    const selectedCount = document.getElementById('selected-count');
    
    // 检查用户是否已登录
    const user = JSON.parse(localStorage.getItem('user'));
    if (!user) {
        // 未登录，跳转到登录页面
        window.location.href = 'login.html';
        return;
    }
    
    // 获取用户信息
    fetchUserInfo();
    
    // 获取用户收藏列表
    fetchUserFavorites();
    
    // 获取浏览历史
    fetchBrowsingHistory();
    
    // 获取关注列表
    fetchFollowingList();
    
    // 获取粉丝列表
    fetchFollowersList();
    
    // 加载用户统计数据
    loadUserStats();
    
    // 初始化头像显示（从本地存储）
    updateAvatarDisplay();
    
    // 初始化设置表单
    initSettingsForm();
    
    // 加载用户头像
    loadUserAvatar();
    
    // 添加退出登录事件监听器
    logoutBtn.addEventListener('click', function() {
        logout();
    });
    
    // 添加菜单切换事件
    menuItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const sectionId = this.getAttribute('data-section');
            switchSection(sectionId);
        });
    });
    
    // 添加收藏排序事件
    if (favoritesSort) {
        favoritesSort.addEventListener('change', function() {
            sortFavorites(this.value);
        });
    }
    
    // 添加多选按钮事件
    if (multiSelectBtn) {
        multiSelectBtn.addEventListener('click', function() {
            toggleMultiSelect(true);
        });
    } else {
        console.warn('多选按钮元素未找到');
    }
    
    // 添加取消多选按钮事件
    if (cancelMultiSelectBtn) {
        cancelMultiSelectBtn.addEventListener('click', function() {
            toggleMultiSelect(false);
        });
    } else {
        console.warn('取消多选按钮元素未找到');
    }
    
    // 旅游规划功能 - 使用全局travelAgent实例
    // 注意：travelAgent实例由travel-planning.js在DOM加载完成后创建
    let travelAgent = window.travelAgent;
    if (!travelAgent) {
        // 如果全局实例还未创建，等待DOM加载完成后再获取
        document.addEventListener('DOMContentLoaded', () => {
            travelAgent = window.travelAgent;
        });
    }
    



        
    
    
    // 添加设置保存事件
    if (saveSettingsBtn) {
        saveSettingsBtn.addEventListener('click', function() {
            saveUserSettings();
        });
    }
    
    // 添加头像上传事件
    if (uploadAvatarBtn) {
        uploadAvatarBtn.addEventListener('click', function() {
            // 创建文件输入元素
            const fileInput = document.createElement('input');
            fileInput.type = 'file';
            fileInput.accept = 'image/*';
            
            // 监听文件选择事件
            fileInput.addEventListener('change', function(e) {
                if (this.files && this.files[0]) {
                    const file = this.files[0];
                    
                    // 检查文件类型
                    if (!file.type.match('image.*')) {
                        alert('请选择图片文件');
                        return;
                    }
                    
                    // 检查文件大小（限制为2MB）
                    if (file.size > 2 * 1024 * 1024) {
                        alert('图片大小不能超过2MB');
                        return;
                    }
                    
                    // 直接上传文件
                    saveUserAvatar(file);
                }
            });
            
            // 触发文件选择对话框
            fileInput.click();
        });
    }
    
    // 添加默认头像事件
    if (defaultAvatarBtn) {
        defaultAvatarBtn.addEventListener('click', function() {
            resetToDefaultAvatar();
        });
    }
    
    // 切换内容区域函数
    function switchSection(sectionId) {
        // 移除所有内容区域的active类
        contentSections.forEach(section => {
            section.classList.remove('active');
        });
        
        // 移除所有菜单项的active类
        menuItems.forEach(item => {
            item.classList.remove('active');
        });
        
        // 添加active类到选中的内容区域和菜单项
        const targetSection = document.getElementById(`${sectionId}-section`);
        const targetMenuItem = document.querySelector(`.profile-menu li[data-section="${sectionId}"]`);
        
        if (targetSection) {
            targetSection.classList.add('active');
        }
        
        if (targetMenuItem) {
            targetMenuItem.classList.add('active');
        }
        
        // 更新URL哈希值，但不触发hashchange事件
        history.replaceState(null, null, `#${sectionId}`);
    }
    
    // 根据URL哈希切换内容区域
    function checkUrlHash() {
        const hash = window.location.hash.substring(1);
        if (hash && document.querySelector(`.profile-menu li[data-section="${hash}"]`)) {
            switchSection(hash);
        }
    }

    // 检查URL哈希值并切换到对应部分
    checkUrlHash();

    // 监听哈希变化事件
    window.addEventListener('hashchange', checkUrlHash);
    
    // 页面加载时检查URL哈希，如果没有哈希值则默认显示收藏页面
    if (!window.location.hash) {
        switchSection('favorites');
    }

    // 获取用户信息
    async function fetchUserInfo() {
        try {
            // 从用户资料API获取完整的用户信息
            const userData = await window.API.userProfile.getUserProfile();
            
            // 更新用户信息显示
            const displayName = userData.profile.display_name || userData.username;
            username.textContent = displayName;
            userEmail.textContent = userData.email;
            
            // 更新头像显示
            if (userData.profile && userData.profile.avatar) {
                updateAvatarDisplay(userData.profile.avatar);
            } else {
                // 如果头像为null或不存在，显示默认头像（用户名首字母）
                updateAvatarDisplay(null);
            }
            
            // 更新本地存储中的用户信息，包含头像数据
            localStorage.setItem('user', JSON.stringify({
                username: userData.username,
                userId: userData.id,
                email: userData.email,
                displayName: displayName,
                avatar: userData.profile && userData.profile.avatar ? userData.profile.avatar : null
            }));
        } catch (error) {
            console.error('获取用户信息错误:', error);
            // 如果获取用户信息失败，可能是登录已过期，清除本地存储并跳转到登录页面
            localStorage.removeItem('user');
            window.location.href = 'login.html';
        }
    }
    
    // 获取用户收藏列表
    function fetchUserFavorites() {
        // 始终从API获取最新收藏列表
        fetch('/api/favorites/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('获取收藏列表失败');
            }
            return response.json();
        })
        .then(data => {
            // 清空加载提示
            favoritesContainer.innerHTML = '';
            
            // 处理分页响应格式
            let favorites = data;
            if (data && data.results && Array.isArray(data.results)) {
                favorites = data.results;
            }
            
            // 检查是否有收藏项目
            if (!favorites || !Array.isArray(favorites) || favorites.length === 0) {
                favoritesContainer.innerHTML = '<div class="no-favorites">您还没有收藏任何非遗项目</div>';
                return;
            }
            
            // 渲染收藏列表
            renderFavorites(favorites);
        })
        .catch(error => {
            console.error('获取收藏列表错误:', error);
            favoritesContainer.innerHTML = '<div class="no-favorites">获取收藏列表失败，请稍后重试</div>';
        });
    }
    
    // 切换多选模式
    function toggleMultiSelect(enable) {
        console.log('切换多选模式:', enable);
        const checkboxes = document.querySelectorAll('.favorite-checkbox');
        const favoriteItems = document.querySelectorAll('.favorite-item');
        
        console.log('找到复选框数量:', checkboxes.length);
        console.log('找到收藏项目数量:', favoriteItems.length);
        
        if (enable) {
            // 显示多选操作栏
            if (multiSelectActions) {
                multiSelectActions.style.display = 'flex';
                console.log('显示多选操作栏');
            } else {
                console.warn('多选操作栏元素未找到');
            }
            
            // 显示复选框
            checkboxes.forEach(checkbox => {
                checkbox.style.display = 'block';
            });
            
            // 添加多选样式
            favoriteItems.forEach(item => {
                item.classList.add('multi-select-mode');
            });
            
            // 隐藏多选按钮
            if (multiSelectBtn) {
                multiSelectBtn.style.display = 'none';
                console.log('隐藏多选按钮');
            }
            
            // 重置选择计数
            updateSelectedCount();
        } else {
            // 隐藏多选操作栏
            if (multiSelectActions) {
                multiSelectActions.style.display = 'none';
                console.log('隐藏多选操作栏');
            }
            
            // 隐藏复选框并取消选中
            checkboxes.forEach(checkbox => {
                checkbox.style.display = 'none';
                const checkboxInput = checkbox.querySelector('input[type="checkbox"]');
                if (checkboxInput) {
                    checkboxInput.checked = false;
                }
            });
            
            // 移除多选样式
            favoriteItems.forEach(item => {
                item.classList.remove('multi-select-mode');
            });
            
            // 显示多选按钮
            if (multiSelectBtn) {
                multiSelectBtn.style.display = 'block';
                console.log('显示多选按钮');
            }
        }
    }
    
    // 更新已选择项目计数
    function updateSelectedCount() {
        if (!selectedCount) {
            console.warn('选择计数元素未找到');
            return;
        }
        
        const checkedBoxes = document.querySelectorAll('.select-checkbox:checked');
        console.log('已选择的项目数量:', checkedBoxes.length);
        selectedCount.textContent = `已选择 ${checkedBoxes.length} 项`;
    }
    
    // 获取选中的项目
    function getSelectedItems() {
        const selectedItems = [];
        const checkedBoxes = document.querySelectorAll('.select-checkbox:checked');
        
        checkedBoxes.forEach(checkbox => {
            const favoriteItem = checkbox.closest('.favorite-item');
            if (favoriteItem) {
                const itemId = favoriteItem.getAttribute('data-id');
                const itemName = favoriteItem.querySelector('h4')?.textContent || '未命名项目';
                const itemInfo = favoriteItem.querySelector('.favorite-info p')?.textContent || '';
                const [category, region] = itemInfo.split(' · ');
                
                selectedItems.push({
                    id: itemId,
                    name: itemName,
                    category: category || '未分类',
                    region: region || '未知地区'
                });
            }
        });
        
        return selectedItems;
    }
    
    // 导出旅游规划
    async function exportTravelPlan() {
        // 确保travelAgent已初始化
        if (!travelAgent) {
            alert('旅游规划功能未初始化，请刷新页面重试');
            return;
        }
        
        // 调用travelAgent的exportTravelPlan方法
        await travelAgent.exportTravelPlan();
    }
    
    // 渲染收藏列表
    function renderFavorites(favorites) {
        // 清空容器
        favoritesContainer.innerHTML = '';
        
        // 检查是否有收藏项目
        if (!Array.isArray(favorites) || favorites.length === 0) {
            favoritesContainer.innerHTML = '<div class="no-favorites">您还没有收藏任何非遗项目</div>';
            return;
        }
        
        // 渲染每个收藏项目
        favorites.forEach(favorite => {
            // 处理不同格式的收藏数据
            let heritage = favorite.heritage || favorite;
            
            const favoriteItem = document.createElement('div');
            favoriteItem.className = 'favorite-item';
            favoriteItem.setAttribute('data-id', heritage.id || (typeof favorite === 'number' ? favorite : 0));
            
            // 确保heritage对象有必要的属性
            const itemId = heritage.id || (typeof favorite === 'number' ? favorite : 0);
            const itemName = heritage.name || heritage.title || '未命名项目';
            const itemCategory = heritage.category || '未分类';
            const itemRegion = heritage.region || '未知地区';
            
            // 确保图片路径直接使用后端返回的 main_image_url 字段
            let imageUrl = '/static/common/default-heritage.jpg';
            
            if (heritage.main_image_url && typeof heritage.main_image_url === 'string' && heritage.main_image_url.trim()) {
                const rawImageUrlString = heritage.main_image_url.trim();
                
                if (rawImageUrlString.startsWith('http://') || rawImageUrlString.startsWith('https://')) {
                    // 完整的HTTP/HTTPS URL
                    imageUrl = rawImageUrlString;
                } else if (rawImageUrlString.startsWith('/')) {
                    // 绝对路径 (例如 /media/...)
                    imageUrl = rawImageUrlString;
                } else {
                    // 不是完整URL或绝对路径，记录警告
                    console.warn(`图片URL "${rawImageUrlString}" 不是预期的格式 (完整的URL或绝对路径)。将使用默认图片。`);
                }
            }
            
            // 添加多选复选框
            const checkboxHtml = `<div class="favorite-checkbox"><input type="checkbox" class="select-checkbox"></div>`;
            
            favoriteItem.innerHTML = `
                ${checkboxHtml}
                <div class="favorite-image" data-bg-image="${imageUrl}"></div>
                <div class="favorite-info">
                    <h4>${itemName}</h4>
                    <p>${itemCategory} · ${itemRegion}</p>
                    <div class="favorite-actions">
                        <button class="view-btn" data-id="${itemId}">查看详情</button>
                        <button class="remove-btn" data-id="${favorite.id || itemId}">取消收藏</button>
                    </div>
                </div>
            `;
            
            // 确保复选框在DOM中正确渲染
            const checkboxElement = favoriteItem.querySelector('.favorite-checkbox');
            if (checkboxElement) {
                // 如果当前处于多选模式，显示复选框
                if (multiSelectActions && multiSelectActions.style.display === 'flex') {
                    checkboxElement.style.display = 'block';
                    favoriteItem.classList.add('multi-select-mode');
                }
            }
            
            favoritesContainer.appendChild(favoriteItem);
            
            // 添加查看详情按钮事件
            favoriteItem.querySelector('.view-btn').addEventListener('click', function() {
                const heritageId = this.getAttribute('data-id');
                if (heritageId && heritageId > 0) {
                    window.location.href = `heritage-detail.html?id=${heritageId}`;
                } else {
                    console.warn('无效的非遗项目ID:', heritageId);
                }
            });
            
            // 添加取消收藏按钮事件
            favoriteItem.querySelector('.remove-btn').addEventListener('click', function() {
                const favoriteId = this.getAttribute('data-id');
                removeFavorite(favoriteId, favoriteItem);
            });
            
            // 添加复选框事件
            const checkbox = favoriteItem.querySelector('.select-checkbox');
            if (checkbox) {
                checkbox.addEventListener('change', function() {
                    updateSelectedCount();
                });
            }
        });
    }
    
    // 取消收藏
    async function removeFavorite(favoriteId, favoriteItem) {
        // 确保在发出DELETE请求之前设置了CSRF cookie
        try {
            await fetch('/api/auth/csrf/');
            console.log('为removeFavorite调用了CSRF令牌端点。');
        } catch (csrfError) {
            console.warn('获取CSRF令牌失败，将继续使用现有cookie（如有）:', csrfError);
            // 即使此操作失败，也要继续，因为cookie可能已经设置
        }
        
        fetch(`/api/favorites/${favoriteId}/`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            credentials: 'include'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('取消收藏失败');
            }
            // 从DOM中移除该收藏项
            favoriteItem.remove();
            
            // 检查是否还有收藏项
            if (favoritesContainer.children.length === 0) {
                favoritesContainer.innerHTML = '<div class="no-favorites">您还没有收藏任何非遗项目</div>';
            }
        })
        .catch(error => {
            console.error('取消收藏错误:', error);
            alert('取消收藏失败，请稍后重试');
        });
    }
    
    // 加载用户统计数据
    async function loadUserStats() {
        try {
            const response = await fetch('/api/user/stats/', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include'
            });
            if (response.ok) {
                const stats = await response.json();
                favoritesCount.textContent = stats.favorites_count;
                visitsCount.textContent = stats.visits_count;
                commentsCount.textContent = stats.comments_count;
                followingTotal.textContent = stats.following_count;
                followersTotal.textContent = stats.followers_count;
            } else {
                // 如果API请求失败，使用默认值
                favoritesCount.textContent = '0';
                visitsCount.textContent = '0';
                commentsCount.textContent = '0';
                followingTotal.textContent = '0';
                followersTotal.textContent = '0';
            }
        } catch (error) {
            console.error('获取用户统计数据失败:', error);
            // 如果发生错误，使用默认值
            favoritesCount.textContent = '0';
            visitsCount.textContent = '0';
            commentsCount.textContent = '0';
            followingTotal.textContent = '0';
            followersTotal.textContent = '0';
        }
    }
    
    // 获取浏览历史
    async function fetchBrowsingHistory() {
        if (!historyContainer) return;

        try {
            // 从API获取浏览历史
            const response = await fetch('/api/history/?page=1&page_size=20', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error(`API错误: ${response.status}`);
            }

            const data = await response.json();
            console.log('[ProfilePage] Received history from API:', data);
            
            if (data && Array.isArray(data.results)) {
                renderBrowsingHistory(data.results);
            } else {
                renderBrowsingHistory([]); // 传递空数组以正确处理UI
            }
        } catch (error) {
            console.error('获取浏览历史失败:', error);
            historyContainer.innerHTML = '<div class="no-history">获取浏览历史失败</div>';
        }
    }

    // 辅助函数：获取当前登录用户 (如果尚未定义)
    function getCurrentUser() {
        const userString = localStorage.getItem('user');
        return userString ? JSON.parse(userString) : null;
    }
    
    // 渲染浏览历史
    function renderBrowsingHistory(history) {
        // 清空容器
        historyContainer.innerHTML = '';
        
        // 如果没有历史记录
        if (!history || history.length === 0) {
            historyContainer.innerHTML = '<div class="no-history">暂无浏览历史</div>';
            return; // 没有历史记录，不显示清除按钮
        }

        // 添加清除历史记录按钮 (仅当有历史记录时)
        const clearHistoryBtn = document.createElement('button');
        clearHistoryBtn.className = 'btn clear-history-btn';
        clearHistoryBtn.textContent = '清除历史记录';
        clearHistoryBtn.addEventListener('click', clearBrowsingHistory);
        
        const historyHeader = document.createElement('div');
        historyHeader.className = 'history-header';
        historyHeader.appendChild(clearHistoryBtn);
        historyContainer.appendChild(historyHeader);
        
        // 按访问时间倒序排序 (确保 visitTime 存在且有效)
        history.sort((a, b) => {
            const dateA = a.visit_time || a.visitTime; // 兼容后端字段名 visit_time
            const dateB = b.visit_time || b.visitTime;
            return new Date(dateB) - new Date(dateA);
        });
        
        // 最多显示20条记录
        const recentHistory = history.slice(0, 20);
        
        // 创建历史记录列表容器
        const historyList = document.createElement('div');
        historyList.className = 'history-list';
        historyContainer.appendChild(historyList);
        
        // 渲染每条历史记录
        recentHistory.forEach(item => {
            const historyItem = document.createElement('div');
            historyItem.className = 'history-item';
            
            // 格式化日期 - 使用date-utils.js中的函数
            const visitDate = new Date(item.visit_time || item.visitTime);
            // 使用自定义格式选项创建日期格式
            const dateFormatOptions = {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                hour12: false
            };
            // 使用dateUtils格式化日期
            let formattedDate = '';
            try {
                formattedDate = visitDate.toLocaleDateString('zh-CN', dateFormatOptions).replace(/\//g, '-');
            } catch (e) {
                console.warn('日期格式化失败:', e);
                formattedDate = '未知日期';
            }
            
            // 确保图片路径直接使用后端返回的URL
            let imageUrl = '/static/common/default-heritage.jpg';
            
            // 兼容后端返回的不同字段名
            const itemImage = item.image_url || item.imageUrl || item.main_image_url || item.mainImageUrl;
            
            if (itemImage) {
                if (itemImage.startsWith('http://') || itemImage.startsWith('https://')) {
                    // 完整的HTTP/HTTPS URL
                    imageUrl = itemImage;
                } else if (itemImage.startsWith('/')) {
                    // 绝对路径 (例如 /media/...)
                    imageUrl = itemImage;
                } else {
                    // 记录意外的相对路径或格式错误的URL
                    console.warn(`浏览历史中的图片URL "${itemImage}" 不是预期的格式 (完整URL或绝对路径)。将使用默认图片。`);
                }
            }
            
            historyItem.innerHTML = `
                <div class="history-image" data-bg-image="${imageUrl}"></div>
                <div class="history-info">
                    <h4>${item.name || '未知项目'}</h4>
                    <div class="history-meta">
                        <span>${item.category || '未分类'} · ${item.region || '未知地区'}</span>
                        <span class="history-date">${formattedDate}</span>
                    </div>
                </div>
            `;
            
            // 添加点击事件
            historyItem.addEventListener('click', function() {
                if (item.id && item.id > 0) {
                    window.location.href = `heritage-detail.html?id=${item.id}`;
                } else {
                    console.warn('无效的历史记录项目ID:', item.id);
                }
            });
            
            historyList.appendChild(historyItem);
        });
    }
    
    // 清除浏览历史
    async function clearBrowsingHistory() {
        if (confirm('确定要清除所有浏览历史吗？')) {
            try {
                const csrfToken = getCookie('csrftoken'); 
                if (!csrfToken) {
                    console.warn('CSRF token not found. Clear history operation might fail.');
                }

                const response = await fetch('/api/history/clear/', {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken // 使用获取到的csrfToken
                    },
                    credentials: 'include'
                });

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.message || `API清除历史失败: ${response.status}`);
                }
                console.log('[ProfilePage] Browsing history cleared on server.');
                
                // 更新显示 - API调用成功，更新UI为已清除状态
                renderBrowsingHistory([]); // 传递空数组以显示“暂无浏览历史”并移除清除按钮
                
                // 更新统计数据
                if (visitsCount) {
                    visitsCount.textContent = '0';
                }
            } catch (apiError) {
                console.error('API清除浏览历史失败:', apiError);
                alert('清除浏览历史失败，请稍后重试。');
            }
        }
    }
    
    // 初始化设置表单
    function initSettingsForm() {
        if (!displayNameInput || !userBioInput || !settingsAvatar) return;
        
        // 从API获取用户资料
        window.API.userProfile.getUserProfile()
            .then(userData => {
                // 设置表单初始值
                displayNameInput.value = userData.profile.display_name || userData.username || '';
                userBioInput.value = userData.profile.bio || '';
            })
            .catch(error => {
                console.error('加载用户设置失败:', error);
            });
    }
    
    // 加载用户头像
    async function loadUserAvatar() {
        if (!userAvatar || !settingsAvatar) return;
        
        try {
            // 从API获取用户资料，包括头像
            const userData = await window.API.userProfile.getUserProfile();
            
            // 检查是否有头像
            if (userData.profile && userData.profile.avatar) {
                // 使用API返回的头像URL
                updateAvatarDisplay(userData.profile.avatar);
            } else {
                // 使用默认头像（用户名首字母）
                const firstLetter = userData.username ? userData.username.charAt(0).toUpperCase() : 'U';
                userAvatar.textContent = firstLetter;
                settingsAvatar.textContent = firstLetter;
            }
        } catch (error) {
            console.error('加载头像失败:', error);
            
            // 加载失败时使用默认头像
            const user = JSON.parse(localStorage.getItem('user')) || {};
            const firstLetter = user.username ? user.username.charAt(0).toUpperCase() : 'U';
            userAvatar.textContent = firstLetter;
            settingsAvatar.textContent = firstLetter;
        }
    }
    
    // 保存用户设置
    async function saveUserSettings() {
        // 获取表单值
        const displayName = displayNameInput.value.trim();
        const userBio = userBioInput.value.trim();
        
        if (!displayName) {
            alert('显示名称不能为空');
            return;
        }
        
        try {
            // 准备要更新的资料数据
            const profileData = {
                profile: {
                    display_name: displayName,
                    bio: userBio
                }
            };
            
            // 调用API更新用户资料
            const updatedUser = await window.API.userProfile.updateUserProfile(profileData);
            
            // 重新获取用户信息以更新页面显示
            await fetchUserInfo();
            
            // 显示成功消息
            alert('设置已保存');
        } catch (error) {
            console.error('保存设置失败:', error);
            alert('保存设置失败: ' + error.message);
        }
    }
    
    // 保存用户头像
    async function saveUserAvatar(avatarData) {
        try {
            // 如果是null，清除头像（设置为默认头像）
            if (avatarData === null) {
                await window.API.userProfile.clearUserAvatar();
                // 立即更新头像显示为默认头像
                updateAvatarDisplay(null);
                // 重新获取用户信息以更新本地存储
                await fetchUserInfo();
                // 刷新页面以确保所有头像显示正确
                window.location.reload();
                return;
            }
            
            // 如果是File对象，直接上传
            if (avatarData instanceof File) {
                await window.API.userProfile.uploadUserAvatar(avatarData);
                // 立即更新头像显示
                const objectUrl = URL.createObjectURL(avatarData);
                updateAvatarDisplay(objectUrl);
                // 重新获取用户信息以更新本地存储
                await fetchUserInfo();
                // 触发全局头像更新，确保其他页面同步显示
                if (typeof window.updateUserIcon === 'function') {
                    window.updateUserIcon();
                }
                // 刷新页面以确保所有头像显示正确
                window.location.reload();
                return;
            }
            
            // 如果是Base64字符串，需要转换为File对象
            if (typeof avatarData === 'string' && avatarData.startsWith('data:')) {
                // 将Base64转换为Blob
                const response = await fetch(avatarData);
                const blob = await response.blob();
                
                // 创建File对象
                const file = new File([blob], 'avatar.png', { type: 'image/png' });
                
                // 上传头像
                await window.API.userProfile.uploadUserAvatar(file);
                // 立即更新头像显示
                updateAvatarDisplay(avatarData);
                // 重新获取用户信息以更新本地存储
                await fetchUserInfo();
                // 触发全局头像更新，确保其他页面同步显示
                if (typeof window.updateUserIcon === 'function') {
                    window.updateUserIcon();
                }
                // 刷新页面以确保所有头像显示正确
                window.location.reload();
                return;
            }
            
            // 如果是URL字符串，需要下载并上传
            if (typeof avatarData === 'string' && (avatarData.startsWith('http') || avatarData.startsWith('/'))) {
                try {
                    // 确保URL是绝对路径
                    let avatarUrl = avatarData;
                    if (avatarData.startsWith('/')) {
                        avatarUrl = window.location.origin + avatarData;
                    }
                    
                    // 下载图片
                    const response = await fetch(avatarUrl);
                    if (!response.ok) {
                        throw new Error(`下载头像失败: ${response.status}`);
                    }
                    
                    const blob = await response.blob();
                    const file = new File([blob], 'avatar.png', { type: blob.type });
                    
                    // 上传头像
                    await window.API.userProfile.uploadUserAvatar(file);
                    // 立即更新头像显示
                    updateAvatarDisplay(avatarUrl);
                    // 重新获取用户信息以更新本地存储
                    await fetchUserInfo();
                    // 触发全局头像更新，确保其他页面同步显示
                    if (typeof window.updateUserIcon === 'function') {
                        window.updateUserIcon();
                    }
                } catch (error) {
                    console.error('处理URL头像失败:', error);
                    throw new Error('处理头像URL失败: ' + error.message);
                }
                return;
            }
            
            // 如果是不支持的类型
            throw new Error('不支持的头像数据类型');
            
        } catch (error) {
            console.error('保存头像失败:', error);
            throw error; // 重新抛出错误，让调用者处理
        }
    }
    
    // 更新头像显示
    function updateAvatarDisplay(avatarData) {
        // 如果没有传入头像数据，尝试从本地存储获取
        if (!avatarData) {
            const user = JSON.parse(localStorage.getItem('user')) || {};
            avatarData = user.avatar;
        }
        
        // 检查是否为null或空值（表示使用默认头像）
        if (!avatarData || avatarData === null) {
            // 显示用户名首字母作为默认头像
            const user = JSON.parse(localStorage.getItem('user')) || {};
            const firstLetter = user.username ? user.username.charAt(0).toUpperCase() : 'U';
            
            userAvatar.textContent = firstLetter;
            if (settingsAvatar) {
                settingsAvatar.textContent = firstLetter;
            }
            
            // 移除可能存在的背景图像
            userAvatar.style.backgroundImage = '';
            if (settingsAvatar) {
                settingsAvatar.style.backgroundImage = '';
            }
            
            // 确保样式正确
            userAvatar.style.backgroundSize = '';
            userAvatar.style.backgroundPosition = '';
            if (settingsAvatar) {
                settingsAvatar.style.backgroundSize = '';
                settingsAvatar.style.backgroundPosition = '';
            }
            return;
        }
        
        // 清空文本内容
        userAvatar.textContent = '';
        if (settingsAvatar) {
            settingsAvatar.textContent = '';
        }
        
        // 处理不同类型的头像数据
        let avatarUrl = avatarData;
        
        // 如果是API返回的相对URL，需要添加域名
        if (typeof avatarData === 'string' && avatarData.startsWith('/media/')) {
            // 使用当前域名
            avatarUrl = window.location.origin + avatarData;
        }
        
        // 如果是预设头像的静态路径，确保使用绝对路径
        if (typeof avatarData === 'string' && avatarData.startsWith('/static/images/avatars/')) {
            avatarUrl = window.location.origin + avatarData;
        }
        
        // 设置背景图像为头像
        userAvatar.style.backgroundImage = `url(${avatarUrl})`;
        if (settingsAvatar) {
            settingsAvatar.style.backgroundImage = `url(${avatarUrl})`;
        }
        
        // 添加样式以确保图像正确显示
        userAvatar.style.backgroundSize = 'cover';
        userAvatar.style.backgroundPosition = 'center';
        if (settingsAvatar) {
            settingsAvatar.style.backgroundSize = 'cover';
            settingsAvatar.style.backgroundPosition = 'center';
        }
    }
    
    // 重置为默认头像
    function resetToDefaultAvatar() {
        // 创建默认头像选择对话框
        const defaultAvatarDialog = document.createElement('div');
        defaultAvatarDialog.className = 'default-avatar-dialog';
        defaultAvatarDialog.innerHTML = `
            <div class="dialog-content">
                <h3>选择默认头像</h3>
                <div class="default-avatars-grid">
                    <div class="default-avatar-option letter" data-type="letter">文字</div>
                    <div class="default-avatar-option" data-type="avatar1" data-bg-image="/static/images/avatars/avatar1.png"></div>
                    <div class="default-avatar-option" data-type="avatar2" data-bg-image="/static/images/avatars/avatar2.png"></div>
                    <div class="default-avatar-option" data-type="avatar3" data-bg-image="/static/images/avatars/avatar3.png"></div>
                    <div class="default-avatar-option" data-type="avatar4" data-bg-image="/static/images/avatars/avatar4.png"></div>
                </div>
                <div class="dialog-buttons">
                    <button class="btn cancel-btn">取消</button>
                </div>
            </div>
        `;
        
        // 添加到页面
        document.body.appendChild(defaultAvatarDialog);
        
        // 添加样式
        const style = document.createElement('style');
        style.textContent = `
            .default-avatar-dialog {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.5);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 1000;
            }
            .dialog-content {
                background-color: white;
                padding: 20px;
                border-radius: 8px;
                width: 400px;
                max-width: 90%;
            }
            .default-avatars-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 15px;
                margin: 20px 0;
            }
            .default-avatar-option {
                width: 80px;
                height: 80px;
                border-radius: 50%;
                background-color: #f0f0f0;
                display: flex;
                justify-content: center;
                align-items: center;
                cursor: pointer;
                background-size: cover;
                background-position: center;
                border: 2px solid transparent;
            }
            .default-avatar-option:hover {
                border-color: #007bff;
            }
            .default-avatar-option.letter {
                font-size: 32px;
                font-weight: bold;
            }
            .dialog-buttons {
                display: flex;
                justify-content: flex-end;
            }
        `;
        document.head.appendChild(style);
        
        // 设置预设头像的背景图像
        const avatarOptions = defaultAvatarDialog.querySelectorAll('.default-avatar-option');
        avatarOptions.forEach(option => {
            const bgImage = option.getAttribute('data-bg-image');
            if (bgImage) {
                option.style.backgroundImage = `url(${bgImage})`;
            }
        });
        
        // 添加事件监听器
        avatarOptions.forEach(option => {
            option.addEventListener('click', async function() {
                const type = this.getAttribute('data-type');
                
                try {
                    if (type === 'letter') {
                        // 使用用户名首字母 - 清除头像
                        await saveUserAvatar(null);
                        
                        // 更新头像显示
                        const user = JSON.parse(localStorage.getItem('user')) || {};
                        const firstLetter = user.username ? user.username.charAt(0).toUpperCase() : 'U';
                        
                        userAvatar.textContent = firstLetter;
                        if (settingsAvatar) {
                            settingsAvatar.textContent = firstLetter;
                        }
                        
                        // 移除背景图像
                        userAvatar.style.backgroundImage = '';
                        if (settingsAvatar) {
                            settingsAvatar.style.backgroundImage = '';
                        }
                        
                        // 更新本地存储
                        const updatedUser = JSON.parse(localStorage.getItem('user')) || {};
                        updatedUser.avatar = null;
                        localStorage.setItem('user', JSON.stringify(updatedUser));
                        
                        // 触发全局头像更新，确保其他页面同步显示
                        if (typeof window.updateUserIcon === 'function') {
                            window.updateUserIcon();
                        }
                        
                        alert('头像已成功设置为文字头像');
                    } else {
                        // 使用预设头像 - 需要将图片转换为文件上传
                        const bgImage = this.getAttribute('data-bg-image');
                        if (bgImage) {
                            try {
                                // 获取图片文件
                                const response = await fetch(bgImage);
                                const blob = await response.blob();
                                const file = new File([blob], 'default_avatar.png', { type: 'image/png' });
                                
                                // 上传头像
                                await saveUserAvatar(file);
                                
                                // 更新本地存储，保存预设头像的URL
                                const updatedUser = JSON.parse(localStorage.getItem('user')) || {};
                                updatedUser.avatar = bgImage; // 保存预设头像的URL
                                localStorage.setItem('user', JSON.stringify(updatedUser));
                                
                                // 立即更新头像显示
                                updateAvatarDisplay(bgImage);
                                
                                // 触发全局头像更新，确保其他页面同步显示
                                if (typeof window.updateUserIcon === 'function') {
                                    window.updateUserIcon();
                                }
                                
                                alert('头像已成功设置为默认头像');
                            } catch (error) {
                                console.error('加载默认头像失败:', error);
                                alert('设置默认头像失败，请稍后重试');
                            }
                        }
                    }
                } catch (error) {
                    console.error('设置头像失败:', error);
                    alert('设置头像失败: ' + error.message);
                }
                
                // 关闭对话框
                document.body.removeChild(defaultAvatarDialog);
                document.head.removeChild(style);
            });
        });
        
        // 取消按钮
        const cancelBtn = defaultAvatarDialog.querySelector('.cancel-btn');
        cancelBtn.addEventListener('click', function() {
            document.body.removeChild(defaultAvatarDialog);
            document.head.removeChild(style);
        });
    }
    
    // 排序收藏列表
    async function sortFavorites(sortType) {
        try {
            // 从API获取排序后的收藏列表
            const response = await fetch(`/api/favorites/?sort=${sortType}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error('获取收藏列表失败');
            }
            
            const data = await response.json();
            
            // 重新渲染收藏列表
            renderFavorites(data.results);
        } catch (error) {
            console.error('排序收藏列表失败:', error);
        }
    }
    
    // 退出登录
    async function logout() {
        // Ensure CSRF cookie is set before making a POST request
        try {
            await fetch('/api/auth/csrf/');
            console.log('CSRF token endpoint called for logout.');
        } catch (csrfError) {
            console.warn('Failed to fetch CSRF token, proceeding with existing cookie if any:', csrfError);
            // Proceed even if this fails, as the cookie might already be set
        }
        
        fetch('/api/auth/logout/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            credentials: 'include'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('登出失败');
            }
            return response.json();
        })
        .then(data => {
            // 清除本地存储中的用户信息
            localStorage.removeItem('user');
            // 跳转到首页
            window.location.href = '../index.html';
        })
        .catch(error => {
            console.error('登出错误:', error);
            // 即使API调用失败，也清除本地存储并跳转
            localStorage.removeItem('user');
            window.location.href = '../index.html';
        });
    }
    
    // 使用公共的getCookie函数（已在utils.js中定义）
    
    // 获取关注列表
    async function fetchFollowingList() {
        try {
            const response = await ForumAPI.getFollowingList();
            // apiRequest直接返回JSON数据，不需要检查response.success
            if (response && response.results) {
                displayFollowingList(response.results);
                followingTotal.textContent = response.count || 0;
            } else {
                followingContainer.innerHTML = '<div class="empty-state">暂无关注的用户</div>';
            }
        } catch (error) {
            console.error('获取关注列表失败:', error);
            followingContainer.innerHTML = '<div class="error-state">加载失败，请刷新重试</div>';
        }
    }
    
    // 获取粉丝列表
    async function fetchFollowersList() {
        try {
            const response = await ForumAPI.getFollowersList();
            // 后端直接返回分页数据，不包装在success字段中
            if (response && response.results) {
                displayFollowersList(response.results);
                followersTotal.textContent = response.count || 0;
            } else {
                followersContainer.innerHTML = '<div class="empty-state">暂无粉丝</div>';
                followersTotal.textContent = '0';
            }
        } catch (error) {
            console.error('获取粉丝列表失败:', error);
            followersContainer.innerHTML = '<div class="error-state">加载失败，请刷新重试</div>';
            followersTotal.textContent = '0';
        }
    }
    
    // 显示关注列表
    function displayFollowingList(followingList) {
        if (!followingList || followingList.length === 0) {
            followingContainer.innerHTML = '<div class="empty-state">暂无关注的用户</div>';
            return;
        }
        
        const html = followingList.map(item => {
            // 处理头像URL
            let avatarUrl = item.user.avatar || '/static/images/default-avatar.png';
            if (avatarUrl.startsWith('/media/')) {
                avatarUrl = window.location.origin + avatarUrl;
            }
            
            return `
            <div class="user-item" data-user-id="${item.user.id}">
                <div class="user-avatar">
                    <img src="${avatarUrl}" alt="${item.user.display_name}">
                </div>
                <div class="user-info">
                    <div class="user-name">${item.user.display_name}</div>
                    <div class="user-bio">${item.user.bio || '这个人很懒，什么都没写~'}</div>
                    <div class="user-stats">
                        <span>发帖 ${item.user.post_count}</span>
                        <span>粉丝 ${item.user.followers_count}</span>
                        <span>关注 ${item.user.following_count}</span>
                    </div>
                    <div class="follow-time">关注于 ${new Date(item.created_at).toLocaleDateString()}</div>
                </div>
                <div class="user-actions">
                    <button class="btn unfollow-btn" onclick="toggleFollow(${item.user.id}, this)">取消关注</button>
                </div>
            </div>
        `;
        }).join('');
        
        followingContainer.innerHTML = html;
    }
    
    // 显示粉丝列表
    function displayFollowersList(followersList) {
        if (!followersList || followersList.length === 0) {
            followersContainer.innerHTML = '<div class="empty-state">暂无粉丝</div>';
            return;
        }
        
        const html = followersList.map(item => {
            // 处理头像URL
            let avatarUrl = item.user.avatar || '/static/images/default-avatar.png';
            if (avatarUrl.startsWith('/media/')) {
                avatarUrl = window.location.origin + avatarUrl;
            }
            
            return `
            <div class="user-item" data-user-id="${item.user.id}">
                <div class="user-avatar">
                    <img src="${avatarUrl}" alt="${item.user.display_name}">
                </div>
                <div class="user-info">
                    <div class="user-name">${item.user.display_name}</div>
                    <div class="user-bio">${item.user.bio || '这个人很懒，什么都没写~'}</div>
                    <div class="user-stats">
                        <span>发帖 ${item.user.post_count}</span>
                        <span>粉丝 ${item.user.followers_count}</span>
                        <span>关注 ${item.user.following_count}</span>
                    </div>
                    <div class="follow-time">关注于 ${new Date(item.created_at).toLocaleDateString()}</div>
                </div>
                <div class="user-actions">
                    ${item.is_mutual ? 
                        '<button class="btn unfollow-btn" onclick="toggleFollow(' + item.user.id + ', this)">取消关注</button>' : 
                        '<button class="btn follow-btn" onclick="toggleFollow(' + item.user.id + ', this)">回关</button>'
                    }
                </div>
            </div>
        `;
        }).join('');
        
        followersContainer.innerHTML = html;
    }
    
    // 切换关注状态
    window.toggleFollow = async function(userId, button) {
        try {
            const response = await ForumAPI.toggleUserFollow(userId);
            // 后端直接返回数据，不包装在success字段中
            if (response && typeof response.is_followed !== 'undefined') {
                // 更新按钮状态
                if (response.is_followed) {
                    button.textContent = '取消关注';
                    button.className = 'btn unfollow-btn';
                } else {
                    button.textContent = '关注';
                    button.className = 'btn follow-btn';
                }
                
                // 显示成功提示
                const message = response.is_followed ? '关注成功！' : '取消关注成功！';
                // 可以添加一个简单的成功提示
                const toast = document.createElement('div');
                toast.className = 'toast-message';
                toast.textContent = message;
                toast.style.cssText = 'position:fixed;top:20px;right:20px;background:#4CAF50;color:white;padding:10px 20px;border-radius:4px;z-index:9999;';
                document.body.appendChild(toast);
                setTimeout(() => document.body.removeChild(toast), 3000);
                
                // 刷新列表
                fetchFollowingList();
                fetchFollowersList();
            } else {
                alert('操作失败，请重试');
            }
        } catch (error) {
            console.error('关注操作失败:', error);
            // 检查是否是网络错误或服务器错误
            if (error.status) {
                alert(`操作失败：${error.status} ${error.data?.detail || '服务器错误'}`);
            } else {
                alert('网络错误，请检查网络连接后重试');
            }
        }
    };
});