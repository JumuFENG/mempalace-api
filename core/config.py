"""MemPalace HTTP API Configuration"""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="MP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # MemPalace data path
    palace_path: Path = Path.home() / ".mempalace"
    
    # ChromaDB settings
    chroma_collection_name: str = "mempalace_drawers"
    
    # API server settings
    api_host: str = "127.0.0.1"
    api_port: int = 8080
    api_reload: bool = False
    api_workers: int = 1
    
    # CORS settings
    cors_origins: list[str] = ["*"]  # Restrict in production
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]
    
    # API key authentication (optional)
    api_key: Optional[str] = None
    
    # Default search settings
    default_n_results: int = 5
    max_n_results: int = 50
    
    # Logging
    log_level: str = "INFO"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Expand ~ in palace_path
        self.palace_path = Path(os.path.expanduser(str(self.palace_path)))

    @property
    def palace_data_path(self) -> Path:
        """Get the palace data path (where ChromaDB and SQLite are stored)."""
        return self.palace_path / "data"

    @property
    def chroma_path(self) -> Path:
        """Get the ChromaDB data path."""
        return self.palace_data_path / "chroma"

    @property
    def kg_path(self) -> Path:
        """Get the knowledge graph SQLite path."""
        return self.palace_data_path / "knowledge_graph.sqlite3"


# Global settings instance
settings = Settings()
