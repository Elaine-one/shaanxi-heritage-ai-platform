// 帖子详情页JavaScript逻辑

class ForumPostManager {
    constructor() {
        this.postId = this.getPostIdFromUrl();
        this.currentCommentSort = 'time_asc';
        this.currentCommentPage = 1;
        this.hasMoreComments = true;
        this.isLoadingComments = false;
        this.commentEditor = null;
        this.postData = null;
        this.commentsData = [];
        
        this.init();
    }
    
    init() {
        if (!this.postId) {
            this.showError('帖子ID无效');
            return;
        }
        
        this.bindEvents();
        this.initializeCommentEditor();
        this.loadPost();
        this.loadComments();
        this.updateUserIcon();
        this.initScrollToTop();
    }
    
    getPostIdFromUrl() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('id');
    }
    
    bindEvents() {
        // 帖子操作按钮
        document.getElementById('likeBtn').addEventListener('click', () => {
            this.toggleLike();
        });
        
        document.getElementById('favoriteBtn').addEventListener('click', () => {
            this.toggleFavorite();
        });
        
        document.getElementById('shareBtn').addEventListener('click', () => {
            this.showShareModal();
        });
        
        document.getElementById('reportBtn').addEventListener('click', () => {
            this.showReportModal();
        });
        
        document.getElementById('followBtn').addEventListener('click', () => {
            this.toggleFollow();
        });
        
        // 评论展开/收起按钮
        document.getElementById('commentToggleBtn').addEventListener('click', () => {
            this.toggleCommentsSection();
        });
        
        // 更多操作按钮
        document.getElementById('moreBtn').addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleMoreMenu();
        });
        
        // 点击其他地方关闭菜单
        document.addEventListener('click', () => {
            this.hideMoreMenu();
        });
        
        // 管理员操作按钮
        document.getElementById('editPostBtn').addEventListener('click', () => {
            this.editPost();
        });
        
        document.getElementById('deletePostBtn').addEventListener('click', () => {
            this.deletePost();
        });
        
        document.getElementById('pinPostBtn').addEventListener('click', () => {
            this.togglePin();
        });
        
        document.getElementById('featurePostBtn').addEventListener('click', () => {
            this.toggleFeature();
        });
        
        // 评论排序
        document.querySelectorAll('.sort-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.handleCommentSort(e.target.dataset.sort);
            });
        });
        
        // 加载更多评论
        document.getElementById('loadMoreCommentsBtn').addEventListener('click', () => {
            this.loadMoreComments();
        });
        
        // 发表评论
        document.getElementById('submitCommentBtn').addEventListener('click', () => {
            this.submitComment();
        });
        
        // 模态框事件
        this.bindModalEvents();
        
        // 工具栏按钮
        this.bindToolbarEvents();
    }
    
    bindModalEvents() {
        // 分享模态框
        const shareModal = document.getElementById('shareModal');
        const closeShareModal = document.getElementById('closeShareModal');
        
        closeShareModal.addEventListener('click', () => {
            this.hideShareModal();
        });
        
        shareModal.addEventListener('click', (e) => {
            if (e.target === shareModal) {
                this.hideShareModal();
            }
        });
        
        document.getElementById('copyLinkBtn').addEventListener('click', () => {
            this.copyShareLink();
        });
        
        document.getElementById('generateQRBtn').addEventListener('click', () => {
            this.generateQRCode();
        });
        
        document.getElementById('copyBtn').addEventListener('click', () => {
            this.copyShareLink();
        });
        
        // 举报模态框
        const reportModal = document.getElementById('reportModal');
        const closeReportModal = document.getElementById('closeReportModal');
        const cancelReport = document.getElementById('cancelReport');
        const reportForm = document.getElementById('reportForm');
        
        closeReportModal.addEventListener('click', () => {
            this.hideReportModal();
        });
        
        cancelReport.addEventListener('click', () => {
            this.hideReportModal();
        });
        
        reportModal.addEventListener('click', (e) => {
            if (e.target === reportModal) {
                this.hideReportModal();
            }
        });
        
        reportForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitReport();
        });
    }
    
    bindToolbarEvents() {
        // 表情按钮
        document.getElementById('emojiBtn').addEventListener('click', () => {
            this.showEmojiPicker();
        });
        
        // 图片上传按钮
        document.getElementById('imageBtn').addEventListener('click', () => {
            this.uploadImage();
        });
        
        // @用户按钮
        document.getElementById('mentionBtn').addEventListener('click', () => {
            this.showUserMention();
        });
    }
    
    initializeCommentEditor() {
        // 初始化Quill富文本编辑器
        if (typeof Quill !== 'undefined') {
            this.commentEditor = new Quill('#commentEditor', {
                theme: 'snow',
                placeholder: '请输入评论内容...',
                modules: {
                    toolbar: [
                        ['bold', 'italic'],
                        ['link', 'image'],
                        [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                        ['clean']
                    ]
                }
            });
            
            // 监听内容变化
            this.commentEditor.on('text-change', (delta, oldDelta, source) => {
                const length = this.commentEditor.getLength() - 1;
                this.updateCommentCharCount(length);
                this.updateSubmitButton(length > 0);
            });
            
            // 初始化时设置按钮状态
            this.updateSubmitButton(false);
            this.updateCommentCharCount(0);
        }
    }
    
    async loadPost() {
        try {
            const post = await forumAPI.getPostDetail(this.postId);
            this.postData = post;
            this.renderPost(post);
            this.updatePageTitle(post.title);
            this.updatePageMeta(post);
            
            const viewResult = await forumAPI.incrementViewCount(this.postId);
            if (viewResult && viewResult.view_count !== undefined) {
                const viewCountEl = document.getElementById('viewCount');
                if (viewCountEl) {
                    viewCountEl.textContent = viewResult.view_count;
                }
                this.postData.view_count = viewResult.view_count;
            }
            
        } catch (error) {
            console.error('加载帖子失败:', error);
            this.showError('帖子不存在或已被删除');
        }
    }
    
    renderPost(post) {
        // 隐藏骨架屏
        document.getElementById('postSkeleton').style.display = 'none';
        document.getElementById('postContentWrapper').style.display = 'block';
        
        // 渲染作者信息
        const authorAvatar = document.getElementById('authorAvatar');
        if (authorAvatar) {
            if (post.author.avatar) {
                authorAvatar.innerHTML = `<img src="${post.author.avatar}" alt="${post.author.username}" class="author-avatar-img">`;
            } else {
                authorAvatar.innerHTML = `<div class="author-avatar-placeholder">${post.author.username.charAt(0).toUpperCase()}</div>`;
            }
        }
        
        document.getElementById('authorName').textContent = post.author.username;
        document.getElementById('authorLevel').textContent = `Lv.${post.author.level || 1}`;
        document.getElementById('postTime').textContent = this.formatDateTime(post.created_at);
        
        // 渲染帖子内容
        document.getElementById('postTitle').textContent = post.title;
        document.getElementById('postContent').innerHTML = post.content;
        
        // 渲染标签
        const tagsContainer = document.getElementById('postTags');
        tagsContainer.innerHTML = post.tags.map(tag => {
            // 处理对象类型的标签，提取name属性
            const tagName = typeof tag === 'object' && tag !== null ? tag.name || tag.tag : tag;
            return `<a href="/pages/forum.html?tag=${encodeURIComponent(tagName)}" class="post-tag">${tagName}</a>`;
        }).join('');
        
        // 更新操作按钮状态
        this.updateActionButtons(post);
        
        // 异步检查管理员权限并显示操作按钮
        this.canManagePost(post).then(canManage => {
            if (canManage) {
                this.updateAdminButtons(post);
            }
        }).catch(error => {
            console.error('[forum-post.js] Error checking manage permission:', error);
        });
        
        // 绑定作者头像和名称点击事件
        if (authorAvatar) {
            authorAvatar.addEventListener('click', () => {
                window.location.href = `/pages/profile.html?user=${post.author.id}`;
            });
        }
        
        document.getElementById('authorName').addEventListener('click', () => {
            window.location.href = `/pages/profile.html?user=${post.author.id}`;
        });
        
        // 渲染右侧作者信息卡片
        this.renderAuthorCard(post.author);
    }
    
    renderAuthorCard(author) {
        // 渲染作者头像
        const profileAvatar = document.getElementById('authorProfileAvatar');
        if (profileAvatar) {
            if (author.avatar) {
                profileAvatar.innerHTML = `<img src="${author.avatar}" alt="${author.username}" class="author-avatar-img">`;
            } else {
                profileAvatar.innerHTML = `<div class="author-avatar-placeholder">${author.username.charAt(0).toUpperCase()}</div>`;
            }
        }
        
        // 渲染作者基本信息
        document.getElementById('authorProfileName').textContent = author.username;
        document.getElementById('authorProfileLevel').textContent = `Lv.${author.level || 1}`;
        document.getElementById('authorProfileBio').textContent = author.bio || '暂无简介';
        
        // 渲染作者统计信息 - 使用真实API返回的数据或默认值
        document.getElementById('authorPostCount').textContent = this.postData ? this.postData.author.post_count || 0 : 0;
        document.getElementById('authorFollowerCount').textContent = this.postData ? this.postData.author.follower_count || 0 : 0;
        document.getElementById('authorFollowingCount').textContent = this.postData ? this.postData.author.following_count || 0 : 0;
        
        // 更新关注按钮状态
        const profileFollowBtn = document.getElementById('profileFollowBtn');
        if (profileFollowBtn) {
            if (author.is_followed) {
                profileFollowBtn.classList.add('following');
                profileFollowBtn.innerHTML = '<i class="fas fa-check"></i>已关注';
            } else {
                profileFollowBtn.classList.remove('following');
                profileFollowBtn.innerHTML = '<i class="fas fa-plus"></i>关注ta';
            }
            
            // 如果是自己的帖子，隐藏关注按钮
            const user = JSON.parse(localStorage.getItem('user') || '{}');
            if (user.id === author.id) {
                profileFollowBtn.style.display = 'none';
            }
            
            // 绑定关注按钮事件
            profileFollowBtn.addEventListener('click', () => {
                this.toggleFollow();
            });
        }
        
        // 绑定头像和名称点击事件
        if (profileAvatar) {
            profileAvatar.addEventListener('click', () => {
                window.location.href = `/pages/profile.html?user=${author.id}`;
            });
        }
        
        document.getElementById('authorProfileName').addEventListener('click', () => {
            window.location.href = `/pages/profile.html?user=${author.id}`;
        });
        
        // 加载作者更多帖子
        this.loadAuthorMorePosts(author.id);
    }
    
    async loadAuthorMorePosts(authorId) {
        try {
            // 调用真实API获取作者的其他帖子
            const response = await forumAPI.getUserPosts(authorId, { page_size: 5 });
            const authorPosts = response.results || [];
            
            const morePostsList = document.getElementById('morePostsList');
            
            if (authorPosts.length > 0) {
                morePostsList.innerHTML = authorPosts.map(post => `
                    <div class="more-post-item" onclick="window.location.href='/pages/forum-post.html?id=${post.id}'">
                        <div class="more-post-title">${post.title}</div>
                        <div class="more-post-meta">
                            <span>${this.formatRelativeTime(post.created_at)}</span>
                        </div>
                    </div>
                `).join('');
            } else {
                morePostsList.innerHTML = '<p style="text-align: center; color: var(--text-secondary); font-size: 0.95rem; padding: 1rem;">该作者暂无其他帖子</p>';
            }
        } catch (error) {
            console.error('加载作者更多帖子失败:', error);
            const morePostsList = document.getElementById('morePostsList');
            morePostsList.innerHTML = '<p style="text-align: center; color: var(--text-secondary); font-size: 0.95rem; padding: 1rem;">加载失败，请稍后重试</p>';
        }
    }
    
    updateActionButtons(post) {
        // 点赞按钮
        const likeBtn = document.getElementById('likeBtn');
        const likeCount = document.getElementById('likeCount');
        likeBtn.classList.toggle('liked', post.is_liked);
        likeCount.textContent = post.like_count;
        
        // 评论数
        const commentToggleCount = document.getElementById('commentToggleCount');
        if (commentToggleCount) {
            commentToggleCount.textContent = post.comment_count || 0;
        }
        
        // 浏览量
        const viewCountEl = document.getElementById('viewCount');
        if (viewCountEl) {
            viewCountEl.textContent = post.view_count || 0;
        }
        
        // 收藏按钮状态
        const favoriteBtn = document.getElementById('favoriteBtn');
        if (favoriteBtn) {
            favoriteBtn.classList.toggle('active', post.is_favorited);
        }
        
        // 关注按钮（帖子头部）
        const followBtn = document.getElementById('followBtn');
        // 关注按钮（作者卡片区域）
        const profileFollowBtn = document.getElementById('profileFollowBtn');
        
        if (post.author.is_followed) {
            followBtn.classList.add('following');
            followBtn.innerHTML = '<i class="fas fa-check"></i>已关注';
            if (profileFollowBtn) {
                profileFollowBtn.classList.add('following');
                profileFollowBtn.innerHTML = '<i class="fas fa-check"></i>已关注';
            }
        } else {
            followBtn.classList.remove('following');
            followBtn.innerHTML = '<i class="fas fa-plus"></i>关注ta';
            if (profileFollowBtn) {
                profileFollowBtn.classList.remove('following');
                profileFollowBtn.innerHTML = '<i class="fas fa-plus"></i>关注ta';
            }
        }
        
        // 如果是自己的帖子，隐藏所有关注按钮
        try {
            const userStr = localStorage.getItem('user');
            if (userStr) {
                const user = JSON.parse(userStr);
                const userId = String(user.id || '');
                const authorId = String(post.author?.id || '');
                
                if (userId && authorId && userId === authorId) {
                    followBtn.classList.add('hidden');
                    if (profileFollowBtn) {
                        profileFollowBtn.classList.add('hidden');
                    }
                } else {
                    followBtn.classList.remove('hidden');
                    if (profileFollowBtn) {
                        profileFollowBtn.classList.remove('hidden');
                    }
                }
            }
        } catch (e) {
            console.error('检查用户信息失败:', e);
        }
    }
    
    updateAdminButtons(post) {
        const pinBtn = document.getElementById('pinPostBtn');
        const featureBtn = document.getElementById('featurePostBtn');
        const adminMenuDivider = document.getElementById('adminMenuDivider');
        const adminMenuItems = document.querySelectorAll('.admin-menu-item');
        
        if (pinBtn) {
            pinBtn.innerHTML = `
                <i class="fas fa-thumbtack"></i>
                <span>${post.is_pinned ? '取消置顶' : '置顶'}</span>
            `;
        }
            
        if (featureBtn) {
            featureBtn.innerHTML = `
                <i class="fas fa-star"></i>
                <span>${post.is_featured ? '取消精华' : '设为精华'}</span>
            `;
        }
        
        // 显示管理员菜单项
        if (adminMenuDivider) adminMenuDivider.style.display = 'block';
        adminMenuItems.forEach(item => item.style.display = 'flex');
    }
    
    toggleCommentsSection() {
        const commentsSection = document.querySelector('.comments-section');
        const commentFormContainer = document.querySelector('.comment-form-container');
        
        if (commentsSection && commentFormContainer) {
            const isHidden = commentsSection.style.display === 'none';
            commentsSection.style.display = isHidden ? 'block' : 'none';
            commentFormContainer.style.display = isHidden ? 'block' : 'none';
            
            if (isHidden) {
                commentsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }
    }
    
    toggleMoreMenu() {
        const menu = document.getElementById('moreActionsMenu');
        if (menu) {
            menu.classList.toggle('show');
        }
    }
    
    hideMoreMenu() {
        const menu = document.getElementById('moreActionsMenu');
        if (menu) {
            menu.classList.remove('show');
        }
    }
    
    async loadComments(reset = false) {
        if (this.isLoadingComments) return;
        
        this.isLoadingComments = true;
        
        try {
            const params = {
                sort: this.currentCommentSort,
                page: reset ? 1 : this.currentCommentPage,
                page_size: 20
            };
            
            const response = await forumAPI.getComments(this.postId, params);
            
            if (reset) {
                this.currentCommentPage = 1;
                this.commentsData = response.results;
                this.renderComments(response.results, true);
            } else {
                this.commentsData = [...this.commentsData, ...response.results];
                this.renderComments(response.results, false);
            }
            
            this.hasMoreComments = !!response.next;
            this.updateCommentCount(response.count);
            this.updateLoadMoreButton();
            
        } catch (error) {
            console.error('加载评论失败:', error);
            this.showError('加载评论失败，请稍后重试');
        } finally {
            this.isLoadingComments = false;
            this.hideCommentsSkeleton();
        }
    }
    
    renderComments(comments, reset = false) {
        const commentsList = document.getElementById('commentsList');
        
        if (reset) {
            commentsList.innerHTML = '';
        }
        
        comments.forEach(comment => {
            const commentElement = this.createCommentElement(comment);
            commentsList.appendChild(commentElement);
        });
    }
    
    createCommentElement(comment, level = 0) {
        const commentDiv = document.createElement('div');
        commentDiv.className = 'comment-item';
        commentDiv.dataset.commentId = comment.id;
        
        const indent = level > 0 ? `margin-left: ${level * 2}rem;` : '';
        
        // 检查删除权限：评论者本人、帖子作者、管理员可删除
        // 使用缓存的用户信息，避免异步调用
        const cachedUser = JSON.parse(localStorage.getItem('user') || 'null');
        const canDelete = cachedUser && (
            cachedUser.id === comment.author.id || // 评论者本人
            (this.postData && cachedUser.id === this.postData.author.id) || // 帖子作者
            cachedUser.is_staff // 管理员
        );
        
        const deleteButton = canDelete ? 
            `<button class="comment-action comment-delete" data-comment-id="${comment.id}">
                <i class="fas fa-trash"></i>
                删除
            </button>` : '';
        
        commentDiv.innerHTML = `
            <div class="comment-header">
                <div class="comment-avatar" onclick="window.location.href='/pages/profile.html?user=${comment.author.id}'">
                    ${comment.author.avatar ? 
                        `<img src="${comment.author.avatar}" alt="${comment.author.username}">` :
                        comment.author.username.charAt(0).toUpperCase()
                    }
                </div>
                <a href="/pages/profile.html?user=${comment.author.id}" class="comment-author">${comment.author.username}</a>
                <span class="comment-time">${this.formatRelativeTime(comment.created_at)}</span>
            </div>
            <div class="comment-content">${comment.content}</div>
            <div class="comment-actions">
                <button class="comment-action comment-like ${comment.is_liked ? 'active' : ''}" data-comment-id="${comment.id}">
                    <i class="fas fa-heart"></i>
                    <span>${comment.like_count}</span>
                </button>
                <button class="comment-action comment-reply" data-comment-id="${comment.id}">
                    <i class="fas fa-reply"></i>
                    回复
                </button>
                <button class="comment-action comment-report" data-comment-id="${comment.id}">
                    <i class="fas fa-flag"></i>
                    举报
                </button>
                ${deleteButton}
            </div>
            <div class="comment-replies" id="replies-${comment.id}"></div>
        `;
        
        if (indent) {
            commentDiv.style.cssText = indent;
        }
        
        // 绑定评论操作事件
        this.bindCommentEvents(commentDiv, comment);
        
        // 渲染回复
        if (comment.replies && comment.replies.length > 0) {
            const repliesContainer = commentDiv.querySelector(`#replies-${comment.id}`);
            comment.replies.forEach(reply => {
                const replyElement = this.createCommentElement(reply, level + 1);
                repliesContainer.appendChild(replyElement);
            });
            
            // 如果回复太多，添加展开/折叠功能
            if (comment.replies.length > 3 && level === 0) {
                this.addExpandCollapseButton(repliesContainer, comment.replies.length);
            }
        }
        
        return commentDiv;
    }
    
    bindCommentEvents(commentElement, comment) {
        // 点赞评论
        const likeBtn = commentElement.querySelector('.comment-like');
        likeBtn.addEventListener('click', () => {
            this.toggleCommentLike(comment.id, likeBtn);
        });
        
        // 回复评论
        const replyBtn = commentElement.querySelector('.comment-reply');
        replyBtn.addEventListener('click', () => {
            this.replyToComment(comment.id, comment.author.username);
        });
        
        // 举报评论
        const reportBtn = commentElement.querySelector('.comment-report');
        reportBtn.addEventListener('click', () => {
            this.reportComment(comment.id);
        });
        
        // 删除评论
        const deleteBtn = commentElement.querySelector('.comment-delete');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => {
                this.deleteComment(comment.id, commentElement);
            });
        }
    }
    
    addExpandCollapseButton(repliesContainer, totalReplies) {
        const expandBtn = document.createElement('button');
        expandBtn.className = 'expand-replies';
        expandBtn.innerHTML = `<i class="fas fa-chevron-down"></i> 展开更多回复 (${totalReplies})`;
        
        let isExpanded = false;
        const replies = Array.from(repliesContainer.children);
        
        // 初始只显示前3个回复
        replies.slice(3).forEach(reply => {
            reply.style.display = 'none';
        });
        
        expandBtn.addEventListener('click', () => {
            isExpanded = !isExpanded;
            
            replies.slice(3).forEach(reply => {
                reply.style.display = isExpanded ? 'block' : 'none';
            });
            
            expandBtn.innerHTML = isExpanded ? 
                '<i class="fas fa-chevron-up"></i> 收起回复' :
                `<i class="fas fa-chevron-down"></i> 展开更多回复 (${totalReplies})`;
        });
        
        repliesContainer.parentNode.appendChild(expandBtn);
    }
    
    handleCommentSort(sort) {
        // 更新选中状态
        document.querySelectorAll('.sort-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.sort === sort);
        });
        
        this.currentCommentSort = sort;
        this.loadComments(true);
    }
    
    loadMoreComments() {
        if (!this.hasMoreComments || this.isLoadingComments) return;
        
        this.currentCommentPage++;
        this.loadComments(false);
    }
    
    async submitComment() {
        if (!(await this.isLoggedIn())) {
            this.showLoginModal();
            return;
        }
        
        if (!this.commentEditor || this.commentEditor.getLength() <= 1) {
            this.showError('请输入评论内容');
            return;
        }
        
        const content = this.commentEditor.root.innerHTML;
        const submitBtn = document.getElementById('submitCommentBtn');
        const formContainer = document.querySelector('.comment-form-container');
        
        submitBtn.classList.add('loading');
        submitBtn.disabled = true;
        if (formContainer) formContainer.classList.add('submitting');
        
        try {
            const commentData = {
                content,
                post: this.postId
            };
            
            const newComment = await forumAPI.createComment(this.postId, commentData);
            
            this.commentEditor.setContents([]);
            this.updateCommentCharCount(0);
            this.updateSubmitButton(false);
            
            const commentsList = document.getElementById('commentsList');
            const newCommentElement = this.createCommentElement(newComment);
            newCommentElement.classList.add('new-comment');
            commentsList.insertBefore(newCommentElement, commentsList.firstChild);
            
            const currentCount = parseInt(document.getElementById('commentCount').textContent);
            this.updateCommentCount(currentCount + 1);
            
            this.showSuccess('评论发表成功！');
            
            setTimeout(() => {
                newCommentElement.classList.remove('new-comment');
            }, 2000);
            
        } catch (error) {
            console.error('发表评论失败:', error);
            this.showError('发表评论失败，请稍后重试');
        } finally {
            submitBtn.classList.remove('loading');
            submitBtn.disabled = false;
            if (formContainer) formContainer.classList.remove('submitting');
        }
    }
    
    async replyToComment(commentId, authorName) {
        if (!(await this.isLoggedIn())) {
            this.showLoginModal();
            return;
        }
        
        // 在编辑器中插入@用户名
        if (this.commentEditor) {
            const currentContent = this.commentEditor.root.innerHTML;
            const mentionText = `@${authorName} `;
            this.commentEditor.root.innerHTML = mentionText + currentContent;
            this.commentEditor.focus();
            
            // 滚动到评论框
            document.getElementById('commentFormContainer').scrollIntoView({
                behavior: 'smooth',
                block: 'center'
            });
        }
    }
    
    // 帖子操作方法
    async toggleLike() {
        if (!(await this.isLoggedIn())) {
            this.showLoginModal();
            return;
        }
        
        // 防抖机制：如果正在处理点赞请求，则忽略新的点击
        if (this.isLikeProcessing) {
            return;
        }
        
        this.isLikeProcessing = true;
        const likeBtn = document.getElementById('likeBtn');
        
        try {
            // 禁用按钮防止重复点击
            likeBtn.disabled = true;
            
            const result = await forumAPI.togglePostLike(this.postId);
            
            // 更新本地数据状态
            if (this.postData) {
                this.postData.is_liked = result.is_liked;
                this.postData.like_count = result.like_count;
            }
            
            const likeCount = document.getElementById('likeCount');
            
            likeBtn.classList.toggle('liked', result.is_liked);
            likeCount.textContent = result.like_count;
            
            // 显示操作反馈
            if (result.is_liked) {
                this.showSuccess('点赞成功');
            } else {
                this.showSuccess('取消点赞成功');
            }
            
        } catch (error) {
            console.error('点赞操作失败:', error);
            this.showError('操作失败，请稍后重试');
        } finally {
            // 恢复按钮状态
            likeBtn.disabled = false;
            this.isLikeProcessing = false;
        }
    }
    
    async toggleFavorite() {
        if (!(await this.isLoggedIn())) {
            this.showLoginModal();
            return;
        }
        
        // 防抖机制：如果正在处理收藏请求，则忽略新的点击
        if (this.isFavoriteProcessing) {
            return;
        }
        
        this.isFavoriteProcessing = true;
        const favoriteBtn = document.getElementById('favoriteBtn');
        
        try {
            // 禁用按钮防止重复点击
            favoriteBtn.disabled = true;
            
            const result = await forumAPI.togglePostFavorite(this.postId);
            
            // 更新本地数据状态
            if (this.postData) {
                this.postData.is_favorited = result.is_favorited;
                this.postData.favorite_count = result.favorite_count;
            }
            
            const favoriteCount = document.getElementById('favoriteCount');
            
            favoriteBtn.classList.toggle('active', result.is_favorited);
            favoriteCount.textContent = result.favorite_count;
            
            // 显示操作反馈
            if (result.is_favorited) {
                this.showSuccess('收藏成功');
            } else {
                this.showSuccess('取消收藏成功');
            }
            
        } catch (error) {
            console.error('收藏操作失败:', error);
            this.showError('操作失败，请稍后重试');
        } finally {
            // 恢复按钮状态
            favoriteBtn.disabled = false;
            this.isFavoriteProcessing = false;
        }
    }
    
    async toggleFollow() {
        if (!(await this.isLoggedIn())) {
            this.showLoginModal();
            return;
        }
        
        if (!this.postData) return;
        
        // 检查是否是自己的帖子
        try {
            const userStr = localStorage.getItem('user');
            if (userStr) {
                const user = JSON.parse(userStr);
                const userId = String(user.id || '');
                const authorId = String(this.postData.author?.id || '');
                if (userId && authorId && userId === authorId) {
                    this.showError('不能关注自己');
                    return;
                }
            }
        } catch (e) {
            console.error('检查用户信息失败:', e);
        }
        
        // 防抖机制
        if (this.isFollowProcessing) {
            return;
        }
        
        this.isFollowProcessing = true;
        const followBtn = document.getElementById('followBtn');
        const profileFollowBtn = document.getElementById('profileFollowBtn');
        
        try {
            if (followBtn) followBtn.disabled = true;
            if (profileFollowBtn) profileFollowBtn.disabled = true;
            
            const result = await forumAPI.toggleUserFollow(this.postData.author.id);
            
            this.postData.author.is_followed = result.is_followed;
            
            // 更新帖子头部的关注按钮
            if (followBtn) {
                if (result.is_followed) {
                    followBtn.classList.add('following');
                    followBtn.innerHTML = '<i class="fas fa-check"></i>已关注';
                } else {
                    followBtn.classList.remove('following');
                    followBtn.innerHTML = '<i class="fas fa-plus"></i>关注ta';
                }
            }
            
            // 更新右侧边栏的关注按钮
            if (profileFollowBtn) {
                if (result.is_followed) {
                    profileFollowBtn.classList.add('following');
                    profileFollowBtn.innerHTML = '<i class="fas fa-check"></i>已关注';
                } else {
                    profileFollowBtn.classList.remove('following');
                    profileFollowBtn.innerHTML = '<i class="fas fa-plus"></i>关注ta';
                }
            }
            
            this.showSuccess(result.is_followed ? '关注成功' : '取消关注成功');
            
        } catch (error) {
            console.error('关注操作失败:', error);
            this.showError('操作失败，请稍后重试');
        } finally {
            // 恢复按钮状态
            if (followBtn) followBtn.disabled = false;
            if (profileFollowBtn) profileFollowBtn.disabled = false;
            this.isFollowProcessing = false;
        }
    }
    
    async toggleCommentLike(commentId, likeBtn) {
        if (!(await this.isLoggedIn())) {
            this.showLoginModal();
            return;
        }
        
        try {
            const result = await forumAPI.toggleCommentLike(commentId);
            
            likeBtn.classList.toggle('active', result.is_liked);
            likeBtn.querySelector('span').textContent = result.like_count;
            
        } catch (error) {
            console.error('点赞评论失败:', error);
            this.showError('操作失败，请稍后重试');
        }
    }
    
    // 管理员操作方法
    async editPost() {
        // 跳转到编辑页面或显示编辑模态框
        window.location.href = `/pages/forum-edit.html?id=${this.postId}`;
    }
    
    async deletePost() {
        if (!confirm('确定要删除这个帖子吗？此操作不可撤销。')) {
            return;
        }
        
        try {
            await forumAPI.deletePost(this.postId);
            this.showSuccess('帖子删除成功');
            
            // 延迟跳转到论坛首页
            setTimeout(() => {
                window.location.href = '/pages/forum.html';
            }, 1500);
            
        } catch (error) {
            console.error('删除帖子失败:', error);
            this.showError('删除失败，请稍后重试');
        }
    }
    
    async togglePin() {
        try {
            const result = await forumAPI.togglePostPin(this.postId);
            
            const pinBtn = document.getElementById('pinPostBtn');
            pinBtn.innerHTML = result.is_pinned ? 
                '<i class="fas fa-thumbtack"></i>取消置顶' : 
                '<i class="fas fa-thumbtack"></i>置顶';
                
            this.showSuccess(result.is_pinned ? '帖子已置顶' : '已取消置顶');
            
        } catch (error) {
            console.error('置顶操作失败:', error);
            this.showError('操作失败，请稍后重试');
        }
    }
    
    async toggleFeature() {
        try {
            const result = await forumAPI.togglePostFeature(this.postId);
            
            const featureBtn = document.getElementById('featurePostBtn');
            featureBtn.innerHTML = result.is_featured ? 
                '<i class="fas fa-star"></i>取消精华' : 
                '<i class="fas fa-star"></i>设为精华';
                
            this.showSuccess(result.is_featured ? '帖子已设为精华' : '已取消精华');
            
        } catch (error) {
            console.error('精华操作失败:', error);
            this.showError('操作失败，请稍后重试');
        }
    }
    
    // 模态框方法
    showShareModal() {
        const modal = document.getElementById('shareModal');
        const shareLink = document.getElementById('shareLink');
        
        shareLink.value = window.location.href;
        modal.classList.add('show');
    }
    
    hideShareModal() {
        const modal = document.getElementById('shareModal');
        modal.classList.remove('show');
    }
    
    async showReportModal() {
        if (!(await this.isLoggedIn())) {
            this.showLoginModal();
            return;
        }
        
        const modal = document.getElementById('reportModal');
        modal.classList.add('show');
    }
    
    hideReportModal() {
        const modal = document.getElementById('reportModal');
        modal.classList.remove('show');
    }
    
    showLoginModal() {
        if (typeof LoginModal !== 'undefined') {
            LoginModal.show({
                title: '需要登录',
                message: '您需要登录后才能进行此操作',
                autoRedirect: true
            });
        } else {
            console.warn('LoginModal not available');
        }
    }
    
    async copyShareLink() {
        const shareLink = document.getElementById('shareLink');
        
        try {
            await navigator.clipboard.writeText(shareLink.value);
            this.showSuccess('链接已复制到剪贴板');
        } catch (error) {
            // 降级方案
            shareLink.select();
            document.execCommand('copy');
            this.showSuccess('链接已复制到剪贴板');
        }
    }
    
    generateQRCode() {
        const qrCode = document.getElementById('qrCode');
        qrCode.style.display = 'block';
        qrCode.innerHTML = '<p>二维码生成功能需要集成第三方库</p>';
        // 这里可以集成QR码生成库，如qrcode.js
    }
    
    async submitReport() {
        const form = document.getElementById('reportForm');
        const formData = new FormData(form);
        
        const reason = formData.get('reason');
        const description = formData.get('description');
        
        if (!reason) {
            this.showError('请选择举报原因');
            return;
        }
        
        try {
            const reportData = {
                post: this.postId,
                reason,
                description
            };
            
            await forumAPI.reportPost(reportData);
            
            this.hideReportModal();
            this.showSuccess('举报已提交，我们会尽快处理');
            
            // 重置表单
            form.reset();
            
        } catch (error) {
            console.error('提交举报失败:', error);
            this.showError('提交失败，请稍后重试');
        }
    }
    
    // 工具栏方法
    showEmojiPicker() {
        // 简单的表情选择器实现
        const emojis = ['😀', '😂', '😍', '🤔', '👍', '👎', '❤️', '🎉'];
        const emojiHtml = emojis.map(emoji => 
            `<button onclick="this.insertEmoji('${emoji}')">${emoji}</button>`
        ).join('');
    }
    
    insertEmoji(emoji) {
        if (this.commentEditor) {
            const range = this.commentEditor.getSelection();
            if (range) {
                this.commentEditor.insertText(range.index, emoji);
            }
        }
    }
    
    uploadImage() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        
        input.onchange = async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            
            try {
                const imageUrl = await forumAPI.uploadImage(file);
                
                if (this.commentEditor) {
                    const range = this.commentEditor.getSelection();
                    this.commentEditor.insertEmbed(range ? range.index : 0, 'image', imageUrl);
                }
                
            } catch (error) {
                console.error('图片上传失败:', error);
                this.showError('图片上传失败，请稍后重试');
            }
        };
        
        input.click();
    }
    
    showUserMention() {
        // TODO: 实现用户搜索和选择功能
    }
    
    // 工具方法
    updatePageTitle(title) {
        document.title = `${title} - 非遗传承网`;
    }
    
    updatePageMeta(post) {
        // 更新页面meta信息
        const description = post.content.replace(/<[^>]*>/g, '').substring(0, 150);
        
        let metaDesc = document.querySelector('meta[name="description"]');
        if (metaDesc) {
            metaDesc.content = description;
        }
    }
    
    updateCommentCount(count) {
        document.getElementById('commentCount').textContent = count;
    }
    
    updateCommentCharCount(count) {
        document.getElementById('commentCharCount').textContent = count;
    }
    
    updateSubmitButton(enabled) {
        const submitBtn = document.getElementById('submitCommentBtn');
        submitBtn.disabled = !enabled;
    }
    
    updateLoadMoreButton() {
        const loadMoreContainer = document.getElementById('loadMoreComments');
        loadMoreContainer.style.display = this.hasMoreComments ? 'block' : 'none';
    }
    
    hideCommentsSkeleton() {
        const skeleton = document.getElementById('commentsSkeleton');
        if (skeleton) {
            skeleton.style.display = 'none';
        }
    }
    
    scrollToCommentForm() {
        const commentForm = document.getElementById('commentForm');
        if (commentForm) {
            commentForm.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
            // 聚焦到评论编辑器
            if (this.commentEditor) {
                this.commentEditor.focus();
            }
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
    
    // 权限检查方法
    async isLoggedIn() {
        try {
            // 使用缓存的用户信息，避免重复的网络请求
            const cachedUser = JSON.parse(localStorage.getItem('user') || 'null');
            if (cachedUser && cachedUser.id) {
                return true;
            }
            
            // 如果没有缓存，才进行网络请求
            const user = await window.checkBackendAuth();
            if (user && user.id) {
                // 缓存用户信息
                localStorage.setItem('user', JSON.stringify(user));
                return true;
            }
            return false;
        } catch (error) {
            console.error('[forum-post.js] Error checking login status:', error);
            return false;
        }
    }
    
    async canManagePost(post) {
        try {
            const user = await window.checkBackendAuth();
            if (!user) return false;
            return user.id === post.author.id || user.is_staff;
        } catch (error) {
            console.error('[forum-post.js] Error checking manage permission:', error);
            return false;
        }
    }
    
    // 时间格式化方法
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
        if (typeof window.updateUserIcon === 'function') {
            await window.updateUserIcon();
        }
        
        const user = await window.checkBackendAuth();
        if (user && user.id) {
            const commentUserAvatar = document.getElementById('commentUserAvatar');
            const commentUsername = document.getElementById('commentUsername');
            
            if (commentUsername) {
                commentUsername.textContent = user.username;
            }
            
            if (commentUserAvatar) {
                try {
                    let avatarUrl = null;
                    
                    if (window.API && window.API.userProfile) {
                        const userData = await window.API.userProfile.getUserProfile();
                        if (userData.profile && userData.profile.avatar) {
                            avatarUrl = userData.profile.avatar;
                        }
                    }
                    
                    if (!avatarUrl && user.avatar) {
                        avatarUrl = user.avatar;
                    }
                    
                    if (!avatarUrl) {
                        const fullUser = JSON.parse(localStorage.getItem('user') || '{}');
                        if (fullUser.avatar) {
                            avatarUrl = fullUser.avatar;
                        }
                    }
                    
                    if (avatarUrl) {
                        if (typeof AvatarCache !== 'undefined') {
                            avatarUrl = AvatarCache.getCacheBustedUrl(avatarUrl, user.id);
                        } else {
                            if (avatarUrl.startsWith('/media/')) {
                                avatarUrl = window.location.origin + avatarUrl;
                            }
                            const separator = avatarUrl.includes('?') ? '&' : '?';
                            avatarUrl += `${separator}_v=${Date.now()}`;
                        }
                        commentUserAvatar.innerHTML = `<img src="${avatarUrl}" alt="${user.username}" class="comment-avatar-img">`;
                    } else {
                        commentUserAvatar.innerHTML = `<div class="user-avatar-placeholder">${user.username.charAt(0).toUpperCase()}</div>`;
                    }
                } catch (error) {
                    console.error('获取用户头像失败:', error);
                    commentUserAvatar.innerHTML = `<div class="user-avatar-placeholder">${user.username.charAt(0).toUpperCase()}</div>`;
                }
            }
        }
    }
    
    // 获取当前用户信息
    async getCurrentUser() {
        try {
            const cachedUser = JSON.parse(localStorage.getItem('user') || 'null');
            if (cachedUser && cachedUser.id) {
                return cachedUser;
            }
            
            const user = await window.checkBackendAuth();
            if (user && user.id) {
                localStorage.setItem('user', JSON.stringify(user));
                return user;
            }
            return null;
        } catch (error) {
            console.error('[forum-post.js] Error getting current user:', error);
            return null;
        }
    }
    
    // 删除评论
    async deleteComment(commentId, commentElement) {
        try {
            if (!confirm('确定要删除这条评论吗？')) {
                return;
            }
            
            const response = await fetch(`/api/forum/comments/${commentId}/delete/`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            if (response.ok) {
                // 从DOM中移除评论元素
                commentElement.remove();
                this.showSuccess('评论删除成功');
                
                // 重新加载评论以更新计数
                await this.loadComments(true);
            } else {
                const errorData = await response.json();
                this.showError(errorData.error || '删除评论失败');
            }
        } catch (error) {
            console.error('[forum-post.js] Error deleting comment:', error);
            this.showError('删除评论时发生错误');
        }
    }
    
    // 举报评论
    async reportComment(commentId) {
        try {
            // 显示举报表单，让用户从固定选项中选择
            const reasonOptions = [
                { value: 'spam', label: '垃圾信息' },
                { value: 'inappropriate', label: '不当内容' },
                { value: 'harassment', label: '骚扰' },
                { value: 'copyright', label: '版权侵犯' },
                { value: 'other', label: '其他' }
            ];
            
            // 创建一个简单的举报表单模态框
            const modal = document.createElement('div');
            modal.className = 'report-modal';
            modal.innerHTML = `
                <div class="report-modal-content">
                    <h3>举报评论</h3>
                    <div class="report-form">
                        <div class="form-group">
                            <label for="reportReason">举报原因：</label>
                            <select id="reportReason" class="form-control">
                                ${reasonOptions.map(opt => `<option value="${opt.value}">${opt.label}</option>`).join('')}
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="reportDescription">详细描述：</label>
                            <textarea id="reportDescription" class="form-control" rows="3" placeholder="请详细描述举报内容"></textarea>
                        </div>
                        <div class="form-actions">
                            <button id="cancelReport" class="btn btn-secondary">取消</button>
                            <button id="submitReport" class="btn btn-danger">提交举报</button>
                        </div>
                    </div>
                </div>
                <style>
                    .report-modal {
                        position: fixed;
                        top: 0;
                        left: 0;
                        right: 0;
                        bottom: 0;
                        background-color: rgba(0, 0, 0, 0.5);
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        z-index: 1000;
                    }
                    .report-modal-content {
                        background-color: white;
                        padding: 20px;
                        border-radius: 8px;
                        width: 90%;
                        max-width: 500px;
                    }
                    .report-form {
                        margin-top: 20px;
                    }
                    .form-group {
                        margin-bottom: 15px;
                    }
                    .form-group label {
                        display: block;
                        margin-bottom: 5px;
                        font-weight: bold;
                    }
                    .form-control {
                        width: 100%;
                        padding: 8px;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                    }
                    .form-actions {
                        display: flex;
                        justify-content: flex-end;
                        gap: 10px;
                    }
                    .btn {
                        padding: 8px 16px;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                    }
                    .btn-secondary {
                        background-color: #6c757d;
                        color: white;
                    }
                    .btn-danger {
                        background-color: #dc3545;
                        color: white;
                    }
                </style>
            `;
            
            document.body.appendChild(modal);
            
            // 取消按钮事件
            modal.querySelector('#cancelReport').addEventListener('click', () => {
                document.body.removeChild(modal);
            });
            
            // 提交按钮事件
            modal.querySelector('#submitReport').addEventListener('click', async () => {
                const reason = modal.querySelector('#reportReason').value;
                const description = modal.querySelector('#reportDescription').value;
                
                await forumAPI.reportComment(commentId, { reason, description });
                
                document.body.removeChild(modal);
                this.showSuccess('举报已提交，我们会尽快处理');
            });
            
        } catch (error) {
            console.error('[forum-post.js] Error reporting comment:', error);
            this.showError('举报失败，请稍后重试');
        }
    }
    
    // 获取CSRF Token
    getCSRFToken() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                         document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ||
                         window.getCookie('csrftoken');
        return csrfToken;
    }
}

// 初始化代码已移至HTML文件中

// 使用全局utils中的getCookie函数