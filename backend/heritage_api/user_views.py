from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Sum
from .user_models import UserProfile
from .user_serializers import UserSerializer, UserProfileSerializer
from .creation_models import UserCreation, CreationLike, CreationComment, CreationViewHistory
from .models import UserFavorite, UserHistory
import zipfile
import io
from django.http import HttpResponse
import json

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # 用户只能访问自己的资料
        return User.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """获取当前登录用户的详细信息，包括头像"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """更新当前登录用户的资料"""
        user = request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='upload-avatar')
    def upload_avatar(self, request):
        """上传用户头像"""
        if 'avatar' not in request.FILES:
            return Response({'error': '没有提供头像文件'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        profile = user.profile
        
        # 删除旧头像（如果存在）
        if profile.avatar:
            profile.avatar.delete(save=False)
        
        # 保存新头像
        profile.avatar = request.FILES['avatar']
        profile.save()
        
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='clear-avatar')
    def clear_avatar(self, request):
        """清除用户头像（设置为默认头像）"""
        user = request.user
        profile = user.profile
        
        # 删除现有头像文件（如果存在）
        if profile.avatar:
            profile.avatar.delete(save=False)
        
        # 清空头像字段
        profile.avatar = None
        profile.save()
        
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)


class UserAnalyticsView(APIView):
    """用户分析和数据管理视图"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """获取用户创作分析数据"""
        try:
            user = request.user
            range_param = request.query_params.get('range', '7')  # 现在前端传递的是数字天数
            
            # 将range_param转换为整数
            try:
                days = int(range_param)
            except ValueError:
                days = 7
                
            # 根据天数确定日期
            start_date = timezone.now().date() - timedelta(days=days)
            
            # 获取用户的创作
            user_creations = UserCreation.objects.filter(user=user, created_at__date__gte=start_date)
            
            # 浏览趋势数据
            views_data = []
            views_labels = []
            current_date = start_date
            while current_date <= timezone.now().date():
                day_creations = user_creations.filter(created_at__date=current_date)
                day_views = CreationViewHistory.objects.filter(
                    creation__in=day_creations,
                    viewed_at__date=current_date
                ).count()
                
                views_labels.append(current_date.strftime('%m-%d'))
                views_data.append(day_views)
                current_date += timedelta(days=1)
            
            # 创作类型分布
            type_stats = user_creations.values('type').annotate(count=Count('id'))
            type_labels = []
            type_data = []
            type_choices = dict(UserCreation._meta.get_field('type').choices)
            
            for stat in type_stats:
                type_labels.append(type_choices.get(stat['type'], stat['type']))
                type_data.append(stat['count'])
            
            # 热门创作
            top_creations = user_creations.annotate(
                views_count=Count('view_history'),
                likes_count=Count('likes'),
                comments_count=Count('comments')
            ).order_by('-views_count')[:5]
            
            top_creations_data = [{
                'title': creation.title,
                'views': creation.views_count,
                'likes': creation.likes_count,
                'comments': creation.comments_count
            } for creation in top_creations]
            
            # 互动统计
            total_likes = CreationLike.objects.filter(creation__user=user).count()
            total_comments = CreationComment.objects.filter(creation__user=user).count()
            total_shares = CreationViewHistory.objects.filter(creation__user=user).count()
            
            analytics_data = {
                'views': {
                    'labels': views_labels,
                    'data': views_data
                },
                'types': {
                    'labels': type_labels,
                    'data': type_data
                },
                'top_creations': top_creations_data,
                'interactions': {
                    'likes': total_likes,
                    'comments': total_comments,
                    'shares': total_shares
                }
            }
            
            return Response(analytics_data)
            
        except Exception as e:
            return Response({'error': f'获取分析数据失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """导出用户数据"""
        try:
            user = request.user
            
            # 创建内存中的zip文件
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # 用户基本信息
                user_data = {
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'date_joined': user.date_joined.isoformat(),
                    'last_login': user.last_login.isoformat() if user.last_login else None
                }
                
                # 用户创作
                creations = UserCreation.objects.filter(user=user)
                creations_data = []
                for creation in creations:
                    creation_dict = {
                        'id': creation.id,
                        'title': creation.title,
                        'description': creation.description,
                        'type': creation.type,
                        'status': creation.status,
                        'created_at': creation.created_at.isoformat(),
                        'updated_at': creation.updated_at.isoformat(),
                        'file_url': creation.file.url if creation.file else None,
                        'cover_image_url': creation.cover_image.url if creation.cover_image else None
                    }
                    creations_data.append(creation_dict)
                
                # 用户收藏
                favorites = UserFavorite.objects.filter(user=user)
                favorites_data = []
                for favorite in favorites:
                    favorite_dict = {
                        'heritage_id': favorite.heritage.id,
                        'heritage_name': favorite.heritage.name,
                        'created_at': favorite.created_at.isoformat()
                    }
                    favorites_data.append(favorite_dict)
                
                # 浏览历史
                history = UserHistory.objects.filter(user=user)
                history_data = []
                for record in history:
                    history_dict = {
                        'heritage_id': record.heritage.id,
                        'heritage_name': record.heritage.name,
                        'visit_time': record.visit_time.isoformat()
                    }
                    history_data.append(history_dict)
                
                # 创作互动
                likes = CreationLike.objects.filter(user=user)
                likes_data = [{'creation_id': like.creation.id, 'created_at': like.created_at.isoformat()} for like in likes]
                
                comments = CreationComment.objects.filter(user=user)
                comments_data = []
                for comment in comments:
                    comment_dict = {
                        'creation_id': comment.creation.id,
                        'content': comment.content,
                        'created_at': comment.created_at.isoformat(),
                        'like_count': comment.like_count
                    }
                    comments_data.append(comment_dict)
                
                # 将所有数据写入zip文件
                export_data = {
                    'user_info': user_data,
                    'creations': creations_data,
                    'favorites': favorites_data,
                    'history': history_data,
                    'likes': likes_data,
                    'comments': comments_data
                }
                
                zip_file.writestr('user_data.json', json.dumps(export_data, ensure_ascii=False, indent=2))
                
                # 添加创作的文件和封面图片
                for creation in creations:
                    if creation.file:
                        try:
                            file_content = creation.file.read()
                            zip_file.writestr(f'creations/files/{creation.id}_{creation.file.name}', file_content)
                        except Exception as e:
                            print(f"Error reading file for creation {creation.id}: {e}")
                    
                    if creation.cover_image:
                        try:
                            image_content = creation.cover_image.read()
                            zip_file.writestr(f'creations/images/{creation.id}_{creation.cover_image.name}', image_content)
                        except Exception as e:
                            print(f"Error reading cover image for creation {creation.id}: {e}")
            
            # 准备响应
            zip_buffer.seek(0)
            response = HttpResponse(zip_buffer.read(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="user_data_{user.username}_{timezone.now().strftime("%Y%m%d")}.zip"'
            
            return response
            
        except Exception as e:
            return Response({'error': f'导出数据失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request):
        """删除用户账户"""
        try:
            user = request.user
            
            # 删除用户的创作文件和封面图片
            creations = UserCreation.objects.filter(user=user)
            for creation in creations:
                if creation.file:
                    try:
                        creation.file.delete(save=False)
                    except Exception as e:
                        print(f"Error deleting file for creation {creation.id}: {e}")
                
                if creation.cover_image:
                    try:
                        creation.cover_image.delete(save=False)
                    except Exception as e:
                        print(f"Error deleting cover image for creation {creation.id}: {e}")
            
            # 删除用户头像
            if hasattr(user, 'profile') and user.profile.avatar:
                try:
                    user.profile.avatar.delete(save=False)
                except Exception as e:
                    print(f"Error deleting user avatar: {e}")
            
            # 删除用户数据（这将级联删除所有相关数据）
            user.delete()
            
            return Response({'message': '账户删除成功'})
            
        except Exception as e:
            return Response({'error': f'删除账户失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 添加用户统计数据视图
class UserStatsView(APIView):
    """获取用户统计数据"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """获取用户统计数据"""
        user = request.user
        
        # 计算收藏数量
        favorites_count = UserFavorite.objects.filter(user=user).count()
        
        # 计算访问历史数量
        visits_count = UserHistory.objects.filter(user=user).count()
        
        # 计算评论数量
        comments_count = CreationComment.objects.filter(user=user).count()
        
        # 计算关注数量（需要实现关注模型）
        following_count = 0
        followers_count = 0
        
        # 尝试从forum_models获取关注模型
        try:
            from .forum_models import UserFollow
            following_count = UserFollow.objects.filter(follower=user).count()
            followers_count = UserFollow.objects.filter(following=user).count()
        except ImportError:
            # 如果关注模型不存在，使用默认值
            pass
        
        return Response({
            'favorites_count': favorites_count,
            'visits_count': visits_count,
            'comments_count': comments_count,
            'following_count': following_count,
            'followers_count': followers_count
        })