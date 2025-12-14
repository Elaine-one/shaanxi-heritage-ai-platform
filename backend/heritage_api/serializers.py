from rest_framework import serializers
from .models import Heritage, HeritageImage, UserFavorite, UserHistory, News, Policy
from .creation_models import (
    UserCreation, CreationLike, CreationComment, CreationTag,
    CreationReport, CreationViewHistory, CreationFavorite, CreationShare
)
from django.contrib.auth.models import User
from .utils import format_datetime

class HeritageImageSerializer(serializers.ModelSerializer):
    """非遗项目图片序列化器，生成完整的图片URL"""
    # 使用 SerializerMethodField 来动态生成完整的 URL
    image = serializers.SerializerMethodField()

    class Meta:
        model = HeritageImage
        # 包含原始 image 字段名（现在是方法名）和其他所需字段
        fields = ['id', 'image', 'is_main']

    def get_image(self, obj):
        """返回图片的完整绝对URL"""
        if obj.image:
            request = self.context.get('request')
            if request:
                # 使用 request.build_absolute_uri 生成包含域名的完整URL
                return request.build_absolute_uri(obj.image.url)
            # 如果没有 request 上下文（例如在 shell 中），则返回相对路径
            # 注意：这在实际 API 响应中不太可能发生，但作为后备
            return obj.image.url # 返回 MEDIA_URL + 文件路径
        return None

class HeritageSerializer(serializers.ModelSerializer):
    """非遗项目序列化器"""
    # 确保在序列化 Heritage 时，其关联的 images 也使用包含 request 上下文的 HeritageImageSerializer
    images = HeritageImageSerializer(many=True, read_only=True)
    # 为列表视图添加主图片 URL 字段
    main_image_url = serializers.SerializerMethodField()
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
            'images', # 使用更新后的 HeritageImageSerializer
            'main_image_url' # 添加主图片 URL
        ]

    def get_main_image_url(self, obj):
        """获取主图片的完整 URL，如果不存在则返回默认图片 URL"""
        main_image = obj.images.filter(is_main=True).first()
        if main_image and main_image.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(main_image.image.url)
            return main_image.image.url # Fallback
        # 如果没有主图或主图没有有效 image 字段，返回默认图片路径
        # 确保 settings.py 中配置了 STATIC_URL
        from django.conf import settings
        return f'{settings.STATIC_URL}common/default-heritage.jpg'


class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'avatar', 'display_name']
    
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
    
    class Meta:
        model = News
        fields = [
            'id', 'title', 'summary', 'content', 'author', 'source', 'source_url',
            'image_url', 'publish_date', 'publish_date_formatted', 'created_at', 
            'updated_at', 'is_active', 'view_count', 'tags', 'tag_list'
        ]
        read_only_fields = ['created_at', 'updated_at', 'view_count']
    
    def get_publish_date_formatted(self, obj):
        """返回格式化的发布时间"""
        return obj.publish_date.strftime('%Y-%m-%d %H:%M')
    
    def get_tag_list(self, obj):
        """返回标签列表"""
        if obj.tags:
            return [tag.strip() for tag in obj.tags.split(',') if tag.strip()]
        return []


# 创作相关序列化器
class CreationTagSerializer(serializers.ModelSerializer):
    """创作标签序列化器"""
    
    class Meta:
        model = CreationTag
        fields = ['id', 'name', 'description', 'created_at']
        read_only_fields = ['created_at']


class UserCreationSerializer(serializers.ModelSerializer):
    """用户创作序列化器"""
    user = UserSerializer(source='author', read_only=True)
    tags = CreationTagSerializer(many=True, read_only=True)
    tag_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    
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
            'tags', 'tag_ids', 'like_count', 'comment_count', 'view_count',
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
        """创建创作，处理标签关联和文件重命名"""
        tag_ids = validated_data.pop('tag_ids', [])
        
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
        
        # 添加标签关联
        if tag_ids:
            tags = CreationTag.objects.filter(id__in=tag_ids)
            creation.tags.set(tags)
        
        return creation
    
    def update(self, instance, validated_data):
        """更新创作，处理标签关联"""
        tag_ids = validated_data.pop('tag_ids', None)
        
        # 更新基本字段
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # 更新标签关联
        if tag_ids is not None:
            tags = CreationTag.objects.filter(id__in=tag_ids)
            instance.tags.set(tags)
        
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


class CreationShareSerializer(serializers.ModelSerializer):
    """创作分享序列化器"""
    user = UserSerializer(read_only=True)
    creation = UserCreationSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    creation_id = serializers.IntegerField(write_only=True)
    
    # 格式化时间
    shared_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = CreationShare
        fields = [
            'id', 'user', 'creation', 'user_id', 'creation_id', 'share_platform',
            'shared_at', 'shared_at_formatted'
        ]
        read_only_fields = ['user', 'creation', 'shared_at']
    
    def get_shared_at_formatted(self, obj):
        """返回格式化的分享时间"""
        return format_datetime(obj.shared_at)
    
    def create(self, validated_data):
        # 从视图中获取用户和创作实例，而不是从validated_data中
        # 因为视图已经通过serializer.save(user=self.request.user)传入了user
        creation_id = validated_data.pop('creation_id', None)
        validated_data.pop('user_id', None)  # 移除user_id，因为user来自视图
        
        if creation_id:
            creation = UserCreation.objects.get(id=creation_id)
            validated_data['creation'] = creation
        
        # user已经在validated_data中（来自视图），不需要额外处理
        share = CreationShare.objects.create(**validated_data)
        return share


class CreationReportSerializer(serializers.ModelSerializer):
    """创作举报序列化器"""
    user = UserSerializer(read_only=True)
    creation = UserCreationSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    creation_id = serializers.IntegerField(write_only=True)
    
    # 举报类型显示名称
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    
    # 格式化时间
    reported_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = CreationReport
        fields = [
            'id', 'user', 'creation', 'user_id', 'creation_id', 'report_type',
            'report_type_display', 'reason', 'evidence', 'status', 'reported_at',
            'reported_at_formatted', 'processed_at', 'processed_by', 'feedback'
        ]
        read_only_fields = ['user', 'creation', 'reported_at', 'processed_at', 'processed_by']
    
    def get_reported_at_formatted(self, obj):
        """返回格式化的举报时间"""
        return format_datetime(obj.reported_at)
    
    def create(self, validated_data):
        # 从视图中获取用户和创作实例，而不是从validated_data中
        # 因为视图已经通过serializer.save(user=self.request.user)传入了user
        creation_id = validated_data.pop('creation_id', None)
        validated_data.pop('user_id', None)  # 移除user_id，因为user来自视图
        
        if creation_id:
            creation = UserCreation.objects.get(id=creation_id)
            validated_data['creation'] = creation
        
        # user已经在validated_data中（来自视图），不需要额外处理
        report = CreationReport.objects.create(**validated_data)
        return report


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
    
    class Meta:
        model = Policy
        fields = [
            'id', 'title', 'summary', 'content', 'policy_number', 'issuing_authority',
            'policy_type', 'policy_type_display', 'effective_date', 'effective_date_formatted',
            'publish_date', 'publish_date_formatted', 'source_url', 'attachment_url',
            'created_at', 'updated_at', 'is_active', 'view_count', 'tags', 'tag_list'
        ]
        read_only_fields = ['created_at', 'updated_at', 'view_count']
    
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