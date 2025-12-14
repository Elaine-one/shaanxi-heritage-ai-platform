/**
 * 帖子详情页管理器 - 处理帖子详情页的所有交互逻辑
 */
class PostDetailManager {
    constructor() {
        // 获取帖子ID
        this.postId = this.getPostId();
        this.postData = null;
        this.commentsData = [];
        this.currentCommentPage = 1;
        this.currentCommentSort = 'newest';
        this.hasMoreComments = true;
        this.isLoadingComments = false;
        this.commentEditor = null;
        
        // 初始化
        this.init();
    }
    
    // 从URL获取帖子ID
    getPostId() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('id');
    }
    
    // 初始化页面
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
    
    // 绑定页面事件
    bindEvents() {
        // 返回论坛按钮
        document.getElementById('backToForumBtn').addEventListener('click', () => {
            window.location.href = '/pages/forum.html';
        });
        
        // 帖子操作按钮
        document.getElementById('likeBtn').addEventListener('click', () => {
            this.togglePostLike();
        });
        
        document.getElementById('favoriteBtn').addEventListener('click', () => {
            this.togglePostFavorite();
        });
        
        document.getElementById('shareBtn').addEventListener('click', () => {
            this.showShareModal();
        });
        
        document.getElementById('followBtn').addEventListener('click', () => {
            this.toggleFollowUser();
        });
        
        // 管理员操作按钮
        document.getElementById('pinPostBtn').addEventListener('click', () => {
            this.togglePostPin();
        });
        
        document.getElementById('featurePostBtn').addEventListener('click', () => {
            this.togglePostFeatured();
        });
        
        document.getElementById('editPostBtn').addEventListener('click', () => {
            this.editPost();
        });
        
        document.getElementById('deletePostBtn').addEventListener('click', () => {
            this.deletePost();
        });
        
        // 评论操作
        document.getElementById('commentSort').addEventListener('change', (e) => {
            this.currentCommentSort = e.target.value;
            this.loadComments(true);
        });
        
        document.getElementById('loadMoreCommentsBtn').addEventListener('click', () => {
            this.loadMoreComments();
        });
        
        document.getElementById('submitCommentBtn').addEventListener('click', () => {
            this.submitComment();
        });
        
        // 绑定模态框事件
        this.bindModalEvents();
        
        // 绑定工具栏事件
        this.bindToolbarEvents();
    }
    
    // 绑定模态框事件
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
        
        // 登录模态框
        const loginModal = document.getElementById('loginModal');
        const closeLoginModal = document.getElementById('closeLoginModal');
        const cancelLogin = document.getElementById('cancelLogin');
        const goToLogin = document.getElementById('goToLogin');
        
        closeLoginModal.addEventListener('click', () => {
            this.hideLoginModal();
        });
        
        cancelLogin.addEventListener('click', () => {
            this.hideLoginModal();
        });
        
        goToLogin.addEventListener('click', () => {
            window.location.href = '/pages/login.html';
        });
        
        loginModal.addEventListener('click', (e) => {
            if (e.target === loginModal) {
                this.hideLoginModal();
            }
        });
    }
    
    // 绑定工具栏事件
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
    
    // 初始化评论编辑器
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
    
    // 加载帖子数据
    async loadPost() {
        try {
            const post = await forumAPI.getPostDetail(this.postId);
            this.postData = post;
            this.renderPost(post);
            this.updatePageTitle(post.title);
            this.updatePageMeta(post);
            
            // 增加浏览量
            await forumAPI.incrementViewCount(this.postId);
            
        } catch (error) {
            console.error('加载帖子失败:', error);
            this.showError('帖子不存在或已被删除');
        }
    }
    
    // 渲染帖子内容
    renderPost(post) {
        // 隐藏骨架屏
        document.getElementById('postSkeleton').style.display = 'none';
        document.getElementById('postContentWrapper').style.display = 'block';
        
        // 渲染作者信息
        const authorAvatar = document.getElementById('authorAvatar');
        if (post.author.avatar) {
            authorAvatar.innerHTML = `<img src="${post.author.avatar}" alt="${post.author.username}">`;
        } else {
            authorAvatar.innerHTML = post.author.username.charAt(0).toUpperCase();
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
                document.getElementById('adminActions').style.display = 'flex';
                this.updateAdminButtons(post);
            }
        }).catch(error => {
            console.error('[post-detail.js] Error checking manage permission:', error);
        });
        
        // 绑定作者头像和名称点击事件
        authorAvatar.addEventListener('click', () => {
            window.location.href = `/pages/profile.html?user=${post.author.id || ''}`;
        });
        
        document.getElementById('authorName').addEventListener('click', () => {
            window.location.href = `/pages/profile.html?user=${post.author.id || ''}`;
        });
    }
    
    // 更新操作按钮状态
    updateActionButtons(post) {
        // 点赞按钮
        const likeBtn = document.getElementById('likeBtn');
        const likeCount = document.getElementById('likeCount');
        likeBtn.classList.toggle('active', post.is_liked);
        likeCount.textContent = post.like_count;
        
        // 收藏按钮
        const favoriteBtn = document.getElementById('favoriteBtn');
        const favoriteCount = document.getElementById('favoriteCount');
        favoriteBtn.classList.toggle('active', post.is_favorited);
        favoriteCount.textContent = post.favorite_count;
        
        // 关注按钮
        const followBtn = document.getElementById('followBtn');
        if (post.author.is_followed) {
            followBtn.classList.add('following');
            followBtn.innerHTML = '<i class="fas fa-check"></i>已关注';
        } else {
            followBtn.classList.remove('following');
            followBtn.innerHTML = '<i class="fas fa-plus"></i>关注ta';
        }
        
        // 如果是自己的帖子，隐藏关注按钮
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        if (user.id === post.author.id) {
            followBtn.style.display = 'none';
        }
    }
    
    // 更新管理员按钮状态
    updateAdminButtons(post) {
        const pinBtn = document.getElementById('pinPostBtn');
        const featureBtn = document.getElementById('featurePostBtn');
        
        pinBtn.innerHTML = post.is_pinned ? 
            '<i class="fas fa-thumbtack"></i>取消置顶' : 
            '<i class="fas fa-thumbtack"></i>置顶';
            
        featureBtn.innerHTML = post.is_featured ? 
            '<i class="fas fa-star"></i>取消精华' : 
            '<i class="fas fa-star"></i>设为精华';
    }
    
    // 加载评论
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
    
    // 渲染评论
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
    
    // 创建评论元素
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
                <div class="comment-avatar" onclick="window.location.href='/pages/profile.html?user=${comment.author.id || ''}'">
                    ${comment.author.avatar ? 
                        `<img src="${comment.author.avatar}" alt="${comment.author.username}">` :
                        comment.author.username.charAt(0).toUpperCase()
                    }
                </div>
                <a href="/pages/profile.html?user=${comment.author.id || ''}" class="comment-author">${comment.author.username}</a>
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
    
    // 绑定评论事件
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
    
    // 添加展开/折叠按钮
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
            
            if (isExpanded) {
                replies.forEach(reply => {
                    reply.style.display = '';
                });
                expandBtn.innerHTML = `<i class="fas fa-chevron-up"></i> 收起回复`;
            } else {
                replies.slice(3).forEach(reply => {
                    reply.style.display = 'none';
                });
                expandBtn.innerHTML = `<i class="fas fa-chevron-down"></i> 展开更多回复 (${totalReplies})`;
            }
        });
        
        repliesContainer.parentNode.insertBefore(expandBtn, repliesContainer);
    }
    
    // 加载更多评论
    async loadMoreComments() {
        if (!this.hasMoreComments || this.isLoadingComments) return;
        
        this.currentCommentPage++;
        await this.loadComments();
    }
    
    // 更新评论计数
    updateCommentCount(count) {
        document.getElementById('commentCount').textContent = `${count} 条评论`;
    }
    
    // 更新加载更多按钮
    updateLoadMoreButton() {
        const loadMoreBtn = document.getElementById('loadMoreCommentsBtn');
        loadMoreBtn.style.display = this.hasMoreComments ? 'block' : 'none';
        
        if (this.isLoadingComments) {
            loadMoreBtn.innerHTML = '<div class="loading-spinner"></div> 加载中...';
        } else {
            loadMoreBtn.innerHTML = '加载更多评论';
        }
    }
    
    // 隐藏评论骨架屏
    hideCommentsSkeleton() {
        const skeleton = document.getElementById('commentsSkeleton');
        if (skeleton) {
            skeleton.style.display = 'none';
        }
    }
    
    // 提交评论
    async submitComment() {
        const content = this.commentEditor.root.innerHTML;
        
        if (!content.trim()) {
            this.showError('评论内容不能为空');
            return;
        }
        
        // 检查用户是否登录
        const user = JSON.parse(localStorage.getItem('user') || 'null');
        if (!user) {
            this.showLoginModal();
            return;
        }
        
        try {
            const newComment = await forumAPI.createComment(this.postId, { content });
            
            // 清空编辑器
            this.commentEditor.setText('');
            this.updateCommentCharCount(0);
            this.updateSubmitButton(false);
            
            // 刷新评论列表
            await this.loadComments(true);
            
            this.showSuccess('评论发表成功');
        } catch (error) {
            console.error('发表评论失败:', error);
            this.showError('发表评论失败，请稍后重试');
        }
    }
    
    // 回复评论
    async replyToComment(parentCommentId, authorName) {
        // 检查用户是否登录
        const user = JSON.parse(localStorage.getItem('user') || 'null');
        if (!user) {
            this.showLoginModal();
            return;
        }
        
        // 在编辑器中插入@用户名
        this.commentEditor.setSelection(this.commentEditor.getLength(), 0);
        this.commentEditor.insertText(this.commentEditor.getLength(), `@${authorName} `);
        
        // 聚焦编辑器
        this.commentEditor.focus();
        
        // 滚动到编辑器
        document.querySelector('.comment-editor').scrollIntoView({ behavior: 'smooth' });
    }
    
    // 切换帖子点赞状态
    async togglePostLike() {
        // 检查用户是否登录
        const user = JSON.parse(localStorage.getItem('user') || 'null');
        if (!user) {
            this.showLoginModal();
            return;
        }
        
        try {
            await forumAPI.togglePostLike(this.postId);
            
            // 重新加载帖子数据以更新点赞状态
            await this.loadPost();
        } catch (error) {
            console.error('点赞操作失败:', error);
            this.showError('操作失败，请稍后重试');
        }
    }
    
    // 切换帖子收藏状态
    async togglePostFavorite() {
        // 检查用户是否登录
        const user = JSON.parse(localStorage.getItem('user') || 'null');
        if (!user) {
            this.showLoginModal();
            return;
        }
        
        try {
            await forumAPI.togglePostFavorite(this.postId);
            
            // 重新加载帖子数据以更新收藏状态
            await this.loadPost();
        } catch (error) {
            console.error('收藏操作失败:', error);
            this.showError('操作失败，请稍后重试');
        }
    }
    
    // 切换用户关注状态
    async toggleFollowUser() {
        // 检查用户是否登录
        const user = JSON.parse(localStorage.getItem('user') || 'null');
        if (!user) {
            this.showLoginModal();
            return;
        }
        
        if (!this.postData) return;
        
        try {
            await forumAPI.toggleUserFollow(this.postData.author.id);
            
            // 重新加载帖子数据以更新关注状态
            await this.loadPost();
        } catch (error) {
            console.error('关注操作失败:', error);
            this.showError('操作失败，请稍后重试');
        }
    }
    
    // 切换评论点赞状态
    async toggleCommentLike(commentId, likeBtn) {
        // 检查用户是否登录
        const user = JSON.parse(localStorage.getItem('user') || 'null');
        if (!user) {
            this.showLoginModal();
            return;
        }
        
        try {
            await forumAPI.toggleCommentLike(commentId);
            
            // 更新点赞状态和计数
            likeBtn.classList.toggle('active');
            const likeCount = likeBtn.querySelector('span');
            const currentCount = parseInt(likeCount.textContent);
            likeCount.textContent = likeBtn.classList.contains('active') ? currentCount + 1 : currentCount - 1;
        } catch (error) {
            console.error('评论点赞操作失败:', error);
            this.showError('操作失败，请稍后重试');
        }
    }
    
    // 删除评论
    async deleteComment(commentId, commentElement) {
        if (!confirm('确定要删除这条评论吗？此操作不可撤销。')) {
            return;
        }
        
        try {
            await forumAPI.deleteComment(commentId);
            
            // 从DOM中移除评论元素
            commentElement.remove();
            
            // 更新评论计数
            const commentCountElement = document.getElementById('commentCount');
            const currentCount = parseInt(commentCountElement.textContent);
            commentCountElement.textContent = `${currentCount - 1} 条评论`;
            
            this.showSuccess('评论删除成功');
        } catch (error) {
            console.error('删除评论失败:', error);
            this.showError('删除失败，请稍后重试');
        }
    }
    
    // 举报评论
    reportComment(commentId) {
        // 这里可以实现举报评论的逻辑
        // 例如，显示举报表单或直接调用API
        this.showError('举报功能开发中');
    }
    
    // 切换帖子置顶状态
    async togglePostPin() {
        try {
            await forumAPI.togglePostPin(this.postId);
            
            // 重新加载帖子数据以更新置顶状态
            await this.loadPost();
        } catch (error) {
            console.error('置顶操作失败:', error);
            this.showError('操作失败，请稍后重试');
        }
    }
    
    // 切换帖子精华状态
    async togglePostFeatured() {
        try {
            await forumAPI.setPostFeatured(this.postId);
            
            // 重新加载帖子数据以更新精华状态
            await this.loadPost();
        } catch (error) {
            console.error('精华操作失败:', error);
            this.showError('操作失败，请稍后重试');
        }
    }
    
    // 编辑帖子
    async editPost() {
        // 跳转到编辑页面
        window.location.href = `/pages/forum-edit.html?id=${this.postId}`;
    }
    
    // 删除帖子
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
    
    // 显示分享模态框
    showShareModal() {
        const shareModal = document.getElementById('shareModal');
        const shareLinkInput = document.getElementById('shareLinkInput');
        
        // 设置分享链接
        shareLinkInput.value = window.location.href;
        
        // 显示模态框
        shareModal.style.display = 'flex';
    }
    
    // 隐藏分享模态框
    hideShareModal() {
        document.getElementById('shareModal').style.display = 'none';
    }
    
    // 复制分享链接
    copyShareLink() {
        const shareLinkInput = document.getElementById('shareLinkInput');
        shareLinkInput.select();
        document.execCommand('copy');
        
        this.showSuccess('链接已复制');
    }
    
    // 生成二维码
    generateQRCode() {
        // 这里可以实现生成二维码的逻辑
        this.showError('二维码生成功能开发中');
    }
    
    // 显示举报模态框
    showReportModal() {
        document.getElementById('reportModal').style.display = 'flex';
    }
    
    // 隐藏举报模态框
    hideReportModal() {
        document.getElementById('reportModal').style.display = 'none';
    }
    
    // 提交举报
    async submitReport() {
        const reportReason = document.getElementById('reportReason').value;
        
        if (!reportReason.trim()) {
            this.showError('请填写举报原因');
            return;
        }
        
        try {
            await forumAPI.reportPost(this.postId, reportReason);
            this.hideReportModal();
            this.showSuccess('举报已提交，感谢您的反馈');
        } catch (error) {
            console.error('提交举报失败:', error);
            this.showError('提交失败，请稍后重试');
        }
    }
    
    // 显示登录模态框
    showLoginModal() {
        document.getElementById('loginModal').style.display = 'flex';
    }
    
    // 隐藏登录模态框
    hideLoginModal() {
        document.getElementById('loginModal').style.display = 'none';
    }
    
    // 初始化返回顶部按钮
    initScrollToTop() {
        const scrollToTopBtn = document.getElementById('scrollToTopBtn');
        
        window.addEventListener('scroll', () => {
            if (window.pageYOffset > 300) {
                scrollToTopBtn.style.display = 'block';
            } else {
                scrollToTopBtn.style.display = 'none';
            }
        });
        
        scrollToTopBtn.addEventListener('click', () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }
    
    // 更新用户图标
    updateUserIcon() {
        const userIcon = document.getElementById('userIcon');
        const user = JSON.parse(localStorage.getItem('user') || 'null');
        
        if (user && user.avatar) {
            userIcon.innerHTML = `<img src="${user.avatar}" alt="${user.username}">`;
        } else if (user && user.username) {
            userIcon.innerHTML = user.username.charAt(0).toUpperCase();
        } else {
            userIcon.innerHTML = '<i class="fas fa-user"></i>';
        }
        
        // 添加点击事件
        userIcon.addEventListener('click', () => {
            if (user) {
                window.location.href = '/pages/profile.html';
            } else {
                window.location.href = '/pages/login.html';
            }
        });
    }
    
    // 更新评论字符计数
    updateCommentCharCount(count) {
        document.getElementById('commentCharCount').textContent = count;
    }
    
    // 更新提交按钮状态
    updateSubmitButton(enabled) {
        const submitBtn = document.getElementById('submitCommentBtn');
        submitBtn.disabled = !enabled;
        
        if (enabled) {
            submitBtn.classList.add('enabled');
        } else {
            submitBtn.classList.remove('enabled');
        }
    }
    
    // 显示表情选择器
    showEmojiPicker() {
        // 这里可以实现表情选择器的逻辑
        this.showError('表情选择器功能开发中');
    }
    
    // 插入表情
    insertEmoji(emoji) {
        if (this.commentEditor) {
            const range = this.commentEditor.getSelection();
            if (range) {
                this.commentEditor.insertText(range.index, emoji);
            }
        }
    }
    
    // 上传图片
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
    
    // 显示用户提及功能
    showUserMention() {
        // 这里可以实现用户提及功能的逻辑
        this.showError('@用户功能开发中');
    }
    
    // 检查是否可以管理帖子
    async canManagePost(post) {
        try {
            // 检查用户是否登录且是管理员或帖子作者
            const user = JSON.parse(localStorage.getItem('user') || 'null');
            
            if (!user) {
                return false;
            }
            
            // 检查是否是管理员或帖子作者
            return user.is_staff || (post && user.id === post.author.id);
        } catch (error) {
            console.error('检查管理权限失败:', error);
            return false;
        }
    }
    
    // 更新页面标题
    updatePageTitle(title) {
        document.title = `${title} - 非遗传承网`;
    }
    
    // 更新页面元数据
    updatePageMeta(post) {
        // 可以在这里添加页面元数据，如描述、关键词等
    }
    
    // 格式化日期时间
    formatDateTime(dateTime) {
        const date = new Date(dateTime);
        const now = new Date();
        const diffMs = now - date;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        
        if (diffDays === 0) {
            return date.toLocaleTimeString('zh-CN', { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
        } else if (diffDays === 1) {
            return '昨天 ' + date.toLocaleTimeString('zh-CN', { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
        } else if (diffDays < 7) {
            return diffDays + '天前';
        } else {
            return date.toLocaleDateString('zh-CN');
        }
    }
    
    // 格式化相对时间
    formatRelativeTime(dateTime) {
        const date = new Date(dateTime);
        const now = new Date();
        const diffMs = now - date;
        const diffSecs = Math.floor(diffMs / 1000);
        const diffMins = Math.floor(diffSecs / 60);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);
        
        if (diffSecs < 60) {
            return diffSecs + '秒前';
        } else if (diffMins < 60) {
            return diffMins + '分钟前';
        } else if (diffHours < 24) {
            return diffHours + '小时前';
        } else if (diffDays < 30) {
            return diffDays + '天前';
        } else {
            return date.toLocaleDateString('zh-CN');
        }
    }
    
    // 显示错误消息
    showError(message) {
        const notification = document.getElementById('notification');
        const notificationMessage = document.getElementById('notificationMessage');
        
        notificationMessage.textContent = '错误: ' + message;
        notification.classList.add('error');
        notification.classList.add('show');
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.classList.remove('error');
            }, 300);
        }, 3000);
    }
    
    // 显示成功消息
    showSuccess(message) {
        const notification = document.getElementById('notification');
        const notificationMessage = document.getElementById('notificationMessage');
        
        notificationMessage.textContent = '成功: ' + message;
        notification.classList.add('success');
        notification.classList.add('show');
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.classList.remove('success');
            }, 300);
        }, 3000);
    }
}

// 将类暴露到全局
if (typeof window !== 'undefined') {
    window.PostDetailManager = PostDetailManager;
}