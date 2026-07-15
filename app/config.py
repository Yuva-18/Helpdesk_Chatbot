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


settings = Settings()
