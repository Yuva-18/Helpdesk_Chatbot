# Deployment

Steps to run this on a real server (target: an IIT Madras Linux server), as two independently-managed processes: `llama-server` (the local LLM) and the FastAPI app (which also serves the frontend, same-origin — see `docs/architecture.md`).

## 1. Rebuild `llama.cpp` on the target machine — do not copy the compiled binary

`llama.cpp/build/bin/llama-server`'s RUNPATH is baked in at compile time to the exact machine it was built on. Copying the binary from another machine (or from this dev environment) will fail at startup with `cannot open shared object file: libllama-server-impl.so`, because the dynamic linker looks in the *original* build machine's path, not wherever the binary now lives.

**Fix**: clone/build `llama.cpp` fresh, on the target server itself:

```bash
cd hd_chatbot
git clone https://github.com/ggml-org/llama.cpp.git   # or however your copy is vendored
cd llama.cpp
cmake -B build
cmake --build build --config Release -j
```

`scripts/start_llama_server.sh` already works around any remaining path drift by resolving `LD_LIBRARY_PATH` from the real `llama.cpp/build/bin` directory at runtime — keep that script as-is, it's not a workaround you can remove, just don't rely on it *instead of* rebuilding locally.

## 2. Model weights

Copy the model file to `models/Llama-3.2-3B-Instruct-Q4_K_M.gguf` (gitignored, not in the repo — see `README.md` for where to obtain it).

## 3. Python environment and config

```bash
cd hd_chatbot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then edit real values, especially support emails
```

Set `CORS_ALLOWED_ORIGINS` in `.env` only if some *other* origin needs to call `/chat` directly — the frontend itself is served same-origin and needs nothing here.

## 4. Ingest the knowledge base

```bash
python scripts/ingest.py
```

Safe to re-run any time the `.jsonl` files under `data/knowledge_base/` change (upserts by stable id). If rows were **removed or renumbered**, upserting alone leaves the old vectors orphaned (we hit this for real during development) — use `python scripts/reset_db.py` instead, which wipes `vectorstore/chroma_db` and rebuilds it from scratch.

## 5. Run both processes under systemd

Two unit templates are provided in `deploy/`. Edit the placeholder `User=` and `/path/to/hd_chatbot` in both files, then:

```bash
sudo cp deploy/llama-server.service deploy/hd-chatbot-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now llama-server.service
sudo systemctl enable --now hd-chatbot-api.service
```

They're independent services (per `CLAUDE.md`'s note that the model server and API server may need to be managed/restarted separately) — restarting one doesn't require restarting the other. `hd-chatbot-api.service` only *orders* itself after `llama-server.service` (`After=`/`Wants=`); it doesn't hard-fail if `llama-server` is down, since `rag_pipeline.py` already degrades gracefully to the verified KB answer when the LLM is unreachable.

Do **not** run `uvicorn --reload` in production — that's dev-only autoreload. The unit file already omits it.

## 6. Verify

```bash
curl -s http://localhost:8000/health
curl -s -X POST http://localhost:8000/chat -H "Content-Type: application/json" \
  -d '{"question": "My LDAP is not working and I cannot access the internet or WiFi."}'
```

Then open `http://<server>:8000/` in a browser — the frontend is served by the same FastAPI app (same-origin, no separate static server needed). Confirm one confident query per category (Eservices/Network/Hpce) and one deliberately off-topic query (should fall back with a support email, not error).

## 7. Logs and updating the knowledge base later

- Logs: `logs/app.log` (also mirrored to console/journalctl under systemd).
- To add/edit KB rules: edit the relevant `.jsonl` under `data/knowledge_base/`, then re-run `python scripts/ingest.py` (or `scripts/reset_db.py` if rows were removed/renumbered). No service restart needed — the API queries ChromaDB live on every request.

## Known open item

The real Network support-team mailbox spelling (`helpdesknetwork@` vs `helpdesknetworks@iitm.ac.in`) was never confirmed against the actual address — currently set to the plural form to match the knowledge base data. Confirm and correct in `.env` and `data/knowledge_base/network/network.jsonl` before relying on this in production; see `docs/architecture.md` for the full history.
