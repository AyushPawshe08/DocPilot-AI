import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse

from app.core.orchestrator import Orchestrator
from app.core.rate_limit import limiter
from app.models.schema import AgentRequest, AgentResponse

logger = logging.getLogger(__name__)

router = APIRouter()


def get_orchestrator() -> Orchestrator:
    return Orchestrator()


@router.get("/health", tags=["meta"])
def health_check() -> dict:
    logger.info("Health check endpoint called.")
    return {"status": "ok"}


@router.post("/agent", response_model=AgentResponse, tags=["agent"])
@limiter.limit("5/minute")
def run_agent(
    request: Request,
    payload: AgentRequest,
    orchestrator: Orchestrator = Depends(get_orchestrator),
) -> AgentResponse:
    logger.info("Received /agent request.")


    try:
        logger.debug(f"User request: {payload.request}")

        result = orchestrator.run(payload.request)

        logger.info(
            f"Document generated successfully. "
            f"Document ID: {result.document_id}, "
            f"Type: {result.plan.document_type}"
        )

        return AgentResponse(
            success=True,
            message="Document generated successfully.",
            document_type=result.plan.document_type,
            tasks=result.plan.tasks,
            quality_report=result.document.quality_report,
            document_id=result.document_id,
            download_url=f"/documents/{result.document_id}",
        )

    except Exception as e:
        logger.exception(f"Error while processing /agent request: {e}")
        raise


@router.get("/documents/{document_id}", tags=["agent"])
def download_document(
    document_id: str,
    orchestrator: Orchestrator = Depends(get_orchestrator),
) -> FileResponse:
    logger.info(f"Download requested for document: {document_id}")

    path = orchestrator.document_service.resolve_path(document_id)

    logger.info(f"Resolved document path: {path}")

    return FileResponse(
        path=path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"{document_id}.docx",
    )