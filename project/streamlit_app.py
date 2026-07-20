"""Streamlit UI for the Autonomous Document Agent.

Calls the FastAPI backend over HTTP — exactly the same as Postman.
Make sure the FastAPI server is running first:
    uvicorn app.main:app --reload

Then run this UI:
    streamlit run streamlit_app.py
"""
import time
from pathlib import Path
import requests
import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Autonomous Document Agent",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
.stApp {
    background: linear-gradient(135deg, #0d0f1a 0%, #111827 50%, #0a0d1a 100%);
    color: #e2e8f0;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #111827 0%, #0d1321 100%) !important;
    border-right: 1px solid #1e293b;
}
.hero {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 40%, #1e40af 100%);
    border: 1px solid #3730a3;
    border-radius: 20px;
    padding: 40px 48px;
    margin-bottom: 32px;
    box-shadow: 0 25px 50px rgba(99,102,241,0.15);
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: -50%; right: -20%;
    width: 400px; height: 400px;
    background: radial-gradient(circle, rgba(139,92,246,0.12) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-badge {
    display: inline-flex; align-items: center;
    background: rgba(99,102,241,0.2);
    border: 1px solid rgba(99,102,241,0.4);
    border-radius: 20px; padding: 4px 14px;
    font-size: 0.8rem; color: #a5b4fc; font-weight: 500; margin-bottom: 16px;
}
.hero-title {
    font-size: 2.6rem; font-weight: 800;
    background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 50%, #a5b4fc 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; margin: 0; line-height: 1.2;
}
.hero-sub { font-size: 1.05rem; color: #a5b4fc; margin-top: 12px; max-width: 620px; }
.card {
    background: rgba(17,24,39,0.7); border: 1px solid #1e293b;
    border-radius: 16px; padding: 24px; margin-bottom: 20px;
}
.card-title {
    font-size: 0.82rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.08em; color: #6366f1; margin-bottom: 12px;
}
.stage-card {
    background: rgba(15,23,42,0.8); border: 1px solid #1e293b;
    border-radius: 12px; padding: 16px; text-align: center;
}
.stage-card.active { border-color:#6366f1; background:rgba(99,102,241,0.08); box-shadow:0 0 20px rgba(99,102,241,0.2); }
.stage-card.done   { border-color:#10b981; background:rgba(16,185,129,0.06); }
.stage-card.waiting { opacity:0.45; }
.stage-icon { font-size:1.8rem; display:block; margin-bottom:8px; }
.stage-name { font-weight:600; font-size:0.9rem; color:#e2e8f0; }
.stage-desc { font-size:0.75rem; color:#64748b; margin-top:4px; }
.stage-status { font-size:0.72rem; font-weight:600; margin-top:8px; padding:3px 10px; border-radius:10px; display:inline-block; }
.s-wait { background:#1e293b; color:#475569; }
.s-run  { background:rgba(99,102,241,0.2); color:#818cf8; animation:pulse 1.5s ease-in-out infinite; }
.s-done { background:rgba(16,185,129,0.15); color:#34d399; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.6} }
.qgrid { display:grid; grid-template-columns:repeat(3,1fr); gap:16px; margin-top:12px; }
.qmet  { background:rgba(15,23,42,0.6); border:1px solid #1e293b; border-radius:12px; padding:16px; text-align:center; }
.qval  { font-size:2rem; font-weight:800; background:linear-gradient(135deg,#818cf8,#6366f1);
         -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.qlbl  { font-size:0.78rem; color:#64748b; font-weight:500; margin-top:4px; text-transform:uppercase; letter-spacing:0.06em; }
.pbadge { display:inline-flex; align-items:center; padding:6px 16px; border-radius:20px; font-weight:600; font-size:0.85rem; }
.p-yes { background:rgba(16,185,129,0.15); color:#34d399; border:1px solid rgba(16,185,129,0.3); }
.p-no  { background:rgba(239,68,68,0.12);  color:#f87171;  border:1px solid rgba(239,68,68,0.3); }
.task-chip {
    display:inline-flex; align-items:flex-start; gap:10px;
    background:rgba(99,102,241,0.06); border:1px solid rgba(99,102,241,0.15);
    border-radius:10px; padding:10px 14px; margin:5px 0;
    width:100%; font-size:0.88rem; color:#c7d2fe; line-height:1.4;
}
.task-num {
    background:rgba(99,102,241,0.25); border-radius:6px; padding:1px 7px;
    font-size:0.75rem; font-weight:700; color:#818cf8; flex-shrink:0; margin-top:1px;
}
.server-ok   { color:#34d399; font-size:0.8rem; font-weight:600; }
.server-fail { color:#f87171; font-size:0.8rem; font-weight:600; }
.stDownloadButton > button {
    background: linear-gradient(135deg,#6366f1 0%,#4f46e5 100%) !important;
    color: white !important; border: none !important; border-radius: 12px !important;
    padding: 14px 32px !important; font-weight: 700 !important;
    width: 100% !important; box-shadow: 0 4px 15px rgba(99,102,241,0.4) !important;
}
.stTextArea textarea {
    background: rgba(15,23,42,0.8) !important; border: 1px solid #1e293b !important;
    border-radius: 12px !important; color: #e2e8f0 !important;
}
hr { border-color: #1e293b; }
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0d0f1a; }
::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
STAGES = [
    {"key": "plan",   "icon": "🧠", "name": "Planner",  "desc": "Classifies doc type & plans tasks"},
    {"key": "draft",  "icon": "✍️", "name": "Executor",  "desc": "Writes the full Markdown draft"},
    {"key": "review", "icon": "🔍", "name": "Reflector", "desc": "Reviews with real tool calls"},
    {"key": "render", "icon": "📄", "name": "Renderer",  "desc": "Exports to polished .docx"},
]

EXAMPLES = [
    "Write a detailed business proposal for an AI-powered inventory management SaaS targeting mid-sized retailers, including market analysis, solution overview, pricing model, and implementation roadmap.",
    "Create a comprehensive technical report on the security architecture for a zero-trust cloud infrastructure, covering threat models, authentication flows, encryption standards, and audit procedures.",
    "Draft a project proposal for building a community solar initiative in an urban neighborhood, including stakeholder analysis, financial projections, regulatory considerations, and a 12-month timeline.",
    "Write a product requirements document for a mobile health tracking app that monitors sleep, exercise, and nutrition, with wearable device integration and AI-driven insights.",
]

# ── Helpers ───────────────────────────────────────────────────────────────────
def render_stages(current=None, done=None):
    done = done or set()
    cols = st.columns(4)
    for i, s in enumerate(STAGES):
        k = s["key"]
        is_done = k in done
        is_act  = (k == current) and not is_done
        cc  = "stage-card done"  if is_done else ("stage-card active" if is_act else "stage-card waiting")
        sc  = "s-done"           if is_done else ("s-run"             if is_act else "s-wait")
        stx = "✓ Done"           if is_done else ("⟳ Running…"        if is_act else "Pending")
        with cols[i]:
            st.markdown(
                f'<div class="{cc}"><span class="stage-icon">{s["icon"]}</span>'
                f'<div class="stage-name">{s["name"]}</div>'
                f'<div class="stage-desc">{s["desc"]}</div>'
                f'<span class="stage-status {sc}">{stx}</span></div>',
                unsafe_allow_html=True,
            )


def check_server(base_url: str) -> tuple[bool, str]:
    """Ping /health and return (ok, message)."""
    try:
        r = requests.get(f"{base_url}/health", timeout=3)
        if r.status_code == 200:
            return True, "Server is online"
        return False, f"Server returned HTTP {r.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Cannot reach server — is uvicorn running?"
    except requests.exceptions.Timeout:
        return False, "Server timed out"
    except Exception as e:
        return False, str(e)


def call_agent(base_url: str, request_text: str, timeout: int) -> dict:
    """POST /agent and return the JSON response dict (raises on error)."""
    resp = requests.post(
        f"{base_url}/agent",
        json={"request": request_text},
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()


def download_doc(base_url: str, download_url: str, timeout: int) -> bytes:
    """GET the download_url and return raw bytes."""
    full_url = f"{base_url}{download_url}"
    resp = requests.get(full_url, timeout=timeout)
    resp.raise_for_status()
    return resp.content


def render_quality_report(qr: dict):
    pc = "p-yes" if qr["passed"] else "p-no"
    pt = "✓ Quality Check Passed" if qr["passed"] else "✗ Quality Check Failed"
    st.markdown(
        f'<div style="margin-bottom:16px;"><span class="pbadge {pc}">{pt}</span></div>'
        f'<div class="qgrid">'
        f'<div class="qmet"><div class="qval">{qr["word_count"]:,}</div><div class="qlbl">Words</div></div>'
        f'<div class="qmet"><div class="qval">{qr["heading_count"]}</div><div class="qlbl">Headings</div></div>'
        f'<div class="qmet"><div class="qval">{qr["bullet_count"]}</div><div class="qlbl">Bullets</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )
    for issue in (qr.get("issues") or []):
        st.warning(f"⚠️ {issue}")


def render_tasks(tasks: list):
    for i, t in enumerate(tasks, 1):
        st.markdown(
            f'<div class="task-chip"><span class="task-num">{i}</span><span>{t}</span></div>',
            unsafe_allow_html=True,
        )


# ── Session state ─────────────────────────────────────────────────────────────
for k, v in {"result": None, "doc_bytes": None, "error": None, "elapsed": None, "generating": False}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div style="text-align:center;padding:16px 0 24px;">'
        '<div style="font-size:3rem;margin-bottom:8px;">🤖</div>'
        '<div style="font-size:1.1rem;font-weight:700;color:#e2e8f0;">Document Agent</div>'
        '<div style="font-size:0.78rem;color:#64748b;margin-top:4px;">v2.0.0 · Groq + Mistral</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("### 🔌 API Server")
    base_url = st.text_input(
        "FastAPI base URL",
        value="http://localhost:8000",
        help="Where your uvicorn server is running",
        label_visibility="collapsed",
    )
    timeout_s = st.slider("Request timeout (s)", 30, 300, 120, 10)

    ok, msg = check_server(base_url)
    cls = "server-ok" if ok else "server-fail"
    icon = "🟢" if ok else "🔴"
    st.markdown(f'<span class="{cls}">{icon} {msg}</span>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 💡 Example Prompts")
    for idx, p in enumerate(EXAMPLES):
        if st.button(p[:72] + "…", key=f"ex_{idx}", use_container_width=True):
            st.session_state["prefill"] = p

    st.markdown("---")
    st.markdown("### ⚙️ Pipeline")
    st.markdown(
        '<div style="font-size:0.82rem;color:#64748b;line-height:2.1;">'
        '<div>🧠 <b style="color:#a5b4fc">Planner</b> — classify & decompose</div>'
        '<div>✍️ <b style="color:#a5b4fc">Executor</b> — draft the document</div>'
        '<div>🔍 <b style="color:#a5b4fc">Reflector</b> — review with tools</div>'
        '<div>📄 <b style="color:#a5b4fc">Renderer</b> — export to .docx</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.caption("Calls your FastAPI server via HTTP — same as Postman.")

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="hero">'
    '<div class="hero-badge">🚀 Autonomous AI Agent</div>'
    '<div class="hero-title">Autonomous Document Agent</div>'
    '<div class="hero-sub">Describe any document in plain English. The agent plans, drafts, reviews, and renders a polished Word file — autonomously.</div>'
    '</div>',
    unsafe_allow_html=True,
)

# ── Input ─────────────────────────────────────────────────────────────────────
prefill = st.session_state.pop("prefill", "")
c1, c2 = st.columns([3, 1], gap="large")

with c1:
    st.markdown('<div class="card-title">📝 What document do you need?</div>', unsafe_allow_html=True)
    user_req = st.text_area(
        "request", value=prefill,
        placeholder="e.g. Write a business proposal for an AI-powered supply chain platform targeting Fortune 500 companies, including market analysis and implementation roadmap…",
        height=150, label_visibility="collapsed", key="req_input",
    )
    n = len(user_req.strip())
    c = "#ef4444" if n < 10 or n > 4000 else "#10b981"
    st.markdown(
        f'<div style="font-size:0.78rem;color:{c};text-align:right;margin-top:-8px;">{n} / 4000</div>',
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        '<div class="card" style="min-height:145px;">'
        '<div class="card-title">How it works</div>'
        '<div style="font-size:0.82rem;color:#94a3b8;line-height:2.1;">'
        '1️⃣ Start your FastAPI server<br>'
        '2️⃣ Describe your document<br>'
        '3️⃣ Click Generate<br>'
        '4️⃣ Download the .docx'
        '</div></div>',
        unsafe_allow_html=True,
    )

_, bcol, _ = st.columns([1, 2, 1])
with bcol:
    clicked = st.button(
        "⚡ Generate Document",
        type="primary",
        disabled=(n < 10 or n > 4000 or st.session_state["generating"] or not ok),
        use_container_width=True,
        key="gen_btn",
    )
    if not ok:
        st.caption("⚠️ Start your FastAPI server first: `uvicorn app.main:app --reload`")

st.markdown("---")

# ── Generation ────────────────────────────────────────────────────────────────
if clicked and not st.session_state["generating"]:
    st.session_state.update({"result": None, "doc_bytes": None, "error": None, "elapsed": None, "generating": True})

    pipe_ph = st.empty()
    stat_ph = st.empty()
    done_set: set = set()

    def upd(cur=None):
        with pipe_ph.container():
            render_stages(current=cur, done=done_set)

    # Show animated pipeline — stages advance on estimated timing
    # (actual pipeline is synchronous from the HTTP call)
    upd("plan")
    stat_ph.info("🧠 Calling **POST /agent** on your FastAPI server…")
    t0 = time.perf_counter()

    try:
        # Single blocking HTTP call — exactly what Postman does
        result = call_agent(base_url, user_req.strip(), timeout_s)

        # Animate stages instantly after response
        for stage in ["plan", "draft", "review", "render"]:
            done_set.add(stage)
        upd(None)

        # Fetch the docx bytes
        stat_ph.info("📄 Downloading generated .docx…")
        doc_bytes = download_doc(base_url, result["download_url"], timeout=30)

        elapsed = time.perf_counter() - t0
        stat_ph.success(f"✅ Document generated in {elapsed:.1f}s!")
        st.session_state["result"]    = result
        st.session_state["doc_bytes"] = doc_bytes
        st.session_state["elapsed"]   = elapsed

    except requests.exceptions.ConnectionError as e:
        stat_ph.empty()
        st.session_state["error"] = (
            f"**Cannot connect to `{base_url}`**\n\n"
            f"Make sure your FastAPI server is running:\n"
            f"```\nuvicorn app.main:app --reload\n```\n\n"
            f"Raw error: `{e}`"
        )
    except requests.exceptions.Timeout:
        stat_ph.empty()
        st.session_state["error"] = (
            f"**Request timed out after {timeout_s}s.**\n\n"
            "The LLM is taking longer than expected. Try increasing the timeout in the sidebar."
        )
    except requests.exceptions.HTTPError as e:
        stat_ph.empty()
        try:
            detail = e.response.json()
            msg = detail.get("message") or detail.get("detail") or str(detail)
        except Exception:
            msg = e.response.text
        st.session_state["error"] = (
            f"**Server returned HTTP {e.response.status_code}**\n\n"
            f"{msg}\n\n"
            f"Check your FastAPI server logs for the full traceback."
        )
    except Exception as e:
        stat_ph.empty()
        st.session_state["error"] = f"**Unexpected error:** {e}"
    finally:
        st.session_state["generating"] = False

# ── Results ───────────────────────────────────────────────────────────────────
if st.session_state["result"] is not None:
    result = st.session_state["result"]
    el     = st.session_state["elapsed"]
    qr     = result.get("quality_report", {})

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📑 Document Type", result.get("document_type", "—").replace("-", " ").title())
    m2.metric("⏱ Time",          f"{el:.1f}s")
    m3.metric("📝 Words",         f'{qr.get("word_count", 0):,}')
    m4.metric("✅ QA",            "Passed" if qr.get("passed") else "Failed")

    st.markdown("---")
    lc, rc = st.columns([3, 2], gap="large")

    with lc:
        st.markdown('<div class="card-title">🧠 Execution Tasks</div>', unsafe_allow_html=True)
        render_tasks(result.get("tasks", []))
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="card-title">🔑 Document ID</div>', unsafe_allow_html=True)
        st.code(result.get("document_id", ""), language=None)

    with rc:
        st.markdown('<div class="card-title">🔍 Quality Report</div>', unsafe_allow_html=True)
        render_quality_report(qr)
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="card-title">⬇️ Download</div>', unsafe_allow_html=True)
        if st.session_state["doc_bytes"]:
            doc_type = result.get("document_type", "document").replace(" ", "_")
            fname = f"{doc_type}_{result.get('document_id', 'output')[:8]}.docx"
            st.download_button(
                "⬇️  Download Word Document (.docx)",
                data=st.session_state["doc_bytes"],
                file_name=fname,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
            st.caption(f"📁 {fname}")
        else:
            st.warning("Could not fetch the .docx file.")

elif st.session_state["error"]:
    st.markdown("---")
    st.error(st.session_state["error"])

else:
    st.markdown(
        '<div style="text-align:center;padding:48px 0;">'
        '<div style="font-size:4rem;margin-bottom:16px;">📄</div>'
        '<div style="font-size:1.2rem;font-weight:600;color:#475569;">Your document will appear here</div>'
        '<div style="font-size:0.9rem;color:#334155;margin-top:8px;">Enter a request above and click <b>Generate Document</b>.</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    render_stages()
