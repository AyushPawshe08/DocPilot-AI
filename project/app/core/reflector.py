"""Review / QA stage.

Unlike the planner and executor (single structured-output calls), the
reflector runs a small, *bounded* ReAct-style loop: it may call the
``count_words`` / ``analyze_structure`` tools to inspect its own draft
before committing to a final version. The loop is capped by
``MAX_QA_ITERATIONS`` so a misbehaving model can never spin forever or
run up an unbounded API bill -- a deliberate scalability/reliability
guard, not an oversight.
"""
import logging

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.config import get_settings
from app.core.prompts import REFLECTOR_PROMPT
from app.core.tools import TOOLS, TOOLS_BY_NAME, build_quality_report
from app.exceptions import ReviewError
from app.models.schema import DraftOutput, FinalDocument
from app.services.llm_service import LLMService, get_llm_service

logger = logging.getLogger(__name__)


class Reflector:
    def __init__(self, llm_service: LLMService | None = None):
        settings = get_settings()
        self._max_iterations = settings.MAX_QA_ITERATIONS
        self._llm_service = llm_service or get_llm_service()

    def review(self, title: str, content: str) -> FinalDocument:
        logger.info("Review stage started (title=%r, content_len=%d)", title, len(content))
        messages = REFLECTOR_PROMPT.format_messages(title=title, content=content)

        for iteration in range(1, self._max_iterations + 1):
            response: AIMessage = self._llm_service.invoke_with_tools(
                messages=messages,
                tools=TOOLS,
                operation_name="review tool inspection",
            )
            messages.append(response)

            if not response.tool_calls:
                logger.info("Review stage: model finished after %d iteration(s)", iteration)
                break

            for call in response.tool_calls:
                tool_fn = TOOLS_BY_NAME.get(call["name"])
                if tool_fn is None:
                    result = f"Unknown tool: {call['name']}"
                else:
                    result = tool_fn.invoke(call["args"])
                logger.info("Review stage: tool %s -> %s", call["name"], result)
                messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))
        else:
            logger.warning("Review stage hit max iterations (%d) without finishing.", self._max_iterations)

        finalization_messages = [
            *messages,
            HumanMessage(
                content=(
                    "Finalize the reviewed document now. Return the final title and "
                    "full polished content using the required structured output schema."
                )
            ),
        ]
        final_draft = self._llm_service.invoke_structured_messages(
            messages=finalization_messages,
            schema=DraftOutput,
            operation_name="review finalization",
        )

        if not final_draft.content.strip():
            raise ReviewError("Reflector produced empty document content.")

        quality_report = build_quality_report(final_draft.content)
        logger.info(
            "Review stage complete: words=%d headings=%d passed=%s",
            quality_report.word_count,
            quality_report.heading_count,
            quality_report.passed,
        )

        return FinalDocument(
            title=final_draft.title,
            content=final_draft.content,
            quality_report=quality_report,
        )

