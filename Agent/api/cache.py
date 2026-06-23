# -*- coding: utf-8 -*-
"""Shared in-memory caches used across API modules."""
from cachetools import TTLCache

progress_callbacks = TTLCache(maxsize=1000, ttl=3600)
