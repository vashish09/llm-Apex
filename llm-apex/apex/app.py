# Libraries
import os
import json
import uuid
import datetime as dt
import requests
import streamlit as st

# -------------------------
# API and app config
# -------------------------
API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
SITE_URL = os.getenv("OPENROUTER_SITE_URL", "http://localhost:8501")
APP_NAME = os.getenv("OPENROUTER_APP_NAME", "APEX")

DEFAULT_MODELS =DEFAULT_MODELS = [
    "openai/gpt-4o-mini",
    "google/gemini-2.0-flash-001",
    "meta-llama/llama-3.1-8b-instruct",
    "google/gemma-2-9b-it",  
    "nvidia/nemotron-3-nano-30b-a3b:free",
]

st.set_page_config(page_title="APEX", layout="wide")

# -------------------------
# Chrome + styling
# -------------------------
st.markdown(
    """
    <style>
      #MainMenu {visibility: hidden;}
      header {visibility: hidden;}
      footer {visibility: hidden;}

      /* Light theme base */
      .stApp {
        background: radial-gradient(1200px circle at 10% 10%, #ffffff 0%, #f6f7fb 45%, #eef2ff 100%);
        color: #111827;
      }

      .apex-title {
        font-size: 56px;
        font-weight: 800;
        letter-spacing: 1px;
        text-align: center;
        margin-top: 22px;
        margin-bottom: 6px;
        color: #0f172a;
      }
      .apex-subtitle {
        text-align: center;
        color: rgba(15, 23, 42, 0.75);
        margin-bottom: 26px;
      }

      .card {
        background: rgba(255,255,255,0.75);
        border: 1px solid rgba(2, 6, 23, 0.08);
        border-radius: 18px;
        padding: 16px;
        box-shadow: 0 10px 30px rgba(2, 6, 23, 0.06);
      }

      /* Inputs */
      textarea, input {
        background-color: rgba(255,255,255,0.95) !important;
        color: #0f172a !important;
        border: 1px solid rgba(2, 6, 23, 0.14) !important;
        border-radius: 12px !important;
      }

      /* Buttons */
      .stButton button {
        background: linear-gradient(135deg, #4f46e5, #2563eb);
        color: white;
        border: 0;
        border-radius: 12px;
        padding: 0.65rem 1.05rem;
        font-weight: 700;
      }
      .stButton button:hover { filter: brightness(1.03); }

      .muted { color: rgba(15, 23, 42, 0.65); font-size: 14px; }
      .tiny { color: rgba(15, 23, 42, 0.55); font-size: 12px; }

      /* Make each column look like a panel */
      div[data-testid="column"] > div {
        background: rgba(255,255,255,0.78);
        border: 1px solid rgba(2, 6, 23, 0.10);
        border-radius: 16px;
        padding: 12px;
        box-shadow: 0 8px 20px rgba(2, 6, 23, 0.05);
      }

      /* Response text area look */
      .resp {
        white-space: pre-wrap;
        line-height: 1.35;
        color: #0f172a;
      }

      /* Links */
      a { color: #2563eb; }
      a:visited { color: #1d4ed8; }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------
# Minimal clipboard helper (JS)
# -------------------------
def copy_button(text: str, key: str, label: str = "Copy"):
    safe = json.dumps(text)  # JS-safe string
    st.components.v1.html(
        f"""
        <div style="display:flex; gap:8px; align-items:center; margin: 6px 0 10px 0; position: relative; z-index: 5;">
          <button id="btn-{key}" style="
              background: #2563eb;
              border: 1px solid rgba(2, 6, 23, 0.12);
              color: #ffffff;
              border-radius: 10px;
              padding: 7px 12px;
              cursor: pointer;
              font-weight: 700;
              font-size: 13px;
            ">{label}</button>
          <span id="ok-{key}" style="color: rgba(15, 23, 42, 0.7); font-size: 12px;"></span>
        </div>
        <script>
          const btn = document.getElementById("btn-{key}");
          const ok = document.getElementById("ok-{key}");
          btn.addEventListener("click", async () => {{
            try {{
              await navigator.clipboard.writeText({safe});
              ok.textContent = "Copied.";
              setTimeout(() => ok.textContent = "", 900);
            }} catch (e) {{
              ok.textContent = "Copy failed (browser blocked).";
              setTimeout(() => ok.textContent = "", 1500);
            }}
          }});
        </script>
        """,
        height=46,
    )

# -------------------------
# Session state
# -------------------------
if "view" not in st.session_state:
    st.session_state.view = "landing"  # landing | chat

if "username" not in st.session_state:
    st.session_state.username = ""

if "models" not in st.session_state:
    st.session_state.models = DEFAULT_MODELS[:]

if "history" not in st.session_state:
    # each item: {id, ts, username, models, temperature, prompt, responses:{model:text}}
    st.session_state.history = []

if "last_responses" not in st.session_state:
    st.session_state.last_responses = {}  # {model: text}

# -------------------------
# OpenRouter call
# -------------------------
def call_openrouter(model: str, messages, temperature: float):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": SITE_URL,
        "X-Title": APP_NAME,
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    if "application/json" in r.headers.get("content-type", ""):
        return r.status_code, r.json(), r.text
    return r.status_code, None, r.text

# -------------------------
# Sidebar: history
# -------------------------
with st.sidebar:
    st.markdown("## History")
    st.markdown('<div class="muted">Stored locally in this browser session.</div>', unsafe_allow_html=True)

    if st.session_state.history:
        for item in reversed(st.session_state.history[-30:]):
            label = f"{item['ts']} — {item.get('username','')} — {item['prompt'][:36]}".strip()
            if st.button(label, key=f"load-{item['id']}"):
                st.session_state.view = "chat"
                st.session_state.username = item.get("username", "")
                st.session_state.models = item.get("models", DEFAULT_MODELS[:])
                st.session_state.last_responses = item.get("responses", {})
                st.session_state._prefill_prompt = item.get("prompt", "")
                st.session_state._prefill_temp = item.get("temperature", 0.2)
                st.rerun()
    else:
        st.markdown('<div class="tiny">No history yet.</div>', unsafe_allow_html=True)

    st.divider()
    colA, colB = st.columns(2)
    with colA:
        if st.button("Clear history"):
            st.session_state.history = []
            st.session_state.last_responses = {}
            st.rerun()
    with colB:
        if st.session_state.history:
            st.download_button(
                "Export JSON",
                data=json.dumps(st.session_state.history, indent=2),
                file_name="apex-history.json",
                mime="application/json",
            )

# -------------------------
# Landing page
# -------------------------
def landing():
    # Click-anywhere overlay -> triggers "Start"
    st.components.v1.html(
        """
        <div class="landing-click" onclick="window.parent.postMessage({type:'APEX_START'}, '*')"></div>
        <script>
          window.addEventListener("message", (e) => {
            // no-op; reserved
          });
        </script>
        """,
        height=0,
    )

    # Message listener (Streamlit doesn't expose direct JS->python events),
    # so we provide a visible Start button too (reliable).
    st.markdown('<div class="landing-wrap">', unsafe_allow_html=True)

    st.markdown('<div class="apex-title">APEX</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="apex-subtitle">5 models. One prompt. Side-by-side answers.</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Get your OpenRouter API key")
    st.markdown(
        """
        <ol class="landing-steps">
          <li>Go to <a href="https://openrouter.ai" target="_blank">openrouter.ai</a> and sign in.</li>
          <li>Open <a href="https://openrouter.ai/keys" target="_blank">openrouter.ai/keys</a>.</li>
          <li>Create an API key and add it to your <code>docker-compose.yml</code> as <code>OPENROUTER_API_KEY</code>.</li>
          <li>Restart Docker: <code>docker compose down</code> then <code>docker compose up -d</code>.</li>
        </ol>
        """,
        unsafe_allow_html=True,
    )

    if not API_KEY:
        st.warning("This server does not have OPENROUTER_API_KEY set yet. Add it and restart, then come back.")
    else:
        st.success("API key detected on server. You can start.")

    st.markdown("### Your name")
    st.session_state.username = st.text_input("Username", value=st.session_state.username, placeholder="e.g., Vashish")

    col1, col2 = st.columns([1, 1])
    with col1:
        start_disabled = not bool(API_KEY)
        if st.button("Start", disabled=start_disabled, use_container_width=True):
            st.session_state.view = "chat"
            st.rerun()
    with col2:
        st.markdown('<div class="muted">Tip: Click Start (recommended). “Click anywhere” overlay depends on browser.</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # card
    st.markdown('</div>', unsafe_allow_html=True)  # landing-wrap

# -------------------------
# Chat page
# -------------------------
def chat():
    st.markdown("<h1 style='text-align:center; margin-top:10px;'>APEX</h1>", unsafe_allow_html=True)
    st.markdown("<div class='muted' style='text-align:center;'>Side-by-side model responses</div>", unsafe_allow_html=True)
    st.write("")

    if not API_KEY:
        st.error("OPENROUTER_API_KEY is not set. Add it in docker-compose.yml and restart.")
        st.stop()

    top = st.container()
    with top:
        c1, c2, c3 = st.columns([1.1, 1.2, 1.2])
        with c1:
            st.session_state.username = st.text_input("Username", value=st.session_state.username)
        with c2:
            temperature = st.slider("temperature", 0.0, 1.0, st.session_state.get("_prefill_temp", 0.2), 0.05)
        with c3:
            if st.button("New chat"):
                st.session_state.last_responses = {}
                st.session_state._prefill_prompt = ""
                st.session_state._prefill_temp = 0.2
                st.rerun()

    st.write("")
    cols = st.columns(5)
    models = []
    for i, c in enumerate(cols):
        with c:
            val = st.text_input(f"Model {i+1}", value=st.session_state.models[i] if i < len(st.session_state.models) else "")
            models.append(val.strip())
    # persist
    st.session_state.models = models

    st.write("")
    prompt = st.text_area(
        "Prompt",
        value=st.session_state.get("_prefill_prompt", "Explain photosynthesis in simple terms."),
        height=140,
        placeholder="Ask anything…",
    )

    run_col, back_col = st.columns([1, 1])
    with run_col:
        run = st.button("Run", use_container_width=True)
    with back_col:
        if st.button("Back to landing", use_container_width=True):
            st.session_state.view = "landing"
            st.rerun()

    # If we ran, call all models
    if run:
        # Basic message format; can be extended to multi-turn later
        messages = [{"role": "user", "content": prompt}]
        responses = {}

        out_cols = st.columns(5)
        for i, model in enumerate(models):
            with out_cols[i]:
                st.subheader(model or "(empty)")
                if not model:
                    st.info("Set a model id.")
                    continue

                try:
                    status, data, raw_text = call_openrouter(model, messages, temperature)
                    if status != 200 or not data:
                        st.error(f"HTTP {status}\n{raw_text[:2000]}")
                        continue
                    text = data["choices"][0]["message"]["content"]
                    responses[model] = text

                    copy_button(text, key=f"{uuid.uuid4().hex}", label="Copy")
                    st.markdown(f"<div class='resp'>{st._escape(text) if hasattr(st,'_escape') else text}</div>", unsafe_allow_html=True)
                except Exception as e:
                    st.error(str(e))

        # Save last + history
        st.session_state.last_responses = responses

        st.session_state.history.append(
            {
                "id": uuid.uuid4().hex,
                "ts": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "username": st.session_state.username,
                "models": models,
                "temperature": temperature,
                "prompt": prompt,
                "responses": responses,
            }
        )

        # clear prefill so next time is fresh unless user wants it
        st.session_state._prefill_prompt = prompt
        st.session_state._prefill_temp = temperature

    # Show last responses again (so you can copy even after rerun)
    if st.session_state.last_responses:
        st.divider()
        st.markdown("### Last responses (saved)")
        out_cols = st.columns(5)
        for i, model in enumerate(models):
            with out_cols[i]:
                st.subheader(model or "(empty)")
                if model in st.session_state.last_responses:
                    text = st.session_state.last_responses[model]
                    copy_button(text, key=f"saved-{i}-{uuid.uuid4().hex}", label="Copy")
                    st.write(text)

# -------------------------
# Router
# -------------------------
if st.session_state.view == "landing":
    landing()
else:
    chat()