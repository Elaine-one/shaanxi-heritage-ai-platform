# -*- coding: utf-8 -*-
"""
业务异常定义
统一的异常层次结构
"""

from typing import Any


class AgentException(Exception):
    """Agent 基础异常"""
    
    def __init__(self, message: str, code: str = None, details: Any = None):
        self.message = message
        self.code = code or "AGENT_ERROR"
        self.details = details
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        return {
            'success': False,
            'error': self.message,
            'error_code': self.code,
            'details': self.details
        }


class ToolExecutionError(AgentException):
    """工具执行错误"""
    
    def __init__(self, tool_name: str, message: str, details: Any = None):
        self.tool_name = tool_name
        super().__init__(
            message=f"工具 '{tool_name}' 执行失败: {message}",
            code="TOOL_EXECUTION_ERROR",
            details=details
        )


class LLMError(AgentException):
    """LLM 调用错误"""
    
    def __init__(self, message: str, provider: str = None, model: str = None):
        self.provider = provider
        self.model = model
        super().__init__(
            message=message,
            code="LLM_ERROR",
            details={'provider': provider, 'model': model}
        )


class SessionNotFoundError(AgentException):
    """会话不存在错误"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        super().__init__(
            message=f"会话 '{session_id}' 不存在或已过期",
            code="SESSION_NOT_FOUND"
        )


class ConfigurationError(AgentException):
    """配置错误"""
    
    def __init__(self, config_key: str, message: str):
        self.config_key = config_key
        super().__init__(
            message=f"配置 '{config_key}' 错误: {message}",
            code="CONFIGURATION_ERROR"
        )


class ValidationError(AgentException):
    """验证错误"""
    
    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(
            message=f"字段 '{field}' 验证失败: {message}",
            code="VALIDATION_ERROR"
        )


class ResourceNotFoundError(AgentException):
    """资源不存在错误"""
    
    def __init__(self, resource_type: str, resource_id: Any):
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(
            message=f"{resource_type} '{resource_id}' 不存在",
            code="RESOURCE_NOT_FOUND"
        )


class RateLimitError(AgentException):
    """速率限制错误"""
    
    def __init__(self, service: str, retry_after: int = None):
        self.service = service
        self.retry_after = retry_after
        super().__init__(
            message=f"服务 '{service}' 请求频率超限，请稍后重试",
            code="RATE_LIMIT_ERROR",
            details={'retry_after': retry_after}
        )


class ExternalServiceError(AgentException):
    """外部服务错误"""
    
    def __init__(self, service: str, message: str, status_code: int = None):
        self.service = service
        self.status_code = status_code
        super().__init__(
            message=f"外部服务 '{service}' 错误: {message}",
            code="EXTERNAL_SERVICE_ERROR",
            details={'service': service, 'status_code': status_code}
        )
