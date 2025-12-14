from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status, generics, mixins
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
import logging

from .models import Heritage, HeritageImage, UserFavorite, News, Policy
from .creation_models import (
    UserCreation, CreationLike, CreationComment, CreationTag,
    CreationReport, CreationViewHistory, CreationFavorite, CreationShare
)
from .serializers import (
    HeritageSerializer, HeritageImageSerializer, UserFavoriteSerializer, 
    NewsSerializer, PolicySerializer, UserCreationSerializer, CreationLikeSerializer,
    CreationCommentSerializer, CreationTagSerializer, CreationReportSerializer,
    CreationViewHistorySerializer, CreationFavoriteSerializer, CreationShareSerializer
)
from rest_framework.permissions import IsAuthenticated, AllowAny
from .redis_utils import redis_client
from .search_service import SearchService

logger = logging.getLogger(__name__)

# Create your views here.
class HeritageViewSet(viewsets.ModelViewSet):
    """非遗项目视图集"""
    queryset = Heritage.objects.all().order_by('id') # 添加默认排序
    serializer_class = HeritageSerializer
    
    def get_queryset(self):
        queryset = Heritage.objects.all()
        
        # 筛选条件
        category = self.request.query_params.get('category')
        level = self.request.query_params.get('level')
        region = self.request.query_params.get('region')
        
        # 支持两种搜索参数名称：keyword（旧）和search（新）
        keyword = self.request.query_params.get('keyword')
        search = self.request.query_params.get('search')
        
        # 优先使用search参数，如果没有则使用keyword参数
        search_term = search if search else keyword
        
        if category:
            queryset = queryset.filter(category=category)
        if level:
            queryset = queryset.filter(level=level)
        if region:
            queryset = queryset.filter(region=region)
        if search_term:
            # 只匹配名字，不匹配描述、历史和地区
            queryset = queryset.filter(Q(name__icontains=search_term))
            
        return queryset
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """获取所有类别"""
        all_categories_qs = Heritage.objects.values_list('category', flat=True) # Get all, not distinct yet
        
        seen_categories = set()
        formatted_categories = []
        for cat_name_raw in all_categories_qs:
            if cat_name_raw is not None:
                cat_name_stripped = str(cat_name_raw).strip()
                if cat_name_stripped and cat_name_stripped not in seen_categories:
                    formatted_categories.append({'id': cat_name_stripped, 'name': cat_name_stripped})
                    seen_categories.add(cat_name_stripped)
        
        formatted_categories.sort(key=lambda x: x['name']) # Sort for consistency
        return Response(formatted_categories)
    
    @action(detail=False, methods=['get'])
    def levels(self, request):
        """获取所有级别"""
        levels_qs = Heritage.objects.values_list('level', flat=True).distinct()
        valid_levels = set()
        for lvl in levels_qs:
            if lvl is not None:
                s_lvl = str(lvl).strip()
                if s_lvl: # Ensure not empty after stripping
                    valid_levels.add(s_lvl)
        return Response(sorted(list(valid_levels)))
    
    @action(detail=False, methods=['get'])
    def regions(self, request):
        """获取所有地区"""
        regions_qs = Heritage.objects.values_list('region', flat=True).distinct()

        seen_regions = set()
        formatted_regions = []
        for region_name in regions_qs:
            if region_name and region_name.strip():
                stripped_name = region_name.strip()
                if stripped_name not in seen_regions:
                    formatted_regions.append({'id': stripped_name, 'name': stripped_name})
                    seen_regions.add(stripped_name)
        return Response(formatted_regions)
    


