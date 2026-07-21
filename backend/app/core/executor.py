import logging

from app.core.prompts import EXECUTOR_PROMPT
from app.exceptions import DraftingError
from app.models.schema import DraftOutput
from app.services.llm_service import LLMService, get_llm_service

logger = logging.getLogger(__name__)


class Executor:
    def __init__(self, llm_service: LLMService | None = None):
        self._llm_service = llm_service or get_llm_service()

    def execute(
        self,
        request: str,
        document_type: str,
        assumptions: list[str],
        tasks: list[str],
        target_length: str,
        target_length_reason: str,
    ) -> DraftOutput:
        logger.info(
            "Execution stage started (document_type=%r, %d tasks, target_length=%r)",
            document_type, len(tasks), target_length,
        )
        draft = self._llm_service.invoke_structured(
            prompt=EXECUTOR_PROMPT,
            schema=DraftOutput,
            inputs={
                "request": request,
                "document_type": document_type,
                "assumptions": "\n".join(assumptions) or "None.",
                "tasks": "\n".join(f"- {t}" for t in tasks),
                "target_length": f"{target_length} ({target_length_reason})",
            },
            operation_name="drafting",
        )

        if not draft.content.strip():
            raise DraftingError("Executor returned empty document content.")

        logger.info("Execution stage complete: title=%r content_len=%d", draft.title, len(draft.content))
        return draft