from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.permissions import AllowAny
from .views import HeritageViewSet, UserFavoriteViewSet, NewsViewSet, PolicyViewSet, TravelPlanExportView
from .views import UserCreationViewSet, CreationTagViewSet, CreationLikeViewSet, CreationCommentViewSet
from .views import CreationViewHistoryViewSet, CreationFavoriteViewSet, CreationShareViewSet, CreationReportViewSet
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from .map_config import get_map_config
from .auth_views import register_user, login_user, logout_user, get_user_info, get_csrf_token, request_password_reset, reset_password, get_security_status, generate_captcha_view, verify_captcha
from .user_views import UserProfileViewSet, UserAnalyticsView, UserStatsView
from .history_views import UserHistoryViewSet
from .agent_views import get_agent_service_url

router = DefaultRouter()
router.register(r'items', HeritageViewSet)
router.register(r'favorites', UserFavoriteViewSet, basename='userfavorite')
router.register(r'profile', UserProfileViewSet, basename='userprofile')
router.register(r'history', UserHistoryViewSet, basename='userhistory')
router.register(r'news', NewsViewSet, basename='news')
router.register(r'policies', PolicyViewSet, basename='policy')
router.register(r'creations', UserCreationViewSet, basename='creation')
router.register(r'creation-tags', CreationTagViewSet, basename='creationtag')
router.register(r'creation-likes', CreationLikeViewSet, basename='creationlike')
router.register(r'creation-comments', CreationCommentViewSet, basename='creationcomment')
router.register(r'creation-history', CreationViewHistoryViewSet, basename='creationhistory')
router.register(r'creation-favorites', CreationFavoriteViewSet, basename='creationfavorite')
router.register(r'creation-shares', CreationShareViewSet, basename='creationshare')
router.register(r'creation-reports', CreationReportViewSet, basename='creationreport')


# 添加静态文件服务
def serve_static_files(request, path):
    # 静态文件根目录
    return serve(request, path, document_root=settings.BASE_DIR / 'heritage_api' / 'static')

urlpatterns = [
    path('', include(router.urls)),
    # 添加静态文件URL
    path('static/<path:path>', serve_static_files),
    # 添加地图API路由
    path('map/config/', get_map_config, name='map-config'),
    
    # Agent服务地址API
    path('agent-service-url/', get_agent_service_url, name='agent-service-url'),
    
    # 用户认证相关路由
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
    
    # 用户分析和数据管理路由
    path('analytics/', UserAnalyticsView.as_view(), name='user-analytics'),
    path('export-data/', UserAnalyticsView.as_view(), name='export-user-data'),
    path('delete-account/', UserAnalyticsView.as_view(), name='delete-user-account'),
    path('clear-avatar/', UserAnalyticsView.as_view(), name='clear-avatar'),
    path('user/stats/', UserStatsView.as_view(), name='user-stats'),
    
    # 旅游规划导出路由
    path('travel-plan/export/', TravelPlanExportView.as_view(), name='travel-plan-export'),
    
    # 论坛相关路由
    path('forum/', include('heritage_api.forum_urls')),
]