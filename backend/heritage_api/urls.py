from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.permissions import AllowAny
from .api.heritage import HeritageViewSet, UserFavoriteViewSet, NewsViewSet, PolicyViewSet, TravelPlanExportView
from .api.heritage import UserCreationViewSet, CreationLikeViewSet, CreationCommentViewSet
from .api.heritage import CreationViewHistoryViewSet, CreationFavoriteViewSet
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from .map_config import get_map_config
from .api.auth import register_user, login_user, logout_user, get_user_info, get_csrf_token, request_password_reset, reset_password, get_security_status, generate_captcha_view, verify_captcha
from .api.user import UserProfileViewSet, UserAnalyticsView, UserStatsView
from .api.history import UserHistoryViewSet
from .api.agent import get_agent_service_url, proxy_agent_request

# 创建路由器并设置API根视图的中文描述
class ChineseDefaultRouter(DefaultRouter):
    """自定义路由器，提供中文API根视图描述"""
    
    def get_api_root_view(self, api_urls=None):
        """
        返回API根视图，使用中文描述
        """
        from rest_framework.views import APIView
        from rest_framework.response import Response
        
        class APIRoot(APIView):
            _ignore_model_permissions = True
            exclude_from_schema = True
            
            def get(self, request, *args, **kwargs):
                # 构建API根响应，包含中文描述
                ret = {}
                
                # 非遗相关
                ret['非遗项目'] = request.build_absolute_uri('items/')
                ret['用户收藏'] = request.build_absolute_uri('favorites/')
                ret['浏览历史'] = request.build_absolute_uri('history/')
                
                # 资讯政策
                ret['非遗资讯'] = request.build_absolute_uri('news/')
                ret['政策法规'] = request.build_absolute_uri('policies/')
                
                # 用户创作
                ret['用户创作'] = request.build_absolute_uri('creations/')
                ret['创作点赞'] = request.build_absolute_uri('creation-likes/')
                ret['创作评论'] = request.build_absolute_uri('creation-comments/')
                ret['创作历史'] = request.build_absolute_uri('creation-history/')
                ret['创作收藏'] = request.build_absolute_uri('creation-favorites/')
                
                # 用户相关
                ret['用户资料'] = request.build_absolute_uri('profile/')
                ret['用户统计'] = request.build_absolute_uri('user/stats/')
                
                # 认证相关
                ret['用户注册'] = request.build_absolute_uri('auth/register/')
                ret['用户登录'] = request.build_absolute_uri('auth/login/')
                ret['用户登出'] = request.build_absolute_uri('auth/logout/')
                ret['用户信息'] = request.build_absolute_uri('auth/user/')
                
                # 其他
                ret['地图配置'] = request.build_absolute_uri('map/config/')
                ret['论坛'] = request.build_absolute_uri('forum/')
                
                return Response(ret)
        
        return APIRoot.as_view()

router = ChineseDefaultRouter()

# 非遗相关
router.register(r'items', HeritageViewSet, basename='heritage')
router.register(r'favorites', UserFavoriteViewSet, basename='userfavorite')
router.register(r'history', UserHistoryViewSet, basename='userhistory')

# 资讯政策
router.register(r'news', NewsViewSet, basename='news')
router.register(r'policies', PolicyViewSet, basename='policy')

# 用户创作
router.register(r'creations', UserCreationViewSet, basename='creation')
router.register(r'creation-likes', CreationLikeViewSet, basename='creationlike')
router.register(r'creation-comments', CreationCommentViewSet, basename='creationcomment')
router.register(r'creation-history', CreationViewHistoryViewSet, basename='creationhistory')
router.register(r'creation-favorites', CreationFavoriteViewSet, basename='creationfavorite')

# 用户相关
router.register(r'profile', UserProfileViewSet, basename='userprofile')


# 添加静态文件服务
def serve_static_files(request, path):
    return serve(request, path, document_root=settings.BASE_DIR / 'heritage_api' / 'static')

urlpatterns = [
    path('', include(router.urls)),
    path('static/<path:path>', serve_static_files),
    path('map/config/', get_map_config, name='map-config'),
    
    path('agent-service-url/', get_agent_service_url, name='agent-service-url'),
    
    # Agent服务反向代理路由
    # 匹配 /api/agent/... 下的所有请求，转发给 Agent 服务
    path('agent/<path:path>', proxy_agent_request, name='agent-proxy'),
    
    # 认证相关
    path('auth/register/', register_user, name='register'),
    path('auth/login/', login_user, name='login'),
    path('auth/logout/', logout_user, name='logout'),
    path('auth/user/', get_user_info, name='user-info'),
    path('auth/csrf/', get_csrf_token, name='csrf-token'),
    path('auth/request-password-reset/', request_password_reset, name='request-password-reset'),
    path('auth/reset-password/', reset_password, name='reset-password'),
    path('auth/security-status/', get_security_status, name='security-status'),
    path('auth/captcha/generate/', generate_captcha_view, name='generate-captcha'),
    path('auth/captcha/verify/', verify_captcha, name='verify-captcha'),
    
    # 用户相关
    path('analytics/', UserAnalyticsView.as_view(), name='user-analytics'),
    path('export-data/', UserAnalyticsView.as_view(), name='export-user-data'),
    path('delete-account/', UserAnalyticsView.as_view(), name='delete-user-account'),
    path('clear-avatar/', UserAnalyticsView.as_view(), name='clear-avatar'),
    path('user/stats/', UserStatsView.as_view(), name='user-stats'),
    
    # 其他
    path('travel-plan/export/', TravelPlanExportView.as_view(), name='travel-plan-export'),
    
    path('forum/', include('heritage_api.forum_urls')),
]
