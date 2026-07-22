#!/usr/bin/env bash
#
# template.sh
# Scaffolds the IIT Madras Helpdesk Chatbot project folder structure.
#
# Usage:
#   chmod +x template.sh
#   ./template.sh [project-name]
#
# If project-name is omitted, defaults to "iitm-helpdesk-chatbot".
# The script is idempotent: re-running it will NOT overwrite files that
# already exist (mkdir -p is safe, and file creation checks first).

set -euo pipefail

PROJECT_NAME="${1:-iitm-helpdesk-chatbot}"

echo "Creating project: ${PROJECT_NAME}"
mkdir -p "${PROJECT_NAME}"
cd "${PROJECT_NAME}"

# ---------------------------------------------------------------------------
# Helper: create a file with content, but never clobber an existing file.
# ---------------------------------------------------------------------------
write_file() {
  local path="$1"
  local content="$2"
  if [ -f "$path" ]; then
    echo "  skip (exists): $path"
  else
    mkdir -p "$(dirname "$path")"
    printf '%s\n' "$content" > "$path"
    echo "  created: $path"
  fi
}

# ---------------------------------------------------------------------------
# Directories
# ---------------------------------------------------------------------------
echo "Creating directories..."
DIRS=(
  "app/api/routes"
  "app/api/schemas"
  "app/core"
  "app/services"
  "app/utils"
  "data/raw"
  "data/processed"
  "data/knowledge_base/eservices"
  "data/knowledge_base/network"
  "vectorstore/chroma_db"
  "models"
  "scripts"
  "frontend"
  "tests"
  "logs"
  "docs"
)

for d in "${DIRS[@]}"; do
  mkdir -p "$d"
  echo "  created: $d/"
done

# ---------------------------------------------------------------------------
# Python package markers (__init__.py) so app/ is importable
# ---------------------------------------------------------------------------
echo "Creating __init__.py files..."
INIT_DIRS=(
  "app"
  "app/api"
  "app/api/routes"
  "app/api/schemas"
  "app/core"
  "app/services"
  "app/utils"
  "tests"
)
for d in "${INIT_DIRS[@]}"; do
  write_file "$d/__init__.py" ""
done

# ---------------------------------------------------------------------------
# Placeholder application files (empty stubs with a docstring so their
# purpose is clear even before you write real code)
# ---------------------------------------------------------------------------
echo "Creating app stub files..."

write_file "app/main.py" '"""FastAPI application entrypoint. Wires routers into the app."""'
write_file "app/config.py" '"""Loads settings (paths, ports, thresholds) from environment variables."""'

write_file "app/api/routes/chat.py" '"""POST /chat endpoint: receives a user question, returns an answer or a fallback."""'
write_file "app/api/routes/health.py" '"""GET /health endpoint for uptime/liveness checks."""'
write_file "app/api/schemas/chat_schema.py" '"""Pydantic request/response models for the /chat endpoint."""'

write_file "app/core/embeddings.py" '"""Wraps Sentence Transformers for generating query and chunk embeddings."""'
write_file "app/core/retriever.py" '"""Handles similarity search against ChromaDB and returns top-k chunks."""'
write_file "app/core/llm.py" '"""Calls the local llama-server /completion endpoint with a raw prompt string."""'
write_file "app/core/prompt_builder.py" '"""Assembles the final prompt from system instructions, retrieved chunks, and the user question."""'
write_file "app/core/confidence.py" '"""Scores retrieval/answer confidence and decides whether to answer or route to fallback."""'

write_file "app/services/rag_pipeline.py" '"""Orchestrates retriever -> prompt_builder -> llm -> confidence into one pipeline call."""'

write_file "app/utils/logger.py" '"""Configures structured logging for the application."""'

# ---------------------------------------------------------------------------
# Scripts
# ---------------------------------------------------------------------------
echo "Creating scripts..."

write_file "scripts/ingest.py" '"""Loads raw docs, chunks them, generates embeddings, and stores them in ChromaDB."""'
write_file "scripts/reset_db.py" '"""Deletes and rebuilds the vectorstore/chroma_db directory from scratch."""'

