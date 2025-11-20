"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, tweets, health


def create_app() -> FastAPI:
    """Create FastAPI application with middleware and routers."""
    app = FastAPI(title="Tweet Capture API", version=settings.app_version)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(tweets.router, prefix="/api/tweets", tags=["tweets"])
    app.include_router(health.router, prefix="/api", tags=["health"])
    return app


app = create_app()
