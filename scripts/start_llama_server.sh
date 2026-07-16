#!/usr/bin/env bash
# Starts llama-server with the local GGUF model.
# Adjust --model path, --port, and --ctx-size as needed.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_PATH="../models/Llama-3.2-3B-Instruct-Q4_K_M.gguf"
PORT=8080

# The compiled binary's RUNPATH points at the build machine's original clone
# path, not wherever this repo happens to live, so libllama-server-impl.so
# isn't found via the default loader search. Point LD_LIBRARY_PATH at the
# real build/bin directory (resolving the ./llama-server symlink) to fix it.
LLAMA_CPP_BIN_DIR="$(cd "$(dirname "$(readlink -f "$SCRIPT_DIR/llama-server")")" && pwd)"

LD_LIBRARY_PATH="$LLAMA_CPP_BIN_DIR${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
  ./llama-server \
  --model "$MODEL_PATH" \
  --port "$PORT" \
  --ctx-size 4096
