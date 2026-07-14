"""Middleware package."""

from app.middleware.logging_middleware import register_middleware

__all__ = ["register_middleware"]
