"""Search service - Semantic search via ChromaDB."""

import hashlib
import json
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from core.config import settings


class SearchService:
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

    def search(
        self,
        query: str,
        wing: Optional[str] = None,
        room: Optional[str] = None,
        n_results: int = 5,
    ) -> list[dict]:
        n_results = min(n_results, settings.max_n_results)
        collection = self._get_collection()

        where_filter = {}
        if wing:
            where_filter["wing"] = wing
        if room:
            where_filter["room"] = room

        if where_filter:
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter,
            )
        else:
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
            )

        search_results = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                search_results.append({
                    "id": doc_id,
                    "content": results["documents"][0][i] if results["documents"] else "",
                    "score": results["distances"][0][i] if results["distances"] else 0.0,
                    "metadata": metadata,
                })

        return search_results

    def get_by_id(self, drawer_id: str) -> Optional[dict]:
        collection = self._get_collection()
        try:
            result = collection.get(ids=[drawer_id])
            if result["ids"]:
                return {
                    "id": result["ids"][0],
                    "content": result["documents"][0] if result["documents"] else "",
                    "metadata": result["metadatas"][0] if result["metadatas"] else {},
                }
        except Exception:
            pass
        return None

    def get_status(self) -> dict:
        collection = self._get_collection()
        count = collection.count()

        wings = set()
        rooms = set()
        try:
            all_data = collection.get(limit=1000)
            for metadata in (all_data.get("metadatas") or []):
                if metadata:
                    if "wing" in metadata:
                        wings.add(metadata["wing"])
                    if "room" in metadata:
                        rooms.add(metadata["room"])
        except Exception:
            pass

        return {
            "collection_name": self.collection_name,
            "total_drawers": count,
            "wings": list(wings),
            "rooms": list(rooms),
        }


search_service = SearchService()
