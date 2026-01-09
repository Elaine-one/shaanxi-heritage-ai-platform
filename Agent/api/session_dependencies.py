# -*- coding: utf-8 -*-
"""
Django Session认证依赖项
支持Django的session认证机制
"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Request, Cookie
from loguru import logger
import sys
from pathlib import Path
import requests
import asyncio

class TokenData:
    """用户token数据"""
    def __init__(self, user_id: str, username: str):
        self.user_id = user_id
        self.username = username

async def get_current_user_from_session(
    request: Request,
    sessionid: Optional[str] = Cookie(None)
) -> TokenData:
    """
    从Django session中获取当前认证用户
    通过Django后端API验证session，避免跨端口cookie问题
    
    Args:
        request: FastAPI请求对象
        sessionid: Django session cookie
    
    Returns:
        TokenData: 当前用户的token数据
    
    Raises:
        HTTPException: 认证失败时抛出401异常
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="未登录或会话已过期",
        headers={"WWW-Authenticate": "Session"},
    )
    
    try:
        # 从cookie中获取sessionid
        if not sessionid:
            logger.warning("未找到sessionid cookie")
            raise credentials_exception
        
        # 通过Django后端API验证session
        django_api_url = "http://localhost:8000/api/profile/me/"
        
        try:
            # 在异步函数中调用同步的requests
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(
                    django_api_url,
                    cookies={"sessionid": sessionid},
                    timeout=10.0
                )
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
        
        except requests.ConnectionError as e:
            logger.error(f"无法连接到Django API: {str(e)}")
            raise credentials_exception
        except requests.Timeout as e:
            logger.error(f"Django API请求超时: {str(e)}")
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
    """
    从Django session中获取当前认证用户（可选）
    如果没有提供session或session无效，返回None而不是抛出异常
    
    Args:
        request: FastAPI请求对象
        sessionid: Django session cookie（可选）
    
    Returns:
        Optional[TokenData]: 当前用户的token数据，未认证返回None
    """
    if not sessionid:
        return None
    
    try:
        return await get_current_user_from_session(request, sessionid)
    except HTTPException:
        return None

def require_auth_from_session(user: TokenData = Depends(get_current_user_from_session)) -> TokenData:
    """
    强制要求Django session认证的依赖项
    
    Args:
        user: 当前用户
    
    Returns:
        TokenData: 当前用户
    
    Raises:
        HTTPException: 未认证时抛出401异常
    """
    return user

def optional_auth_from_session(user: Optional[TokenData] = Depends(get_current_user_optional_from_session)) -> Optional[TokenData]:
    """
    可选Django session认证的依赖项
    
    Args:
        user: 当前用户（可选）
    
    Returns:
        Optional[TokenData]: 当前用户，未认证返回None
    """
    return user