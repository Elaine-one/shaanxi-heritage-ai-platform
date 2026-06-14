"""URL configuration for heritage_project project."""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.http import JsonResponse, FileResponse, HttpResponseNotFound
import os


def health_check(request):
    """健康检查端点"""
    return JsonResponse({'status': 'healthy', 'service': 'heritage-app'})


def admin_spa_view(request, path=''):
    """Vue Admin SPA 文件服务"""
    admin_static_dir = settings.BASE_DIR / 'admin_static'
    if path and os.path.isfile(admin_static_dir / path):
        return FileResponse(open(admin_static_dir / path, 'rb'))
    index_path = admin_static_dir / 'index.html'
    if os.path.exists(index_path):
        return FileResponse(open(index_path, 'rb'))
    return JsonResponse({'error': 'Admin frontend not built'}, status=404)


def serve_frontend(request, path=''):
    """
    直接服务前端文件，模拟 nginx 的 root + try_files 行为：
      root /app/frontend;
      try_files $uri $uri/ /index.html;

    开发环境由 Django 处理，生产环境由 nginx 直接处理（此路由不会触发）。
    """
    frontend_dir = settings.FRONTEND_DIR

    if path:
        file_path = frontend_dir / path
        if os.path.isfile(file_path):
            return serve(request, path, document_root=frontend_dir)

    # 根路径或未匹配文件，回退到 index.html
    index_path = frontend_dir / 'index.html'
    if os.path.exists(index_path):
        return serve(request, 'index.html', document_root=frontend_dir)

    return HttpResponseNotFound('Frontend not found')


# API 和管理路由（优先匹配）
urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("heritage_api.urls")),
    path("health", health_check, name='health'),

    # Vue Admin SPA
    path("vue-admin/", admin_spa_view, name='admin-spa'),
    re_path(r'^vue-admin/(?P<path>.+)$', admin_spa_view, name='admin-spa-assets'),
]

# 开发环境：Django 静态文件和媒体文件服务
# 生产环境由 nginx 直接处理，不走 Django
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / 'static')

# 前端文件服务（放在最后，作为兜底）
# 模拟 nginx: root /app/frontend; try_files $uri /index.html;
urlpatterns += [
    re_path(r'^(?P<path>.+)$', serve_frontend, name='frontend-file'),
    path("", serve_frontend, name='index'),
]
