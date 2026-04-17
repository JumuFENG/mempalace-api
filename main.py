"""MemPalace HTTP API - Main entry point."""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from routers import search_router, store_router, knowledge_router

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting MemPalace API on {settings.api_host}:{settings.api_port}")
    logger.info(f"Palace path: {settings.palace_path}")
    yield
    logger.info("Shutting down MemPalace API")


app = FastAPI(
    title="MemPalace HTTP API",
    description="HTTP REST API wrapper for MemPalace memory system",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

app.include_router(search_router, prefix="/api/mempalace")
app.include_router(store_router, prefix="/api/mempalace")
app.include_router(knowledge_router, prefix="/api/mempalace/kg")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "mempalace-api"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        workers=settings.api_workers,
    )
