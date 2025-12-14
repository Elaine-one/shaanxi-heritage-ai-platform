from django.db import models
from django.contrib.auth.models import User

# 导入用户资料模型
from .user_models import UserProfile

# 导入论坛相关模型
from .forum_models import *

# Create your models here.
class Heritage(models.Model):
    level = models.CharField(max_length=50, default='未知级别', blank=True, null=True, verbose_name="级别")
    name = models.CharField(max_length=100, unique=True, verbose_name="项目名称")
    pinyin_name = models.CharField(max_length=200, blank=True, null=True, verbose_name="项目拼音名称")
    category = models.CharField(max_length=50, verbose_name="类别")
    region = models.CharField(max_length=50, verbose_name="地区")
    batch = models.CharField(max_length=50, blank=True, null=True, verbose_name="批次")
    description = models.TextField(verbose_name="描述")
    history = models.TextField(blank=True, null=True, verbose_name="历史渊源")
    latitude = models.FloatField(verbose_name="纬度", null=True, blank=True)
    longitude = models.FloatField(verbose_name="经度", null=True, blank=True)
    features = models.TextField(blank=True, null=True, verbose_name="基本内容/特征")
    value = models.TextField(blank=True, null=True, verbose_name="重要价值")
    status = models.TextField(blank=True, null=True, verbose_name="存续状况")
    protection_measures = models.TextField(blank=True, null=True, verbose_name="保护措施")
    inheritors = models.TextField(blank=True, null=True, verbose_name="传承人")
    related_works = models.TextField(blank=True, null=True, verbose_name="相关制品")
    main_image_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="主图片URL")
    gallery_image_urls = models.JSONField(default=list, blank=True, verbose_name="图库图片URL列表")

    class Meta:
        ordering = ['id']
        verbose_name = "非物质文化遗产"
        verbose_name_plural = "非物质文化遗产"

    def __str__(self):
        return self.name

class HeritageImage(models.Model):
    heritage = models.ForeignKey(Heritage, related_name='images', on_delete=models.CASCADE, verbose_name="非遗项目")
    image = models.ImageField(upload_to='heritage_images/', verbose_name="图片")
    is_main = models.BooleanField(default=False, verbose_name="是否主图")

    class Meta:
        verbose_name = "非遗图片"
        verbose_name_plural = "非遗图片"

    def __str__(self):
        return f"Image for {self.heritage.name}"


class UserFavorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites', verbose_name="用户")
    heritage = models.ForeignKey(Heritage, on_delete=models.CASCADE, related_name='favorited_by', verbose_name="非遗项目")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="收藏时间")

    class Meta:
        unique_together = ('user', 'heritage') #确保每个用户对每个项目只能收藏一次
        ordering = ['-created_at']
        verbose_name = "用户收藏"
        verbose_name_plural = "用户收藏"

    def __str__(self):
        return f"{self.user.username} favorites {self.heritage.name}"


class UserHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='browsing_history', verbose_name="用户")
    heritage = models.ForeignKey(Heritage, on_delete=models.CASCADE, related_name='viewed_by', verbose_name="非遗项目")
    visit_time = models.DateTimeField(auto_now_add=True, verbose_name="浏览时间")

    class Meta:
        unique_together = ('user', 'heritage')
        ordering = ['-visit_time']
        verbose_name = "浏览历史"
        verbose_name_plural = "浏览历史"

    def __str__(self):
        return f"{self.user.username} viewed {self.heritage.name} at {self.visit_time}"


class News(models.Model):
    """非遗资讯模型"""
    title = models.CharField(max_length=200, verbose_name="标题")
    summary = models.TextField(max_length=500, verbose_name="摘要", blank=True, null=True)
    content = models.TextField(verbose_name="内容")
    author = models.CharField(max_length=100, verbose_name="作者", blank=True, null=True)
    source = models.CharField(max_length=200, verbose_name="来源", blank=True, null=True)
    source_url = models.URLField(max_length=500, verbose_name="来源链接", blank=True, null=True)
    image_url = models.URLField(max_length=500, verbose_name="配图链接", blank=True, null=True)
    publish_date = models.DateTimeField(verbose_name="发布时间")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    view_count = models.PositiveIntegerField(default=0, verbose_name="浏览次数")
    tags = models.CharField(max_length=200, verbose_name="标签", blank=True, null=True, help_text="多个标签用逗号分隔")
    
    class Meta:
        ordering = ['-publish_date']
        verbose_name = "新闻资讯"
        verbose_name_plural = "新闻资讯"
    
    def __str__(self):
        return self.title


class Policy(models.Model):
    POLICY_TYPE_CHOICES = [
        ('law', '法律法规'),
        ('regulation', '部门规章'),
        ('notice', '通知公告'),
        ('standard', '标准规范'),
        ('guidance', '指导意见'),
        ('plan', '规划计划'),
        ('other', '其他'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="标题")
    summary = models.TextField(max_length=500, blank=True, null=True, verbose_name="摘要")
    content = models.TextField(verbose_name="内容")
    policy_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="政策编号")
    issuing_authority = models.CharField(max_length=100, verbose_name="发布机构")
    policy_type = models.CharField(max_length=20, choices=POLICY_TYPE_CHOICES, default='other', verbose_name="政策类型")
    publish_date = models.DateField(verbose_name="发布日期")
    effective_date = models.DateField(blank=True, null=True, verbose_name="生效日期")
    source_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="来源链接")
    attachment_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="附件链接")
    tags = models.CharField(max_length=200, blank=True, null=True, verbose_name="标签")
    view_count = models.PositiveIntegerField(default=0, verbose_name="浏览量")
    is_active = models.BooleanField(default=True, verbose_name="是否激活")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        ordering = ['-publish_date']
        verbose_name = "政策法规"
        verbose_name_plural = "政策法规"

    def __str__(self):
        return self.title
