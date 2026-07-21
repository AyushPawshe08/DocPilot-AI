from langchain_core.tools import tool

from app.models.schema import QualityReport


@tool
def count_words(text: str) -> int:
    """Count the number of words in ``text``. Use this to verify the
    document is substantial enough (roughly 800-1500 words for a
    multi-page business document)."""
    return len(text.split())


@tool
def analyze_structure(text: str) -> dict:
    """Analyze the markdown structure of ``text`` and return the number
    of level-1/level-2 headings and bullet points found. Use this to
    verify the document has real section structure rather than being one
    wall of text."""
    headings = 0
    bullets = 0
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("#"):
            headings += 1
        elif line.startswith("- ") or line.startswith("* "):
            bullets += 1
    return {"heading_count": headings, "bullet_count": bullets}


TOOLS = [count_words, analyze_structure]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}


def build_quality_report(text: str, min_words: int = 500) -> QualityReport:
    """Deterministic, non-LLM quality check used both by the tool-calling
    loop and as a final safety net before rendering the .docx file."""
    word_count = count_words.invoke({"text": text})
    structure = analyze_structure.invoke({"text": text})

    issues: list[str] = []
    if word_count < min_words:
        issues.append(f"Document is short ({word_count} words, expected >= {min_words}).")
    if structure["heading_count"] == 0:
        issues.append("Document has no headings.")

    return QualityReport(
        word_count=word_count,
        heading_count=structure["heading_count"],
        bullet_count=structure["bullet_count"],
        passed=not issues,
        issues=issues,
    )
