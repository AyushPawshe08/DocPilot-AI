# Autonomous Document Agent

An autonomous AI agent that takes a natural-language request ("write me a
project proposal for X") and produces a polished, downloadable Microsoft
Word document â€” planning the work, drafting the content, reviewing its own
output with real tool calls, and rendering the final `.docx`, all without
further human input.

## 1. Architecture

```
Client
  â”‚  POST /agent {"request": "..."}
  â–¼
FastAPI (app/main.py, app/api/routes.py)
  â”‚
  â–¼
Orchestrator (app/core/orchestrator.py)
  â”‚
  â”œâ”€â–º Planner    (LLM, structured output)  â†’ PlannerOutput  {document_type, assumptions, tasks}
  â”œâ”€â–º Executor   (LLM, structured output)  â†’ DraftOutput    {title, content}
  â”œâ”€â–º Reflector  (LLM + tools, bounded loop) â†’ FinalDocument {title, content, quality_report}
  â””â”€â–º DocumentService (deterministic, no LLM) â†’ .docx file on disk
```

Each stage is a small, independent class with a single public method and a
single responsibility:

| Stage | Responsibility | LLM call? |
|---|---|---|
| `Planner` | Decide document type, note assumptions, break the request into tasks | Yes (structured output) |
| `Executor` | Turn the plan into a full Markdown draft | Yes (structured output) |
| `Reflector` | Critique and improve the draft, **using tools to verify its own claims** | Yes (tool-calling loop) |
| `DocumentService` | Render Markdown â†’ `.docx`, store it, resolve it for download | No |

The `Orchestrator` is the only component that knows the stages run in this
order â€” every other class could be reused in a different pipeline (e.g. a
CLI, a batch job, a different agent) without modification.

## 2. Why this design

### 2.1 Planning and reasoning are separated from drafting
The planner is asked to think about *what* to produce (document type,
missing information, ordered tasks) before any prose is generated. This
mirrors how a human writer works and gives us an inspectable, structured
artifact (`PlannerOutput`) we can log, test, and show to the user â€” instead
of hoping a single giant prompt "gets it right" in one shot.

### 2.2 Tool orchestration in the review stage
The original version of this project asked the LLM to review its own
document and simply *trust* that it was long enough and well-structured.
That's a common failure mode for LLM agents: the model asserts something is
true without checking.

`Reflector` fixes this with a small ReAct-style loop:

```python
response = self._tool_llm.invoke(messages)      # model may call a tool
if response.tool_calls:
    result = TOOLS_BY_NAME[call["name"]].invoke(call["args"])
    messages.append(ToolMessage(content=str(result), ...))
    # loop continues, model sees the real measurement
```

Two tools are exposed (`app/core/tools.py`):

* `count_words` â€“ ground truth on document length
* `analyze_structure` â€“ counts headings/bullets so the model can't just
  *say* it added sections

The loop is capped at `MAX_QA_ITERATIONS` (default 3, configurable via
`.env`). This is a deliberate reliability boundary: an LLM that keeps
calling tools without converging cannot run up an unbounded bill or hang a
request â€” it simply falls through to a final structured-output call after
the cap is hit. After the loop (by either path) a final
`build_quality_report()` runs **without** the LLM, as a deterministic
safety net the model cannot talk its way around.

### 2.3 Structured output over free-text parsing
Every LLM call uses `.with_structured_output(PydanticModel)` rather than
asking for JSON in a string and regex-parsing it. This eliminates an entire
class of bugs (truncated JSON, markdown code fences around the JSON,
trailing commentary) and gives us free validation via Pydantic.

### 2.4 Deterministic rendering is kept separate from generation
`DocumentService` never calls the LLM. Keeping it pure means:
* it's fast and free to call,
* it's trivially unit-testable (see `tests/test_document_service.py`),
* a prompt-injection attempt inside the generated content can't do
  anything more interesting than appear as inert text in the file.

### 2.5 Errors are typed, not stringly-typed
`app/exceptions.py` defines one exception per pipeline stage
(`PlanningError`, `DraftingError`, `ReviewError`, `DocumentGenerationError`,
`DocumentNotFoundError`). `main.py` maps each to an appropriate HTTP status
in one place (502 for upstream LLM failures, 404 for a missing document,
500 as a fallback) so individual endpoints stay free of `try/except`
boilerplate, and a client can distinguish "the LLM provider failed" from
"you asked for a document that doesn't exist."

### 2.6 Dependency injection over module-level singletons
The original code built `Orchestrator()` (and the LLM chains inside each
stage) once at import time. That makes two things hard: testing without a
real API key, and ever swapping an implementation per-request or per-tenant.
Every stage class now accepts its dependencies as constructor arguments
with sane defaults, and the FastAPI route depends on `get_orchestrator()`
via `Depends(...)`, so tests can override it with a single line:

```python
app.dependency_overrides[get_orchestrator] = lambda: fake_orchestrator
```

`tests/test_orchestrator.py` demonstrates this end to end with zero network
calls.

### 2.7 Safe, ID-based file handling
The original service returned a raw filesystem path as the API response
and had no download endpoint at all. This version:
* generates a `document_id` (a UUID4 hex string) server-side,
* exposes `GET /documents/{document_id}` to actually download the file,
* validates the id against `^[0-9a-f]{32}$` before touching the filesystem
  in `resolve_path()`, closing the obvious path-traversal hole a
  naive "download by filename" endpoint would have.

## 3. Bug fixed from the original prototype

The original `Reflector` called
`reflector_chain.invoke({"title": ..., "content": ...})`, but the prompt
template referenced `{sections}`, not `{content}` â€” a `KeyError` on every
single request. This is exactly the kind of bug that's invisible until you
actually exercise the code path, which is why this rewrite ships with unit
tests that execute the orchestrator (with fakes) and the document renderer
(for real) rather than relying on manual testing alone.

## 4. Scalability notes

* **Stateless app process** â€” nothing but generated files is stored on
  local disk, so the API layer can be scaled horizontally behind a load
  balancer. The only shared state that would need externalizing for a
  multi-instance deployment is `OUTPUT_DIR` (swap for S3/GCS + a signed
  URL in `resolve_path`/`download_document`).
* **Bounded LLM usage** â€” the QA loop's iteration cap and per-call
  `timeout`/`max_retries` (`app/config.py`) mean one slow or flaky
  request can't cascade into resource exhaustion.
* **Cheap to parallelize later** â€” because each stage is a pure function
  of its inputs (no shared mutable state), running multiple `/agent`
  requests concurrently, or eventually parallelizing independent
  sub-tasks within a single request, doesn't require restructuring.
* **Swappable LLM provider** â€” all LLM construction goes through
  `get_llm()`; moving from Groq to another provider touches one file.

## 5. Project layout

```
app/
  main.py                 FastAPI app, middleware, exception handlers
  config.py                Settings (env-driven, validated at startup)
  logging_config.py        Structured logging setup
  exceptions.py            Typed exception hierarchy
  api/
    routes.py               HTTP endpoints
  core/
    orchestrator.py         Pipeline coordination
    planner.py               Stage 1
    executor.py               Stage 2
    reflector.py               Stage 3 (tool-calling loop)
    tools.py                    Tools available to the reflector
    prompts.py                   Prompt templates
  services/
    llm_service.py           LLM client factory
    document_service.py      Markdown -> .docx renderer
  models/
    schema.py                 Pydantic models (API + internal)
tests/
  test_document_service.py
  test_tools.py
  test_orchestrator.py
  test_schema.py
```

## 6. Running it

```bash
pip install -r requirements.txt
cp .env.example .env        # then fill in GROQ_API_KEY
uvicorn app.main:app --reload
```

* `POST /agent` â€” body `{"request": "..."}` â†’ generates the document and
  returns metadata + `download_url`.
* `GET /documents/{document_id}` â€” downloads the generated `.docx`.
* `GET /health` â€” liveness check.
* `GET /docs` â€” interactive Swagger UI (from FastAPI, free).

### Streamlit UI

You can also run the app with a browser UI:

```bash
streamlit run streamlit_app.py
```

The Streamlit interface lets you enter a document request, generate a Word
document, inspect the plan and quality report, and download the generated
`.docx` file.
## 7. Testing

```bash
pytest
```

All 12 tests run without a real `GROQ_API_KEY` or any network access: the
orchestrator tests inject fakes for the three LLM-backed stages, and the
document-service/tools tests exercise real, deterministic code.

## 8. Known limitations / next steps

* The planner's `tasks` are currently used as *context* for the executor
  prompt rather than being executed as discrete, independently-tool-using
  steps. A natural next iteration is to let the executor call a
  research/fact-lookup tool per task before drafting, turning "planning"
  into genuine multi-step task execution rather than a single drafting
  call informed by a plan.
* No persistence beyond the local filesystem â€” fine for a take-home/demo,
  not for production multi-instance deployment (see Â§4).
* No authentication/rate limiting on the API â€” would be required before
  exposing this beyond a trusted network.

## LLM fallback behavior

All Planner, Executor, and Reflector model calls go through `LLMService`.
Groq is the primary provider and Mistral is the fallback provider. If the
primary invocation fails because of a rate limit, timeout, provider API error,
or any unexpected exception, the same request is retried once with Mistral and
the fallback event is logged. If both providers fail, the API returns a typed
`LLMServiceError` as a 502 upstream-provider failure.

Required environment variables:

```text
GROQ_API_KEY=...
GROQ_MODEL_NAME=llama-3.3-70b-versatile
MISTRAL_API_KEY=...
MISTRAL_MODEL_NAME=mistral-small-latest
LLM_PROVIDER_MAX_RETRIES=1
```

