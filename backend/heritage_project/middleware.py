"""
IP白名单中间件
限制只有特定IP地址可以访问管理后台
"""
import os
import logging

logger = logging.getLogger(__name__)


class IPWhitelistMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed_ips = os.getenv('ADMIN_ALLOWED_IPS', '127.0.0.1,::1').split(',')
        self.allowed_ips = [ip.strip() for ip in self.allowed_ips if ip.strip()]
        self.restricted_paths = ['/admin/', '/admin']
        self.debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'

    def __call__(self, request):
        if any(request.path.startswith(path) for path in self.restricted_paths):
            client_ip = self.get_client_ip(request)
            
            if client_ip not in self.allowed_ips:
                logger.warning(f"Admin access denied for IP: {client_ip}")
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden(
                    "<h1>403 Forbidden</h1>"
                    "<p>您没有权限访问此页面。</p>"
                    "<p>如需访问管理后台，请联系系统管理员。</p>"
                )
        
        return self.get_response(request)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip
