"""FastAPI application entrypoint. Wires routers into the app."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import chat, health
from app.config import settings

app = FastAPI(title="IIT Madras Computer Center Helpdesk Chatbot")

# The frontend is served same-origin below (StaticFiles), so it needs no CORS
# of its own. This middleware only matters for a separate, external consumer
# (e.g. a different domain calling /chat directly) — off by default.
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(health.router)
app.include_router(chat.router)

# Mounted last so it acts as a catch-all — /health and /chat above still win.
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
