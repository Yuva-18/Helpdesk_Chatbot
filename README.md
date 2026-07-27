# IIT Madras Computer Center Helpdesk Chatbot

A RAG-based IT helpdesk chatbot built for the IIT Madras Computer Center. It answers common IT questions (LDAP, IMail, WiFi, etc.) by retrieving from a curated knowledge base and generating a grounded answer with a local LLM. When it isn't confident it has the right answer, it never guesses — it routes the user to the correct support email instead.

See [`docs/architecture.md`](docs/architecture.md) for design decisions and [`docs/deployment.md`](docs/deployment.md) for production deployment steps. [`CLAUDE.md`](CLAUDE.md) has a full technical walkthrough of every module if you need to go deeper than this guide.

## How it works (high level)

```
user question -> embed it -> search the knowledge base (ChromaDB) -> confident enough?
    yes -> build a grounded prompt -> ask the local LLM -> return the answer
    no  -> skip the LLM entirely -> return the right support team's email instead
```

Three things run together to make this work: a **local LLM server** (`llama.cpp`, serving a quantized Llama 3.2 3B model), a **FastAPI backend** (the RAG pipeline + API), and a **static frontend** (plain HTML/CSS/JS chat UI). This guide sets up and runs all three.

---

## Prerequisites

- **Ubuntu Linux** (or similar). This hasn't been tested on macOS/Windows directly — if you're on Windows, use WSL2.
- **Python 3.12+**
- **git**
- **~4 GB free disk space** (the model weights alone are ~1.9 GB, plus `llama.cpp`'s build)
- **A C++ build toolchain** (`cmake`, `g++`/`gcc`) — needed to compile `llama.cpp`. On Ubuntu: `sudo apt-get install -y build-essential cmake`
- Enough RAM to comfortably run a 3B parameter quantized model (8 GB+ recommended)

---

## 1. Clone the repository

```bash
git clone <this-repo-url>
cd hd_chatbot
```

## 2. Set up the Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Every command in this guide assumes `.venv` is activated and you're in the project root — several scripts resolve paths (like `.env`) relative to the current directory, so running from elsewhere will cause confusing "file not found" errors.

## 3. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and check the values make sense for your machine (the defaults work for local development as-is — you generally don't need to change anything to get started). Key settings:

| Variable | What it's for |
|---|---|
| `LLAMA_SERVER_URL` | Where the backend finds the local LLM server (default `http://localhost:8080/completion`) |
| `CHROMA_PERSIST_DIR` | Where the vector database is stored on disk |
| `EMBEDDING_MODEL_NAME` | The Sentence Transformers model used for semantic search (`all-MiniLM-L6-v2`) |
| `TOP_K` / `CONFIDENCE_THRESHOLD` | How many results to retrieve, and how good the best match needs to be before the bot will answer instead of falling back |
| `ESERVICES_SUPPORT_EMAIL` / `NETWORK_SUPPORT_EMAIL` | Where users get routed when the bot isn't confident |

`.env` is gitignored on purpose (it can hold machine-specific or sensitive values) — always edit your local copy, never commit it.

## 4. Set up the local LLM

The model server (`llama.cpp`) and the model weights themselves are **not** included in this repository (they're large binaries — a 715 MB build and a 1.9 GB model file — so both are gitignored). You need to obtain them separately, once.

### 4a. Clone and build `llama.cpp`

```bash
git clone https://github.com/ggml-org/llama.cpp.git
cd llama.cpp
cmake -B build
cmake --build build --config Release -j "$(nproc)"
cd ..
```

This produces a `llama-server` binary at `llama.cpp/build/bin/llama-server`. The build takes a few minutes depending on your CPU.

### 4b. Get the model weights

You need `Llama-3.2-3B-Instruct-Q4_K_M.gguf` (a quantized, instruction-tuned Llama 3.2 3B model) placed at `models/Llama-3.2-3B-Instruct-Q4_K_M.gguf`. This project was built and tested against the quantization published by **`bartowski/Llama-3.2-3B-Instruct-GGUF`** on Hugging Face — search for that repo and download the `Q4_K_M` variant, or substitute your own GGUF model (update `models/Llama-3.2-3B-Instruct-Q4_K_M.gguf` in `scripts/start_llama_server.sh` if you use a different filename).

```bash
mkdir -p models
# place/download the .gguf file at models/Llama-3.2-3B-Instruct-Q4_K_M.gguf
```

### 4c. Link the binary

`scripts/start_llama_server.sh` expects a `llama-server` binary alongside it:

```bash
cd scripts
ln -s ../llama.cpp/build/bin/llama-server ./llama-server
cd ..
```

**Known gotcha:** the compiled binary's internal `RUNPATH` can be hardcoded to the machine it was built on, causing `error while loading shared libraries: libllama-server-impl.so: cannot open shared object file` if `llama.cpp` ends up at a different path than where it was compiled. `start_llama_server.sh` already works around this automatically (it sets `LD_LIBRARY_PATH` at runtime) — if you still hit this error, see Troubleshooting below.

## 5. Load the knowledge base into the vector database

```bash
python scripts/ingest.py
```

This reads every rule in `data/knowledge_base/**/*.jsonl`, embeds each one, and stores it in a local ChromaDB database at `vectorstore/chroma_db`. It's safe to re-run any time the knowledge base changes — it upserts by stable ID rather than duplicating. The first run will also download the `all-MiniLM-L6-v2` embedding model (~90 MB) from Hugging Face into `~/.cache/huggingface`.

---

## Running the application

You need **two things running at once**, each in its own terminal (or background process). The FastAPI backend serves the frontend itself (same-origin), so there's no separate frontend server anymore.

### Terminal 1 — the LLM server

```bash
cd scripts
./start_llama_server.sh
```

Wait for `llama_server: listening on http://127.0.0.1:8080` in the output before continuing. Verify it's up:

```bash
curl http://localhost:8080/health
# {"status":"ok"}
```

### Terminal 2 — the FastAPI backend (also serves the frontend)

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

Verify:

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

Then open **http://localhost:8000** in your browser — that's the chat UI, served by this same process.

> **Working on a remote server over SSH (e.g. VS Code Remote-SSH)?** "localhost" in your browser refers to *your own laptop*, not the remote machine these servers are running on. You'll need to forward port `8000` (VS Code's "Ports" panel, or `ssh -L 8000:localhost:8000 ...`) before the page will load. Port `8080` doesn't need forwarding — only the backend talks to it directly.

### Try it

Ask something like *"My WiFi is not working, I am a project staff"* — you should get a grounded answer citing the matched category. Ask something unrelated like *"what's the weather today"* — you should get a fallback message with a support email instead of a made-up answer.

---

## Running tests

```bash
pytest
```


## Rebuilding the vector database from scratch

If you ever need to wipe and rebuild the ChromaDB store entirely (e.g. after removing rules from the knowledge base — `ingest.py` only adds/updates, it never deletes stale entries):

```bash
python scripts/reset_db.py
```

---

## Troubleshooting

**`ModuleNotFoundError` when running `scripts/ingest.py` or similar directly** — make sure you're running from the project root with `.venv` activated. Some scripts add the project root to `sys.path` automatically, but always run `python scripts/<name>.py` from the repo root, not from inside `scripts/`.

**`error while loading shared libraries: libllama-server-impl.so`** — the compiled binary's RUNPATH points at the wrong location. `start_llama_server.sh` should already handle this by setting `LD_LIBRARY_PATH` at runtime; if it still fails, confirm `scripts/llama-server` actually resolves (via symlink) to a real, freshly-built `llama.cpp/build/bin/llama-server`.

**Frontend loads but `/chat` requests fail with a CORS error in the browser console** — confirm the FastAPI backend (`uvicorn`) is actually running and reachable at the URL hardcoded in `frontend/script.js`'s `API_BASE_URL` (default `http://localhost:8000`).

**Page won't load at all on a remote/SSH setup** — see the port-forwarding note above; this is almost always a tunnel issue, not an app issue. Confirm the servers are actually up first with `curl http://localhost:<port>/health` **from the remote machine itself**.

**LLM responses are slow the first time** — the embedding model and the LLM both need to load into memory on first use; subsequent requests are much faster.
