from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinLengthValidator


class ForumPost(models.Model):
    """论坛帖子模型"""
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('published', '已发布'),
        ('hidden', '已隐藏'),
        ('deleted', '已删除'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="标题", validators=[MinLengthValidator(5)])
    content = models.TextField(verbose_name="内容", validators=[MinLengthValidator(10)])
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_posts', verbose_name="作者")
    
    # 状态和标识
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='published', verbose_name="状态")
    is_pinned = models.BooleanField(default=False, verbose_name="是否置顶")
    is_featured = models.BooleanField(default=False, verbose_name="是否精华")
    is_locked = models.BooleanField(default=False, verbose_name="是否锁定")
    
    # 统计数据
    view_count = models.PositiveIntegerField(default=0, verbose_name="浏览量")
    like_count = models.PositiveIntegerField(default=0, verbose_name="点赞数")
    comment_count = models.PositiveIntegerField(default=0, verbose_name="评论数")
    favorite_count = models.PositiveIntegerField(default=0, verbose_name="收藏数")
    
    # 时间字段
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    last_reply_at = models.DateTimeField(null=True, blank=True, verbose_name="最后回复时间")
    
    # 标签
    tags = models.ManyToManyField('ForumTag', blank=True, related_name='posts', verbose_name="标签")
    
    class Meta:
        ordering = ['-is_pinned', '-last_reply_at', '-created_at']
        verbose_name = "论坛帖子"
        verbose_name_plural = "论坛帖子"
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['-last_reply_at']),
            models.Index(fields=['is_pinned', '-last_reply_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return self.title
    
    def update_last_reply_time(self):
        """更新最后回复时间"""
        self.last_reply_at = timezone.now()
        self.save(update_fields=['last_reply_at'])
    
    def increment_view_count(self):
        """增加浏览量"""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def get_hot_score(self):
        """计算热度分数"""
        # 简单的热度算法：点赞数 * 2 + 评论数 * 3 + 浏览数 * 0.1
        return self.like_count * 2 + self.comment_count * 3 + self.view_count * 0.1


class ForumComment(models.Model):
    """论坛评论模型"""
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name='comments', verbose_name="帖子")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_comments', verbose_name="作者")
    content = models.TextField(verbose_name="内容", validators=[MinLengthValidator(2)])
    
    # 嵌套评论支持
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, 
                              related_name='replies', verbose_name="父评论")
    
    # 统计数据
    like_count = models.PositiveIntegerField(default=0, verbose_name="点赞数")
    
    # 状态
    is_deleted = models.BooleanField(default=False, verbose_name="是否删除")
    
    # 时间字段
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        ordering = ['created_at']
        verbose_name = "论坛评论"
        verbose_name_plural = "论坛评论"
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['parent']),
        ]
    
    def __str__(self):
        return f"{self.author.username} 在 {self.post.title} 的评论"
    
    def get_level(self):
        """获取评论层级"""
        level = 0
        parent = self.parent
        while parent:
            level += 1
            parent = parent.parent
        return level


class ForumTag(models.Model):
    """论坛标签模型"""
    name = models.CharField(max_length=50, unique=True, verbose_name="标签名")
    description = models.TextField(blank=True, verbose_name="描述")
    color = models.CharField(max_length=7, default='#007bff', verbose_name="颜色")
    
    # 统计数据
    post_count = models.PositiveIntegerField(default=0, verbose_name="帖子数量")
    
    # 时间字段
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    class Meta:
        ordering = ['-post_count', 'name']
        verbose_name = "论坛标签"
        verbose_name_plural = "论坛标签"
    
    def __str__(self):
        return self.name


class ForumPostLike(models.Model):
    """帖子点赞模型"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_likes', verbose_name="用户")
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name='likes', verbose_name="帖子")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="点赞时间")
    
    class Meta:
        unique_together = ('user', 'post')
        verbose_name = "帖子点赞"
        verbose_name_plural = "帖子点赞"
    
    def __str__(self):
        return f"{self.user.username} 点赞了 {self.post.title}"


class ForumCommentLike(models.Model):
    """评论点赞模型"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comment_likes', verbose_name="用户")
    comment = models.ForeignKey(ForumComment, on_delete=models.CASCADE, related_name='likes', verbose_name="评论")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="点赞时间")
    
    class Meta:
        unique_together = ('user', 'comment')
        verbose_name = "评论点赞"
        verbose_name_plural = "评论点赞"
    
    def __str__(self):
        return f"{self.user.username} 点赞了评论"


