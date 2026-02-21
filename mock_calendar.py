"""
mock_calendar.py
----------------
Calendar data store backed by MongoDB Atlas.
Data persists across app restarts. Falls back to in-memory
if MongoDB is unavailable.
"""

import os
import copy
from dotenv import load_dotenv

load_dotenv()

# Default mock calendar events — seeded on first run
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


# ── MongoDB Connection ──────────────────────────────────────────────────────
_db = None


def _get_db():
    """Get the MongoDB database connection (singleton)."""
    global _db
    if _db is None:
        try:
            from pymongo import MongoClient
            mongo_uri = os.getenv("MONGODB_URI")
            if mongo_uri:
                client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
                # Test connection
                client.admin.command("ping")
                _db = client["calendar_assistant"]
                print("✅ Connected to MongoDB Atlas")
            else:
                print("⚠️ No MONGODB_URI found — using in-memory only")
        except Exception as e:
            print(f"⚠️ MongoDB connection failed: {e} — using in-memory only")
    return _db


def _load_from_db() -> dict:
    """Load all events from MongoDB and return as a dict."""
    db = _get_db()
    if db is None:
        return None

    try:
        collection = db["events"]
        events = {}
        for doc in collection.find():
            event_id = doc["event_id"]
            events[event_id] = {
                "title": doc["title"],
                "date": doc["date"],
                "start_time": doc["start_time"],
                "end_time": doc["end_time"],
                "description": doc.get("description", ""),
            }
        return events
    except Exception as e:
        print(f"⚠️ Error loading from MongoDB: {e}")
        return None


def _seed_db(calendar: dict):
    """Seed MongoDB with default calendar events."""
    db = _get_db()
    if db is None:
        return

    try:
        collection = db["events"]
        for event_id, evt in calendar.items():
            collection.update_one(
                {"event_id": event_id},
                {"$set": {**evt, "event_id": event_id}},
                upsert=True,
            )
    except Exception as e:
        print(f"⚠️ Error seeding MongoDB: {e}")


def sync_to_db(calendar: dict):
    """
    Sync the entire in-memory calendar to MongoDB.
    Called after every create/update/delete operation.
    """
    db = _get_db()
    if db is None:
        return

    try:
        collection = db["events"]
        # Get current DB event IDs
        db_ids = set(doc["event_id"] for doc in collection.find({}, {"event_id": 1}))
        mem_ids = set(calendar.keys())

        # Delete events removed from memory
        removed = db_ids - mem_ids
        if removed:
            collection.delete_many({"event_id": {"$in": list(removed)}})

        # Upsert all current events
        for event_id, evt in calendar.items():
            collection.update_one(
                {"event_id": event_id},
                {"$set": {**evt, "event_id": event_id}},
                upsert=True,
            )
    except Exception as e:
        print(f"⚠️ Error syncing to MongoDB: {e}")


def get_next_event_id(calendar: dict) -> str:
    """Generate the next sequential event ID (e.g. EVT004, EVT005, …)."""
    if not calendar:
        return "EVT001"
    max_num = max(int(eid.replace("EVT", "")) for eid in calendar)
    return f"EVT{max_num + 1:03d}"


def init_calendar(session_state) -> dict:
    """
    Initialize the calendar:
    1. Try loading from MongoDB (persistent data)
    2. If empty/unavailable, seed with defaults
    3. Store in session_state for the current session
    """
    if "calendar" not in session_state:
        # Try loading from MongoDB first
        db_data = _load_from_db()

        if db_data is not None and len(db_data) > 0:
            # Loaded from DB — use persistent data
            session_state.calendar = db_data
        else:
            # No DB data — seed with defaults
            session_state.calendar = copy.deepcopy(DEFAULT_CALENDAR)
            _seed_db(session_state.calendar)

    return session_state.calendar
