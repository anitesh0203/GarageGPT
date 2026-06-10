"""
GarageGPT — Streamlit UI
Run: streamlit run app.py
"""

import os
import streamlit as st
from dotenv import load_dotenv
from agent.orchestrator import Orchestrator

load_dotenv()

st.set_page_config(page_title="GarageGPT", page_icon="🚗", layout="centered")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0f1117; color: #e2e8f0; }
    .header { text-align: center; padding: 2rem 0 1rem; }
    .header h1 { font-family: 'Space Grotesk', sans-serif; font-size: 2.4rem; font-weight: 700; color: #f8fafc; letter-spacing: -0.02em; margin: 0; }
    .header h1 span { color: #38bdf8; }
    .header p { color: #64748b; font-size: 0.95rem; margin-top: 0.4rem; }
    .chat-bubble-user { background: #1e293b; border: 1px solid #334155; border-radius: 12px 12px 2px 12px; padding: 12px 16px; margin: 8px 0; color: #e2e8f0; font-size: 0.95rem; max-width: 85%; margin-left: auto; }
    .chat-bubble-bot { background: #0f2744; border: 1px solid #1e3a5f; border-radius: 2px 12px 12px 12px; padding: 12px 16px; margin: 8px 0; color: #e2e8f0; font-size: 0.95rem; max-width: 90%; }
    .agent-badge { display: inline-block; font-size: 0.72rem; font-weight: 600; padding: 2px 8px; border-radius: 999px; margin-bottom: 6px; letter-spacing: 0.04em; text-transform: uppercase; }
    .badge-bot { background: #0e4d92; color: #93c5fd; }
    .stTextInput > div > div > input { background: #1e293b !important; border: 1px solid #334155 !important; color: #f1f5f9 !important; border-radius: 10px !important; padding: 12px 16px !important; }
    .stTextInput > div > div > input:focus { border-color: #38bdf8 !important; box-shadow: 0 0 0 2px #38bdf822 !important; }
    .stButton > button { background: #0ea5e9 !important; color: #fff !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; font-size: 0.9rem !important; }
    .stButton > button:hover { background: #0284c7 !important; }
    footer { visibility: hidden; }
    .stDeployButton { display: none; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header">
    <h1>Garage<span>GPT</span></h1>
    <p>AI-powered car buying advisor · Real US listings · Multi-agent reasoning</p>
</div>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "agent" not in st.session_state:
    st.session_state.agent = Orchestrator(verbose=False)
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Suggestion chips (only shown before first message) ───────────────────────
if not st.session_state.messages:
    st.markdown("**Try asking:**")
    suggestions = [
        "Find me a reliable SUV under $30,000",
        "Compare Honda CR-V and Toyota RAV4 on safety and cost",
        "Find me a 2022 BMW X3 near Bridgewater NJ",
        "Is the Mazda CX-5 a good deal to negotiate?",
    ]
    cols = st.columns(2)
    for i, s in enumerate(suggestions):
        if cols[i % 2].button(s, key=f"sug_{i}"):
            st.session_state.pending_query = s

# ── Chat history ──────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="chat-bubble-user">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div class="chat-bubble-bot">'
            f'<span class="agent-badge badge-bot">GarageGPT</span><br>{msg["content"]}'
            f'</div>',
            unsafe_allow_html=True,
        )

# ── Input form — using st.form prevents reruns on every keystroke ─────────────
with st.form(key="chat_form", clear_on_submit=True):
    col1, col2 = st.columns([5, 1])
    with col1:
        user_input = st.text_input(
            label="query",
            label_visibility="collapsed",
            placeholder="Ask about any car — make, model, budget, safety...",
            value=st.session_state.pop("pending_query", ""),
        )
    with col2:
        submitted = st.form_submit_button("Ask →")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Options")
    if st.button("🗑 Clear conversation"):
        st.session_state.messages = []
        st.session_state.agent.clear_history()
        st.rerun()
    st.markdown("---")
    st.markdown(f"**Turns:** {len(st.session_state.messages) // 2}")
    st.markdown(f"**History in context:** {min(len(st.session_state.agent.conversation_history), 3)} turn(s)")
    st.markdown("---")
    st.markdown("**Agents**")
    st.markdown("🔍 Research — listings + safety")
    st.markdown("💰 Budget — fuel + TCO")
    st.markdown("🤝 Negotiation — deal advice")

# ── Handle submission — only fires when form is submitted ─────────────────────
if submitted and user_input.strip():
    query = user_input.strip()
    st.session_state.messages.append({"role": "user", "content": query})

    with st.spinner("Researching..."):
        answer = st.session_state.agent.run(query)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()