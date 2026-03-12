from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Heritage, UserFavorite, UserHistory, News, Policy
from .user_models import UserProfile
from .creation_models import (
    UserCreation, CreationLike, CreationComment,
    CreationViewHistory, CreationFavorite
)
from .forum_models import (
    ForumPost, ForumComment, ForumTag, ForumPostLike, ForumCommentLike,
    ForumPostFavorite, ForumUserFollow, ForumReport,
    ForumAnnouncement, ForumRule, ForumUserStats
)


# ============================================
# 内联类定义
# ============================================

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = '用户资料'
    verbose_name_plural = '用户资料'
    fields = ('avatar', 'display_name', 'bio')


class ForumUserStatsInline(admin.TabularInline):
    model = ForumUserStats
    can_delete = False
    verbose_name = '论坛统计'
    verbose_name_plural = '论坛统计'
    fields = ('level', 'experience', 'post_count', 'comment_count', 'like_received', 'follower_count', 'following_count')
    readonly_fields = ('post_count', 'comment_count', 'like_received', 'follower_count', 'following_count')
    extra = 0


class ForumPostInline(admin.TabularInline):
    model = ForumPost
    verbose_name = '发表的帖子'
    verbose_name_plural = '发表的帖子'
    fields = ('title', 'status', 'view_count', 'like_count', 'created_at')
    readonly_fields = ('title', 'status', 'view_count', 'like_count', 'created_at')
    extra = 0
    show_change_link = True
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('-created_at')[:10]


class ForumCommentInline(admin.TabularInline):
    model = ForumComment
    verbose_name = '帖子评论'
    verbose_name_plural = '帖子评论'
    fields = ('author', 'content_preview', 'like_count', 'is_deleted', 'created_at')
    readonly_fields = ('author', 'content_preview', 'like_count', 'created_at')
    extra = 0
    show_change_link = True
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = '评论内容'
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('-created_at')[:20]


class ForumPostLikeInline(admin.TabularInline):
    model = ForumPostLike
    verbose_name = '点赞用户'
    verbose_name_plural = '点赞用户'
    fields = ('user', 'created_at')
    readonly_fields = ('user', 'created_at')
    extra = 0
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('-created_at')[:20]


class ForumPostFavoriteInline(admin.TabularInline):
    model = ForumPostFavorite
    verbose_name = '收藏用户'
    verbose_name_plural = '收藏用户'
    fields = ('user', 'created_at')
    readonly_fields = ('user', 'created_at')
    extra = 0
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('-created_at')[:20]


class CreationCommentInline(admin.TabularInline):
    model = CreationComment
    verbose_name = '创作评论'
    verbose_name_plural = '创作评论'
    fields = ('user', 'content_preview', 'like_count', 'is_active', 'created_at')
    readonly_fields = ('user', 'content_preview', 'like_count', 'created_at')
    extra = 0
    show_change_link = True
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = '评论内容'


class CreationLikeInline(admin.TabularInline):
    model = CreationLike
    verbose_name = '点赞用户'
    verbose_name_plural = '点赞用户'
    fields = ('user', 'created_at')
    readonly_fields = ('user', 'created_at')
    extra = 0


class CreationFavoriteInline(admin.TabularInline):
    model = CreationFavorite
    verbose_name = '收藏用户'
    verbose_name_plural = '收藏用户'
    fields = ('user', 'created_at')
    readonly_fields = ('user', 'created_at')
    extra = 0


# ============================================
# 第一部分：用户管理
# ============================================

# 先取消注册User，再重新注册
admin.site.unregister(User)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline, ForumUserStatsInline)
    list_display = ('username', 'email', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    ordering = ('-date_joined',)
    
    fieldsets = (
        ('基本信息', {'fields': ('username', 'password')}),
        ('个人信息', {'fields': ('first_name', 'last_name', 'email')}),
        ('权限', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('重要日期', {'fields': ('last_login', 'date_joined')}),
    )


# ============================================
# 第二部分：非遗管理
# ============================================

@admin.register(Heritage)
class HeritageAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'level', 'region', 'batch')
    list_filter = ('category', 'level', 'region', 'batch')
    search_fields = ('name', 'description')
    ordering = ('id',)
    list_per_page = 20
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'pinyin_name', 'category', 'level', 'region', 'batch')
        }),
        ('详细描述', {
            'fields': ('description', 'history', 'features', 'value', 'status', 'protection_measures')
        }),
        ('地理位置', {
            'fields': ('latitude', 'longitude')
        }),
        ('相关信息', {
            'fields': ('inheritors', 'related_works')
        }),
        ('图片', {
            'fields': ('main_image_url', 'gallery_image_urls')
        })
    )


