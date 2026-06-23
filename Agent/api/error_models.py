# -*- coding: utf-8 -*-
"""Unified API error response models."""

from pydantic import BaseModel
from typing import Optional, Any


class ErrorDetail(BaseModel):
    code: str
    message: str


class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[ErrorDetail] = None


def error_response(status_code: int, detail: str) -> dict:
    """Build a unified error response dict.

    Code mapping mirrors HTTP semantics so frontend can switch on code
    instead of parsing status integers.
    """
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        422: "VALIDATION_ERROR",
        500: "INTERNAL_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
    }
    return {
        "success": False,
        "error": {
            "code": code_map.get(status_code, "ERROR"),
            "message": detail,
        },
        "detail": detail,  # backward compat — frontend reads errData.detail
    }
