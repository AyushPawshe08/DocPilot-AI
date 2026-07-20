# Submission Guide

This guide is written for the 8-10 minute assignment video. It gives you the exact talking points, demo requests, and commands needed to present the autonomous document agent clearly.

## What The Project Builds

The project is a FastAPI-based autonomous AI agent that accepts:

```json
{"request": "..."}
```

at `POST /agent`, creates an execution plan, drafts a structured business document, reviews it with deterministic tools, generates a Microsoft Word `.docx` file, and returns:

- a success message
- the selected document type
- the agent-generated task list
- a quality report
- a generated document id
- a download URL for the `.docx`

## Run The API

From the `project` folder:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open the API docs:

```text
http://127.0.0.1:8000/docs
```

The `.env` file must contain a valid Groq API key:

```text
GROQ_API_KEY=your-groq-api-key
MODEL_NAME=llama-3.3-70b-versatile
```

Groq was chosen because it supports fast, free-tier LLM usage without requiring paid OpenAI or Anthropic credits.

## Test Input 1: Standard Business Request

Use this as the simple demo case:

```json
{
  "request": "Create a professional project proposal for implementing an AI-powered customer support chatbot for a mid-sized e-commerce company. Include business objectives, scope, implementation phases, risks, success metrics, timeline, and expected benefits."
}
```

What to show in the response:

- The agent identifies the document type as a proposal or project proposal.
- The returned `tasks` field shows the generated task list.
- The `quality_report` shows the document was checked for length and structure.
- Use `download_url` to download the generated `.docx`.

## Test Input 2: Complex Or Ambiguous Request

Use this as the complex demo case:

```json
{
  "request": "We need something for leadership about moving our internal HR onboarding process to an AI-assisted workflow next quarter, but do not make it too technical. Include cost savings, employee experience, compliance concerns, and a rollout plan. Assume some details if needed, but make it polished enough to share with executives."
}
```

Why this is complex:

- The requested document type is not explicitly named.
- The audience is leadership, so the agent must avoid excessive technical detail.
- Several business dimensions are requested at once: savings, experience, compliance, rollout.
- The agent must make reasonable assumptions because company size, exact budget, tools, and timeline are missing.

What to show:

- The planner decides the most appropriate document type.
- The task list reflects multiple workstreams.
- The final Word document is structured for an executive audience.

## Video Structure

### 1. Live Demo: 3-4 Minutes

1. Start the API with Uvicorn.
2. Open `/docs`.
3. Run the standard request.
4. Point out:
   - `document_type`
   - `tasks`
   - `quality_report`
   - `download_url`
5. Download and open the `.docx`.
6. Run the complex request.
7. Explain that the agent made assumptions and created its own plan before writing.

### 2. What I Built: 2-3 Minutes

Explain the architecture:

- FastAPI exposes `POST /agent` and `GET /documents/{document_id}`.
- `Planner` converts the natural language request into a structured execution plan.
- `Executor` uses the plan to draft the business document.
- `Reflector` reviews and improves the document before final output.
- `DocumentService` deterministically renders Markdown-like content into `.docx`.
- Pydantic models validate API inputs, outputs, and structured LLM responses.
- LangChain with Groq handles the LLM integration.

Suggested wording:

> I separated the agent into planning, execution, reflection, and rendering stages. This makes the workflow easy to test and explain, and it avoids hiding all agent behavior inside one large prompt. The API returns the plan so the user can see what the agent decided to do before producing the Word document.

### 3. Mandatory Engineering Improvement: 1-2 Minutes

Implemented improvement: **Tool calling with reflection/self-check**.

What it does:

- The reflector can call `count_words` to verify document length.
- The reflector can call `analyze_structure` to inspect heading and bullet structure.
- The loop is capped by `MAX_QA_ITERATIONS` so the agent cannot run forever.
- A deterministic `build_quality_report` runs at the end as a final safety check.

Why it improves the agent:

- The model does not merely claim the document is polished; it measures the document.
- It improves reliability because final quality checks are deterministic Python functions.
- It makes the agent behavior visible and defensible during the demo.

Suggested wording:

> I chose tool calling and reflection because document quality is easy for an LLM to overstate. Instead of trusting the model when it says the document is complete, the review stage calls real Python tools to measure word count and structure. This gives the agent a simple feedback loop before generating the final `.docx`.

### 4. Debugging Insight: 1-2 Minutes

Use this issue:

> During development, the reflection prompt and the data passed into the chain did not use the same variable names. The prompt expected one field name, but the code passed another, which caused the review step to fail at runtime. The root cause was that prompt templates are validated only when the chain is invoked, so the bug was not obvious from reading the code. I resolved it by aligning the prompt inputs with the data model and adding tests around the orchestrator pipeline so this failure would be caught automatically.

### 5. Tradeoff Discussion: 1-2 Minutes

Use this tradeoff:

> I chose a simple single-agent staged architecture instead of a multi-agent system. A multi-agent design could separate researcher, writer, reviewer, and formatter roles, but it would add coordination complexity and make the assignment harder to complete and test in a short time. The staged single-agent workflow still demonstrates autonomy because it plans, executes, reviews, and generates a final artifact, while keeping the code easy to reason about and reliable enough for a live demo.

## Useful Commands

Run tests:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Start server:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Download a document after receiving a `document_id`:

```text
http://127.0.0.1:8000/documents/<document_id>
```

## What To Emphasize To Evaluators

- Python code is modular and testable.
- The system exposes a clean REST API.
- The agent creates and returns its own task list.
- The final output is a real `.docx` file, not just text.
- The reflection stage uses tool calling and deterministic checks.
- The pipeline handles validation, typed exceptions, and safe document download by id.
