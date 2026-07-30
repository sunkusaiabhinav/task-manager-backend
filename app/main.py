"""
Application entry point — FastAPI app factory.

Responsibilities:
  - Create the FastAPI application instance
  - Configure metadata (title, version, docs URLs)
  - Register startup/shutdown lifecycle events
  - Mount all routers
  - Register global exception handlers
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.db.session import create_tables
from app.schemas.task import HealthResponse

# ── Logging setup ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ── Application factory ───────────────────────────────────────────────────
def create_app() -> FastAPI:
    """
    Build and configure the FastAPI application.
    Using a factory function makes it easy to create test instances
    with different configurations.
    """
    app = FastAPI(
        title=settings.app_name,
        description=(
            "A production-style Task Manager REST API.\n\n"
            "Built as a learning project covering FastAPI, Docker, "
            "GitHub Actions CI/CD, and security scanning."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ── CORS ──────────────────────────────────────────────────────────────
    # Allow all origins in development; lock this down in production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if not settings.is_production else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Lifecycle events ──────────────────────────────────────────────────
    @app.on_event("startup")
    async def on_startup() -> None:
        logger.info("Starting up %s [env=%s]", settings.app_name, settings.app_env)
        await create_tables()
        logger.info("Database tables verified/created.")

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        logger.info("Shutting down %s", settings.app_name)

    # ── Global exception handler ──────────────────────────────────────────
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception on %s %s", request.method, request.url)
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred."},
        )

    # ── Health endpoint ───────────────────────────────────────────────────
    @app.get(
        "/health",
        response_model=HealthResponse,
        tags=["Health"],
        summary="Health check",
    )
    async def health_check() -> HealthResponse:
        """
        Liveness probe endpoint.

        Used by:
          - Docker HEALTHCHECK
          - Kubernetes liveness probes
          - CI/CD pipeline smoke tests
          - Load balancers
        """
        return HealthResponse(
            status="ok",
            app_name=settings.app_name,
            environment=settings.app_env,
        )

    # ── Routers ───────────────────────────────────────────────────────────
    app.include_router(v1_router, prefix=settings.api_v1_prefix)

    return app


# ── ASGI application instance ─────────────────────────────────────────────
app = create_app()
