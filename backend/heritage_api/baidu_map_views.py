from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import os

@api_view(['GET'])
def get_baidu_map_ak(request):
    """
    获取百度地图AK密钥
    为了安全考虑，AK存储在服务器端，前端通过API获取
    """
    try:
        # 优先从环境变量获取AK
        ak = os.environ.get('BAIDU_MAP_AK')
        
        # 如果环境变量没有设置，从settings获取
        if not ak:
            ak = getattr(settings, 'BAIDU_MAP_AK', None)
        
        # 如果settings中也没有，返回空字符串
        if not ak:
            ak = ''
        
        return Response({
            'ak': ak,
            'status': 'success'
        })
    except Exception as e:
        return Response({
            'error': '获取百度地图AK失败',
            'status': 'error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)