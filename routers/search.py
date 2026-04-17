"""Search routes - Semantic search and wake-up endpoints."""

from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from core.config import settings
from services.searcher import search_service

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    wing: Optional[str] = None
    room: Optional[str] = None
    n_results: Optional[int] = None


class SearchResult(BaseModel):
    id: str
    content: str
    score: float
    metadata: dict


class SearchResponse(BaseModel):
    results: list[SearchResult]
    total: int


@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    n_results = request.n_results or settings.default_n_results
    results = search_service.search(
        query=request.query,
        wing=request.wing,
        room=request.room,
        n_results=n_results,
    )
    return SearchResponse(
        results=[SearchResult(**r) for r in results],
        total=len(results),
    )


class WakeUpResponse(BaseModel):
    l0_identity: str
    l1_critical: str
    total_tokens: str
    wings: list[str]
    rooms: dict[str, list[str]]


@router.get("/wake-up", response_model=WakeUpResponse)
async def wake_up(wing: Optional[str] = Query(None)):
    status = search_service.get_status()
    wings = status.get("wings", [])
    rooms = {}

    if wing:
        wings_to_show = [wing] if wing in wings else []
    else:
        wings_to_show = wings

    for w in wings_to_show:
        room_query = search_service.search(
            query="*",
            wing=w,
            n_results=1000,
        )
        unique_rooms = set()
        for r in room_query:
            if r.get("metadata", {}).get("room"):
                unique_rooms.add(r["metadata"]["room"])
        rooms[w] = sorted(list(unique_rooms))

    return WakeUpResponse(
        l0_identity="MemPalace Memory System",
        l1_critical=f"Wings: {', '.join(wings_to_show) if wings_to_show else 'No wings configured'}",
        total_tokens="~170 tokens",
        wings=wings_to_show,
        rooms=rooms,
    )


class StatusResponse(BaseModel):
    palace_path: str
    collection_name: str
    total_drawers: int
    wings: list[str]
    rooms: list[str]
    knowledge_graph: dict


@router.get("/status", response_model=StatusResponse)
async def status():
    from services.knowledge_graph import kg_service

    search_status = search_service.get_status()
    kg_stats = kg_service.stats()

    return StatusResponse(
        palace_path=str(settings.palace_path),
        collection_name=settings.chroma_collection_name,
        total_drawers=search_status["total_drawers"],
        wings=search_status["wings"],
        rooms=search_status["rooms"],
        knowledge_graph=kg_stats,
    )
