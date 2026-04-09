"""
FarmIQ Auth Module
Handles FarmIQ ID authentication and FastAPI dependency injection

Modules:
- farmiq_id: FarmIQ ID validation and storage
- dependencies: FastAPI dependency injection for services
"""

from auth.farmiq_id import (
    FarmiqIdValidator,
    FarmiqIdStorage,
    FarmiqIdAudit,
)
from auth.dependencies import (
    get_farmiq_id_from_header,
    get_user_by_farmiq_id,
    get_user_context,
    get_embedding_service,
    get_llm_service,
    get_conversation_service,
    get_retrieval_service,
    get_ingestion_service,
)

__all__ = [
    # FarmIQ ID
    "FarmiqIdValidator",
    "FarmiqIdStorage",
    "FarmiqIdAudit",
    # Dependencies
    "get_farmiq_id_from_header",
    "get_user_by_farmiq_id",
    "get_user_context",
    "get_embedding_service",
    "get_llm_service",
    "get_conversation_service",
    "get_retrieval_service",
    "get_ingestion_service",
]
