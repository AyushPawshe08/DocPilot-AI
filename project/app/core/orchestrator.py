"""Coordinates the plan -> draft -> review -> render pipeline.

The Orchestrator is intentionally the *only* place that knows the stages
run in this order. Each stage is independent, unit-testable, and could be
swapped, parallelized, or turned into separate microservices later
without the API layer or the stages themselves changing.
"""
import logging
import time

from app.config import get_settings
from app.core.executor import Executor
from app.core.planner import Planner
from app.core.reflector import Reflector
from app.models.schema import AgentResult
from app.services.document_service import DocumentService
from app.services.llm_service import LLMService, get_llm_service

logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(
        self,
        planner: Planner | None = None,
        executor: Executor | None = None,
        reflector: Reflector | None = None,
        document_service: DocumentService | None = None,
        llm_service: LLMService | None = None,
    ):
        # Constructor injection (with sane defaults) rather than module-level
        # singletons: makes it trivial to substitute fakes/mocks in tests.
        settings = get_settings()
        shared_llm_service = llm_service or get_llm_service()
        self.planner = planner or Planner(shared_llm_service)
        self.executor = executor or Executor(shared_llm_service)
        self.reflector = reflector or Reflector(shared_llm_service)
        self.document_service = document_service or DocumentService(settings.OUTPUT_DIR)

    def run(self, request: str) -> AgentResult:
        start = time.perf_counter()
        logger.info("Agent run started")

        plan = self.planner.create_plan(request)

        draft = self.executor.execute(
            request=request,
            document_type=plan.document_type,
            assumptions=plan.assumptions,
            tasks=plan.tasks,
            target_length=plan.target_length,
            target_length_reason=plan.target_length_reason,
        )

        final_document = self.reflector.review(
            title=draft.title,
            content=draft.content,
        )

        document_id, document_path = self.document_service.generate(
            title=final_document.title,
            content=final_document.content,
        )

        elapsed = time.perf_counter() - start
        logger.info("Agent run complete in %.2fs (document_id=%s)", elapsed, document_id)

        return AgentResult(
            plan=plan,
            document=final_document,
            document_id=document_id,
            document_path=document_path,
        )
