"""
IP白名单中间件
限制只有特定IP地址可以访问管理后台
"""

from django.http import HttpResponseForbidden
from django.conf import settings

class IPWhitelistMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # 允许访问管理后台的IP地址列表（只有您的IP可以访问）
        self.allowed_ips = ['127.0.0.1', 'localhost']
        # 需要限制的路径（管理后台）
        self.restricted_paths = ['/admin/', '/admin']

    def __call__(self, request):
        # 检查是否访问受限路径
        if any(request.path.startswith(path) for path in self.restricted_paths):
            # 获取客户端真实IP
            client_ip = self.get_client_ip(request)
            
            # 检查IP是否在白名单中
            if client_ip not in self.allowed_ips:
                return HttpResponseForbidden(
                    "访问被阻止：您没有权限访问此页面。\n"
                    "请联系系统管理员获取访问权限。"
                )
        
        return self.get_response(request)

    def get_client_ip(self, request):
        """获取客户端真实IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
