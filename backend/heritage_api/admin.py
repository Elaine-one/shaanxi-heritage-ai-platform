from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Heritage, HeritageImage, UserFavorite, UserHistory, News, Policy
from .user_models import UserProfile
from .creation_models import (
    UserCreation, CreationLike, CreationComment, CreationTag, 
    CreationReport, CreationViewHistory, CreationFavorite, CreationShare
)
from .forum_models import (
    ForumPost, ForumComment, ForumTag, ForumPostLike, ForumCommentLike,
    ForumPostFavorite, ForumUserFollow, ForumReport, ForumAnnouncement,
    ForumUserStats
)

# 内联显示UserProfile
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = '用户资料'
    verbose_name_plural = '用户资料'
    fields = ('avatar', 'display_name', 'bio')

# 扩展User管理界面
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    fieldsets = (
        ('基本信息', {'fields': ('username', 'password')}),
        ('个人信息', {'fields': ('first_name', 'last_name', 'email')}),
        ('权限', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('重要日期', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        ('创建用户', {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
    )

# 重新注册User模型
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# 注册其他模型
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

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_name', 'bio')
    search_fields = ('user__username', 'display_name')
    list_filter = ('user__date_joined',)
    list_per_page = 20
    verbose_name = '用户资料'
    verbose_name_plural = '用户资料'

@admin.register(UserFavorite)
class UserFavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'heritage', 'created_at')
    list_filter = ('created_at', 'heritage__category')
    search_fields = ('user__username', 'heritage__name')
    ordering = ('-created_at',)
    list_per_page = 20
    verbose_name = '用户收藏'
    verbose_name_plural = '用户收藏'

@admin.register(UserHistory)
class UserHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'heritage', 'visit_time')
    list_filter = ('visit_time', 'heritage__category')
    search_fields = ('user__username', 'heritage__name')
    ordering = ('-visit_time',)
    list_per_page = 20
    verbose_name = '浏览历史'
    verbose_name_plural = '浏览历史'

# 注册HeritageImage模型
@admin.register(HeritageImage)
class HeritageImageAdmin(admin.ModelAdmin):
    list_display = ('heritage', 'image', 'is_main')
    list_filter = ('is_main', 'heritage__category')
    search_fields = ('heritage__name',)
    ordering = ('heritage', '-is_main')
    list_per_page = 20
    verbose_name = '非遗图片'
    verbose_name_plural = '非遗图片'


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'source', 'publish_date', 'view_count', 'is_active')
    list_filter = ('is_active', 'publish_date', 'source')
    search_fields = ('title', 'summary', 'content', 'author', 'tags')
    ordering = ('-publish_date',)
    # date_hierarchy = 'publish_date'  # 暂时注释掉以避免时区问题
    list_per_page = 20
    list_editable = ('is_active',)
    
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'summary', 'author', 'source', 'source_url')
        }),
        ('内容', {
            'fields': ('content', 'image_url')
        }),
        ('发布设置', {
            'fields': ('publish_date', 'is_active')
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


# 论坛相关模型管理
@admin.register(ForumPost)
class ForumPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'is_pinned', 'is_featured', 'view_count', 'like_count', 'comment_count', 'created_at')
    list_filter = ('status', 'is_pinned', 'is_featured', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    ordering = ('-is_pinned', '-created_at')
    list_per_page = 20
    list_editable = ('status', 'is_pinned', 'is_featured')
    
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


@admin.register(ForumComment)
class ForumCommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'author', 'content_preview', 'parent', 'like_count', 'is_deleted', 'created_at')
    list_filter = ('is_deleted', 'created_at')
    search_fields = ('content', 'author__username', 'post__title')
    ordering = ('-created_at',)
    list_per_page = 20
    list_editable = ('is_deleted',)
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = '评论内容'
    
    fieldsets = (
        ('评论信息', {
            'fields': ('post', 'author', 'parent', 'content')
        }),
        ('状态设置', {
            'fields': ('is_deleted',)
        }),
        ('统计信息', {
            'fields': ('like_count',),
            'classes': ('collapse',)
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('like_count', 'created_at', 'updated_at')


@admin.register(ForumTag)
class ForumTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'post_count', 'color', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('-post_count', 'name')
    list_per_page = 20
    
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


@admin.register(ForumPostLike)
class ForumPostLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'post__title')
    ordering = ('-created_at',)
    list_per_page = 20
    verbose_name = '帖子点赞'
    verbose_name_plural = '帖子点赞'
    
    readonly_fields = ('created_at',)


@admin.register(ForumCommentLike)
class ForumCommentLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'comment', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'comment__content')
    ordering = ('-created_at',)
    list_per_page = 20
    verbose_name = '评论点赞'
    verbose_name_plural = '评论点赞'
    
    readonly_fields = ('created_at',)


@admin.register(ForumPostFavorite)
class ForumPostFavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'post__title')
    ordering = ('-created_at',)
    list_per_page = 20
    verbose_name = '帖子收藏'
    verbose_name_plural = '帖子收藏'
    
    readonly_fields = ('created_at',)


@admin.register(ForumUserFollow)
class ForumUserFollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'following', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('follower__username', 'following__username')
    ordering = ('-created_at',)
    list_per_page = 20
    verbose_name = '用户关注'
    verbose_name_plural = '用户关注'
    
    readonly_fields = ('created_at',)


@admin.register(ForumReport)
class ForumReportAdmin(admin.ModelAdmin):
    list_display = ('reporter', 'reason', 'get_target', 'status', 'handler', 'created_at', 'handled_at')
    list_filter = ('reason', 'status', 'created_at')
    search_fields = ('reporter__username', 'description', 'handler_note')
    ordering = ('-created_at',)
    list_per_page = 20
    list_editable = ('status', 'handler')
    
    def get_target(self, obj):
        if obj.post:
            return f"帖子: {obj.post.title}"
        elif obj.comment:
            return f"评论: {obj.comment.content[:30]}..."
        return "未知目标"
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


@admin.register(ForumAnnouncement)
class ForumAnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'is_active', 'is_pinned', 'created_at', 'updated_at')
    list_filter = ('is_active', 'is_pinned', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    ordering = ('-is_pinned', '-created_at')
    list_per_page = 20
    list_editable = ('is_active', 'is_pinned')
    
    fieldsets = (
        ('公告信息', {
            'fields': ('title', 'content', 'author')
        }),
        ('状态设置', {
            'fields': ('is_active', 'is_pinned')
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ForumUserStats)
class ForumUserStatsAdmin(admin.ModelAdmin):
    list_display = ('user', 'level', 'experience', 'post_count', 'comment_count', 'like_received', 'follower_count', 'following_count', 'last_active_at')
    list_filter = ('level', 'last_active_at')
    search_fields = ('user__username',)
    ordering = ('-level', '-experience')
    list_per_page = 20
    verbose_name = '用户论坛统计'
    verbose_name_plural = '用户论坛统计'
    
    fieldsets = (
        ('用户信息', {
            'fields': ('user',)
        }),
        ('统计数据', {
            'fields': ('post_count', 'comment_count', 'like_received', 'follower_count', 'following_count')
        }),
        ('等级和经验', {
            'fields': ('level', 'experience')
        }),
        ('时间戳', {
            'fields': ('last_active_at',)
        })
    )
    
    readonly_fields = ('last_active_at',)

# 创作相关模型管理
@admin.register(UserCreation)
class UserCreationAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'type', 'status', 'is_featured', 'view_count', 'like_count', 'created_at')
    list_filter = ('type', 'status', 'is_public', 'is_featured', 'created_at')
    search_fields = ('title', 'description', 'author__username')
    ordering = ('-created_at',)
    list_per_page = 20
    list_editable = ('status', 'is_featured')
    
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

@admin.register(CreationLike)
class CreationLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'creation', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'creation__title')
    ordering = ('-created_at',)
    list_per_page = 20
    verbose_name = '创作点赞'
    verbose_name_plural = '创作点赞'

@admin.register(CreationComment)
class CreationCommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'creation', 'content_preview', 'like_count', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__username', 'creation__title', 'content')
    ordering = ('-created_at',)
    list_per_page = 20
    list_editable = ('is_active',)
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = '评论内容'

@admin.register(CreationTag)
class CreationTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'usage_count', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('-usage_count', 'name')
    list_per_page = 20
    list_editable = ('is_active',)
    verbose_name = '创作标签'
    verbose_name_plural = '创作标签'

@admin.register(CreationReport)
class CreationReportAdmin(admin.ModelAdmin):
    list_display = ('reporter', 'creation', 'report_type', 'status', 'created_at')
    list_filter = ('report_type', 'status', 'created_at')
    search_fields = ('reporter__username', 'creation__title', 'description')
    ordering = ('-created_at',)
    list_per_page = 20
    list_editable = ('status',)
    
    fieldsets = (
        ('举报信息', {
            'fields': ('reporter', 'creation', 'report_type', 'description', 'evidence_urls')
        }),
        ('处理信息', {
            'fields': ('status', 'handled_by', 'handled_at', 'resolution')
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('created_at', 'updated_at')

@admin.register(CreationViewHistory)
class CreationViewHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'creation', 'viewed_at', 'duration')
    list_filter = ('viewed_at',)
    search_fields = ('user__username', 'creation__title')
    ordering = ('-viewed_at',)
    list_per_page = 20
    verbose_name = '创作浏览历史'
    verbose_name_plural = '创作浏览历史'

@admin.register(CreationFavorite)
class CreationFavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'creation', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'creation__title')
    ordering = ('-created_at',)
    list_per_page = 20
    verbose_name = '创作收藏'
    verbose_name_plural = '创作收藏'

@admin.register(CreationShare)
class CreationShareAdmin(admin.ModelAdmin):
    list_display = ('user', 'creation', 'platform', 'shared_at')
    list_filter = ('platform', 'shared_at')
    search_fields = ('user__username', 'creation__title')
    ordering = ('-shared_at',)
    list_per_page = 20
    verbose_name = '创作分享'
    verbose_name_plural = '创作分享'


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = ('title', 'policy_number', 'issuing_authority', 'get_policy_type_display', 'publish_date', 'view_count', 'is_active')
    list_filter = ('is_active', 'policy_type', 'publish_date', 'issuing_authority')
    search_fields = ('title', 'summary', 'content', 'policy_number', 'issuing_authority', 'tags')
    ordering = ('-publish_date',)
    date_hierarchy = 'publish_date'
    list_per_page = 20
    list_editable = ('is_active',)
    
    def get_policy_type_display(self, obj):
        """显示政策类型的可读名称"""
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
