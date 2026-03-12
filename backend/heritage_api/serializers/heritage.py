from rest_framework import serializers
from ..models import Heritage, UserFavorite, UserHistory, News, Policy
from ..creation_models import (
    UserCreation, CreationLike, CreationComment,
    CreationViewHistory, CreationFavorite
)
from django.contrib.auth.models import User
from ..utils import format_datetime

class HeritageSerializer(serializers.ModelSerializer):
    """非遗项目序列化器"""
    # 为列表视图添加主图片 URL 字段
    main_image_url = serializers.SerializerMethodField()
    gallery_image_urls = serializers.JSONField()
    # level, category, and region are CharFields in the model and will be serialized by default
    # when included in Meta.fields. Explicit StringRelatedField is not necessary for them.
    # 添加别名字段，保持与前端代码一致
    lat = serializers.FloatField(source='latitude')
    lng = serializers.FloatField(source='longitude')

    class Meta:
        model = Heritage
        # 更新字段列表以匹配 models.py 中的 Heritage 模型
        fields = [
            'id', 'name', 'pinyin_name', 'level', 'category', 'region', 'batch',
            'description', 'history', 'features', 'value', 'status',
            'protection_measures', 'inheritors', 'related_works',
            'lat', 'lng',  # 添加别名
            'latitude', 'longitude',  # 保留原字段
            'main_image_url',  # 添加主图片 URL
            'gallery_image_urls'  # 添加图库图片URL列表
        ]

    def get_main_image_url(self, obj):
        """获取主图片的完整 URL，如果不存在则返回默认图片 URL"""
        if obj.main_image_url:
            return obj.main_image_url
        # 如果没有主图，返回默认图片路径
        # 确保 settings.py 中配置了 STATIC_URL
        from django.conf import settings
        return f'{settings.STATIC_URL}common/default-heritage.jpg'