class ForumPostFavorite(models.Model):
    """帖子收藏模型"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_favorites', verbose_name="用户")
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name='favorites', verbose_name="帖子")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="收藏时间")
    
    class Meta:
        unique_together = ('user', 'post')
        ordering = ['-created_at']
        verbose_name = "帖子收藏"
        verbose_name_plural = "帖子收藏"
    
    def __str__(self):
        return f"{self.user.username} 收藏了 {self.post.title}"


class ForumUserFollow(models.Model):
    """用户关注模型"""
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following', verbose_name="关注者")
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers', verbose_name="被关注者")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="关注时间")
    
    class Meta:
        unique_together = ('follower', 'following')
        verbose_name = "用户关注"
        verbose_name_plural = "用户关注"
    
    def __str__(self):
        return f"{self.follower.username} 关注了 {self.following.username}"


class ForumReport(models.Model):
    """举报模型"""
    REPORT_TYPE_CHOICES = [
        ('spam', '垃圾信息'),
        ('inappropriate', '不当内容'),
        ('harassment', '骚扰'),
        ('copyright', '版权侵犯'),
        ('other', '其他'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('resolved', '已解决'),
        ('rejected', '已拒绝'),
    ]
    
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made', verbose_name="举报者")
    
    # 被举报的内容（帖子或评论）
    post = models.ForeignKey(ForumPost, null=True, blank=True, on_delete=models.CASCADE, 
                            related_name='reports', verbose_name="被举报帖子")
    comment = models.ForeignKey(ForumComment, null=True, blank=True, on_delete=models.CASCADE, 
                               related_name='reports', verbose_name="被举报评论")
    
    reason = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES, verbose_name="举报原因")
    description = models.TextField(blank=True, verbose_name="详细描述")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="处理状态")
    handler = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, 
                               related_name='reports_handled', verbose_name="处理人")
    handler_note = models.TextField(blank=True, verbose_name="处理备注")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="举报时间")
    handled_at = models.DateTimeField(null=True, blank=True, verbose_name="处理时间")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "举报"
        verbose_name_plural = "举报"
    
    def __str__(self):
        target = self.post.title if self.post else f"评论#{self.comment.id}"
        return f"{self.reporter.username} 举报了 {target}"


class ForumAnnouncement(models.Model):
    """论坛公告模型"""
    title = models.CharField(max_length=200, verbose_name="标题")
    content = models.TextField(verbose_name="内容")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcements', verbose_name="发布者")
    
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    is_pinned = models.BooleanField(default=False, verbose_name="是否置顶")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        ordering = ['-is_pinned', '-created_at']
        verbose_name = "论坛公告"
        verbose_name_plural = "论坛公告"
    
    def __str__(self):
        return self.title


class ForumUserStats(models.Model):
    """用户论坛统计模型"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='forum_stats', verbose_name="用户")
    
    # 统计数据
    post_count = models.PositiveIntegerField(default=0, verbose_name="发帖数")
    comment_count = models.PositiveIntegerField(default=0, verbose_name="评论数")
    like_received = models.PositiveIntegerField(default=0, verbose_name="获得点赞数")
    follower_count = models.PositiveIntegerField(default=0, verbose_name="粉丝数")
    following_count = models.PositiveIntegerField(default=0, verbose_name="关注数")
    
    # 等级和积分
    level = models.PositiveIntegerField(default=1, verbose_name="等级")
    experience = models.PositiveIntegerField(default=0, verbose_name="经验值")
    
    # 时间字段
    last_active_at = models.DateTimeField(auto_now=True, verbose_name="最后活跃时间")
    
    class Meta:
        verbose_name = "用户论坛统计"
        verbose_name_plural = "用户论坛统计"
    
    def __str__(self):
        return f"{self.user.username} 的论坛统计"
    
    def calculate_level(self):
        """根据经验值计算等级"""
        # 简单的等级计算：每100经验值升1级
        new_level = max(1, self.experience // 100 + 1)
        if new_level != self.level:
            self.level = new_level
            self.save(update_fields=['level'])
        return new_level
    
    def add_experience(self, points):
        """增加经验值"""
        self.experience += points
        self.calculate_level()
        self.save(update_fields=['experience'])