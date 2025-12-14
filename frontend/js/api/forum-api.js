// 论坛API接口

const forumAPI = {
    // 获取帖子列表
    getPosts: async (params = {}) => {
        const queryParams = new URLSearchParams();
        
        // 添加查询参数
        if (params.sort) queryParams.append('sort', params.sort);
        if (params.tag) queryParams.append('tag', params.tag);
        if (params.search) queryParams.append('search', params.search);
        if (params.page) queryParams.append('page', params.page);
        if (params.page_size) queryParams.append('page_size', params.page_size);
        
        const endpoint = `/forum/posts/?${queryParams.toString()}`;
        return await apiRequest(endpoint);
    },
    
    // 获取帖子详情
    getPostDetail: async (postId) => {
        return await apiRequest(`/forum/posts/${postId}/`);
    },
    
    // 创建新帖子
    createPost: async (postData) => {
        console.log('forumAPI.createPost 调用，数据:', postData);
        console.log('JSON序列化后的数据:', JSON.stringify(postData));
        
        const result = await apiRequest('/forum/posts/', {
            method: 'POST',
            body: JSON.stringify(postData)
        });
        
        console.log('createPost 响应结果:', result);
        return result;
    },
    
    // 更新帖子
    updatePost: async (postId, postData) => {
        return await apiRequest(`/forum/posts/${postId}/`, {
            method: 'PUT',
            body: JSON.stringify(postData)
        });
    },
    
    // 删除帖子
    deletePost: async (postId) => {
        return await apiRequest(`/forum/posts/${postId}/`, {
            method: 'DELETE'
        });
    },
    
    // 点赞帖子
    likePost: async (postId) => {
        return await apiRequest(`/forum/posts/${postId}/like/`, {
            method: 'POST'
        });
    },

    // 切换帖子点赞状态
    togglePostLike: async (postId) => {
        return await apiRequest(`/forum/posts/${postId}/like/`, {
            method: 'POST'
        });
    },
    
    // 收藏帖子
    favoritePost: async (postId) => {
        return await apiRequest(`/forum/posts/${postId}/favorite/`, {
            method: 'POST'
        });
    },

    // 切换帖子收藏状态
    togglePostFavorite: async (postId) => {
        return await apiRequest(`/forum/posts/${postId}/favorite/`, {
            method: 'POST'
        });
    },
    
    // 举报帖子
    reportPost: async (postId, reportData) => {
        return await apiRequest(`/forum/posts/${postId}/report/`, {
            method: 'POST',
            body: JSON.stringify(reportData)
        });
    },

    // 增加帖子浏览量
    incrementViewCount: async (postId) => {
        try {
            return await apiRequest(`/forum/posts/${postId}/view/`, {
                method: 'POST'
            });
        } catch (error) {
            console.warn('增加浏览量失败:', error);
            // 不抛出错误，避免影响页面加载
            return null;
        }
    },
    
    // 设置帖子为精华
    setPostFeatured: async (postId, featured = true) => {
        return await apiRequest(`/forum/posts/${postId}/featured/`, {
            method: 'POST',
            body: JSON.stringify({ featured })
        });
    },
    
    // 置顶帖子
    pinPost: async (postId, pinned = true) => {
        return await apiRequest(`/forum/posts/${postId}/pin/`, {
            method: 'POST',
            body: JSON.stringify({ pinned })
        });
    },

    // 切换帖子置顶状态
    togglePostPin: async (postId) => {
        return await apiRequest(`/forum/posts/${postId}/pin/`, {
            method: 'POST'
        });
    },
    
    // 获取评论列表
    getComments: async (postId, params = {}) => {
        const queryParams = new URLSearchParams();
        
        if (params.sort) queryParams.append('sort', params.sort);
        if (params.page) queryParams.append('page', params.page);
        if (params.page_size) queryParams.append('page_size', params.page_size);
        
        const endpoint = `/forum/posts/${postId}/comments/?${queryParams.toString()}`;
        return await apiRequest(endpoint);
    },
    
    // 创建评论
    createComment: async (postId, commentData) => {
        return await apiRequest(`/forum/posts/${postId}/comments/`, {
            method: 'POST',
            body: JSON.stringify(commentData)
        });
    },
    
    // 回复评论
    replyComment: async (postId, parentCommentId, commentData) => {
        return await apiRequest(`/forum/posts/${postId}/comments/`, {
            method: 'POST',
            body: JSON.stringify({
                ...commentData,
                parent: parentCommentId
            })
        });
    },
    
    // 更新评论
    updateComment: async (commentId, commentData) => {
        return await apiRequest(`/forum/comments/${commentId}/`, {
            method: 'PUT',
            body: JSON.stringify(commentData)
        });
    },
    
    // 删除评论
    deleteComment: async (commentId) => {
        return await apiRequest(`/forum/comments/${commentId}/`, {
            method: 'DELETE'
        });
    },
    
    // 点赞评论
    likeComment: async (commentId) => {
        return await apiRequest(`/forum/comments/${commentId}/like/`, {
            method: 'POST'
        });
    },

    // 切换评论点赞状态
    toggleCommentLike: async (commentId) => {
        return await apiRequest(`/forum/comments/${commentId}/like/`, {
            method: 'POST'
        });
    },
    
    // 举报评论
    reportComment: async (commentId, reportData) => {
        return await apiRequest(`/forum/comments/${commentId}/report/`, {
            method: 'POST',
            body: JSON.stringify(reportData)
        });
    },
    
    // 获取热门标签
    getPopularTags: async () => {
        return await apiRequest('/forum/tags/popular/');
    },
    
    // 获取活跃用户
    getActiveUsers: async (period = 'week') => {
        return await apiRequest(`/forum/users/active/?period=${period}`);
    },
    
    // 获取公告列表
    getAnnouncements: async () => {
        return await apiRequest('/forum/announcements/');
    },
    
    // 搜索用户（用于@功能）
    searchUsers: async (query) => {
        return await apiRequest(`/forum/users/search/?q=${encodeURIComponent(query)}`);
    },
    
    // 关注用户
    followUser: async (userId) => {
        return await apiRequest(`/forum/users/${userId}/follow/`, {
            method: 'POST'
        });
    },
    
    // 取消关注用户
    unfollowUser: async (userId) => {
        return await apiRequest(`/forum/users/${userId}/unfollow/`, {
            method: 'POST'
        });
    },

    // 切换用户关注状态
    toggleUserFollow: async (userId) => {
        return await apiRequest(`/forum/users/${userId}/follow/`, {
            method: 'POST'
        });
    },
    
    // 上传图片
    uploadImage: async (file) => {
        const formData = new FormData();
        formData.append('image', file);
        
        return await apiRequest('/forum/upload/image/', {
            method: 'POST',
            body: formData,
            headers: {} // 让浏览器自动设置Content-Type
        });
    },
    
    // 获取用户的帖子
    getUserPosts: async (userId, params = {}) => {
        const queryParams = new URLSearchParams();
        
        if (params.page) queryParams.append('page', params.page);
        if (params.page_size) queryParams.append('page_size', params.page_size);
        
        const endpoint = `/forum/users/${userId}/posts/?${queryParams.toString()}`;
        return await apiRequest(endpoint);
    },
    
    // 获取用户的收藏
    getUserFavorites: async (params = {}) => {
        const queryParams = new URLSearchParams();
        
        if (params.page) queryParams.append('page', params.page);
        if (params.page_size) queryParams.append('page_size', params.page_size);
        
        const endpoint = `/forum/favorites/?${queryParams.toString()}`;
        return await apiRequest(endpoint);
    },
    
    // 获取通知
    getNotifications: async (params = {}) => {
        const queryParams = new URLSearchParams();
        
        if (params.unread_only) queryParams.append('unread_only', 'true');
        
        const endpoint = `/forum/my/notifications/?${queryParams.toString()}`;
        return await apiRequest(endpoint);
    },
    
    // 获取关注列表
    getFollowingList: async (params = {}) => {
        const queryParams = new URLSearchParams();
        
        if (params.page) queryParams.append('page', params.page);
        if (params.page_size) queryParams.append('page_size', params.page_size);
        
        const endpoint = `/forum/my/following/?${queryParams.toString()}`;
        return await apiRequest(endpoint);
    },
    
    // 获取粉丝列表
    getFollowersList: async (params = {}) => {
        const queryParams = new URLSearchParams();
        
        if (params.page) queryParams.append('page', params.page);
        if (params.page_size) queryParams.append('page_size', params.page_size);
        
        const endpoint = `/forum/my/followers/?${queryParams.toString()}`;
        return await apiRequest(endpoint);
    },
    
    // 标记通知为已读
    markNotificationRead: async (notificationId) => {
        return await apiRequest(`/forum/notifications/${notificationId}/read/`, {
            method: 'POST'
        });
    },
    
    // 标记所有通知为已读
    markAllNotificationsRead: async () => {
        return await apiRequest('/forum/notifications/read_all/', {
            method: 'POST'
        });
    }
};

// 将API暴露到全局
if (typeof window !== 'undefined') {
    window.ForumAPI = forumAPI;
    window.forumAPI = forumAPI; // 保持向后兼容
}

// 如果是Node.js环境，导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = forumAPI;
}