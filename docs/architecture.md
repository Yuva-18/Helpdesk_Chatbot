# Architecture & Design Decisions

Document key choices here as you make them, for example:
- Why the `/completion` endpoint is used instead of `/v1/chat/completions`
- Chunking strategy and chunk size rationale
- Confidence threshold and fallback routing logic

## Ingestion (`scripts/ingest.py`)

- **What gets embedded**: each knowledge base rule's `question` field only, not the answer. FAQ-style retrieval works best matching the user's question against other questions (semantically similar phrasing), not against answer text. The `answer`, `category`, `support_email`, `source_url`, and `last_updated` fields are stored as ChromaDB metadata on the same vector, so once a question match is found, the full rule is available without a second lookup.
- **Vector store IDs**: `<category>_<rule id>` (e.g. `eservices_rule_01`) — stable and unique across both knowledge base files, and makes re-running ingestion an upsert instead of a duplicate-insert.
- **Metadata type constraint**: ChromaDB metadata values must be `str`/`int`/`float`/`bool` — no lists, no `None`. `keywords` (a JSON list in the source data) is joined into a comma-separated string before storage; `source_url: null` is stored as `""`.
- **`langchain_community.vectorstores.Chroma` deprecation**: `requirements.txt` pins `langchain-community` (not the newer standalone `langchain-chroma` package), and importing `Chroma` from it prints a `DeprecationWarning`/`LangChainDeprecationWarning` — it still works correctly (verified via ingestion + similarity search) and is what's actually installed, so it's used as-is. Migrating to `langchain-chroma` is a future dependency change, not done as part of ingestion.
- **`scripts/reset_db.py` is still a stub.** `ingest.py` upserts by stable ID, so it never *duplicates* on re-run, but it also never deletes vectors for rules removed from the source `.jsonl` files. `reset_db.py` (wipe + rebuild) is the intended way to handle that case — not yet implemented.
