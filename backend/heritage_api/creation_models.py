from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import FileExtensionValidator

class UserCreation(models.Model):
    """用户创作模型"""
    
    CREATION_TYPE_CHOICES = [
        ('video', '视频创作'),
        ('photo', '图片创作'),
        ('article', '文章创作'),
        ('music', '音乐创作'),
    ]
    
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('published', '已发布'),
        ('reviewing', '审核中'),
        ('rejected', '已拒绝'),
        ('archived', '已归档'),
    ]
    
    # 基本信息
    title = models.CharField(max_length=100, verbose_name="创作标题")
    description = models.TextField(verbose_name="创作描述")
    type = models.CharField(max_length=20, choices=CREATION_TYPE_CHOICES, verbose_name="创作类型")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="状态")
    
    # 媒体文件
    media_file = models.FileField(
        upload_to='user_creations/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name="媒体文件",
        validators=[
            FileExtensionValidator(
                allowed_extensions=['mp4', 'avi', 'mov', 'jpg', 'jpeg', 'png', 'gif', 'mp3', 'wav']
            )
        ]
    )
    thumbnail = models.ImageField(
        upload_to='creation_thumbnails/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name="缩略图"
    )
    
    # 关联信息
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='creations', verbose_name="作者")
    heritage = models.ForeignKey(
        'Heritage', 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        related_name='creations',
        verbose_name="关联非遗项目"
    )
    
    # 统计信息
    view_count = models.PositiveIntegerField(default=0, verbose_name="浏览数")
    like_count = models.PositiveIntegerField(default=0, verbose_name="点赞数")
    comment_count = models.PositiveIntegerField(default=0, verbose_name="评论数")
    share_count = models.PositiveIntegerField(default=0, verbose_name="分享数")
    
    # 元数据
    tags = models.JSONField(default=list, blank=True, verbose_name="标签")
    is_featured = models.BooleanField(default=False, verbose_name="是否精选")
    is_public = models.BooleanField(default=True, verbose_name="是否公开")
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    published_at = models.DateTimeField(blank=True, null=True, verbose_name="发布时间")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "用户创作"
        verbose_name_plural = "用户创作"
        indexes = [
            models.Index(fields=['status', 'is_public', 'created_at']),
            models.Index(fields=['author', 'created_at']),
            models.Index(fields=['heritage', 'created_at']),
            models.Index(fields=['type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.author.username}"
    
    def save(self, *args, **kwargs):
        # 如果状态变为已发布且发布时间为空，则设置发布时间
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return f"/creations/{self.id}/"


class CreationLike(models.Model):
    """创作点赞模型"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='creation_likes', verbose_name="用户")
    creation = models.ForeignKey(UserCreation, on_delete=models.CASCADE, related_name='likes', verbose_name="创作")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="点赞时间")
    
    class Meta:
        unique_together = ('user', 'creation')
        verbose_name = "创作点赞"
        verbose_name_plural = "创作点赞"
    
    def __str__(self):
        return f"{self.user.username} likes {self.creation.title}"


class CreationComment(models.Model):
    """创作评论模型"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='creation_comments', verbose_name="用户")
    creation = models.ForeignKey(UserCreation, on_delete=models.CASCADE, related_name='comments', verbose_name="创作")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='replies', verbose_name="父评论")
    content = models.TextField(verbose_name="评论内容")
    is_active = models.BooleanField(default=True, verbose_name="是否有效")
    
    # 统计信息
    like_count = models.PositiveIntegerField(default=0, verbose_name="点赞数")
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        ordering = ['created_at']
        verbose_name = "创作评论"
        verbose_name_plural = "创作评论"
    
    def __str__(self):
        return f"{self.user.username}评论: {self.content[:50]}"


class CreationViewHistory(models.Model):
    """创作浏览历史模型"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='creation_views', verbose_name="用户")
    creation = models.ForeignKey(UserCreation, on_delete=models.CASCADE, related_name='view_history', verbose_name="创作")
    viewed_at = models.DateTimeField(auto_now_add=True, verbose_name="浏览时间")
    duration = models.PositiveIntegerField(default=0, verbose_name="观看时长(秒)")
    
    class Meta:
        unique_together = ('user', 'creation')
        ordering = ['-viewed_at']
        verbose_name = "创作浏览历史"
        verbose_name_plural = "创作浏览历史"
    
    def __str__(self):
        return f"{self.user.username} viewed {self.creation.title}"


class CreationFavorite(models.Model):
    """创作收藏模型"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='creation_favorites', verbose_name="用户")
    creation = models.ForeignKey(UserCreation, on_delete=models.CASCADE, related_name='favorites', verbose_name="创作")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="收藏时间")
    
    class Meta:
        unique_together = ('user', 'creation')
        verbose_name = "创作收藏"
        verbose_name_plural = "创作收藏"
    
    def __str__(self):
        return f"{self.user.username} favorites {self.creation.title}"


