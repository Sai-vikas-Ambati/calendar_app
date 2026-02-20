"""
app.py
------
Streamlit chat interface for CalBot — the Google Calendar Scheduling Assistant.
Run with:  streamlit run app.py
"""

import streamlit as st
from datetime import datetime
import pytz

from mock_calendar import init_calendar
from groq_client import create_chat_session, process_chat
from tools import list_events

IST = pytz.timezone("Asia/Kolkata")

# ── Page Configuration ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="CalBot — Calendar Assistant",
    page_icon="📅",
    layout="centered",
)

# ── Custom Styling ──────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Main header */
    .main-header {
        text-align: center;
        padding: 0.5rem 0 1rem 0;
    }
    .main-header h1 {
        font-size: 1.8rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .main-header p {
        color: #888;
        font-size: 0.95rem;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #e0e0ff;
    }
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] li,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div {
        color: #c0c0e0;
    }
    section[data-testid="stSidebar"] code {
        background: rgba(102, 126, 234, 0.15);
        color: #a3b1ff;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.82rem;
    }

    /* Event card in sidebar */
    .event-card {
        background: rgba(102, 126, 234, 0.12);
        border-left: 3px solid #667eea;
        padding: 8px 12px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 8px;
    }
    .event-card strong { color: #a3b1ff; }
    .event-card span { color: #8888bb; font-size: 0.85rem; }

    /* Chat message tweaks */
    .stChatMessage {
        border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Session State Initialization ────────────────────────────────────────────
calendar = init_calendar(st.session_state)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_session" not in st.session_state:
    st.session_state.chat_session = create_chat_session()

# ── Sidebar ─────────────────────────────────────────────────────────────────
now = datetime.now(IST)
today_iso = now.strftime("%Y-%m-%d")
today_display = now.strftime("%A, %B %d, %Y")

with st.sidebar:
    st.markdown("# 📅 CalBot")
    st.caption("Your AI Calendar Assistant")
    st.markdown("---")

    # Today's date info
    st.markdown(f"**🗓️ Today:** {today_display}")

    # Today's events
    st.markdown("### 📋 Today's Events")
    todays_events = [
        (eid, evt)
        for eid, evt in calendar.items()
        if evt["date"] == today_iso
    ]
    if todays_events:
        todays_events.sort(key=lambda x: x[1]["start_time"])
        for eid, evt in todays_events:
            start_fmt = datetime.strptime(evt["start_time"], "%H:%M").strftime(
                "%I:%M %p"
            )
            end_fmt = datetime.strptime(evt["end_time"], "%H:%M").strftime(
                "%I:%M %p"
            )
            st.markdown(
                f'<div class="event-card">'
                f"<strong>{evt['title']}</strong><br>"
                f"<span>{start_fmt} – {end_fmt}  •  {eid}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.info("No events today — your schedule is clear! 🎉")

    st.markdown("---")

    # Example commands
    st.markdown("### 💬 Try saying…")
    examples = [
        "Schedule a team standup tomorrow at 10am for 30 minutes",
        "What meetings do I have today?",
        "Am I free at 3pm today?",
        "Move my 10am standup to 11am",
        "Cancel my project review",
        "What do I have this week?",
    ]
    for ex in examples:
        st.markdown(f"- `{ex}`")

    st.markdown("---")
    st.caption("ℹ️ Calendar data is stored in-memory and resets on restart.")

# ── Main Chat Area ──────────────────────────────────────────────────────────
st.markdown(
    '<div class="main-header">'
    "<h1>📅 CalBot — Calendar Assistant</h1>"
    "<p>Manage your calendar through natural conversation</p>"
    "</div>",
    unsafe_allow_html=True,
)

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Welcome message on first load
if not st.session_state.messages:
    welcome = (
        "👋 Hi! I'm **CalBot**, your calendar assistant.\n\n"
        "I can help you **schedule**, **list**, **check availability**, "
        "**update**, or **cancel** events on your calendar.\n\n"
        "Just tell me what you need in plain English!"
    )
    with st.chat_message("assistant"):
        st.markdown(welcome)
    st.session_state.messages.append({"role": "assistant", "content": welcome})

# ── Chat Input ──────────────────────────────────────────────────────────────
if user_input := st.chat_input("Type your message…"):
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Process with Groq LLM
    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            reply = process_chat(
                st.session_state.chat_session,
                user_input,
                calendar,
            )
        st.markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})
