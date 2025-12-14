from rest_framework import serializers
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from .forum_models import (
    ForumPost, ForumComment, ForumTag, ForumPostLike, ForumCommentLike,
    ForumPostFavorite, ForumUserFollow, ForumReport, ForumAnnouncement,
    ForumUserStats
)
from .user_models import UserProfile


class UserBasicSerializer(serializers.ModelSerializer):
    """用户基本信息序列化器"""
    avatar = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    is_followed = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'avatar', 'level', 'is_followed']
    
    def get_avatar(self, obj):
        if hasattr(obj, 'profile') and obj.profile.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile.avatar.url)
        return None
    
    def get_level(self, obj):
        if hasattr(obj, 'forum_stats'):
            return obj.forum_stats.level
        return 1
    
    def get_is_followed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            from .forum_models import ForumUserFollow
            return ForumUserFollow.objects.filter(
                follower=request.user,
                following=obj
            ).exists()
        return False


class ForumTagSerializer(serializers.ModelSerializer):
    """论坛标签序列化器"""
    
    class Meta:
        model = ForumTag
        fields = ['id', 'name', 'description', 'color', 'post_count']
        read_only_fields = ['post_count']


class ForumCommentSerializer(serializers.ModelSerializer):
    """论坛评论序列化器"""
    author = UserBasicSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    
    class Meta:
        model = ForumComment
        fields = [
            'id', 'content', 'author', 'parent', 'like_count',
            'is_deleted', 'created_at', 'updated_at', 'replies',
            'is_liked', 'level'
        ]
        read_only_fields = ['author', 'like_count', 'created_at', 'updated_at']
    
    def get_replies(self, obj):
        if obj.replies.exists():
            return ForumCommentSerializer(
                obj.replies.filter(is_deleted=False),
                many=True,
                context=self.context
            ).data
        return []
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False
    
    def get_level(self, obj):
        return obj.get_level()
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['author'] = request.user
        
        with transaction.atomic():
            comment = super().create(validated_data)
            
            # 更新帖子的评论数和最后回复时间
            post = comment.post
            post.comment_count = post.comments.filter(is_deleted=False).count()
            post.last_reply_at = timezone.now()
            post.save(update_fields=['comment_count', 'last_reply_at'])
            
            # 增加用户经验值
            stats, created = ForumUserStats.objects.get_or_create(user=request.user)
            stats.comment_count += 1
            stats.add_experience(2)  # 评论获得2经验值
            
        return comment


