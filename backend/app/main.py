import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware


from app.api.routes import router
from app.config import get_settings
from app.core.rate_limit import limiter
from app.exceptions import (
    AgentError,
    DocumentGenerationError,
    DocumentNotFoundError,
    DraftingError,
    LLMServiceError,
    PlanningError,
    ReviewError,
)
from app.logging_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)
settings = get_settings()



app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Autonomous AI agent that plans, drafts, reviews, and renders Word documents.",
)

# Rate limiting setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


_STATUS_BY_EXCEPTION: list[tuple[type[AgentError], int]] = [
    (DocumentNotFoundError, 404),
    (PlanningError, 502),
    (DraftingError, 502),
    (LLMServiceError, 502),
    (ReviewError, 502),
    (DocumentGenerationError, 500),
    (AgentError, 500),
]


@app.exception_handler(AgentError)
def handle_agent_error(request: Request, exc: AgentError) -> JSONResponse:
    status_code = 500
    for exc_type, code in _STATUS_BY_EXCEPTION:
        if isinstance(exc, exc_type):
            status_code = code
            break

    logger.error("Request to %s failed: %s", request.url.path, exc)
    return JSONResponse(
        status_code=status_code,
        content={"success": False, "message": str(exc), "error_type": type(exc).__name__},
    )


@app.get("/", tags=["root"])
def home() -> dict:
    return {"message": f"{settings.APP_NAME} is running.", "version": settings.APP_VERSION}

