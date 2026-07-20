from langchain_core.tools import tool

from app.models.schema import QualityReport


@tool
def count_words(text: str) -> int:
    return len(text.split())


@tool
def analyze_structure(text: str) -> dict:
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