class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    is_followed = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'avatar', 'display_name', 'is_followed']
    
    def get_avatar(self, obj):
        """获取用户头像URL"""
        if hasattr(obj, 'profile') and obj.profile.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile.avatar.url)
            return obj.profile.avatar.url
        return None
    
    def get_display_name(self, obj):
        """获取用户显示名"""
        if hasattr(obj, 'profile') and obj.profile.display_name:
            return obj.profile.display_name
        return obj.username
    
    def get_is_followed(self, obj):
        """检查当前用户是否关注了该用户"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # 使用ForumUserFollow模型检查关注状态
            from ..forum_models import ForumUserFollow
            return ForumUserFollow.objects.filter(
                follower=request.user,
                following=obj
            ).exists()
        return False

class UserFavoriteSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    heritage = HeritageSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    heritage_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = UserFavorite
        fields = ['id', 'user', 'heritage', 'user_id', 'heritage_id', 'created_at']
        read_only_fields = ['user', 'heritage', 'created_at']

    def create(self, validated_data):
        user_id = validated_data.pop('user_id')
        heritage_id = validated_data.pop('heritage_id')
        user = User.objects.get(id=user_id)
        heritage = Heritage.objects.get(id=heritage_id)
        favorite = UserFavorite.objects.create(user=user, heritage=heritage, **validated_data)
        return favorite


class NewsSerializer(serializers.ModelSerializer):
    """非遗资讯序列化器"""
    # 格式化发布时间
    publish_date_formatted = serializers.SerializerMethodField()
    # 标签列表
    tag_list = serializers.SerializerMethodField()
    # 实时浏览量（Redis + 数据库）
    view_count = serializers.SerializerMethodField()
    
    class Meta:
        model = News
        fields = [
            'id', 'title', 'summary', 'content', 'author', 'source', 'source_url',
            'image_url', 'publish_date', 'publish_date_formatted', 'created_at', 
            'updated_at', 'is_active', 'is_featured', 'view_count', 'tags', 'tag_list'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_view_count(self, obj):
        """获取实时浏览量（数据库值 + Redis增量）"""
        try:
            from ..redis_utils import redis_client
            redis_increment = redis_client.get_view_count('news', obj.id)
            if redis_increment is not None:
                return (obj.view_count or 0) + redis_increment
        except Exception:
            pass
        return obj.view_count or 0
    
    def get_publish_date_formatted(self, obj):
        """返回格式化的发布时间"""
        return obj.publish_date.strftime('%Y-%m-%d %H:%M')
    
    def get_tag_list(self, obj):
        """返回标签列表"""
        if obj.tags:
            return [tag.strip() for tag in obj.tags.split(',') if tag.strip()]
        return []


# 创作相关序列化器
class UserCreationSerializer(serializers.ModelSerializer):
    """用户创作序列化器"""
    user = UserSerializer(source='author', read_only=True)
    tags = serializers.JSONField()
    
    # 统计字段
    like_count = serializers.IntegerField(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    view_count = serializers.IntegerField(read_only=True)
    favorite_count = serializers.IntegerField(read_only=True)
    share_count = serializers.IntegerField(read_only=True)
    
    # 格式化时间
    created_at_formatted = serializers.SerializerMethodField()
    updated_at_formatted = serializers.SerializerMethodField()
    published_at_formatted = serializers.SerializerMethodField()
    
    # 媒体文件URL
    image_url = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()
    audio_url = serializers.SerializerMethodField()
    
    class Meta:
        model = UserCreation
        fields = [
            'id', 'user', 'title', 'description', 'type', 'status',
            'media_file', 'thumbnail', 'image_url', 'video_url', 'audio_url',
            'tags', 'like_count', 'comment_count', 'view_count',
            'favorite_count', 'share_count', 'is_featured', 'is_public',
            'created_at', 'created_at_formatted', 'updated_at', 'updated_at_formatted',
            'published_at', 'published_at_formatted'
        ]
        read_only_fields = [
            'user', 'like_count', 'comment_count', 'view_count', 'favorite_count',
            'share_count', 'created_at', 'updated_at', 'published_at'
        ]
    
    def get_created_at_formatted(self, obj):
        """返回格式化的创建时间"""
        return format_datetime(obj.created_at)
    
    def get_updated_at_formatted(self, obj):
        """返回格式化的更新时间"""
        return format_datetime(obj.updated_at)
    
    def get_published_at_formatted(self, obj):
        """返回格式化的发布时间"""
        return format_datetime(obj.published_at)
    
    def get_image_url(self, obj):
        """返回图片的完整URL"""
        # 对于照片类型，使用media_file；对于其他类型，使用thumbnail
        if obj.type == 'photo' and obj.media_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.media_file.url)
            return obj.media_file.url
        elif obj.thumbnail:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        return None
    
    def get_video_url(self, obj):
        """返回视频的完整URL"""
        if obj.media_file and obj.type == 'video':
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.media_file.url)
            return obj.media_file.url
        return None
    
    def get_audio_url(self, obj):
        """返回音频的完整URL"""
        if obj.media_file and obj.type == 'music':
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.media_file.url)
            return obj.media_file.url
        return None
    
    def create(self, validated_data):
        """创建创作，处理文件重命名"""
        # 处理从视图传递的额外参数（如user）
        # 这些参数不会在validated_data中，但可以通过self.context获取
        request = self.context.get('request')
        if request and request.user:
            validated_data['author'] = request.user
        
        # 自动发布创作，无需审核
        validated_data['status'] = 'published'
        
        # 处理文件重命名
        if 'media_file' in validated_data and validated_data['media_file']:
            media_file = validated_data['media_file']
            
            # 验证文件大小（50MB限制）
            if hasattr(media_file, 'size') and media_file.size > 50 * 1024 * 1024:
                raise serializers.ValidationError('文件大小不能超过50MB')
            
            # 验证文件类型
            allowed_extensions = {
                'video': ['mp4', 'avi', 'mov'],
                'photo': ['jpg', 'jpeg', 'png', 'gif'],
                'music': ['mp3', 'wav']
            }
            
            # 根据创作类型确定允许的文件扩展名
            creation_type = validated_data.get('type', 'article')
            if creation_type in allowed_extensions:
                file_extension = media_file.name.split('.')[-1].lower()
                if file_extension not in allowed_extensions[creation_type]:
                    raise serializers.ValidationError(
                        f'不支持的文件格式。{creation_type}类型支持: {", ".join(allowed_extensions[creation_type])}'
                    )
            
            # 生成唯一文件名：用户ID_时间戳_随机数.扩展名
            import uuid
            from django.utils import timezone
            
            user_id = request.user.id if request and request.user else 0
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            random_str = str(uuid.uuid4())[:8]
            file_extension = media_file.name.split('.')[-1].lower()
            
            new_filename = f"{user_id}_{timestamp}_{random_str}.{file_extension}"
            media_file.name = new_filename
        
        creation = UserCreation.objects.create(**validated_data)
        
        return creation
    
    def update(self, instance, validated_data):
        """更新创作"""
        # 更新基本字段
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance


class CreationLikeSerializer(serializers.ModelSerializer):
    """创作点赞序列化器"""
    user = UserSerializer(read_only=True)
    creation = UserCreationSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    creation_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = CreationLike
        fields = ['id', 'user', 'creation', 'user_id', 'creation_id', 'created_at']
        read_only_fields = ['user', 'creation', 'created_at']
    
    def create(self, validated_data):
        user_id = validated_data.pop('user_id')
        creation_id = validated_data.pop('creation_id')
        user = User.objects.get(id=user_id)
        creation = UserCreation.objects.get(id=creation_id)
        like = CreationLike.objects.create(user=user, creation=creation, **validated_data)
        return like


class CreationCommentSerializer(serializers.ModelSerializer):
    """创作评论序列化器"""
    user = UserSerializer(read_only=True)
    creation = UserCreationSerializer(read_only=True)
    
    # 回复相关字段
    parent_comment = serializers.PrimaryKeyRelatedField(queryset=CreationComment.objects.all(), required=False)
    reply_to_user = UserSerializer(read_only=True)
    
    # 格式化时间
    created_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = CreationComment
        fields = [
            'id', 'user', 'creation', 'content',
            'parent_comment', 'reply_to_user', 'like_count', 'created_at',
            'created_at_formatted', 'is_active'
        ]
        read_only_fields = ['user', 'creation', 'like_count', 'created_at', 'is_active']
    
    def get_created_at_formatted(self, obj):
        """返回格式化的评论时间"""
        return format_datetime(obj.created_at)
    
    def create(self, validated_data):
        # 视图已经通过serializer.save(user=self.request.user, creation=creation)传入了user和creation
        comment = CreationComment.objects.create(**validated_data)
        return comment


class CreationViewHistorySerializer(serializers.ModelSerializer):
    """创作浏览历史序列化器"""
    user = UserSerializer(read_only=True)
    creation = UserCreationSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    creation_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = CreationViewHistory
        fields = ['id', 'user', 'creation', 'user_id', 'creation_id', 'viewed_at']
        read_only_fields = ['user', 'creation', 'viewed_at']
    
    def create(self, validated_data):
        # 从视图中获取用户和创作实例，而不是从validated_data中
        # 因为视图已经通过serializer.save(user=self.request.user)传入了user
        creation_id = validated_data.pop('creation_id', None)
        validated_data.pop('user_id', None)  # 移除user_id，因为user来自视图
        
        if creation_id:
            creation = UserCreation.objects.get(id=creation_id)
            validated_data['creation'] = creation
        
        # user已经在validated_data中（来自视图），不需要额外处理
        view_history = CreationViewHistory.objects.create(**validated_data)
        return view_history


class CreationFavoriteSerializer(serializers.ModelSerializer):
    """创作收藏序列化器"""
    user = UserSerializer(read_only=True)
    creation = UserCreationSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    creation_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = CreationFavorite
        fields = ['id', 'user', 'creation', 'user_id', 'creation_id', 'created_at']
        read_only_fields = ['user', 'creation', 'created_at']
    
    def create(self, validated_data):
        # 从视图中获取用户和创作实例，而不是从validated_data中
        # 因为视图已经通过serializer.save(user=self.request.user)传入了user
        creation_id = validated_data.pop('creation_id', None)
        validated_data.pop('user_id', None)  # 移除user_id，因为user来自视图
        
        if creation_id:
            creation = UserCreation.objects.get(id=creation_id)
            validated_data['creation'] = creation
        
        # user已经在validated_data中（来自视图），不需要额外处理
        favorite = CreationFavorite.objects.create(**validated_data)
        return favorite


class UserHistorySerializer(serializers.ModelSerializer):
    """用户浏览历史序列化器"""
    user = UserSerializer(read_only=True)
    heritage = HeritageSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    heritage_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = UserHistory
        fields = ['id', 'user', 'heritage', 'user_id', 'heritage_id', 'visit_time']
        read_only_fields = ['user', 'heritage', 'visit_time']
    
    def create(self, validated_data):
        # 从视图中获取用户和非遗实例，而不是从validated_data中
        # 因为视图已经通过serializer.save(user=self.request.user)传入了user
        heritage_id = validated_data.pop('heritage_id', None)
        validated_data.pop('user_id', None)  # 移除user_id，因为user来自视图
        
        if heritage_id:
            heritage = Heritage.objects.get(id=heritage_id)
            validated_data['heritage'] = heritage
        
        # user已经在validated_data中（来自视图），不需要额外处理
        history = UserHistory.objects.create(**validated_data)
        return history


class PolicySerializer(serializers.ModelSerializer):
    """相关政策序列化器"""
    # 格式化发布时间
    publish_date_formatted = serializers.SerializerMethodField()
    # 格式化生效日期
    effective_date_formatted = serializers.SerializerMethodField()
    # 政策类型显示名称
    policy_type_display = serializers.CharField(source='get_policy_type_display', read_only=True)
    # 标签列表
    tag_list = serializers.SerializerMethodField()
    # 实时浏览量（Redis + 数据库）
    view_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Policy
        fields = [
            'id', 'title', 'summary', 'content', 'policy_number', 'issuing_authority',
            'policy_type', 'policy_type_display', 'effective_date', 'effective_date_formatted',
            'publish_date', 'publish_date_formatted', 'source_url', 'attachment_url',
            'created_at', 'updated_at', 'is_active', 'view_count', 'tags', 'tag_list'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_view_count(self, obj):
        """获取实时浏览量（数据库值 + Redis增量）"""
        try:
            from ..redis_utils import redis_client
            redis_increment = redis_client.get_view_count('policy', obj.id)
            if redis_increment is not None:
                return (obj.view_count or 0) + redis_increment
        except Exception:
            pass
        return obj.view_count or 0
    
    def get_publish_date_formatted(self, obj):
        """返回格式化的发布时间"""
        return format_datetime(obj.publish_date)
    
    def get_effective_date_formatted(self, obj):
        """返回格式化的生效日期"""
        return format_datetime(obj.effective_date, '%Y-%m-%d')
    
    def get_tag_list(self, obj):
        """返回标签列表"""
        if obj.tags:
            return [tag.strip() for tag in obj.tags.split(',') if tag.strip()]
        return []