class ForumPostListSerializer(serializers.ModelSerializer):
    """论坛帖子列表序列化器"""
    author = UserBasicSerializer(read_only=True)
    tags = ForumTagSerializer(many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    last_reply_info = serializers.SerializerMethodField()
    hot_score = serializers.SerializerMethodField()
    
    class Meta:
        model = ForumPost
        fields = [
            'id', 'title', 'author', 'status', 'is_pinned', 'is_featured',
            'view_count', 'like_count', 'comment_count', 'favorite_count',
            'created_at', 'updated_at', 'last_reply_at', 'tags',
            'is_liked', 'is_favorited', 'last_reply_info', 'hot_score'
        ]
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False
    
    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.favorites.filter(user=request.user).exists()
        return False
    
    def get_last_reply_info(self, obj):
        last_comment = obj.comments.filter(is_deleted=False).order_by('-created_at').first()
        if last_comment:
            return {
                'user': last_comment.author.username,
                'time': last_comment.created_at
            }
        return None
    
    def get_hot_score(self, obj):
        return obj.get_hot_score()


class ForumPostDetailSerializer(serializers.ModelSerializer):
    """论坛帖子详情序列化器"""
    author = UserBasicSerializer(read_only=True)
    tags = ForumTagSerializer(many=True, read_only=True)
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=50),
        write_only=True,
        required=False
    )
    is_liked = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    can_manage = serializers.SerializerMethodField()
    
    class Meta:
        model = ForumPost
        fields = [
            'id', 'title', 'content', 'author', 'status', 'is_pinned',
            'is_featured', 'is_locked', 'view_count', 'like_count',
            'comment_count', 'favorite_count', 'created_at', 'updated_at',
            'last_reply_at', 'tags', 'tag_names', 'is_liked', 'is_favorited',
            'comments', 'can_edit', 'can_delete', 'can_manage'
        ]
        read_only_fields = [
            'author', 'view_count', 'like_count', 'comment_count',
            'favorite_count', 'created_at', 'updated_at', 'last_reply_at'
        ]
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False
    
    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.favorites.filter(user=request.user).exists()
        return False
    
    def get_comments(self, obj):
        # 只返回顶级评论，回复通过嵌套获取
        top_level_comments = obj.comments.filter(
            parent=None, is_deleted=False
        ).order_by('created_at')
        return ForumCommentSerializer(
            top_level_comments,
            many=True,
            context=self.context
        ).data
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.author == request.user or request.user.is_staff
        return False
    
    def get_can_delete(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.author == request.user or request.user.is_staff
        return False
    
    def get_can_manage(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.is_staff
        return False
    
    def create(self, validated_data):
        request = self.context.get('request')
        tag_names = validated_data.pop('tag_names', [])
        validated_data['author'] = request.user
        
        with transaction.atomic():
            post = super().create(validated_data)
            
            # 处理标签
            if tag_names:
                tags = []
                for tag_name in tag_names:
                    tag, created = ForumTag.objects.get_or_create(
                        name=tag_name.strip()
                    )
                    if created:
                        tag.post_count = 1
                    else:
                        tag.post_count += 1
                    tag.save()
                    tags.append(tag)
                post.tags.set(tags)
            
            # 增加用户经验值
            stats, created = ForumUserStats.objects.get_or_create(user=request.user)
            stats.post_count += 1
            stats.add_experience(5)  # 发帖获得5经验值
            
        return post
    
    def update(self, instance, validated_data):
        tag_names = validated_data.pop('tag_names', None)
        
        with transaction.atomic():
            post = super().update(instance, validated_data)
            
            # 更新标签
            if tag_names is not None:
                # 减少旧标签的计数
                for old_tag in post.tags.all():
                    old_tag.post_count = max(0, old_tag.post_count - 1)
                    old_tag.save()
                
                # 设置新标签
                tags = []
                for tag_name in tag_names:
                    tag, created = ForumTag.objects.get_or_create(
                        name=tag_name.strip()
                    )
                    if created:
                        tag.post_count = 1
                    else:
                        tag.post_count += 1
                    tag.save()
                    tags.append(tag)
                post.tags.set(tags)
            
        return post


class ForumPostCreateSerializer(serializers.ModelSerializer):
    """论坛帖子创建序列化器"""
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = ForumPost
        fields = ['title', 'content', 'tag_names']
    
    def create(self, validated_data):
        request = self.context.get('request')
        tag_names = validated_data.pop('tag_names', [])
        validated_data['author'] = request.user
        
        with transaction.atomic():
            post = ForumPost.objects.create(**validated_data)
            
            # 处理标签
            if tag_names:
                tags = []
                for tag_name in tag_names:
                    tag_name = tag_name.strip()
                    if tag_name:
                        tag, created = ForumTag.objects.get_or_create(
                            name=tag_name
                        )
                        if created:
                            tag.post_count = 1
                        else:
                            tag.post_count += 1
                        tag.save()
                        tags.append(tag)
                post.tags.set(tags)
            
            # 增加用户统计
            stats, created = ForumUserStats.objects.get_or_create(user=request.user)
            stats.post_count += 1
            stats.add_experience(5)
            
        return post


class ForumAnnouncementSerializer(serializers.ModelSerializer):
    """论坛公告序列化器"""
    author = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = ForumAnnouncement
        fields = [
            'id', 'title', 'content', 'author', 'is_active',
            'is_pinned', 'created_at', 'updated_at'
        ]
        read_only_fields = ['author', 'created_at', 'updated_at']


class ForumReportSerializer(serializers.ModelSerializer):
    """举报序列化器"""
    reporter = UserBasicSerializer(read_only=True)
    post_title = serializers.CharField(source='post.title', read_only=True)
    
    class Meta:
        model = ForumReport
        fields = [
            'id', 'reporter', 'post', 'comment', 'reason', 'description',
            'status', 'created_at', 'post_title'
        ]
        read_only_fields = ['reporter', 'status', 'created_at']
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['reporter'] = request.user
        return super().create(validated_data)


class ForumUserStatsSerializer(serializers.ModelSerializer):
    """用户论坛统计序列化器"""
    username = serializers.CharField(source='user.username', read_only=True)
    avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = ForumUserStats
        fields = [
            'username', 'avatar', 'post_count', 'comment_count',
            'like_received', 'follower_count', 'following_count',
            'level', 'experience', 'last_active_at'
        ]
    
    def get_avatar(self, obj):
        if hasattr(obj.user, 'profile') and obj.user.profile.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.user.profile.avatar.url)
        return None


class ForumLikeSerializer(serializers.Serializer):
    """点赞操作序列化器"""
    is_liked = serializers.BooleanField(read_only=True)
    like_count = serializers.IntegerField(read_only=True)


class ForumFavoriteSerializer(serializers.Serializer):
    """收藏操作序列化器"""
    is_favorited = serializers.BooleanField(read_only=True)
    favorite_count = serializers.IntegerField(read_only=True)


class ForumFollowSerializer(serializers.Serializer):
    """关注操作序列化器"""
    is_followed = serializers.BooleanField(read_only=True)
    follower_count = serializers.IntegerField(read_only=True)


class ForumSearchSerializer(serializers.Serializer):
    """搜索参数序列化器"""
    q = serializers.CharField(required=False, allow_blank=True)
    tag = serializers.CharField(required=False, allow_blank=True)
    author = serializers.CharField(required=False, allow_blank=True)
    sort = serializers.ChoiceField(
        choices=['latest', 'hot', 'replies', 'featured'],
        default='latest'
    )
    page = serializers.IntegerField(default=1, min_value=1)
    page_size = serializers.IntegerField(default=20, min_value=1, max_value=100)