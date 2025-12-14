from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([AllowAny])
def get_map_config(request):
    """
    获取地图配置信息，包括百度地图AK
    允许任何用户访问，因为地图功能是公开的
    """
    # 从Django设置中获取百度地图AK
    bmap_ak = settings.BAIDU_MAP_AK
    
    # 返回包含百度地图AK的JSON响应
    return Response({
        'bmap_ak': bmap_ak,
        'status': 'success'
    })