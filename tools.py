"""
tools.py
--------
Five calendar tool functions used by the LLM's function-calling feature.
Each function operates on the in-memory mock calendar dictionary and
returns a plain-text string (never raises exceptions).
"""

from datetime import datetime, timedelta
import pytz

IST = pytz.timezone("Asia/Kolkata")


# ---------------------------------------------------------------------------
# 1. CREATE EVENT
# ---------------------------------------------------------------------------
def create_event(
    calendar: dict,
    title: str,
    date: str,
    time: str,
    duration_minutes: int,
    description: str = "",
) -> str:
    """Add a new event to the mock calendar."""
    try:
        from mock_calendar import get_next_event_id

        # Parse start time and calculate end time
        start_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        end_dt = start_dt + timedelta(minutes=int(duration_minutes))

        event_id = get_next_event_id(calendar)
        calendar[event_id] = {
            "title": title,
            "date": date,
            "start_time": start_dt.strftime("%H:%M"),
            "end_time": end_dt.strftime("%H:%M"),
            "description": description,
        }

        start_fmt = start_dt.strftime("%I:%M %p")
        end_fmt = end_dt.strftime("%I:%M %p")
        return (
            f"Event created successfully!\n"
            f"• Event ID: {event_id}\n"
            f"• Title: {title}\n"
            f"• Date: {date}\n"
            f"• Time: {start_fmt} – {end_fmt}\n"
            f"• Duration: {duration_minutes} minutes\n"
            f"• Description: {description}"
        )
    except Exception as e:
        return f"Error creating event: {str(e)}"


# ---------------------------------------------------------------------------
# 2. LIST EVENTS
# ---------------------------------------------------------------------------
def list_events(calendar: dict, date: str) -> str:
    """List all events for a given date."""
    try:
        events = [
            (eid, evt)
            for eid, evt in calendar.items()
            if evt["date"] == date
        ]

        if not events:
            return f"No events found on {date}. Your calendar is free! 🎉"

        # Sort by start time
        events.sort(key=lambda x: x[1]["start_time"])

        lines = [f"Events on {date} ({len(events)} found):"]
        for eid, evt in events:
            start_fmt = datetime.strptime(evt["start_time"], "%H:%M").strftime("%I:%M %p")
            end_fmt = datetime.strptime(evt["end_time"], "%H:%M").strftime("%I:%M %p")
            lines.append(
                f"• [{eid}] {evt['title']} — {start_fmt} to {end_fmt}"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"Error listing events: {str(e)}"


# ---------------------------------------------------------------------------
# 3. CHECK AVAILABILITY
# ---------------------------------------------------------------------------
def check_availability(
    calendar: dict, date: str, time: str, duration_minutes: int
) -> str:
    """Check if a time slot is available on the given date."""
    try:
        req_start = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        req_end = req_start + timedelta(minutes=int(duration_minutes))

        conflicts = []
        for eid, evt in calendar.items():
            if evt["date"] != date:
                continue
            evt_start = datetime.strptime(f"{date} {evt['start_time']}", "%Y-%m-%d %H:%M")
            evt_end = datetime.strptime(f"{date} {evt['end_time']}", "%Y-%m-%d %H:%M")

            # Overlap check: two ranges overlap if start1 < end2 AND start2 < end1
            if req_start < evt_end and evt_start < req_end:
                start_fmt = evt_start.strftime("%I:%M %p")
                end_fmt = evt_end.strftime("%I:%M %p")
                conflicts.append(
                    f"• [{eid}] {evt['title']} — {start_fmt} to {end_fmt}"
                )

        if not conflicts:
            start_fmt = req_start.strftime("%I:%M %p")
            end_fmt = req_end.strftime("%I:%M %p")
            return f"The slot {start_fmt} – {end_fmt} on {date} is available! ✅"

        return (
            f"The requested time slot is busy. Conflicting event(s):\n"
            + "\n".join(conflicts)
        )
    except Exception as e:
        return f"Error checking availability: {str(e)}"


# ---------------------------------------------------------------------------
# 4. UPDATE EVENT
# ---------------------------------------------------------------------------
def update_event(
    calendar: dict, event_id: str, new_date: str = "", new_time: str = ""
) -> str:
    """Update the date and/or time of an existing event."""
    try:
        event_id = event_id.upper()
        if event_id not in calendar:
            return (
                f"Event ID '{event_id}' not found. "
                f"Please list your events first to find the correct ID."
            )

        evt = calendar[event_id]
        old_date = evt["date"]
        old_start = evt["start_time"]
        old_end = evt["end_time"]

        # Calculate original duration to preserve it
        old_start_dt = datetime.strptime(old_start, "%H:%M")
        old_end_dt = datetime.strptime(old_end, "%H:%M")
        duration = old_end_dt - old_start_dt

        # Apply updates
        if new_date:
            evt["date"] = new_date
        if new_time:
            new_start_dt = datetime.strptime(new_time, "%H:%M")
            new_end_dt = new_start_dt + duration
            evt["start_time"] = new_start_dt.strftime("%H:%M")
            evt["end_time"] = new_end_dt.strftime("%H:%M")

        old_start_fmt = datetime.strptime(old_start, "%H:%M").strftime("%I:%M %p")
        old_end_fmt = datetime.strptime(old_end, "%H:%M").strftime("%I:%M %p")
        new_start_fmt = datetime.strptime(evt["start_time"], "%H:%M").strftime("%I:%M %p")
        new_end_fmt = datetime.strptime(evt["end_time"], "%H:%M").strftime("%I:%M %p")

        return (
            f"Event '{evt['title']}' ({event_id}) updated!\n"
            f"• Old: {old_date} {old_start_fmt} – {old_end_fmt}\n"
            f"• New: {evt['date']} {new_start_fmt} – {new_end_fmt}"
        )
    except Exception as e:
        return f"Error updating event: {str(e)}"


# ---------------------------------------------------------------------------
# 5. DELETE EVENT
# ---------------------------------------------------------------------------
def delete_event(calendar: dict, event_id: str) -> str:
    """Remove an event from the mock calendar by ID."""
    try:
        event_id = event_id.upper()
        if event_id not in calendar:
            return (
                f"Event ID '{event_id}' not found. "
                f"Please list your events first to find the correct ID."
            )

        evt = calendar.pop(event_id)
        start_fmt = datetime.strptime(evt["start_time"], "%H:%M").strftime("%I:%M %p")
        end_fmt = datetime.strptime(evt["end_time"], "%H:%M").strftime("%I:%M %p")
        return (
            f"Event cancelled successfully!\n"
            f"• Title: {evt['title']}\n"
            f"• Date: {evt['date']}\n"
            f"• Time: {start_fmt} – {end_fmt}\n"
            f"• Event ID: {event_id}"
        )
    except Exception as e:
        return f"Error deleting event: {str(e)}"
