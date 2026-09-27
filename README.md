# IT Service Desk Copilot 🛠️

**IT Service Desk Copilot** is an enterprise-grade AI assistant built with the **Google Agent Development Kit (ADK)** and powered by **Gemini 2.5 Flash**. It assists IT support engineers and system administrators by managing support tickets, searching technical knowledge base articles, generating visual troubleshooting diagrams, and maintaining long-term memory across sessions.

---

## 🌟 Key Features

* **📚 Firestore Knowledge Base Search**:
  Queries technical resolution articles, tags, and categories stored in Google Cloud Firestore (`knowledge_base` collection) to provide fast diagnostic guidance for network, identity, database, and infrastructure issues.

* **📋 Support Ticket Lifecycle Management**:
  Provides complete CRUD operations on support tickets stored in Firestore (`support_tickets` collection):
  * `create_support_ticket`: Create new tickets with title, category, severity, and assigned team.
  * `check_ticket_status`: Retrieve ticket details and resolution history by Ticket ID.
  * `list_support_tickets`: Stream and filter tickets by status (`Open`, `In Progress`, `Resolved`).
  * `update_ticket_status`: Modify ticket statuses and append technical resolution notes.

* **🖼️ Visual Troubleshooting Diagram Generator**:
  Uses Pillow (`PIL`) to generate dark-themed technical flowchart diagrams. Generated diagrams are:
  1. Saved locally as Playground artifacts (`diagram_*.png`).
  2. Uploaded to a public Google Cloud Storage bucket (`gs://it-service-desk-copilot-qwiklabs-gcp-02-05ea477ba8ab`).
  3. Returned as public HTTPS links embedded in agent responses and A2UI image cards.

* **🧠 Long-Term Memory (Vertex AI Memory Bank)**:
  Integrated with **Vertex AI Memory Bank** (`PreloadMemoryTool` and `generate_memories_callback`). Automatically remembers user preferences, team defaults, SLA constraints, and past resolution contexts across distinct chat sessions.

* **🎨 Agent-Driven Adaptive UI (A2UI v0.8)**:
  Uses the `a2ui-agent-sdk` (`A2uiSchemaManager`) and `app/a2ui_utils.py` callback to stream rich, structured UI components (`Card`, `Column`, `Row`, `Text`, `Image`) directly to the chat interface.

* **🌐 Full-Stack A2A Web Chat Frontend**:
  Includes a standalone **FastAPI proxy** (`frontend/main.py`) that communicates with the deployed agent over the **A2A (Agent-to-Agent)** protocol with Application Default Credentials (`ADC`), serving a responsive web UI (`frontend/static/index.html`) with an inline A2UI renderer.

---

## 📁 Repository Structure

```text
it-service-desk-copilot/
├── app/
│   ├── agent.py               # Main ADK Agent setup, Gemini model, Memory Bank, & function tools
│   └── a2ui_utils.py          # A2UI v0.8 message parser and rewrapper callback for adk web / chat UI
├── frontend/
│   ├── main.py                # FastAPI proxy connecting browser to deployed agent over A2A
│   ├── requirements.txt       # Frontend dependencies (fastapi, uvicorn, a2a-sdk)
│   └── static/
│       └── index.html         # Web chat UI with native A2UI card renderer
├── tests/
│   ├── integration/           # Integration tests for agent execution and server API
│   └── unit/                  # Unit tests for tools and utils
├── agents-cli-manifest.yaml   # ADK agent deployment manifest
├── pyproject.toml             # Python dependencies and project configuration
├── deployment_metadata.json   # Remote Agent Engine deployment details
└── README.md                  # Project documentation
```

---

## 🛠️ Function Tools Reference

| Tool Name | Parameters | Description |
| :--- | :--- | :--- |
| `search_knowledge_base` | `query: str, category: str = ""` | Searches Firestore `knowledge_base` documents by keyword, tag, or category. |
| `create_support_ticket` | `title: str, description: str, category: str, severity: str, assigned_team: str` | Generates a new support ticket record in Firestore. |
| `check_ticket_status` | `ticket_id: str` | Retrieves detailed information for a specific ticket. |
| `list_support_tickets` | `status_filter: str = ""` | Lists all tickets, optionally filtered by `Open`, `In Progress`, or `Resolved`. |
| `update_ticket_status` | `ticket_id: str, new_status: str, resolution_notes: str = ""` | Updates status and appends diagnostic/resolution notes to a ticket. |
| `generate_troubleshooting_diagram` | `topic: str, steps: str` | Renders a flowchart image, uploads to GCS, and saves an artifact. |
| `PreloadMemoryTool` | — | Automatically preloads relevant facts from Vertex AI Memory Bank prior to model inference. |

---

## 🚀 Getting Started

### 1. Installation & Environment Setup

Ensure `uv` is installed, then set up the virtual environment:

```bash
# Set Google Cloud Service Account credentials
export GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/sa-key.json
export GOOGLE_CLOUD_PROJECT="qwiklabs-gcp-02-05ea477ba8ab"
export GOOGLE_CLOUD_LOCATION="us-central1"

# Install project dependencies
uv sync
```

### 2. Running Automated Tests

Run the full test suite using `pytest`:

```bash
uv run pytest
```

---

## 💻 Running the App Locally

### Option A: Local Agent Playground (`adk web`)

Run the ADK development web UI with Memory Bank attached:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/sa-key.json
export GOOGLE_CLOUD_PROJECT="qwiklabs-gcp-02-05ea477ba8ab"
export GOOGLE_CLOUD_LOCATION="us-central1"

uv run adk web --port 8080 --allow_origins "*" --reload_agents --memory_service_uri=agentengine://6162537823556599808
```
Then open **`http://localhost:8080`** in your browser.

---

### Option B: Full-Stack Web Frontend (`frontend/main.py`)

Run the FastAPI proxy wired to the remote deployed agent over A2A:

```bash
cd frontend
export GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/../sa-key.json
export AGENT_ENGINE_RESOURCE_NAME="projects/343117334186/locations/us-central1/reasoningEngines/7170781190134169600"
export AGENT_DIRECTORY="app"

uv run python main.py
```
Then open **`http://localhost:8080`** in your browser.

---

## ☁️ Deployment

The agent is configured for deployment to **Google Cloud Vertex AI Agent Engine (`agent_runtime`)**. 

To redeploy the agent to Agent Platform:

```bash
uv run agents-cli deploy --no-confirm-project --project qwiklabs-gcp-02-05ea477ba8ab --region us-central1
```

---

## 🎥 Recording Demo Videos

To record an automated screen-capture video of the agent UI in action using Playwright:

```bash
export NODE_PATH="$(pwd)/node_modules"
node .agents/skills/record-demo/record-agent.js \
  -q "Show all open support tickets" \
  -q "Generate a troubleshooting diagram for VPN authentication failures" \
  --wait 35000 \
  --speed 1.5 \
  -o agent_demo.webm
```
