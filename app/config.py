"""Loads settings (paths, ports, thresholds) from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    host: str
    port: int

    llama_server_url: str

    chroma_persist_dir: str

    embedding_model_name: str

    top_k: int
    confidence_threshold: float

    eservices_support_email: str
    network_support_email: str
    hpce_support_email: str

    cors_allowed_origins: str = ""

    @property
    def cors_origins(self) -> list[str]:
        """Comma-separated CORS_ALLOWED_ORIGINS env var, parsed into a list.
        Empty by default — the frontend is served same-origin (app/main.py)
        and needs no CORS; only set this for a separate, external consumer."""
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    @property
    def support_email_by_category(self) -> dict[str, str]:
        """Category -> fallback support email. Add a new category by adding
        one field above plus one entry here."""
        return {
            "Eservices": self.eservices_support_email,
            "Network": self.network_support_email,
            "Hpce": self.hpce_support_email,
        }


settings = Settings()

# Shared ChromaDB collection name — must stay identical between scripts/ingest.py
# (which writes it) and app/core/retriever.py (which reads it).
COLLECTION_NAME = "helpdesk_kb"
