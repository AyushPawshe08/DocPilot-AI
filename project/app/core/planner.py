import logging

from app.config import get_settings
from app.core.prompts import PLANNER_PROMPT
from app.exceptions import PlanningError
from app.models.schema import PlannerOutput
from app.services.llm_service import LLMService, get_llm_service

logger = logging.getLogger(__name__)


class Planner:
    def __init__(self, llm_service: LLMService | None = None):
        settings = get_settings()
        self._settings = settings
        self._llm_service = llm_service or get_llm_service()

    def create_plan(self, request: str) -> PlannerOutput:
        logger.info("Planning stage started (request length=%d chars)", len(request))
        plan = self._llm_service.invoke_structured(
            prompt=PLANNER_PROMPT,
            schema=PlannerOutput,
            inputs={
                "request": request,
                "min_tasks": self._settings.MIN_TASKS,
                "max_tasks": self._settings.MAX_TASKS,
            },
            operation_name="planning",
        )

        if not plan.tasks:
            raise PlanningError("Planner returned an empty task list.")

        logger.info(
            "Planning stage complete: document_type=%r tasks=%d assumptions=%d",
            plan.document_type,
            len(plan.tasks),
            len(plan.assumptions),
        )
        return plan
