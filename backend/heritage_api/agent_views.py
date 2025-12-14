from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import os
from .encryption_utils import decrypt_agent_url

@api_view(['GET'])
@permission_classes([AllowAny])
def get_agent_service_url(request):
    """
    获取Agent服务地址
    为了安全考虑，Agent服务地址存储在服务器端，前端通过API获取
    支持加密的URL，提高安全性
    """
    try:
        # 优先从环境变量获取Agent服务地址
        agent_url = os.environ.get('AGENT_SERVICE_URL')
        
        # 如果环境变量没有设置，使用默认值
        if not agent_url:
            agent_url = 'http://localhost:8001'
        
        # 检查URL是否已加密（简单检测：是否包含非URL字符）
        # 如果URL看起来像加密的（不包含http://或https://），尝试解密
        if not agent_url.startswith(('http://', 'https://')):
            decrypted_url = decrypt_agent_url(agent_url)
            if decrypted_url:
                agent_url = decrypted_url
        
        return Response({
            'url': agent_url,
            'status': 'success'
        })
    except Exception as e:
        return Response({
            'error': '获取Agent服务地址失败',
            'status': 'error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)