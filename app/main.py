"""FastAPI application entrypoint. Wires routers into the app."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import chat, health

app = FastAPI(title="IIT Madras Computer Center Helpdesk Chatbot")

# The frontend is served separately (a plain static file, not by this app),
# so browser requests to /chat come from a different origin. Wide open for
# now since this is local/internal development; tighten allow_origins to the
# real frontend URL before production deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(chat.router)
