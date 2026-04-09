"""
FarmIQ Config Module
Consolidated configuration management for the backend

Modules:
- settings: Environment and application settings
- models: LLM model configurations

Environment Support:
- development: Local development
- staging: Staging environment
- production: Production environment
"""

from config.settings import Settings, settings
from config.models import (
    ModelConfig,
    ModelSelector,
    TEXT_MODELS,
    EMBEDDING_MODEL,
    OCR_MODEL,
    DEFAULT_TEXT_MODEL,
    EMBEDDING_MODEL_NAME,
    OCR_MODEL_NAME,
)

__all__ = [
    # Settings
    "Settings",
    "settings",
    # Models
    "ModelConfig",
    "ModelSelector",
    "TEXT_MODELS",
    "EMBEDDING_MODEL",
    "OCR_MODEL",
    "DEFAULT_TEXT_MODEL",
    "EMBEDDING_MODEL_NAME",
    "OCR_MODEL_NAME",
]
