"""Wraps Sentence Transformers for generating query and chunk embeddings."""

from sentence_transformers import SentenceTransformer

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SentenceTransformerEmbeddings:
    """Embeddings wrapper exposing embed_documents/embed_query, matching the
    interface langchain vectorstores (e.g. Chroma) expect."""

    def __init__(self, model_name: str | None = None):
        self._model_name = model_name or settings.embedding_model_name
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            logger.info("Loading embedding model: %s", self._model_name)
            self._model = SentenceTransformer(self._model_name)
        return self._model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        embedding = self.model.encode(text, convert_to_numpy=True, show_progress_bar=False)
        return embedding.tolist()

sentence_transformer_embeddings = SentenceTransformerEmbeddings()
