"""Storage service - Store memories in ChromaDB."""

import hashlib
import json
import uuid
from datetime import datetime
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from core.config import settings


class StorageService:
    def __init__(self):
        self.palace_path = str(settings.palace_path)
        self.collection_name = settings.chroma_collection_name
        self._client: Optional[chromadb.PersistentClient] = None
        self._collection = None

    def _get_client(self) -> chromadb.PersistentClient:
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=str(settings.chroma_path),
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                )
            )
        return self._client

    def _get_collection(self):
        if self._collection is None:
            client = self._get_client()
            try:
                self._collection = client.get_collection(name=self.collection_name)
            except Exception:
                self._collection = client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "MemPalace drawers collection"}
                )
        return self._collection

    def _generate_id(self, content: str, wing: str, room: str) -> str:
        raw = f"{wing}:{room}:{content[:100]}"
        return f"drawer_{hashlib.sha256(raw.encode()).hexdigest()[:16]}"

    def store(
        self,
        content: str,
        wing: str,
        room: str,
        hall: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        collection = self._get_collection()
        drawer_id = self._generate_id(content, wing, room)

        doc_metadata = {
            "wing": wing,
            "room": room,
            "created_at": datetime.utcnow().isoformat(),
        }
        if hall:
            doc_metadata["hall"] = hall
        if metadata:
            doc_metadata.update(metadata)

        try:
            collection.add(
                documents=[content],
                ids=[drawer_id],
                metadatas=[doc_metadata],
            )
        except Exception:
            collection.update(
                documents=[content],
                ids=[drawer_id],
                metadatas=[doc_metadata],
            )

        return drawer_id

    def store_conversation(
        self,
        messages: list[dict],
        wing: str,
        room: str,
        session_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> list[str]:
        drawer_ids = []
        for idx, msg in enumerate(messages):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if not content:
                continue

            formatted_content = f"[{role.upper()}] {content}"

            msg_metadata = {
                "session_id": session_id or "default",
                "turn_index": idx,
                "type": "message",
            }
            if metadata:
                msg_metadata.update(metadata)

            drawer_id = self.store(
                content=formatted_content,
                wing=wing,
                room=room,
                hall="hall_events",
                metadata=msg_metadata,
            )
            drawer_ids.append(drawer_id)

        return drawer_ids

    def delete(self, drawer_id: str) -> bool:
        collection = self._get_collection()
        try:
            collection.delete(ids=[drawer_id])
            return True
        except Exception:
            return False

    def count(self) -> int:
        collection = self._get_collection()
        return collection.count()


storage_service = StorageService()
