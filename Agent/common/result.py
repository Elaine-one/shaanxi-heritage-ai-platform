# -*- coding: utf-8 -*-
"""
统一结果类型
用于各层统一返回格式，支持链式调用
"""

from typing import Generic, TypeVar, Optional, Any, Callable
from dataclasses import dataclass
from functools import wraps

T = TypeVar('T')
E = TypeVar('E')


@dataclass
class Result(Generic[T]):
    """
    统一结果类型
    
    使用示例:
        result = Result.ok(data)
        result = Result.err("错误信息", "ERROR_CODE")
        
        if result.success:
            data = result.data
        else:
            error = result.error
    """
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    
    @classmethod
    def ok(cls, data: T = None) -> 'Result[T]':
        """创建成功结果"""
        return cls(success=True, data=data)
    
    @classmethod
    def err(cls, error: str, error_code: str = None) -> 'Result[T]':
        """创建失败结果"""
        return cls(success=False, error=error, error_code=error_code)
    
    def is_ok(self) -> bool:
        """判断是否成功"""
        return self.success
    
    def is_err(self) -> bool:
        """判断是否失败"""
        return not self.success
    
    def unwrap(self) -> T:
        """获取数据，失败时抛出异常"""
        if not self.success:
            raise ValueError(f"Result is error: {self.error}")
        return self.data
    
    def unwrap_or(self, default: T) -> T:
        """获取数据，失败时返回默认值"""
        return self.data if self.success else default
    
    def map(self, func: Callable[[T], Any]) -> 'Result':
        """映射成功结果"""
        if self.success:
            try:
                return Result.ok(func(self.data))
            except Exception as e:
                return Result.err(str(e))
        return self
    
    def and_then(self, func: Callable[[T], 'Result']) -> 'Result':
        """链式调用"""
        if self.success:
            return func(self.data)
        return self
    
    def to_dict(self) -> dict:
        """转换为字典"""
        if self.success:
            return {
                'success': True,
                'data': self.data
            }
        else:
            return {
                'success': False,
                'error': self.error,
                'error_code': self.error_code
            }


def Success(data: T = None) -> Result[T]:
    """创建成功结果的快捷函数"""
    return Result.ok(data)


def Failure(error: str, error_code: str = None) -> Result[T]:
    """创建失败结果的快捷函数"""
    return Result.err(error, error_code)


def result_handler(func):
    """
    装饰器：自动捕获异常并转换为 Result
    
    使用示例:
        @result_handler
        async def my_function():
            # 可能抛出异常的代码
            return data
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            result = await func(*args, **kwargs)
            if isinstance(result, Result):
                return result
            return Result.ok(result)
        except Exception as e:
            return Result.err(str(e))
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            if isinstance(result, Result):
                return result
            return Result.ok(result)
        except Exception as e:
            return Result.err(str(e))
    
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper
