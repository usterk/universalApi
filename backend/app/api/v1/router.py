"""Main API router aggregator."""

from fastapi import APIRouter

from app.api.v1 import auth, sources, documents, plugins, jobs, workflows
from app.core.events.sse import router as events_router

api_router = APIRouter()

# Core routes
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(sources.router, prefix="/sources", tags=["sources"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(plugins.router, prefix="/plugins", tags=["plugins"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
api_router.include_router(events_router, prefix="/events", tags=["events"])
