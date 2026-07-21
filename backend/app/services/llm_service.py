import logging
from functools import lru_cache
from typing import Any, Callable, TypeVar

from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import get_settings
from app.exceptions import LLMServiceError


logger = logging.getLogger(__name__)

T = TypeVar("T")


class LLMService:

    def __init__(self, primary_llm: Any | None = None, fallback_llm: Any | None = None):
        settings = get_settings()
        self.primary_model_name = settings.GROQ_MODEL_NAME
        self.fallback_model_name = settings.GEMINI_MODEL_NAME
        self._primary_llm = primary_llm or ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model=settings.GROQ_MODEL_NAME,
            temperature=settings.LLM_TEMPERATURE,
            timeout=settings.LLM_REQUEST_TIMEOUT,
            max_retries=settings.LLM_PROVIDER_MAX_RETRIES,
        )
        self._fallback_llm = fallback_llm or ChatGoogleGenerativeAI(
            api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_MODEL_NAME,
            temperature=settings.LLM_TEMPERATURE,
        )

    def invoke_structured(
        self,
        *,
        prompt: Any,
        schema: type[T],
        inputs: dict[str, Any],
        operation_name: str,
    ) -> T:
        """Invoke a prompt with structured output and automatic fallback."""

        def invoke(llm: Any) -> T:
            chain = prompt | llm.with_structured_output(schema)
            return chain.invoke(inputs)

        return self._invoke_with_fallback(invoke, operation_name)

    def invoke_structured_messages(
        self,
        *,
        messages: list[Any],
        schema: type[T],
        operation_name: str,
    ) -> T:
        """Invoke structured output directly from a prepared message list."""

        def invoke(llm: Any) -> T:
            return llm.with_structured_output(schema).invoke(messages)

        return self._invoke_with_fallback(invoke, operation_name)

    def invoke_with_tools(
        self,
        *,
        messages: list[Any],
        tools: list[Any],
        operation_name: str,
    ) -> Any:
        """Invoke a tool-bound chat model with automatic fallback."""

        def invoke(llm: Any) -> Any:
            return llm.bind_tools(tools).invoke(messages)

        return self._invoke_with_fallback(invoke, operation_name)

    def _invoke_with_fallback(self, invoke: Callable[[Any], T], operation_name: str) -> T:
        try:
            return invoke(self._primary_llm)
        except Exception as primary_error:  
            logger.warning(
                "Primary LLM failed during %s; retrying with fallback model %s: %s",
                operation_name,
                self.fallback_model_name,
                primary_error,
            )

        try:
            return invoke(self._fallback_llm)
        except Exception as fallback_error:  # noqa: BLE001
            logger.exception(
                "Fallback LLM also failed during %s using model %s",
                operation_name,
                self.fallback_model_name,
            )
            raise LLMServiceError(
                f"Both primary model {self.primary_model_name!r} and fallback model "
                f"{self.fallback_model_name!r} failed during {operation_name}: {fallback_error}"
            ) from fallback_error


@lru_cache
def get_llm_service() -> LLMService:
    return LLMService()
