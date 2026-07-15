"""Handles similarity search against ChromaDB and returns top-k chunks."""

from dataclasses import dataclass

from langchain_community.vectorstores import Chroma

from app.config import COLLECTION_NAME, settings
from app.core.embeddings import sentence_transformer_embeddings
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RetrievedRule:
    """One knowledge base rule matched against a user query, with its relevance score."""

    rule_id: str
    category: str
    question: str
    answer: str
    support_email: str
    source_url: str
    keywords: str
    score: float


class Retriever:
    def __init__(self):
        self._vectorstore = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=sentence_transformer_embeddings,
            persist_directory=settings.chroma_persist_dir,
        )

    def retrieve(self, query: str, k: int | None = None) -> list[RetrievedRule]:
        """Embeds the query and returns the k closest knowledge base rules,
        ranked by relevance score (higher is more relevant)."""
        top_k = k or settings.top_k
        results = self._vectorstore.similarity_search_with_relevance_scores(query, k=top_k)

        rules = [
            RetrievedRule(
                rule_id=doc.metadata["rule_id"],
                category=doc.metadata["category"],
                question=doc.page_content,
                answer=doc.metadata["answer"],
                support_email=doc.metadata["support_email"],
                source_url=doc.metadata["source_url"],
                keywords=doc.metadata["keywords"],
                score=score,
            )
            for doc, score in results
        ]

        logger.info(
            "Retrieved %d rule(s) for query %r (top score=%.3f)",
            len(rules),
            query,
            rules[0].score if rules else 0.0,
        )
        return rules


retriever = Retriever()
