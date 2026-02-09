import os
import logging
import httpx
import traceback
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

# 获取Agent服务地址，默认为 localhost:8001
AGENT_SERVICE_URL = os.environ.get('AGENT_SERVICE_URL')

# 强制要求必须配置 AGENT_SERVICE_URL
if not AGENT_SERVICE_URL:
    logger.error("AGENT_SERVICE_URL environment variable is not set!")
    raise ValueError("AGENT_SERVICE_URL environment variable is not set!")

# 最终检查
if not AGENT_SERVICE_URL.startswith('http'):
    logger.error(f"Invalid AGENT_SERVICE_URL: {AGENT_SERVICE_URL}")
    raise ValueError(f"Invalid AGENT_SERVICE_URL: {AGENT_SERVICE_URL}")


# 修复 SSL_CERT_FILE 环境变量指向不存在文件导致的问题
if 'SSL_CERT_FILE' in os.environ:
    ssl_cert_file = os.environ['SSL_CERT_FILE']
    if not os.path.exists(ssl_cert_file):
        logger.warning(f"Removing invalid SSL_CERT_FILE environment variable: {ssl_cert_file}")
        del os.environ['SSL_CERT_FILE']


@api_view(['GET'])
@permission_classes([AllowAny])
def get_agent_service_url(request):
    """
    获取Agent服务地址
    """
    try:
        # 优先从环境变量获取Agent服务地址
        agent_url = os.environ.get('AGENT_SERVICE_URL')
        
        if not agent_url:
             return Response({
                'error': 'Agent服务地址未配置',
                'status': 'error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'url': agent_url,
            'status': 'success'
        })
    except Exception as e:
        return Response({
            'error': '获取Agent服务地址失败',
            'status': 'error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
def proxy_agent_request(request, path):
    """
    代理转发请求到 Agent 服务 (同步版本，避免 WSGI/Async 兼容性问题)
    
    Args:
        request: Django 请求对象
        path: 转发路径
    """
    # 构建目标 URL
    # 确保 AGENT_SERVICE_URL 不以 / 结尾，path 不以 / 开头（或者处理好拼接）
    base_url = AGENT_SERVICE_URL.rstrip('/')
    target_url = f"{base_url}/{path}"
    
    # 获取查询参数
    params = request.GET.dict()
    
    # 获取请求头
    headers = {}
    for key, value in request.headers.items():
        # 排除一些不应该转发的头
        if key.lower() not in ['host', 'content-length', 'connection']:
            headers[key] = value
            
    # 添加内部标识头（可选）
    headers['X-Forwarded-For-Proxy'] = 'Django-Backend'

    # 获取请求体
    try:
        content = request.body
    except Exception:
        content = b""
    
    method = request.method
    
    logger.info(f"Proxying {method} request to: {target_url}")

    try:
        # 使用同步 Client，关闭 SSL 验证（内网 HTTP 通信）
        # PDF 生成和上传可能非常耗时，增加超时时间到 300 秒
        with httpx.Client(timeout=300.0, verify=False) as client:
            response = client.request(
                method=method,
                url=target_url,
                params=params,
                content=content,
                headers=headers
            )
            
            # 创建 Django 响应
            # 如果是流式响应（如导出文件），可能需要特殊处理，这里先处理普通响应
            django_response = HttpResponse(
                content=response.content,
                status=response.status_code
            )
            
            # 转发响应头
            for key, value in response.headers.items():
                if key.lower() not in ['content-length', 'content-encoding', 'transfer-encoding', 'connection']:
                    django_response[key] = value
                    
            return django_response
            
    except httpx.RequestError as e:
        logger.error(f"Proxy request failed: {str(e)}\n{traceback.format_exc()}")
        return JsonResponse({
            'error': 'Agent Service Unavailable',
            'details': str(e)
        }, status=503)
    except Exception as e:
        logger.error(f"Proxy internal error: {str(e)}\n{traceback.format_exc()}")
        return JsonResponse({
            'error': 'Internal Proxy Error',
            'details': str(e)
        }, status=500)
