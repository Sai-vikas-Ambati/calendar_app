"""
mock_calendar.py
----------------
In-memory mock calendar data store and helper functions.
The calendar persists in Streamlit's session_state during the app session
and resets when the app restarts.
"""

# Default mock calendar events — realistic sample data for demo
DEFAULT_CALENDAR = {
    "EVT001": {
        "title": "Team Standup",
        "date": "2026-02-23",
        "start_time": "10:00",
        "end_time": "10:30",
        "description": "Daily team sync",
    },
    "EVT002": {
        "title": "Project Review",
        "date": "2026-02-23",
        "start_time": "14:00",
        "end_time": "15:00",
        "description": "Q1 project review meeting",
    },
    "EVT003": {
        "title": "Client Call",
        "date": "2026-02-24",
        "start_time": "11:00",
        "end_time": "11:30",
        "description": "Weekly client update call",
    },
}


def get_next_event_id(calendar: dict) -> str:
    """Generate the next sequential event ID (e.g. EVT004, EVT005, …)."""
    if not calendar:
        return "EVT001"
    max_num = max(int(eid.replace("EVT", "")) for eid in calendar)
    return f"EVT{max_num + 1:03d}"


def init_calendar(session_state) -> dict:
    """
    Initialize the mock calendar in Streamlit session_state.
    Returns the calendar dict (creates a copy on first call so the
    default data is never mutated).
    """
    if "calendar" not in session_state:
        import copy
        session_state.calendar = copy.deepcopy(DEFAULT_CALENDAR)
    return session_state.calendar
