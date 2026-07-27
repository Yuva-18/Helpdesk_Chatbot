"""Loads raw docs, chunks them, generates embeddings, and stores them in ChromaDB."""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from langchain_community.vectorstores import Chroma

from app.config import COLLECTION_NAME, settings
from app.core.embeddings import sentence_transformer_embeddings
from app.utils.logger import get_logger

logger = get_logger(__name__)

KNOWLEDGE_BASE_DIR = Path("data/knowledge_base")


def load_knowledge_base() -> tuple[list[str], list[str], list[dict]]:
    """Reads every data/knowledge_base/**/*.jsonl file and returns
    (ids, texts_to_embed, metadatas) ready for the vector store."""
    ids: list[str] = []
    texts: list[str] = []
    metadatas: list[dict] = []

    jsonl_files = sorted(KNOWLEDGE_BASE_DIR.glob("**/*.jsonl"))
    if not jsonl_files:
        raise FileNotFoundError(f"No .jsonl files found under {KNOWLEDGE_BASE_DIR}")

    for path in jsonl_files:
        file_count = 0
        with path.open(encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    rule = json.loads(line)
                except json.JSONDecodeError as exc:
                    logger.warning("Skipping malformed line %s:%s (%s)", path, line_no, exc)
                    continue

                doc_id = f"{rule['category'].lower()}_{rule['id']}"
                ids.append(doc_id)
                texts.append(rule["question"])
                metadatas.append(
                    {
                        "rule_id": rule["id"],
                        "category": rule["category"],
                        "answer": rule["answer"],
                        "keywords": ", ".join(rule.get("keywords", [])),
                        "support_email": rule["support_email"],
                        "source_url": rule.get("source_url") or "",
                        "last_updated": rule.get("last_updated") or "",
                    }
                )
                file_count += 1
        logger.info("Loaded %d rules from %s", file_count, path)

    return ids, texts, metadatas


def upsert_rules(ids: list[str], texts: list[str], metadatas: list[dict]) -> None:
    """Embeds and upserts the given rules into the shared ChromaDB collection.
    Shared with scripts/reset_db.py so both scripts store data identically."""
    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=sentence_transformer_embeddings,
        persist_directory=settings.chroma_persist_dir,
    )
    vectorstore.add_texts(texts=texts, metadatas=metadatas, ids=ids)

    logger.info(
        "Ingestion complete: %d vectors stored in collection '%s' (persisted at %s)",
        len(ids),
        COLLECTION_NAME,
        settings.chroma_persist_dir,
    )


def main() -> None:
    ids, texts, metadatas = load_knowledge_base()
    logger.info("Total rules to ingest: %d", len(ids))
    upsert_rules(ids, texts, metadatas)


if __name__ == "__main__":
    main()
