"""
Base Classes for Layered Architecture
Used across all modules
"""

from app.shared.base.entity import BaseEntity
from app.shared.base.service import BaseService
from app.shared.base.repository import BaseRepository

__all__ = [
    "BaseEntity",
    "BaseService",
    "BaseRepository",
]
