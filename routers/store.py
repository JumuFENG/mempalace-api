"""Store routes - Memory storage endpoints."""

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from services.storage import storage_service

router = APIRouter()


class StoreRequest(BaseModel):
    content: str
    wing: str
    room: str
    hall: Optional[str] = None
    metadata: Optional[dict] = None


class StoreResponse(BaseModel):
    id: str
    message: str


@router.post("/store", response_model=StoreResponse, status_code=201)
async def store(request: StoreRequest):
    drawer_id = storage_service.store(
        content=request.content,
        wing=request.wing,
        room=request.room,
        hall=request.hall,
        metadata=request.metadata,
    )
    return StoreResponse(id=drawer_id, message="Memory stored successfully")


class MessageItem(BaseModel):
    role: str
    content: str


class StoreConversationRequest(BaseModel):
    wing: str
    room: str
    messages: list[MessageItem]
    session_id: Optional[str] = None
    metadata: Optional[dict] = None


class StoreConversationResponse(BaseModel):
    stored_count: int
    drawer_ids: list[str]


@router.post("/store/conversation", response_model=StoreConversationResponse, status_code=201)
async def store_conversation(request: StoreConversationRequest):
    message_dicts = [msg.model_dump() for msg in request.messages]
    drawer_ids = storage_service.store_conversation(
        messages=message_dicts,
        wing=request.wing,
        room=request.room,
        session_id=request.session_id,
        metadata=request.metadata,
    )
    return StoreConversationResponse(
        stored_count=len(drawer_ids),
        drawer_ids=drawer_ids,
    )


class DeleteRequest(BaseModel):
    drawer_id: str


class DeleteResponse(BaseModel):
    success: bool
    message: str


@router.delete("/store/{drawer_id}", response_model=DeleteResponse)
async def delete_drawer(drawer_id: str):
    success = storage_service.delete(drawer_id)
    return DeleteResponse(
        success=success,
        message="Memory deleted" if success else "Memory not found",
    )