@admin.register(UserFavorite)
class UserFavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'heritage', 'created_at')
    list_filter = ('created_at', 'heritage__category')
    search_fields = ('user__username', 'heritage__name')
    ordering = ('-created_at',)
    list_per_page = 20
    verbose_name = '用户收藏'
    verbose_name_plural = '用户收藏'
    
    readonly_fields = ('user', 'heritage', 'created_at')
    
    def has_add_permission(self, request):
        return False


@admin.register(UserHistory)
class UserHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'heritage', 'visit_time')
    list_filter = ('visit_time', 'heritage__category')
    search_fields = ('user__username', 'heritage__name')
    ordering = ('-visit_time',)
    list_per_page = 20
    verbose_name = '浏览历史'
    verbose_name_plural = '浏览历史'
    
    readonly_fields = ('user', 'heritage', 'visit_time')
    
    def has_add_permission(self, request):
        return False


# ============================================
# 第三部分：资讯管理
# ============================================

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'publish_date', 'view_count', 'is_featured', 'is_active')
    list_filter = ('is_active', 'is_featured', 'publish_date', 'source')
    search_fields = ('title', 'summary', 'content', 'author', 'tags')
    ordering = ('-publish_date',)
    list_per_page = 20
    list_editable = ('is_active', 'is_featured')
    verbose_name = '新闻资讯'
    verbose_name_plural = '新闻资讯'
    
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'summary', 'author', 'source', 'source_url')
        }),
        ('内容', {
            'fields': ('content', 'image_url')
        }),
        ('发布设置', {
            'fields': ('publish_date', 'is_active', 'is_featured')
        }),
        ('分类标签', {
            'fields': ('tags',)
        }),
        ('统计信息', {
            'fields': ('view_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('view_count', 'created_at', 'updated_at')


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = ('title', 'policy_number', 'issuing_authority', 'get_policy_type_display', 'publish_date', 'view_count', 'is_active')
    list_filter = ('is_active', 'policy_type', 'publish_date', 'issuing_authority')
    search_fields = ('title', 'summary', 'content', 'policy_number', 'issuing_authority', 'tags')
    ordering = ('-publish_date',)
    list_per_page = 20
    list_editable = ('is_active',)
    verbose_name = '政策法规'
    verbose_name_plural = '政策法规'
    
    def get_policy_type_display(self, obj):
        return obj.get_policy_type_display()
    get_policy_type_display.short_description = '政策类型'
    get_policy_type_display.admin_order_field = 'policy_type'
    
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'summary', 'policy_number', 'issuing_authority', 'policy_type')
        }),
        ('内容', {
            'fields': ('content',)
        }),
        ('日期设置', {
            'fields': ('publish_date', 'effective_date', 'is_active')
        }),
        ('链接附件', {
            'fields': ('source_url', 'attachment_url')
        }),
        ('分类标签', {
            'fields': ('tags',)
        }),
        ('统计信息', {
            'fields': ('view_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('view_count', 'created_at', 'updated_at')


# ============================================
# 第四部分：论坛管理
# ============================================

@admin.register(ForumPost)
class ForumPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'is_pinned', 'is_featured', 'view_count', 'like_count', 'comment_count', 'created_at')
    list_filter = ('status', 'is_pinned', 'is_featured', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    ordering = ('-is_pinned', '-created_at')
    list_per_page = 20
    list_editable = ('status', 'is_pinned', 'is_featured')
    inlines = [ForumCommentInline, ForumPostLikeInline, ForumPostFavoriteInline]
    verbose_name = '论坛帖子'
    verbose_name_plural = '论坛帖子'
    
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'content', 'author', 'tags')
        }),
        ('状态设置', {
            'fields': ('status', 'is_pinned', 'is_featured', 'is_locked')
        }),
        ('统计信息', {
            'fields': ('view_count', 'like_count', 'comment_count', 'favorite_count'),
            'classes': ('collapse',)
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at', 'last_reply_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('view_count', 'like_count', 'comment_count', 'favorite_count', 'created_at', 'updated_at', 'last_reply_at')


@admin.register(ForumTag)
class ForumTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'post_count', 'color', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('-post_count', 'name')
    list_per_page = 20
    verbose_name = '论坛标签'
    verbose_name_plural = '论坛标签'
    
    fieldsets = (
        ('标签信息', {
            'fields': ('name', 'description', 'color')
        }),
        ('统计信息', {
            'fields': ('post_count',),
            'classes': ('collapse',)
        }),
        ('时间戳', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('post_count', 'created_at')


@admin.register(ForumAnnouncement)
class ForumAnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'is_pinned', 'order', 'publish_date', 'created_at')
    list_filter = ('is_active', 'is_pinned', 'publish_date')
    search_fields = ('title', 'content')
    ordering = ('order', '-publish_date')
    list_per_page = 20
    list_editable = ('is_active', 'is_pinned', 'order')
    verbose_name = '论坛公告'
    verbose_name_plural = '论坛公告'
    
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'content', 'link')
        }),
        ('状态设置', {
            'fields': ('is_active', 'is_pinned', 'order')
        }),
        ('发布设置', {
            'fields': ('publish_date',)
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ForumRule)
class ForumRuleAdmin(admin.ModelAdmin):
    list_display = ('content', 'is_active', 'order', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('content',)
    ordering = ('order', 'id')
    list_per_page = 20
    list_editable = ('is_active', 'order')
    verbose_name = '论坛版规'
    verbose_name_plural = '论坛版规'
    
    fieldsets = (
        ('规则内容', {
            'fields': ('content',)
        }),
        ('状态设置', {
            'fields': ('is_active', 'order')
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ForumReport)
class ForumReportAdmin(admin.ModelAdmin):
    list_display = ('reporter', 'get_target', 'reason', 'status', 'handler', 'created_at')
    list_filter = ('reason', 'status', 'created_at')
    search_fields = ('reporter__username', 'description', 'handler_note')
    ordering = ('-created_at',)
    list_per_page = 20
    list_editable = ('status', 'handler')
    verbose_name = '举报管理'
    verbose_name_plural = '举报管理'
    
    def get_target(self, obj):
        if obj.post:
            return f"帖子: {obj.post.title[:20]}"
        elif obj.comment:
            return f"评论: {obj.comment.content[:20]}"
        return "未知"
    get_target.short_description = '举报目标'
    
    fieldsets = (
        ('举报信息', {
            'fields': ('reporter', 'post', 'comment', 'reason', 'description')
        }),
        ('处理信息', {
            'fields': ('status', 'handler', 'handler_note')
        }),
        ('时间戳', {
            'fields': ('created_at', 'handled_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('created_at', 'handled_at')


# ============================================
# 第五部分：创作管理
# ============================================

@admin.register(UserCreation)
class UserCreationAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'type', 'status', 'is_featured', 'view_count', 'like_count', 'created_at')
    list_filter = ('type', 'status', 'is_public', 'is_featured', 'created_at')
    search_fields = ('title', 'description', 'author__username')
    ordering = ('-created_at',)
    list_per_page = 20
    list_editable = ('status', 'is_featured')
    inlines = [CreationCommentInline, CreationLikeInline, CreationFavoriteInline]
    verbose_name = '用户创作'
    verbose_name_plural = '用户创作'
    
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'description', 'type', 'author', 'heritage')
        }),
        ('媒体文件', {
            'fields': ('media_file', 'thumbnail')
        }),
        ('状态设置', {
            'fields': ('status', 'is_public', 'is_featured')
        }),
        ('统计信息', {
            'fields': ('view_count', 'like_count', 'comment_count', 'share_count'),
            'classes': ('collapse',)
        }),
        ('标签', {
            'fields': ('tags',)
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('view_count', 'like_count', 'comment_count', 'share_count', 'created_at', 'updated_at', 'published_at')


# ============================================
# 第六部分：隐藏的中间表（仅通过URL访问）
# ============================================

@admin.register(ForumCommentLike)
class ForumCommentLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'comment', 'created_at')
    search_fields = ('user__username', 'comment__content')
    ordering = ('-created_at',)
    verbose_name = '评论点赞'
    verbose_name_plural = '评论点赞'
    
    readonly_fields = ('created_at',)


@admin.register(ForumUserFollow)
class ForumUserFollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'following', 'created_at')
    search_fields = ('follower__username', 'following__username')
    ordering = ('-created_at',)
    verbose_name = '用户关注'
    verbose_name_plural = '用户关注'
    
    readonly_fields = ('created_at',)


@admin.register(CreationViewHistory)
class CreationViewHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'creation', 'viewed_at', 'duration')
    search_fields = ('user__username', 'creation__title')
    ordering = ('-viewed_at',)
    verbose_name = '创作浏览历史'
    verbose_name_plural = '创作浏览历史'
    
    readonly_fields = ('user', 'creation', 'viewed_at', 'duration')
    
    def has_add_permission(self, request):
        return False
