"""Unit tests for app/core/retriever.py.

These exercise the real, already-ingested ChromaDB collection rather than
mocking Chroma/the embedding model — matching this project's convention of
verifying real behavior over mocked approximations (see docs/architecture.md).
Requires `python scripts/ingest.py` to have been run already; tests skip with
a clear message if the collection is empty.
"""

from pathlib import Path

from app.config import settings
from app.core.retriever import RetrievedRule, retriever

KNOWLEDGE_BASE_DIR = Path("data/knowledge_base")


def test_retrieve_returns_at_most_default_top_k(require_ingested_kb):
    results = retriever.retrieve("How do I check my IP address?")

    assert 0 < len(results) <= settings.top_k
    assert all(isinstance(r, RetrievedRule) for r in results)


def test_retrieve_respects_k_override(require_ingested_kb):
    results = retriever.retrieve("How do I check my IP address?", k=2)

    assert len(results) <= 2


def test_results_are_sorted_by_score_descending(require_ingested_kb):
    results = retriever.retrieve("How do I check my IP address?")

    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_retrieve_finds_the_correct_eservices_rule(require_ingested_kb):
    results = retriever.retrieve("My LDAP is not working and I cannot access the internet or WiFi.")

    top = results[0]
    assert top.rule_id == "rule_01"
    assert top.category == "Eservices"


def test_retrieve_finds_the_correct_network_rule(require_ingested_kb):
    results = retriever.retrieve("How do I check my IP address?")

    top = results[0]
    assert top.rule_id == "rule_01"
    assert top.category == "Network"


def test_retrieve_finds_the_correct_hpce_rule(require_ingested_kb):
    """Regression test: rule_17 ('How do I cancel a running job?') originally
    shipped with its support_email field missing entirely."""
    results = retriever.retrieve("How do I cancel a running job?")

    top = results[0]
    assert top.rule_id == "rule_17"
    assert top.category == "Hpce"
    assert top.support_email == "helpdeskhpce@iitm.ac.in"


def test_collection_size_matches_source_jsonl_row_count(require_ingested_kb):
    """Regression test for a real bug found in this project: ingest.py upserts
    but never deletes, so if a rule's id changes (e.g. renumbering existing
    rows when merging in new ones) the old vector is orphaned and left behind,
    inflating the collection beyond what the source data actually contains.
    (Caught two such orphans — network_rule_1/network_rule_2 — this way.)"""
    expected = sum(
        1
        for path in KNOWLEDGE_BASE_DIR.glob("**/*.jsonl")
        for line in path.read_text().splitlines()
        if line.strip()
    )
    actual = retriever._vectorstore._collection.count()

    assert actual == expected, (
        f"collection has {actual} vectors but source .jsonl files have {expected} rows — "
        "likely orphaned vectors from renumbered/removed rules; wipe and re-run "
        "scripts/ingest.py (or use scripts/reset_db.py once implemented)"
    )