class UserFavoriteViewSet(viewsets.ModelViewSet):
    queryset = UserFavorite.objects.all()
    serializer_class = UserFavoriteSerializer
    permission_classes = [IsAuthenticated] # 只有登录用户才能操作收藏

    def get_queryset(self):
        # 只返回当前登录用户的收藏
        queryset = UserFavorite.objects.filter(user=self.request.user)
        
        # 处理排序参数
        sort = self.request.query_params.get('sort', 'date-desc')
        
        # 根据排序参数排序
        if sort == 'date-asc':
            queryset = queryset.order_by('created_at')
        elif sort == 'name-asc':
            queryset = queryset.order_by('heritage__name')
        elif sort == 'name-desc':
            queryset = queryset.order_by('-heritage__name')
        else: # 默认按创建时间降序
            queryset = queryset.order_by('-created_at')
        
        return queryset

    def perform_create(self, serializer):
        # 创建收藏时，自动将当前登录用户设置为收藏者
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='add')
    def add_favorite(self, request):
        user = request.user
        heritage_id = request.data.get('heritage_id')
        if not heritage_id:
            return Response({'error': 'heritage_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            heritage = Heritage.objects.get(id=heritage_id)
        except Heritage.DoesNotExist:
            return Response({'error': 'Heritage not found'}, status=status.HTTP_404_NOT_FOUND)

        favorite, created = UserFavorite.objects.get_or_create(user=user, heritage=heritage)
        if created:
            serializer = self.get_serializer(favorite)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({'message': 'Already favorited'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='remove')
    def remove_favorite(self, request):
        user = request.user
        heritage_id = request.data.get('heritage_id')
        if not heritage_id:
            return Response({'error': 'heritage_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            favorite = UserFavorite.objects.get(user=user, heritage_id=heritage_id)
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except UserFavorite.DoesNotExist:
            return Response({'error': 'Favorite not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], url_path='check')
    def check_favorite(self, request):
        user = request.user
        heritage_id = request.query_params.get('heritage_id')
        if not heritage_id:
            return Response({'error': 'heritage_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        is_favorited = UserFavorite.objects.filter(user=user, heritage_id=heritage_id).exists()
        return Response({'is_favorited': is_favorited}, status=status.HTTP_200_OK)


class NewsViewSet(viewsets.ModelViewSet):
    """非遗资讯视图集"""
    queryset = News.objects.filter(is_active=True).order_by('-publish_date')
    serializer_class = NewsSerializer
    
    def get_queryset(self):
        queryset = News.objects.filter(is_active=True)
        
        # 搜索功能 - 使用新的搜索服务
        search = self.request.query_params.get('search')
        if search:
            try:
                search_service = SearchService()
                queryset = search_service.search_news(
                    query=search,
                    queryset=queryset
                )
                logger.debug(f"新闻搜索: '{search}', 结果数量: {queryset.count()}")
            except Exception as e:
                logger.error(f"新闻搜索失败: {e}")
                # 降级到原始搜索方式
                queryset = queryset.filter(
                    Q(title__icontains=search) | 
                    Q(summary__icontains=search) |
                    Q(content__icontains=search) |
                    Q(tags__icontains=search)
                )
        
        # 标签筛选
        tag = self.request.query_params.get('tag')
        if tag:
            queryset = queryset.filter(tags__icontains=tag)
            
        return queryset.order_by('-publish_date')
    
    def retrieve(self, request, *args, **kwargs):
        """获取单个资讯详情时增加浏览次数"""
        instance = self.get_object()
        
        # 使用通用函数处理浏览量增加
        from .utils import handle_view_count_increase
        handle_view_count_increase(instance, 'news')
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def sources(self, request):
        """获取所有来源"""
        sources = News.objects.filter(is_active=True, source__isnull=False).exclude(source='').values_list('source', flat=True).distinct()
        return Response(sorted(list(sources)))
    
    @action(detail=False, methods=['get'])
    def search_suggestions(self, request):
        """获取搜索建议"""
        query = request.query_params.get('q', '').strip()
        if not query or len(query) < 2:
            return Response([])
        
        try:
            search_service = SearchService()
            suggestions = search_service.get_search_suggestions(query, 'news')
            return Response(suggestions)
        except Exception as e:
            logger.error(f"获取政策搜索建议失败: {e}")
            return Response([])
    
    @action(detail=False, methods=['get'])
    def tags(self, request):
        """获取所有标签"""
        all_tags = set()
        news_with_tags = News.objects.filter(is_active=True, tags__isnull=False).exclude(tags='')
        
        for news in news_with_tags:
            if news.tags:
                tags = [tag.strip() for tag in news.tags.split(',') if tag.strip()]
                all_tags.update(tags)
        
        return Response(sorted(list(all_tags)))


# 创作相关视图
class CreationTagViewSet(viewsets.ModelViewSet):
    """创作标签视图集"""
    queryset = CreationTag.objects.all().order_by('name')
    serializer_class = CreationTagSerializer
    permission_classes = [IsAuthenticated]


class UserCreationViewSet(viewsets.ModelViewSet):
    """用户创作视图集"""
    queryset = UserCreation.objects.all().order_by('-created_at')
    serializer_class = UserCreationSerializer
    
    def get_permissions(self):
        """根据请求方法设置不同的权限"""
        if self.action in ['list', 'retrieve', 'trending_tags', 'statistics', 'creation_types', 'status_options']:
            # 列表、详情查看、热门标签、统计数据等不需要认证
            permission_classes = [AllowAny]
        else:
            # 创建、修改、删除等操作需要认证
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = UserCreation.objects.all()
        
        # 用户筛选
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # 创作类型筛选 - 支持两种参数名：creation_type（旧）和category（新）
        creation_type = self.request.query_params.get('creation_type')
        category = self.request.query_params.get('category')
        
        # 优先使用category参数，如果没有则使用creation_type参数
        type_param = category if category and category != 'all' else creation_type
        if type_param:
            queryset = queryset.filter(type=type_param)
        
        # 状态筛选
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # 标签筛选
        tag = self.request.query_params.get('tag')
        if tag:
            queryset = queryset.filter(tags__name__icontains=tag)
        
        # 搜索功能
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search)
            )
        
        # 是否精选
        is_featured = self.request.query_params.get('is_featured')
        if is_featured is not None:
            queryset = queryset.filter(is_featured=is_featured.lower() == 'true')
        
        # 是否公开
        is_public = self.request.query_params.get('is_public')
        if is_public is not None:
            queryset = queryset.filter(is_public=is_public.lower() == 'true')
        
        return queryset.order_by('-created_at')
        
    def retrieve(self, request, *args, **kwargs):
        """获取创作详情，同时增加浏览量"""
        instance = self.get_object()
        
        # 增加浏览量
        from .utils import handle_view_count_increase
        handle_view_count_increase(instance, 'creation')
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_create(self, serializer):
        # 创建创作时，自动将当前登录用户设置为作者
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """发布创作"""
        creation = self.get_object()
        if creation.user != request.user:
            return Response({'error': '没有权限操作此创作'}, status=status.HTTP_403_FORBIDDEN)
        
        creation.status = 'published'
        creation.save()
        serializer = self.get_serializer(creation)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        """取消发布创作"""
        creation = self.get_object()
        if creation.user != request.user:
            return Response({'error': '没有权限操作此创作'}, status=status.HTTP_403_FORBIDDEN)
        
        creation.status = 'draft'
        creation.save()
        serializer = self.get_serializer(creation)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def feature(self, request, pk=None):
        """设为精选"""
        # 检查是否为管理员
        if not request.user.is_staff:
            return Response({'error': '只有管理员可以设置精选'}, status=status.HTTP_403_FORBIDDEN)
        
        creation = self.get_object()
        creation.is_featured = True
        creation.save()
        serializer = self.get_serializer(creation)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def unfeature(self, request, pk=None):
        """取消精选"""
        # 检查是否为管理员
        if not request.user.is_staff:
            return Response({'error': '只有管理员可以取消精选'}, status=status.HTTP_403_FORBIDDEN)
        
        creation = self.get_object()
        creation.is_featured = False
        creation.save()
        serializer = self.get_serializer(creation)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def recommend(self, request, pk=None):
        """设为推荐"""
        # 检查是否为管理员
        if not request.user.is_staff:
            return Response({'error': '只有管理员可以设置推荐'}, status=status.HTTP_403_FORBIDDEN)
        
        creation = self.get_object()
        creation.is_recommended = True
        creation.save()
        serializer = self.get_serializer(creation)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def unrecommend(self, request, pk=None):
        """取消推荐"""
        # 检查是否为管理员
        if not request.user.is_staff:
            return Response({'error': '只有管理员可以取消推荐'}, status=status.HTTP_403_FORBIDDEN)
        
        creation = self.get_object()
        creation.is_recommended = False
        creation.save()
        serializer = self.get_serializer(creation)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_creations(self, request):
        """获取当前用户的创作"""
        queryset = UserCreation.objects.filter(author=request.user)
        
        # 状态筛选
        status = request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        page = self.paginate_queryset(queryset.order_by('-created_at'))
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_favorites(self, request):
        """获取当前用户收藏的创作"""
        from .creation_models import CreationFavorite
        
        # 获取用户收藏的创作ID
        favorite_creation_ids = CreationFavorite.objects.filter(
            user=request.user
        ).values_list('creation_id', flat=True)
        
        queryset = UserCreation.objects.filter(id__in=favorite_creation_ids)
        
        page = self.paginate_queryset(queryset.order_by('-created_at'))
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def creation_types(self, request):
        """获取所有创作类型"""
        type_choices = dict(UserCreation._meta.get_field('type').choices)
        result = [{'value': value, 'label': label} for value, label in type_choices.items()]
        return Response(result)

    @action(detail=False, methods=['get'])
    def status_options(self, request):
        """获取所有状态选项"""
        status_choices = dict(UserCreation._meta.get_field('status').choices)
        result = [{'value': value, 'label': label} for value, label in status_choices.items()]
        return Response(result)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取创作统计数据"""
        try:
            # 总创作数量
            total_creations = UserCreation.objects.filter(status='published').count()
            
            # 今日创作数量
            today = timezone.now().date()
            today_creations = UserCreation.objects.filter(
                status='published',
                created_at__date=today
            ).count()
            
            # 本周创作数量
            week_start = today - timedelta(days=today.weekday())
            week_creations = UserCreation.objects.filter(
                status='published',
                created_at__date__gte=week_start
            ).count()
            
            # 本月创作数量
            month_start = today.replace(day=1)
            month_creations = UserCreation.objects.filter(
                status='published',
                created_at__date__gte=month_start
            ).count()
            
            # 各类型创作数量
            type_stats = UserCreation.objects.filter(status='published').values('type').annotate(
                count=Count('id')
            ).order_by('-count')
            
            statistics = {
                'total': total_creations,
                'today': today_creations,
                'week': week_creations,
                'month': month_creations,
                'by_type': list(type_stats)
            }
            
            return Response(statistics)
        except Exception as e:
            logger.error(f"获取创作统计数据失败: {e}")
            return Response({'error': '获取统计数据失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def trending_tags(self, request):
        """获取热门标签"""
        try:
            # 获取最近30天内的已发布创作
            thirty_days_ago = timezone.now() - timedelta(days=30)
            
            # 获取所有标签并统计使用次数
            creations = UserCreation.objects.filter(
                created_at__gte=thirty_days_ago,
                status='published'
            ).values_list('tags', flat=True)
            
            # 统计标签使用次数
            tag_counts = {}
            for tags_list in creations:
                if tags_list:  # 确保标签列表不为空
                    for tag in tags_list:
                        if tag:  # 确保标签不为空
                            tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            # 按使用次数排序，取前20个
            sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:20]
            
            # 格式化结果
            result = [
                {
                    'name': tag_name,
                    'count': count
                }
                for tag_name, count in sorted_tags
            ]
            
            return Response(result)
        except Exception as e:
            logger.error(f"获取热门标签失败: {e}")
            return Response({'error': '获取热门标签失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def view_history(self, request):
        """获取用户创作浏览历史"""
        try:
            user = request.user
            
            # 获取用户的创作浏览历史
            view_history = CreationViewHistory.objects.filter(
                user=user
            ).select_related('creation').order_by('-viewed_at')
            
            # 序列化数据
            history_data = []
            for record in view_history:
                creation_data = self.get_serializer(record.creation).data
                creation_data['viewed_at'] = record.viewed_at.isoformat()
                history_data.append(creation_data)
            
            return Response(history_data)
            
        except Exception as e:
            logger.error(f"获取创作浏览历史失败: {e}")
            return Response({'error': '获取创作浏览历史失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreationLikeViewSet(viewsets.ModelViewSet):
    """创作点赞视图集"""
    queryset = CreationLike.objects.all().order_by('-created_at')
    serializer_class = CreationLikeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 只返回当前登录用户的点赞，并按创建时间降序排序
        return CreationLike.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        # 创建点赞时，自动将当前登录用户设置为点赞者
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='toggle')
    def toggle_like(self, request):
        """切换点赞状态"""
        user = request.user
        creation_id = request.data.get('creation_id')
        
        if not creation_id:
            return Response({'error': 'creation_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            creation = UserCreation.objects.get(id=creation_id)
        except UserCreation.DoesNotExist:
            return Response({'error': '创作不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        # 检查是否已点赞
        like_exists = CreationLike.objects.filter(user=user, creation=creation).exists()
        
        if like_exists:
            # 取消点赞
            CreationLike.objects.filter(user=user, creation=creation).delete()
            # 更新点赞数
            creation.like_count = max(0, creation.like_count - 1)
            creation.save()
            return Response({'message': '取消点赞成功', 'liked': False, 'like_count': creation.like_count})
        else:
            # 添加点赞
            CreationLike.objects.create(user=user, creation=creation)
            # 更新点赞数
            creation.like_count += 1
            creation.save()
            return Response({'message': '点赞成功', 'liked': True, 'like_count': creation.like_count})

    @action(detail=False, methods=['get'], url_path='check')
    def check_like(self, request):
        """检查是否已点赞"""
        user = request.user
        creation_id = request.query_params.get('creation_id')
        
        if not creation_id:
            return Response({'error': 'creation_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        is_liked = CreationLike.objects.filter(user=user, creation_id=creation_id).exists()
        return Response({'liked': is_liked})


class CreationCommentViewSet(viewsets.ModelViewSet):
    """创作评论视图集"""
    queryset = CreationComment.objects.all().order_by('-created_at')
    serializer_class = CreationCommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = CreationComment.objects.all()
        
        # 创作筛选
        creation_id = self.request.query_params.get('creation_id')
        if creation_id:
            queryset = queryset.filter(creation_id=creation_id)
        
        # 用户筛选
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # 只显示活跃评论
        queryset = queryset.filter(is_active=True)
        
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        # 从请求数据中获取creation_id
        creation_id = self.request.data.get('creation_id')
        if not creation_id:
            raise serializers.ValidationError({'creation_id': 'creation_id is required'})
        
        # 获取创作实例
        creation = UserCreation.objects.get(id=creation_id)
        
        # 创建评论时，自动将当前登录用户设置为评论者，并关联到创作
        comment = serializer.save(user=self.request.user, creation=creation)
        # 更新创作的评论数
        comment.creation.comment_count += 1
        comment.creation.save(update_fields=['comment_count'])

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """点赞评论"""
        comment = self.get_object()
        comment.like_count += 1
        comment.save()
        serializer = self.get_serializer(comment)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """删除评论 - 重写删除逻辑，添加权限控制"""
        comment = self.get_object()
        
        # 权限检查：评论者本人、创作作者、管理员可删除
        if not (comment.user == request.user or 
                comment.creation.author == request.user or 
                request.user.is_staff):
            return Response(
                {'error': '您没有权限删除此评论'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 执行软删除
        comment.is_active = False
        comment.save(update_fields=['is_active'])
        
        # 更新创作评论数
        comment.creation.comment_count = max(0, comment.creation.comment_count - 1)
        comment.creation.save(update_fields=['comment_count'])
        
        return Response(
            {'message': '评论已删除'},
            status=status.HTTP_200_OK
        )


class CreationViewHistoryViewSet(viewsets.ModelViewSet):
    """创作浏览历史视图集"""
    queryset = CreationViewHistory.objects.all().order_by('-viewed_at')
    serializer_class = CreationViewHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 只返回当前登录用户的浏览历史
        return CreationViewHistory.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # 创建浏览记录时，自动将当前登录用户设置为浏览者
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """清除用户所有创作浏览历史"""
        try:
            user = request.user
            deleted_count = CreationViewHistory.objects.filter(user=user).delete()[0]
            return Response({
                'message': f'已清除 {deleted_count} 条创作浏览历史记录'
            })
        except Exception as e:
            logger.error(f"清除创作浏览历史失败: {e}")
            return Response({'error': '清除创作浏览历史失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def record_view(self, request):
        """记录创作浏览"""
        user = request.user
        creation_id = request.data.get('creation_id')
        
        if not creation_id:
            return Response({'error': 'creation_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            creation = UserCreation.objects.get(id=creation_id)
        except UserCreation.DoesNotExist:
            return Response({'error': '创作不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        # 创建或更新浏览记录
        view_history, created = CreationViewHistory.objects.get_or_create(
            user=user,
            creation=creation,
            defaults={'viewed_at': timezone.now()}
        )
        
        if not created:
            # 更新浏览时间
            view_history.viewed_at = timezone.now()
            view_history.save()
        
        serializer = self.get_serializer(view_history)
        return Response(serializer.data)


class CreationFavoriteViewSet(viewsets.ModelViewSet):
    """创作收藏视图集"""
    queryset = CreationFavorite.objects.all().order_by('-created_at')
    serializer_class = CreationFavoriteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 只返回当前登录用户的收藏，并按创建时间降序排序
        return CreationFavorite.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        # 创建收藏时，自动将当前登录用户设置为收藏者
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='toggle')
    def toggle_favorite(self, request):
        """切换收藏状态"""
        user = request.user
        creation_id = request.data.get('creation_id')
        
        if not creation_id:
            return Response({'error': 'creation_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            creation = UserCreation.objects.get(id=creation_id)
        except UserCreation.DoesNotExist:
            return Response({'error': '创作不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        # 检查是否已收藏
        favorite_exists = CreationFavorite.objects.filter(user=user, creation=creation).exists()
        
        if favorite_exists:
            # 取消收藏
            CreationFavorite.objects.filter(user=user, creation=creation).delete()
            return Response({'message': '取消收藏成功', 'favorited': False})
        else:
            # 添加收藏
            CreationFavorite.objects.create(user=user, creation=creation)
            return Response({'message': '收藏成功', 'favorited': True})

    @action(detail=False, methods=['get'], url_path='check')
    def check_favorite(self, request):
        """检查是否已收藏"""
        user = request.user
        creation_id = request.query_params.get('creation_id')
        
        if not creation_id:
            return Response({'error': 'creation_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        is_favorited = CreationFavorite.objects.filter(user=user, creation_id=creation_id).exists()
        return Response({'favorited': is_favorited})


class CreationShareViewSet(viewsets.ModelViewSet):
    """创作分享视图集"""
    queryset = CreationShare.objects.all()
    serializer_class = CreationShareSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 只返回当前登录用户的分享记录
        return CreationShare.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # 创建分享记录时，自动将当前登录用户设置为分享者
        serializer.save(user=self.request.user)


class CreationReportViewSet(viewsets.ModelViewSet):
    """创作举报视图集"""
    queryset = CreationReport.objects.all()
    serializer_class = CreationReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 普通用户只能看到自己的举报记录
        if not self.request.user.is_staff:
            return CreationReport.objects.filter(user=self.request.user)
        # 管理员可以看到所有举报记录
        return CreationReport.objects.all()

    def perform_create(self, serializer):
        # 创建举报时，自动将当前登录用户设置为举报者
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """处理举报"""
        if not request.user.is_staff:
            return Response({'error': '没有权限处理举报'}, status=status.HTTP_403_FORBIDDEN)
        
        report = self.get_object()
        status_value = request.data.get('status')
        feedback = request.data.get('feedback', '')
        
        if status_value not in ['pending', 'processing', 'resolved', 'rejected']:
            return Response({'error': '无效的状态值'}, status=status.HTTP_400_BAD_REQUEST)
        
        report.status = status_value
        report.feedback = feedback
        report.processed_by = request.user
        report.processed_at = timezone.now()
        report.save()
        
        serializer = self.get_serializer(report)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search_suggestions(self, request):
        """获取搜索建议"""
        query = request.query_params.get('q', '').strip()
        if not query or len(query) < 2:
            return Response([])
        
        try:
            search_service = SearchService()
            suggestions = search_service.get_search_suggestions(query, 'policy')
            return Response(suggestions)
        except Exception as e:
            logger.error(f"获取政策搜索建议失败: {e}")
            return Response([])


class PolicyViewSet(viewsets.ModelViewSet):
    """相关政策视图集"""
    queryset = Policy.objects.filter(is_active=True).order_by('-publish_date')
    serializer_class = PolicySerializer
    
    def get_queryset(self):
        queryset = Policy.objects.filter(is_active=True)
        
        # 搜索功能 - 使用新的搜索服务
        search = self.request.query_params.get('search')
        if search:
            try:
                search_service = SearchService()
                queryset = search_service.search_policies(
                    query=search,
                    queryset=queryset
                )
                logger.debug(f"政策搜索: '{search}', 结果数量: {queryset.count()}")
            except Exception as e:
                logger.error(f"政策搜索失败: {e}")
                # 降级到原始搜索方式
                queryset = queryset.filter(
                    Q(title__icontains=search) | 
                    Q(summary__icontains=search) |
                    Q(content__icontains=search) |
                    Q(policy_number__icontains=search) |
                    Q(issuing_authority__icontains=search) |
                    Q(tags__icontains=search)
                )
        
        # 政策类型筛选
        policy_type = self.request.query_params.get('policy_type')
        if policy_type:
            queryset = queryset.filter(policy_type=policy_type)
        
        # 发布机构筛选
        authority = self.request.query_params.get('authority')
        if authority:
            queryset = queryset.filter(issuing_authority__icontains=authority)
        
        # 标签筛选
        tag = self.request.query_params.get('tag')
        if tag:
            queryset = queryset.filter(tags__icontains=tag)
            
        return queryset.order_by('-publish_date')
    
    def retrieve(self, request, *args, **kwargs):
        """获取单个政策详情时增加浏览次数"""
        instance = self.get_object()
        
        # 使用通用函数处理浏览量增加
        from .utils import handle_view_count_increase
        handle_view_count_increase(instance, 'policy')
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def policy_types(self, request):
        """获取所有政策类型"""
        policy_types = Policy.objects.filter(is_active=True).values_list('policy_type', flat=True).distinct()
        type_choices = dict(Policy._meta.get_field('policy_type').choices)
        
        result = []
        for policy_type in policy_types:
            if policy_type in type_choices:
                result.append({
                    'value': policy_type,
                    'label': type_choices[policy_type]
                })
        
        return Response(result)
    
    @action(detail=False, methods=['get'])
    def issuing_authorities(self, request):
        """获取所有发布机构"""
        authorities = Policy.objects.filter(is_active=True).values_list('issuing_authority', flat=True).distinct()
        return Response(sorted(list(set(authorities))))
    
    @action(detail=False, methods=['get'])
    def tags(self, request):
        """获取所有标签"""
        all_tags = set()
        policies_with_tags = Policy.objects.filter(is_active=True, tags__isnull=False).exclude(tags='')
        
        for policy in policies_with_tags:
            if policy.tags:
                tags = [tag.strip() for tag in policy.tags.split(',') if tag.strip()]
                all_tags.update(tags)
        
        return Response(sorted(list(all_tags)))


# 旅游规划导出视图
class TravelPlanExportView(APIView):
    """旅游规划导出API"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """导出旅游规划"""
        from django.http import HttpResponse
        import csv
        from io import StringIO
        
        item_ids = request.data.get('item_ids', [])
        export_format = request.data.get('format', 'csv')
        
        if not item_ids or not isinstance(item_ids, list):
            return Response({'error': '无效的item_ids参数'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取对应的非遗项目
        heritage_items = Heritage.objects.filter(id__in=item_ids)
        
        if export_format == 'csv':
            # 创建CSV响应
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="非遗旅游规划.csv"'
            
            # 创建CSV写入器
            writer = csv.writer(response)
            
            # 写入CSV头
            writer.writerow(['序号', '名称', '类别', '地区'])
            
            # 写入数据行
            for i, item in enumerate(heritage_items, 1):
                writer.writerow([i, item.name, item.category, item.region])
            
            return response
        elif export_format == 'json':
            # 创建JSON响应
            items_data = []
            for item in heritage_items:
                items_data.append({
                    'id': item.id,
                    'name': item.name,
                    'category': item.category,
                    'region': item.region
                })
            
            return Response({
                'success': True,
                'data': items_data
            })
        else:
            return Response({'error': '不支持的导出格式'}, status=status.HTTP_400_BAD_REQUEST)
