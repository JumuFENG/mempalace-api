"""Knowledge Graph routes - Entity relationship endpoints."""

from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from services.knowledge_graph import kg_service

router = APIRouter()


class KGAddRequest(BaseModel):
    subject: str
    predicate: str
    obj: str
    valid_from: Optional[str] = None


class KGAddResponse(BaseModel):
    success: bool
    message: str


@router.post("/add", response_model=KGAddResponse)
async def kg_add(request: KGAddRequest):
    success = kg_service.add_triple(
        subject=request.subject,
        predicate=request.predicate,
        obj=request.obj,
        valid_from=request.valid_from,
    )
    return KGAddResponse(
        success=success,
        message="Triple added successfully" if success else "Triple may already exist",
    )


class KGQueryRequest(BaseModel):
    entity: str
    direction: Optional[str] = "both"
    as_of: Optional[str] = None


class Triple(BaseModel):
    predicate: str
    object: str
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None
    direction: Optional[str] = None


class KGQueryResponse(BaseModel):
    entity: str
    triples: list[Triple]


@router.post("/query", response_model=KGQueryResponse)
async def kg_query(request: KGQueryRequest):
    result = kg_service.query_entity(
        name=request.entity,
        direction=request.direction or "both",
        as_of=request.as_of,
    )
    return KGQueryResponse(
        entity=result["entity"],
        triples=[Triple(**t) for t in result["triples"]],
    )


class KGInvalidateRequest(BaseModel):
    subject: str
    predicate: str
    obj: str
    ended: Optional[str] = None


class KGInvalidateResponse(BaseModel):
    success: bool
    message: str


@router.post("/invalidate", response_model=KGInvalidateResponse)
async def kg_invalidate(request: KGInvalidateRequest):
    success = kg_service.invalidate(
        subject=request.subject,
        predicate=request.predicate,
        obj=request.obj,
        ended=request.ended,
    )
    return KGInvalidateResponse(
        success=success,
        message="Fact invalidated" if success else "Fact not found",
    )


class TimelineEntry(BaseModel):
    subject: str
    predicate: str
    object: str
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None


class TimelineResponse(BaseModel):
    timeline: list[TimelineEntry]


@router.get("/timeline", response_model=TimelineResponse)
async def kg_timeline(entity: Optional[str] = Query(None)):
    entries = kg_service.timeline(entity_name=entity)
    return TimelineResponse(timeline=[TimelineEntry(**e) for e in entries])


class KGStatsResponse(BaseModel):
    entities: int
    triples: int
    current_facts: int
    predicates: list[str]


@router.get("/stats", response_model=KGStatsResponse)
async def kg_stats():
    stats = kg_service.stats()
    return KGStatsResponse(**stats)
