# -*- coding: utf-8 -*-
"""
Django Session认证依赖项
支持Django的session认证机制
使用异步HTTP客户端提升性能
"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Request, Cookie
from loguru import logger
import httpx
from Agent.config.settings import Config

_async_client: Optional[httpx.AsyncClient] = None


async def get_async_client() -> httpx.AsyncClient:
    """获取全局异步 HTTP 客户端（连接池复用）"""
    global _async_client
    if _async_client is None:
        _async_client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)
        )
    return _async_client


async def close_async_client():
    """关闭异步 HTTP 客户端（应用关闭时调用）"""
    global _async_client
    if _async_client is not None:
        await _async_client.aclose()
        _async_client = None
        logger.info("异步HTTP客户端已关闭")


class TokenData:
    """用户token数据"""
    def __init__(self, user_id: str, username: str):
        self.user_id = user_id
        self.username = username


async def get_current_user_from_session(
    request: Request,
    sessionid: Optional[str] = Cookie(None)
) -> TokenData:
    """从Django session中获取当前认证用户（异步版本）"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="未登录或会话已过期",
        headers={"WWW-Authenticate": "Session"},
    )
    
    try:
        if not sessionid:
            logger.warning("未找到sessionid cookie")
            raise credentials_exception
        
        base_url = Config.BACKEND_API_URL.rstrip('/')
        django_api_url = f"{base_url}/profile/me/"
        
        try:
            client = await get_async_client()
            response = await client.get(
                django_api_url,
                cookies={"sessionid": sessionid}
            )
            
            logger.info(f"Django API响应状态: {response.status_code}")
            
            if response.status_code != 200:
                logger.warning(f"Django API返回状态码: {response.status_code}, 响应内容: {response.text[:200]}")
                raise credentials_exception
            
            user_data = response.json()
            user_id = user_data.get('id')
            username = user_data.get('username')
            
            if not user_id or not username:
                logger.warning(f"Django API返回的用户数据不完整: {user_data}")
                raise credentials_exception
        
        except httpx.ConnectError as e:
            logger.error(f"无法连接到Django API: {str(e)}")
            raise credentials_exception
        except httpx.TimeoutException as e:
            logger.error(f"Django API请求超时: {str(e)}")
            raise credentials_exception
        except httpx.HTTPStatusError as e:
            logger.error(f"Django API HTTP错误: {str(e)}")
            raise credentials_exception
        except Exception as e:
            logger.error(f"调用Django API时发生错误: {type(e).__name__}: {str(e)}")
            raise credentials_exception
        
        logger.info(f"Session认证成功: user_id={user_id}, username={username}")
        
        return TokenData(user_id=str(user_id), username=username)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session认证失败: {str(e)}")
        raise credentials_exception


async def get_current_user_optional_from_session(
    request: Request,
    sessionid: Optional[str] = Cookie(None)
) -> Optional[TokenData]:
    """从Django session中获取当前认证用户（可选）"""
    if not sessionid:
        return None
    
    try:
        return await get_current_user_from_session(request, sessionid)
    except HTTPException:
        return None


def require_auth_from_session(user: TokenData = Depends(get_current_user_from_session)) -> TokenData:
    """强制要求Django session认证的依赖项"""
    return user


def optional_auth_from_session(user: Optional[TokenData] = Depends(get_current_user_optional_from_session)) -> Optional[TokenData]:
    """可选Django session认证的依赖项"""
    return user
