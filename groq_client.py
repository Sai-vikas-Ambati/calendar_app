"""
groq_client.py
--------------
Groq API configuration, tool/function declarations, and the chat
processing loop that handles multi-step tool calling.
Uses Groq's LLM (Llama 3.3 70B) with native function-calling support.
"""

import os
import json
from datetime import datetime
import pytz
from dotenv import load_dotenv
from groq import Groq
import streamlit as st

from tools import (
    create_event,
    list_events,
    check_availability,
    update_event,
    delete_event,
)

load_dotenv()

IST = pytz.timezone("Asia/Kolkata")


def _get_secret(key: str) -> str:
    """Read a secret from st.secrets (Streamlit Cloud) or .env (local)."""
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key, "")


# ── Configure Groq Client ───────────────────────────────────────────────────
client = Groq(api_key=_get_secret("GROQ_API_KEY"))

MODEL_NAME = "llama-3.3-70b-versatile"

# ── Tool / Function Declarations (OpenAI-compatible format) ─────────────────
TOOL_DECLARATIONS = [
    {
        "type": "function",
        "function": {
            "name": "create_event",
            "description": (
                "Create a new calendar event. Call this when the user wants "
                "to schedule, add, or book a meeting/event."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title / name of the event",
                    },
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format",
                    },
                    "time": {
                        "type": "string",
                        "description": "Start time in HH:MM 24-hour format",
                    },
                    "duration_minutes": {
                        "type": "integer",
                        "description": "Duration of the event in minutes",
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional description of the event",
                    },
                },
                "required": ["title", "date", "time", "duration_minutes"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_events",
            "description": (
                "List all calendar events for a specific date. "
                "Call this when user asks what meetings/events they have."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format",
                    },
                },
                "required": ["date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": (
                "Check if a specific time slot is available on a given date. "
                "Call this when user asks if they are free at a certain time."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format",
                    },
                    "time": {
                        "type": "string",
                        "description": "Start time in HH:MM 24-hour format",
                    },
                    "duration_minutes": {
                        "type": "integer",
                        "description": "Duration to check in minutes (default 30)",
                    },
                },
                "required": ["date", "time", "duration_minutes"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_event",
            "description": (
                "Update the date and/or time of an existing event. "
                "Requires the event ID. If the user refers to an event by "
                "name, first call list_events to find the ID."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "string",
                        "description": "Event ID (e.g. EVT001)",
                    },
                    "new_date": {
                        "type": "string",
                        "description": "New date in YYYY-MM-DD (leave empty to keep current)",
                    },
                    "new_time": {
                        "type": "string",
                        "description": "New start time in HH:MM 24-hour format (leave empty to keep current)",
                    },
                },
                "required": ["event_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_event",
            "description": (
                "Delete / cancel an existing event by its event ID. "
                "If the user refers to an event by name, first call "
                "list_events to find the correct ID."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "string",
                        "description": "Event ID to delete (e.g. EVT002)",
                    },
                },
                "required": ["event_id"],
            },
        },
    },
]

# ── Map function names → Python callables ───────────────────────────────────
TOOL_MAP = {
    "create_event": create_event,
    "list_events": list_events,
    "check_availability": check_availability,
    "update_event": update_event,
    "delete_event": delete_event,
}


def _build_system_prompt() -> str:
    """Build the system prompt with today's date injected at runtime."""
    now = datetime.now(IST)
    today_str = now.strftime("%A, %B %d, %Y")
    today_iso = now.strftime("%Y-%m-%d")

    return (
        "You are a helpful and professional calendar assistant named CalBot.\n"
        "You help users manage their calendar through natural conversation.\n\n"
        "RULES:\n"
        "- Always confirm details before creating events.\n"
        "- Always ask for confirmation before deleting events.\n"
        "- When user refers to a meeting by name or time without providing an "
        "event ID, first call list_events to find the correct event ID before "
        "updating or deleting.\n"
        "- Understand relative dates naturally — today, tomorrow, next Monday, "
        "this Friday.\n"
        f"- Today's date is {today_str} ({today_iso}).\n"
        "- Use YYYY-MM-DD format for all dates when calling tools.\n"
        "- Use HH:MM 24-hour format for all times when calling tools.\n"
        "- Be concise, friendly, and professional.\n"
        "- If user does not specify duration, assume 30 minutes.\n"
        "- When listing or checking events, always resolve relative dates "
        "(today, tomorrow, etc.) to the actual YYYY-MM-DD date."
    )


def create_chat_session():
    """
    Create a new chat session as a list of messages.
    Groq uses a stateless API, so we manage history ourselves.
    """
    return [{"role": "system", "content": _build_system_prompt()}]


def process_chat(chat_history: list, user_message: str, calendar: dict) -> str:
    """
    Send a user message through Groq with tool-calling support.
    Handles the multi-step tool-calling loop:
      1. Append user message to history
      2. Call Groq API with tools
      3. If response contains tool_calls, execute them
      4. Append tool results and call API again
      5. Repeat until we get a text response
    Returns the final assistant text.
    """
    try:
        # Add user message to history
        chat_history.append({"role": "user", "content": user_message})

        # Loop to handle multi-step tool calls
        max_iterations = 10  # Safety limit
        for _ in range(max_iterations):
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=chat_history,
                tools=TOOL_DECLARATIONS,
                tool_choice="auto",
            )

            assistant_msg = response.choices[0].message

            # Check if there are tool calls
            if assistant_msg.tool_calls:
                # Add assistant message (with tool calls) to history
                chat_history.append({
                    "role": "assistant",
                    "content": assistant_msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in assistant_msg.tool_calls
                    ],
                })

                # Execute each tool call and add results
                for tool_call in assistant_msg.tool_calls:
                    fn_name = tool_call.function.name
                    fn_args = json.loads(tool_call.function.arguments)

                    if fn_name in TOOL_MAP:
                        tool_fn = TOOL_MAP[fn_name]
                        result = tool_fn(calendar, **fn_args)
                    else:
                        result = f"Unknown tool: {fn_name}"

                    # Add tool result to history
                    chat_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    })
            else:
                # No tool calls — we have the final text response
                reply = assistant_msg.content or "I processed your request."
                chat_history.append({"role": "assistant", "content": reply})
                return reply

        return "I'm sorry, I had trouble processing that request. Please try again."

    except Exception as e:
        return (
            f"I'm sorry, I encountered an error while processing your request. "
            f"Please try again.\n\n_(Error detail: {str(e)})_"
        )
