"""Deletes and rebuilds the vectorstore/chroma_db directory from scratch."""

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.utils.logger import get_logger
from ingest import load_knowledge_base, upsert_rules

logger = get_logger(__name__)


def main() -> None:
    persist_dir = Path(settings.chroma_persist_dir)
    if persist_dir.exists():
        for entry in persist_dir.iterdir():
            if entry.name == ".gitkeep":
                continue
            if entry.is_dir():
                shutil.rmtree(entry)
            else:
                entry.unlink()
        logger.info("Cleared existing vector store at %s", persist_dir)

    ids, texts, metadatas = load_knowledge_base()
    logger.info("Rebuilding from %d rules (source .jsonl files are the only source of truth)", len(ids))
    upsert_rules(ids, texts, metadatas)


if __name__ == "__main__":
    main()
