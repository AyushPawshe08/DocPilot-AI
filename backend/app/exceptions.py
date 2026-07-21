


class AgentError(Exception):
    """Base class for all errors raised by the agent pipeline."""


class PlanningError(AgentError):
    """Raised when the planner fails to produce a valid execution plan."""


class DraftingError(AgentError):
    """Raised when the executor fails to produce a document draft."""


class ReviewError(AgentError):
    """Raised when the reflector/QA stage fails or exceeds its iteration budget."""


class LLMServiceError(AgentError):
    """Raised when both the primary and fallback LLM providers fail."""


class DocumentGenerationError(AgentError):
    """Raised when rendering the final .docx file fails."""


class DocumentNotFoundError(AgentError):
    """Raised when a requested generated document does not exist."""