write_file "scripts/start_llama_server.sh" '#!/usr/bin/env bash
# Starts llama-server with the local GGUF model.
# Adjust --model path, --port, and --ctx-size as needed.
set -euo pipefail

MODEL_PATH="../models/llama-3.2-3b-instruct.Q4_K_M.gguf"
PORT=8080

./llama-server \
  --model "$MODEL_PATH" \
  --port "$PORT" \
  --ctx-size 4096'
chmod +x scripts/start_llama_server.sh

# ---------------------------------------------------------------------------
# Frontend placeholders
# ---------------------------------------------------------------------------
echo "Creating frontend stubs..."
write_file "frontend/index.html" '<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>IIT Madras Helpdesk Chatbot</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <div id="chat-container"></div>
  <script src="script.js"></script>
</body>
</html>'
write_file "frontend/style.css" "/* Chat interface styles */"
write_file "frontend/script.js" "// Chat interface logic: sends queries to /chat and renders responses"

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
echo "Creating test stubs..."
write_file "tests/test_retriever.py" '"""Unit tests for app/core/retriever.py."""'
write_file "tests/test_llm.py" '"""Unit tests for app/core/llm.py."""'
write_file "tests/test_rag_pipeline.py" '"""Integration tests for app/services/rag_pipeline.py."""'
write_file "tests/test_api.py" '"""End-to-end tests for the FastAPI routes."""'

# ---------------------------------------------------------------------------
# Docs
# ---------------------------------------------------------------------------
echo "Creating docs..."
write_file "docs/architecture.md" '# Architecture & Design Decisions

Document key choices here as you make them, for example:
- Why the `/completion` endpoint is used instead of `/v1/chat/completions`
- Chunking strategy and chunk size rationale
- Confidence threshold and fallback routing logic'

write_file "docs/deployment.md" '# Deployment Guide

Steps to deploy on the IIT Madras Linux server:
1. ...
2. ...'

# ---------------------------------------------------------------------------
# Data placeholders (.gitkeep so empty dirs are tracked by git)
# ---------------------------------------------------------------------------
echo "Adding .gitkeep to empty data/log/vectorstore dirs..."
for d in "data/raw" "data/processed" "data/knowledge_base/eservices" "data/knowledge_base/network" "vectorstore/chroma_db" "models" "logs"; do
  write_file "$d/.gitkeep" ""
done

# ---------------------------------------------------------------------------
# Root-level project files
# ---------------------------------------------------------------------------
echo "Creating root project files..."

write_file ".gitignore" '# Environment
.env

# Python
__pycache__/
*.pyc
.venv/
venv/

# Model weights (too large for git)
models/*.gguf

# Vector store data
vectorstore/chroma_db/*
!vectorstore/chroma_db/.gitkeep

# Logs
logs/*.log

# OS / editor
.DS_Store
.vscode/'

write_file ".env.example" '# Server
HOST=0.0.0.0
PORT=8000

# llama-server (local LLM)
LLAMA_SERVER_URL=http://localhost:8080/completion

# ChromaDB
CHROMA_PERSIST_DIR=vectorstore/chroma_db

# Embeddings
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2

# RAG behavior
TOP_K=4
CONFIDENCE_THRESHOLD=0.5

# Fallback support emails
ESERVICES_SUPPORT_EMAIL=eservices-support@example.iitm.ac.in
NETWORK_SUPPORT_EMAIL=network-support@example.iitm.ac.in'

write_file "requirements.txt" 'fastapi
uvicorn[standard]
langchain
langchain-community
chromadb
sentence-transformers
pydantic
python-dotenv
requests
pytest'

write_file "README.md" "# IIT Madras Computer Center Helpdesk Chatbot

RAG-based IT helpdesk chatbot. See docs/architecture.md for design decisions
and docs/deployment.md for deployment steps."

echo ""
echo "Done. Project scaffolded at: $(pwd)"
echo "Next steps:"
echo "  1. cd ${PROJECT_NAME}"
echo "  2. python3 -m venv .venv && source .venv/bin/activate"
echo "  3. pip install -r requirements.txt"
echo "  4. cp .env.example .env   # then fill in real values"
