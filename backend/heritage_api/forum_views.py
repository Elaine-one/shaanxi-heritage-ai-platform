from rest_framework import generics, status, permissions, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth.models import User
from django.db.models import Q, F, Count, Case, When, IntegerField
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import uuid

from .forum_models import (
    ForumPost, ForumComment, ForumTag, ForumPostLike, ForumCommentLike,
    ForumPostFavorite, ForumUserFollow, ForumReport, ForumAnnouncement,
    ForumUserStats
)
from .forum_serializers import (
    ForumPostListSerializer, ForumPostDetailSerializer, ForumPostCreateSerializer,
    ForumCommentSerializer, ForumTagSerializer, ForumAnnouncementSerializer,
    ForumReportSerializer, ForumUserStatsSerializer, ForumLikeSerializer,
    ForumFavoriteSerializer, ForumFollowSerializer, ForumSearchSerializer
)


class ForumPagination(PageNumberPagination):
    """论坛分页器"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class ForumPostListView(generics.ListCreateAPIView):
    """论坛帖子列表视图"""
    serializer_class = ForumPostListSerializer
    pagination_class = ForumPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def post(self, request, *args, **kwargs):
        import logging
        logger = logging.getLogger('heritage_api')
        
        logger.debug(f'POST请求到达ForumPostListView')
        logger.debug(f'请求数据: {request.data}')
        logger.debug(f'用户认证状态: {request.user.is_authenticated}')
        logger.debug(f'当前用户: {request.user}')
        logger.debug(f'Content-Type: {request.content_type}')
        
        # 检查序列化器
        serializer = self.get_serializer(data=request.data)
        logger.debug(f'序列化器类: {type(serializer)}')
        logger.debug(f'序列化器验证结果: {serializer.is_valid()}')
        if not serializer.is_valid():
            logger.error(f'序列化器验证错误: {serializer.errors}')
        
        return super().post(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = ForumPost.objects.filter(
            status='published'
        ).select_related('author', 'author__profile').prefetch_related('tags')
        
        # 搜索参数
        search_query = self.request.query_params.get('q', '')
        tag_filter = self.request.query_params.get('tag', '')
        author_filter = self.request.query_params.get('author', '')
        sort_by = self.request.query_params.get('sort', 'latest')
        
        # 搜索过滤
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query)
            )
        
        if tag_filter:
            queryset = queryset.filter(tags__name=tag_filter)
        
        if author_filter:
            queryset = queryset.filter(author__username=author_filter)
        
        # 排序
        if sort_by == 'hot':
            # 按热度排序：点赞数 * 2 + 评论数 * 3 + 浏览数 * 0.1
            queryset = queryset.annotate(
                hot_score=(
                    F('like_count') * 2 +
                    F('comment_count') * 3 +
                    F('view_count') * 0.1
                )
            ).order_by('-is_pinned', '-hot_score', '-created_at')
        elif sort_by == 'replies':
            queryset = queryset.order_by('-is_pinned', '-last_reply_at', '-created_at')
        elif sort_by == 'featured':
            queryset = queryset.filter(is_featured=True).order_by('-created_at')
        else:  # latest
            queryset = queryset.order_by('-is_pinned', '-created_at')
        
        return queryset.distinct()
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ForumPostCreateSerializer
        return ForumPostListSerializer
    
    def perform_create(self, serializer):
        import logging
        logger = logging.getLogger('heritage_api')
        
        try:
            logger.debug(f'创建帖子请求数据: {self.request.data}')
            logger.debug(f'用户认证状态: {self.request.user.is_authenticated}')
            logger.debug(f'当前用户: {self.request.user}')
            logger.debug(f'用户类型: {type(self.request.user)}')
            
            # 检查用户认证
            if not self.request.user.is_authenticated:
                logger.error('用户未认证')
                raise serializers.ValidationError({'detail': '用户未认证'})
            
            # 保存帖子，序列化器会自动设置author
            post = serializer.save()
            logger.info(f'帖子创建成功: {post.id} - {post.title}')
            
        except Exception as e:
            logger.error(f'创建帖子时发生错误: {str(e)}')
            raise


class ForumPostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """论坛帖子详情视图"""
    queryset = ForumPost.objects.filter(status='published')
    serializer_class = ForumPostDetailSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_object(self):
        obj = super().get_object()
        # 增加浏览量（防止重复计数）
        if self.request.method == 'GET':
            session_key = f'viewed_post_{obj.id}'
            if not self.request.session.get(session_key):
                obj.increment_view_count()
                self.request.session[session_key] = True
        return obj
    
    def perform_update(self, serializer):
        # 只有作者或管理员可以编辑
        if (serializer.instance.author != self.request.user and 
            not self.request.user.is_staff):
            raise permissions.PermissionDenied("您没有权限编辑此帖子")
        serializer.save()
    
    def perform_destroy(self, instance):
        # 只有作者或管理员可以删除
        if (instance.author != self.request.user and 
            not self.request.user.is_staff):
            raise permissions.PermissionDenied("您没有权限删除此帖子")
        
        with transaction.atomic():
            # 软删除：修改状态而不是真正删除
            instance.status = 'deleted'
            instance.save()
            
            # 减少用户统计
            if hasattr(instance.author, 'forum_stats'):
                stats = instance.author.forum_stats
                stats.post_count = max(0, stats.post_count - 1)
                stats.save()


class ForumCommentListCreateView(generics.ListCreateAPIView):
    """论坛评论列表和创建视图"""
    serializer_class = ForumCommentSerializer
    pagination_class = ForumPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        post_id = self.kwargs['post_id']
        sort_by = self.request.query_params.get('sort', 'time_asc')
        
        queryset = ForumComment.objects.filter(
            post_id=post_id,
            parent=None,  # 只返回顶级评论
            is_deleted=False
        ).select_related('author', 'author__profile')
        
        if sort_by == 'time_desc':
            queryset = queryset.order_by('-created_at')
        elif sort_by == 'hot':
            queryset = queryset.order_by('-like_count', '-created_at')
        else:  # time_asc
            queryset = queryset.order_by('created_at')
        
        return queryset
    
    def perform_create(self, serializer):
        post_id = self.kwargs['post_id']
        post = get_object_or_404(ForumPost, id=post_id, status='published')
        
        if post.is_locked and not self.request.user.is_staff:
            raise permissions.PermissionDenied("此帖子已锁定，无法评论")
        
        serializer.save(post=post)


class ForumTagListView(generics.ListAPIView):
    """论坛标签列表视图"""
    queryset = ForumTag.objects.all()
    serializer_class = ForumTagSerializer
    pagination_class = None  # 不分页
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search', '')
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset[:50]  # 最多返回50个标签


class ForumAnnouncementListView(generics.ListAPIView):
    """论坛公告列表视图"""
    queryset = ForumAnnouncement.objects.filter(is_active=True)
    serializer_class = ForumAnnouncementSerializer
    pagination_class = None


class ForumUserStatsListView(generics.ListAPIView):
    """活跃用户排行榜视图"""
    serializer_class = ForumUserStatsSerializer
    pagination_class = None
    
    def get_queryset(self):
        # 返回本周最活跃的用户
        week_ago = timezone.now() - timezone.timedelta(days=7)
        return ForumUserStats.objects.filter(
            last_active_at__gte=week_ago
        ).order_by('-experience')[:10]


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_post_like(request, post_id):
    """切换帖子点赞状态"""
    post = get_object_or_404(ForumPost, id=post_id, status='published')
    
    with transaction.atomic():
        like, created = ForumPostLike.objects.get_or_create(
            user=request.user,
            post=post
        )
        
        if not created:
            # 取消点赞
            like.delete()
            post.like_count = max(0, post.like_count - 1)
            is_liked = False
            
            # 减少作者获得的点赞数
            if hasattr(post.author, 'forum_stats'):
                stats = post.author.forum_stats
                stats.like_received = max(0, stats.like_received - 1)
                stats.save()
        else:
            # 点赞
            post.like_count += 1
            is_liked = True
            
            # 增加作者获得的点赞数
            stats, created = ForumUserStats.objects.get_or_create(user=post.author)
            stats.like_received += 1
            stats.save()
        
        post.save(update_fields=['like_count'])
    
    return Response({
        'is_liked': is_liked,
        'like_count': post.like_count
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_comment_like(request, comment_id):
    """切换评论点赞状态"""
    comment = get_object_or_404(ForumComment, id=comment_id, is_deleted=False)
    
    with transaction.atomic():
        like, created = ForumCommentLike.objects.get_or_create(
            user=request.user,
            comment=comment
        )
        
        if not created:
            # 取消点赞
            like.delete()
            comment.like_count = max(0, comment.like_count - 1)
            is_liked = False
        else:
            # 点赞
            comment.like_count += 1
            is_liked = True
        
        comment.save(update_fields=['like_count'])
    
    return Response({
        'is_liked': is_liked,
        'like_count': comment.like_count
    })


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_comment(request, comment_id):
    """删除评论"""
    comment = get_object_or_404(ForumComment, id=comment_id, is_deleted=False)
    
    # 权限检查：评论者本人、帖子作者、管理员可删除
    if not (comment.author == request.user or 
            comment.post.author == request.user or 
            request.user.is_staff):
        return Response(
            {'error': '您没有权限删除此评论'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    with transaction.atomic():
        # 软删除：标记为已删除而不是真正删除
        comment.is_deleted = True
        comment.save(update_fields=['is_deleted'])
        
        # 更新帖子评论数
        comment.post.comment_count = max(0, comment.post.comment_count - 1)
        comment.post.save(update_fields=['comment_count'])
        
        # 更新用户统计
        if hasattr(comment.author, 'forum_stats'):
            stats = comment.author.forum_stats
            stats.comment_count = max(0, stats.comment_count - 1)
            stats.save(update_fields=['comment_count'])
    
    return Response(
        {'message': '评论已删除'},
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_post_favorite(request, post_id):
    """切换帖子收藏状态"""
    post = get_object_or_404(ForumPost, id=post_id, status='published')
    
    with transaction.atomic():
        favorite, created = ForumPostFavorite.objects.get_or_create(
            user=request.user,
            post=post
        )
        
        if not created:
            # 取消收藏
            favorite.delete()
            post.favorite_count = max(0, post.favorite_count - 1)
            is_favorited = False
        else:
            # 收藏
            post.favorite_count += 1
            is_favorited = True
        
        post.save(update_fields=['favorite_count'])
    
    return Response({
        'is_favorited': is_favorited,
        'favorite_count': post.favorite_count
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_user_follow_status(request, user_id):
    """检查用户关注状态"""
    target_user = get_object_or_404(User, id=user_id)
    
    if target_user == request.user:
        return Response({
            'is_following': False,
            'message': '不能关注自己'
        })
    
    is_following = ForumUserFollow.objects.filter(
        follower=request.user,
        following=target_user
    ).exists()
    
    return Response({
        'is_following': is_following
    })


@api_view(['POST', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def toggle_user_follow(request, user_id):
    """切换用户关注状态"""
    target_user = get_object_or_404(User, id=user_id)
    
    if target_user == request.user:
        return Response(
            {'error': '不能关注自己'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    with transaction.atomic():
        if request.method == 'DELETE':
            # 取消关注
            try:
                follow = ForumUserFollow.objects.get(
                    follower=request.user,
                    following=target_user
                )
                follow.delete()
                is_followed = False
                
                # 更新统计
                if hasattr(request.user, 'forum_stats'):
                    request.user.forum_stats.following_count = max(
                        0, request.user.forum_stats.following_count - 1
                    )
                    request.user.forum_stats.save()
                
                if hasattr(target_user, 'forum_stats'):
                    target_user.forum_stats.follower_count = max(
                        0, target_user.forum_stats.follower_count - 1
                    )
                    target_user.forum_stats.save()
            except ForumUserFollow.DoesNotExist:
                is_followed = False
        else:
            # POST请求：关注或切换
            follow, created = ForumUserFollow.objects.get_or_create(
                follower=request.user,
                following=target_user
            )
            
            if not created:
                # 已存在，取消关注
                follow.delete()
                is_followed = False
                
                # 更新统计
                if hasattr(request.user, 'forum_stats'):
                    request.user.forum_stats.following_count = max(
                        0, request.user.forum_stats.following_count - 1
                    )
                    request.user.forum_stats.save()
                
                if hasattr(target_user, 'forum_stats'):
                    target_user.forum_stats.follower_count = max(
                        0, target_user.forum_stats.follower_count - 1
                    )
                    target_user.forum_stats.save()
            else:
                # 关注
                is_followed = True
                
                # 更新统计
                follower_stats, created = ForumUserStats.objects.get_or_create(
                    user=request.user
                )
                follower_stats.following_count += 1
                follower_stats.save()
                
                following_stats, created = ForumUserStats.objects.get_or_create(
                    user=target_user
                )
                following_stats.follower_count += 1
                following_stats.save()
    
    follower_count = target_user.followers.count()
    
    return Response({
        'is_followed': is_followed,
        'follower_count': follower_count
    })


@api_view(['POST'])
@permission_classes([permissions.AllowAny])  # 允许匿名用户增加浏览量
def increment_post_view(request, post_id):
    """增加帖子浏览量"""
    post = get_object_or_404(ForumPost, id=post_id, status='published')
    
    # 防止重复计数（基于session）
    session_key = f'viewed_post_{post_id}'
    if not request.session.get(session_key):
        post.increment_view_count()
        request.session[session_key] = True
    
    return Response({
        'view_count': post.view_count,
        'success': True
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def report_post(request, post_id):
    """举报帖子"""
    post = get_object_or_404(ForumPost, id=post_id, status='published')
    
    serializer = ForumReportSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save(post=post)
        return Response(
            {'message': '举报已提交，我们会尽快处理'},
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def report_comment(request, comment_id):
    """举报评论"""
    comment = get_object_or_404(ForumComment, id=comment_id, is_deleted=False)
    
    serializer = ForumReportSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save(comment=comment)
        return Response(
            {'message': '举报已提交，我们会尽快处理'},
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def toggle_post_pin(request, post_id):
    """切换帖子置顶状态（管理员功能）"""
    post = get_object_or_404(ForumPost, id=post_id)
    
    post.is_pinned = not post.is_pinned
    post.save(update_fields=['is_pinned'])
    
    return Response({
        'is_pinned': post.is_pinned,
        'message': '置顶成功' if post.is_pinned else '取消置顶成功'
    })


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def toggle_post_feature(request, post_id):
    """切换帖子精华状态（管理员功能）"""
    post = get_object_or_404(ForumPost, id=post_id)
    
    post.is_featured = not post.is_featured
    post.save(update_fields=['is_featured'])
    
    return Response({
        'is_featured': post.is_featured,
        'message': '设为精华成功' if post.is_featured else '取消精华成功'
    })


@api_view(['GET'])
def search_users(request):
    """搜索用户（用于@功能）"""
    query = request.GET.get('q', '').strip()
    if not query or len(query) < 2:
        return Response([])
    
    users = User.objects.filter(
        username__icontains=query
    ).select_related('profile')[:10]
    
    results = []
    for user in users:
        avatar_url = None
        if hasattr(user, 'profile') and user.profile.avatar:
            avatar_url = request.build_absolute_uri(user.profile.avatar.url)
        
        results.append({
            'id': user.id,
            'username': user.username,
            'avatar': avatar_url
        })
    
    return Response(results)


@api_view(['GET'])
def active_users(request):
    """获取活跃用户列表"""
    period = request.query_params.get('period', 'week')  # week, month, all
    
    # 根据时间段筛选
    if period == 'week':
        time_filter = timezone.now() - timezone.timedelta(days=7)
    elif period == 'month':
        time_filter = timezone.now() - timezone.timedelta(days=30)
    else:
        time_filter = None
    
    # 构建查询
    queryset = User.objects.select_related('profile')
    
    if time_filter:
        # 按发帖和评论活跃度排序
        queryset = queryset.annotate(
            recent_posts=Count('forum_posts', filter=Q(forum_posts__created_at__gte=time_filter)),
            recent_comments=Count('forum_comments', filter=Q(forum_comments__created_at__gte=time_filter)),
            activity_score=F('recent_posts') * 2 + F('recent_comments')
        ).filter(activity_score__gt=0).order_by('-activity_score')
    else:
        # 按总发帖和评论数排序
        queryset = queryset.annotate(
            total_posts=Count('forum_posts'),
            total_comments=Count('forum_comments'),
            activity_score=F('total_posts') * 2 + F('total_comments')
        ).filter(activity_score__gt=0).order_by('-activity_score')
    
    # 限制返回数量
    users = queryset[:10]
    
    user_data = []
    for user in users:
        try:
            profile = user.profile
            avatar_url = profile.avatar.url if profile.avatar else None
        except:
            avatar_url = None
            
        user_data.append({
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name or user.username,
            'avatar': avatar_url,
            'activity_score': getattr(user, 'activity_score', 0)
        })
    
    return Response(user_data)


@csrf_exempt
@require_http_methods(["POST"])
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def upload_image(request):
    """上传图片"""
    if 'image' not in request.FILES:
        return Response(
            {'error': '没有上传文件'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    image_file = request.FILES['image']
    
    # 验证文件类型
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    if image_file.content_type not in allowed_types:
        return Response(
            {'error': '不支持的文件类型'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # 验证文件大小（5MB限制）
    if image_file.size > 5 * 1024 * 1024:
        return Response(
            {'error': '文件大小不能超过5MB'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # 生成唯一文件名
        file_extension = image_file.name.split('.')[-1]
        filename = f"forum_images/{uuid.uuid4()}.{file_extension}"
        
        # 保存文件
        file_path = default_storage.save(filename, ContentFile(image_file.read()))
        file_url = request.build_absolute_uri(default_storage.url(file_path))
        
        return Response({
            'url': file_url,
            'filename': filename
        })
    
    except Exception as e:
        return Response(
            {'error': '文件上传失败'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_posts(request, user_id):
    """获取用户的帖子列表"""
    user = get_object_or_404(User, id=user_id)
    
    posts = ForumPost.objects.filter(
        author=user,
        status='published'
    ).order_by('-created_at')
    
    paginator = ForumPagination()
    page = paginator.paginate_queryset(posts, request)
    
    serializer = ForumPostListSerializer(
        page,
        many=True,
        context={'request': request}
    )
    
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_favorites(request):
    """获取用户收藏的帖子列表"""
    favorites = ForumPostFavorite.objects.filter(
        user=request.user
    ).select_related('post', 'post__author').order_by('-created_at')
    
    paginator = ForumPagination()
    page = paginator.paginate_queryset(favorites, request)
    
    posts = [favorite.post for favorite in page]
    serializer = ForumPostListSerializer(
        posts,
        many=True,
        context={'request': request}
    )
    
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_notifications(request):
    """获取用户通知（简化版）"""
    # 这里可以实现更复杂的通知系统
    # 目前返回用户帖子的新评论
    user_posts = ForumPost.objects.filter(author=request.user)
    
    recent_comments = ForumComment.objects.filter(
        post__in=user_posts,
        is_deleted=False
    ).exclude(
        author=request.user
    ).select_related(
        'author', 'post'
    ).order_by('-created_at')[:20]
    
    notifications = []
    for comment in recent_comments:
        notifications.append({
            'id': comment.id,
            'type': 'comment',
            'message': f"{comment.author.username} 评论了您的帖子 \"{comment.post.title}\"",
            'created_at': comment.created_at,
            'post_id': comment.post.id
        })
    
    return Response(notifications)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_following_list(request):
    """获取用户关注列表"""
    following = ForumUserFollow.objects.filter(
        follower=request.user
    ).select_related('following', 'following__profile').order_by('-created_at')
    
    paginator = ForumPagination()
    page = paginator.paginate_queryset(following, request)
    
    following_data = []
    for follow in page:
        user = follow.following
        avatar_url = None
        if hasattr(user, 'profile') and user.profile.avatar:
            avatar_url = request.build_absolute_uri(user.profile.avatar.url)
        
        # 获取用户统计信息
        stats = getattr(user, 'forum_stats', None)
        
        following_data.append({
            'user': {
                'id': user.id,
                'username': user.username,
                'avatar': avatar_url,
                'display_name': getattr(user.profile, 'display_name', '') if hasattr(user, 'profile') else '',
                'bio': getattr(user.profile, 'bio', '') if hasattr(user, 'profile') else '',
                'post_count': stats.post_count if stats else 0,
                'followers_count': stats.follower_count if stats else 0,
                'following_count': stats.following_count if stats else 0
            },
            'created_at': follow.created_at
        })
    
    return paginator.get_paginated_response(following_data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_followers_list(request):
    """获取用户粉丝列表"""
    followers = ForumUserFollow.objects.filter(
        following=request.user
    ).select_related('follower', 'follower__profile').order_by('-created_at')
    
    paginator = ForumPagination()
    page = paginator.paginate_queryset(followers, request)
    
    followers_data = []
    for follow in page:
        user = follow.follower
        avatar_url = None
        if hasattr(user, 'profile') and user.profile.avatar:
            avatar_url = request.build_absolute_uri(user.profile.avatar.url)
        
        # 获取用户统计信息
        stats = getattr(user, 'forum_stats', None)
        
        # 检查是否互相关注
        is_mutual = ForumUserFollow.objects.filter(
            follower=request.user,
            following=user
        ).exists()
        
        followers_data.append({
            'user': {
                'id': user.id,
                'username': user.username,
                'avatar': avatar_url,
                'display_name': getattr(user.profile, 'display_name', '') if hasattr(user, 'profile') else '',
                'bio': getattr(user.profile, 'bio', '') if hasattr(user, 'profile') else '',
                'post_count': stats.post_count if stats else 0,
                'followers_count': stats.follower_count if stats else 0,
                'following_count': stats.following_count if stats else 0
            },
            'created_at': follow.created_at,
            'is_mutual': is_mutual
        })
    
    return paginator.get_paginated_response(followers_data)