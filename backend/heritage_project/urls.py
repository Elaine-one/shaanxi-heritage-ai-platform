"""URL configuration for heritage_project project."""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.shortcuts import redirect

# API 路由
# API 路由

# 兼容旧版本的zybTrackerStatisticsAction请求
from django.http import JsonResponse

def handle_zyb_tracker(request):
    """处理旧版本的zybTrackerStatisticsAction请求，返回成功响应"""
    return JsonResponse({'success': True, 'message': '统计数据已处理'})

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("heritage_api.urls")),
    # 添加兼容路由，处理旧版本的zybTrackerStatisticsAction请求
    path("hybridaction/zybTrackerStatisticsAction", handle_zyb_tracker, name='zyb-tracker'),
    # 添加根路径指向 index.html
    path("", TemplateView.as_view(template_name='index.html'), name='index'),
    # 添加其他前端页面的路由
    path("index.html", TemplateView.as_view(template_name='index.html'), name='index-html'),
    path("pages/non-heritage-list.html", TemplateView.as_view(template_name='pages/non-heritage-list.html'), name='non-heritage-list'),
    path("pages/heritage-map.html", TemplateView.as_view(template_name='pages/heritage-map.html'), name='heritage-map'),
    path("pages/heritage-detail.html", TemplateView.as_view(template_name='pages/heritage-detail.html'), name='heritage-detail'),
    path("pages/login.html", TemplateView.as_view(template_name='pages/login.html'), name='login'),
    path("pages/register.html", TemplateView.as_view(template_name='pages/register.html'), name='register'),
    path("pages/profile.html", TemplateView.as_view(template_name='pages/profile.html'), name='profile'),
    path("pages/forum.html", TemplateView.as_view(template_name='pages/forum.html'), name='forum'),
    path("pages/forum-post.html", TemplateView.as_view(template_name='pages/forum-post.html'), name='forum-post'),
    path("pages/post-detail.html", TemplateView.as_view(template_name='pages/post-detail.html'), name='post-detail'),
    path("pages/policy.html", TemplateView.as_view(template_name='pages/policy.html'), name='policy'),
    path("pages/news.html", TemplateView.as_view(template_name='pages/news.html'), name='news'),
    path("pages/creation-center.html", TemplateView.as_view(template_name='pages/creation-center.html'), name='creation-center'),
    path("pages/user-creation.html", TemplateView.as_view(template_name='pages/user-creation.html'), name='user-creation'),
    path("pages/forgot-password.html", TemplateView.as_view(template_name='pages/forgot-password.html'), name='forgot-password'),
    path("pages/reset-password.html", TemplateView.as_view(template_name='pages/reset-password.html'), name='reset-password'),
    # 添加论坛页面路由
    path("forum", TemplateView.as_view(template_name='pages/forum.html'), name='forum'),
    path("forum/", TemplateView.as_view(template_name='pages/forum.html'), name='forum-slash'),
    path("forum/post/<int:post_id>", TemplateView.as_view(template_name='pages/forum-post-detail.html'), name='forum-post-detail'),
]

# 开发环境下提供媒体文件和静态文件访问
if settings.DEBUG:
    # 开发环境下提供媒体文件访问
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # 开发环境下提供静态文件访问
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR.parent / 'frontend')
    # 添加根路径映射以支持直接访问前端文件
    urlpatterns += static('/', document_root=settings.BASE_DIR.parent / 'frontend')
