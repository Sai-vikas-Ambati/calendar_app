# 📅 CalBot — Google Calendar Scheduling Assistant

A conversational AI assistant that manages a calendar through natural chat. Built with **Groq API** (Llama 3.3 70B with native tool calling), **Streamlit**, and **MongoDB Atlas** for persistent storage.

> **Only 2 keys needed** — `GROQ_API_KEY` from [Groq Console](https://console.groq.com) and a `MONGODB_URI` connection string. No OAuth, no Google Cloud setup required.

### 🌐 [Live Demo →](https://calendarapp-5ajkmlfy4sokfrcr5dtrmf.streamlit.app/)

![CalBot Demo](screenshots/calbot_demo.png)

---

## ✨ Features

- **Natural Language Scheduling** — create, list, update, and cancel events through conversation
- **Smart Tool Calling** — the LLM decides which calendar operation to perform based on user input
- **Multi-Step Operations** — e.g., "Move my standup to 11am" triggers list → find ID → update
- **Availability Checking** — detects time-slot overlaps with existing events
- **Relative Date Understanding** — handles "today", "tomorrow", "next Monday", etc.
- **Pre-Populated Demo Data** — 3 sample events seeded on first run
- **MongoDB Persistence** — calendar data survives app restarts

---

## 📋 Prerequisites

- **Python 3.9+**
- **Groq API Key** — free from [Groq Console](https://console.groq.com)
- **MongoDB Atlas** — free tier at [mongodb.com](https://www.mongodb.com/atlas)

---

## 🚀 Setup & Run

### 1. Clone / Download the project

```bash
cd calendar_assistant
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API Key

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_api_key_here
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
```

### 4. Run the app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## 💬 Example Conversations

### Schedule an Event
```
You:  Schedule a project kickoff meeting tomorrow at 2pm for 1 hour
Bot:  Done! I've scheduled 'Project Kickoff Meeting' for 2026-02-22
      at 02:00 PM – 03:00 PM. Event ID: EVT004
```

### List Events
```
You:  What do I have on Feb 23?
Bot:  You have 2 events on 2026-02-23:
      • [EVT001] Team Standup — 10:00 AM to 10:30 AM
      • [EVT002] Project Review — 02:00 PM to 03:00 PM
```

### Check Availability
```
You:  Am I free at 2:30pm on Feb 23?
Bot:  You're busy — Project Review runs from 02:00 PM to 03:00 PM.
```

### Update an Event
```
You:  Move my standup to 11am
Bot:  Team Standup (EVT001) updated!
      • Old: 2026-02-23 10:00 AM – 10:30 AM
      • New: 2026-02-23 11:00 AM – 11:30 AM
```

### Cancel an Event
```
You:  Cancel the project review
Bot:  Are you sure you want to cancel 'Project Review'?
You:  Yes
Bot:  Done! Project Review has been cancelled.
```

---

## 🏗️ Architecture
```mermaid
flowchart TD
    A([👤 User]) -->|Types message| B[🖥️ Streamlit UI\napp.py]
    
    B -->|Message + Chat History\n+ Tool Definitions| C[🤖 Groq LLM\nLlama 3.3 70B]
    
    C -->|Direct text response| B
    C -->|Tool call request| D[⚙️ Tool Router\ngroq_client.py]
    
    D --> E{Which Tool?}
    
    E -->|create_event| T1[📝 Create Event]
    E -->|list_events| T2[📋 List Events]
    E -->|check_availability| T3[🔍 Check Availability]
    E -->|update_event| T4[✏️ Update Event]
    E -->|delete_event| T5[🗑️ Delete Event]
    
    T1 & T2 & T3 & T4 & T5 -->|Read / Write| F[(🗄️ MongoDB Atlas)]
    
    F -->|Result| D
    D -->|Tool result| C
    B -->|Display response| A
```

---

## 📁 Project Structure

```
calendar_assistant/
├── app.py                  # Streamlit UI and chat loop
├── tools.py                # 5 mock calendar tool functions
├── groq_client.py          # Groq API setup and tool calling logic
├── mock_calendar.py        # Initial mock calendar data and helpers
├── requirements.txt        # Python dependencies
├── .env                    # GROQ_API_KEY (create this)
├── .gitignore              # Ignores .env, __pycache__, etc.
└── README.md               # This file
```

| File | Purpose |
|------|---------|
| `app.py` | Streamlit chat interface, sidebar, session state management |
| `tools.py` | `create_event`, `list_events`, `check_availability`, `update_event`, `delete_event` |
| `groq_client.py` | Groq API config, function declarations, multi-step tool-call loop |
| `mock_calendar.py` | Default event data, ID generation, session initialization |

---

## 🔧 How Tool Calling Works

1. User types a message in the chat
2. Message is sent to Groq (Llama 3.3 70B) along with 5 tool/function declarations
3. The LLM decides whether to call a tool (or respond directly)
4. If a function call is returned, the app executes the corresponding Python function
5. The function result is sent back to the LLM
6. Steps 3–5 repeat for multi-step operations
7. The LLM generates a natural language response for the user

---

## ⚠️ Notes

- Calendar data is **persisted in MongoDB Atlas** — survives app restarts
- If MongoDB is unavailable, falls back to in-memory (like before)
- Default timezone is **IST (Asia/Kolkata)**
- Uses **Groq API** with **Llama 3.3 70B Versatile** for fast responses with tool calling
- All 5 tool functions return strings and never raise exceptions — the app will never crash

---

## 📜 License
