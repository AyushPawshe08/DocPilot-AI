from pydantic import BaseModel, Field, field_validator

class AgentRequest(BaseModel):
    request: str = Field(
        ...,
        min_length=10,
        max_length=4000,
        description="Natural language description of the document to generate.",
    )

    @field_validator("request")
    @classmethod
    def strip_and_validate(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Request cannot be empty or whitespace only.")
        return value


class QualityReport(BaseModel):
    word_count: int
    heading_count: int
    bullet_count: int
    passed: bool
    issues: list[str] = Field(default_factory=list)


class AgentResponse(BaseModel):
    success: bool
    message: str
    document_type: str
    tasks: list[str]
    quality_report: QualityReport
    document_id: str
    download_url: str



from typing import Literal

class PlannerOutput(BaseModel):
    document_type: str = Field(..., description="e.g. 'business proposal', 'technical report'")
    assumptions: list[str] = Field(default_factory=list)
    target_length: Literal["short", "medium", "long"] = Field(
        ...,
        description="short: ~300-600 words, medium: ~700-1200 words, long: ~1500-2500 words",
    )
    target_length_reason: str = Field(
        ...,
        description="One-sentence justification for the chosen target_length.",
    )
    tasks: list[str] = Field(
        ...,
        min_length=1,
        description="Ordered list of actions the executor should take into account.",
    )

class DraftOutput(BaseModel):
    title: str
    content: str = Field(..., description="Markdown-flavoured document body.")


class FinalDocument(BaseModel):
    title: str
    content: str
    quality_report: QualityReport


class AgentResult(BaseModel):
    plan: PlannerOutput
    document: FinalDocument
    document_id: str
    document_path: str
