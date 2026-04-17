"""Routers module initialization."""

from routers.search import router as search_router
from routers.store import router as store_router
from routers.knowledge import router as knowledge_router

__all__ = ["search_router", "store_router", "knowledge_router"]
