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
