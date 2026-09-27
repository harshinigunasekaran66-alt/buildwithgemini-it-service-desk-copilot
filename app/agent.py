import datetime
import os
import re
import uuid

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.memory import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.cloud import firestore, storage
from google.genai import types
from PIL import Image, ImageDraw

from app.a2ui_utils import a2ui_callback


# Hardcoded GCP Project ID as required (do NOT use GOOGLE_CLOUD_PROJECT or google.auth.default)
PROJECT_ID = "qwiklabs-gcp-02-05ea477ba8ab"
BUCKET_NAME = "it-service-desk-copilot-qwiklabs-gcp-02-05ea477ba8ab"


# Lazy or direct initialization of Firestore and Storage clients with hardcoded project ID
db = firestore.Client(project=PROJECT_ID)
storage_client = storage.Client(project=PROJECT_ID)


def search_knowledge_base(query: str, category: str = "") -> str:
    """Searches the Firestore knowledge base for technical articles and resolution steps.

    Args:
        query: Keywords to search in article titles, tags, or content (e.g., 'vpn', 'okta', 'oom', 'postgres').
        category: Optional category filter (e.g., 'Network', 'Identity', 'DevOps', 'Database').

    Returns:
        A string listing matching knowledge base articles.
    """
    try:
        articles_ref = db.collection("knowledge_base")
        docs = articles_ref.stream()
        results = []

        query_lower = query.lower()
        category_lower = category.lower()

        for doc in docs:
            data = doc.to_dict()
            title = data.get("title", "")
            content = data.get("content", "")
            tags = [t.lower() for t in data.get("tags", [])]
            doc_category = data.get("category", "")

            # Match category if provided
            if category_lower and category_lower not in doc_category.lower():
                continue

            # Match query in title, content, or tags
            if (
                query_lower in title.lower()
                or query_lower in content.lower()
                or any(query_lower in t for t in tags)
                or not query_lower
            ):
                results.append(
                    f"[{data.get('article_id')}] {title} (Category: {doc_category})\n"
                    f"Summary/Resolution: {content}\n"
                    f"Tags: {', '.join(data.get('tags', []))}\n"
                )

        if not results:
            return f"No KB articles found matching query '{query}'."

        return "\n---\n".join(results)
    except Exception as e:
        return f"Error searching knowledge base: {str(e)}"


def create_support_ticket(
    title: str,
    description: str,
    category: str = "General",
    severity: str = "Medium",
    assigned_team: str = "IT-Support",
) -> str:
    """Creates a new IT support ticket in Firestore.

    Args:
        title: Short title summarizing the issue.
        description: Detailed explanation of the technical problem.
        category: Category of the ticket (e.g., 'Network', 'Identity', 'DevOps', 'Database', 'Hardware').
        severity: Urgency/severity level ('Low', 'Medium', 'High', 'Critical').
        assigned_team: Team assigned to handle the issue (default: 'IT-Support').

    Returns:
        A confirmation message with the generated Ticket ID.
    """
    try:
        tickets_ref = db.collection("support_tickets")
        # Count existing documents to generate ticket ID
        existing_docs = list(tickets_ref.stream())
        ticket_num = 100 + len(existing_docs) + 1
        ticket_id = f"TICKET-{ticket_num}"

        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        ticket_data = {
            "ticket_id": ticket_id,
            "title": title,
            "description": description,
            "category": category,
            "severity": severity,
            "status": "Open",
            "assigned_team": assigned_team,
            "created_at": now_str,
            "updated_at": now_str,
        }

        tickets_ref.document(ticket_id).set(ticket_data)
        return (
            f"✅ Ticket created successfully!\n"
            f"Ticket ID: {ticket_id}\n"
            f"Title: {title}\n"
            f"Severity: {severity}\n"
            f"Assigned Team: {assigned_team}\n"
            f"Status: Open"
        )
    except Exception as e:
        return f"Error creating support ticket: {str(e)}"


def check_ticket_status(ticket_id: str) -> str:
    """Checks the status and details of a support ticket in Firestore.

    Args:
        ticket_id: The Ticket ID to query (e.g., 'TICKET-101').

    Returns:
        A formatted summary of the ticket status and history.
    """
    try:
        formatted_id = ticket_id.upper().strip()
        doc = db.collection("support_tickets").document(formatted_id).get()

        if not doc.exists:
            return f"Ticket '{ticket_id}' not found in database."

        data = doc.to_dict()
        return (
            f"📋 Ticket Information:\n"
            f"ID: {data.get('ticket_id')}\n"
            f"Title: {data.get('title')}\n"
            f"Status: {data.get('status')}\n"
            f"Severity: {data.get('severity')}\n"
            f"Category: {data.get('category')}\n"
            f"Assigned Team: {data.get('assigned_team')}\n"
            f"Description: {data.get('description')}\n"
            f"Created At: {data.get('created_at')}\n"
            f"Updated At: {data.get('updated_at')}"
        )
    except Exception as e:
        return f"Error retrieving ticket status: {str(e)}"


def list_support_tickets(status_filter: str = "") -> str:
    """Lists support tickets stored in Firestore, optionally filtered by status.

    Args:
        status_filter: Optional status filter ('Open', 'In Progress', 'Resolved').

    Returns:
        A list of support tickets.
    """
    try:
        tickets_ref = db.collection("support_tickets")
        docs = tickets_ref.stream()

        results = []
        filter_lower = status_filter.lower().strip()

        for doc in docs:
            data = doc.to_dict()
            status = data.get("status", "")

            if filter_lower and filter_lower not in status.lower():
                continue

            results.append(
                f"[{data.get('ticket_id')}] {data.get('title')} | Status: {status} | Severity: {data.get('severity')} | Assigned: {data.get('assigned_team')}"
            )

        if not results:
            return f"No tickets found matching filter '{status_filter}'."

        return "Support Tickets:\n" + "\n".join(results)
    except Exception as e:
        return f"Error listing support tickets: {str(e)}"


def update_ticket_status(
    ticket_id: str,
    new_status: str,
    resolution_notes: str = "",
) -> str:
    """Updates the status and resolution notes of an existing support ticket in Firestore.

    Args:
        ticket_id: The Ticket ID to update (e.g., 'TICKET-101').
        new_status: The new status ('Open', 'In Progress', 'Resolved', 'Closed').
        resolution_notes: Optional resolution notes or diagnostic updates.

    Returns:
        A confirmation message indicating the ticket update.
    """
    try:
        formatted_id = ticket_id.upper().strip()
        doc_ref = db.collection("support_tickets").document(formatted_id)
        doc = doc_ref.get()

        if not doc.exists:
            return f"Ticket '{ticket_id}' not found in database."

        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        updates = {
            "status": new_status,
            "updated_at": now_str,
        }
        if resolution_notes:
            updates["resolution_notes"] = resolution_notes

        doc_ref.update(updates)
        return (
            f"✅ Ticket '{formatted_id}' updated successfully!\n"
            f"New Status: {new_status}\n"
            f"Updated At: {now_str}"
            + (f"\nResolution Notes: {resolution_notes}" if resolution_notes else "")
        )
    except Exception as e:
        return f"Error updating support ticket: {str(e)}"


def generate_troubleshooting_diagram(
    topic: str,
    steps: str = "",
) -> str:
    """Generates a visual troubleshooting flowchart diagram for an IT issue, uploads it to Cloud Storage, and saves it as an artifact.

    Args:
        topic: Title or issue topic for the flowchart diagram (e.g. 'VPN Gateway Troubleshooting', 'Docker OOM Recovery').
        steps: Comma-separated or newline-separated troubleshooting steps (e.g. 'Check MTU Size, Flush DNS Cache, Restart VPN Service').

    Returns:
        A confirmation message containing the public Cloud Storage image URL.
    """
    try:
        # Default steps if none provided
        step_list = [s.strip() for s in re.split(r"[\n,;]+", steps) if s.strip()]
        if not step_list:
            step_list = [
                "1. Verify network connectivity & DNS resolution",
                "2. Check service logs and active connection pool status",
                "3. Restart local daemon or clear stale session tokens",
                "4. Escalation: Contact system administrator if issue persists",
            ]

        # Calculate dimensions
        card_height = 70
        spacing = 30
        width = 800
        height = 160 + len(step_list) * (card_height + spacing)

        # Dark theme canvas
        img = Image.new("RGB", (width, height), color="#181825")
        draw = ImageDraw.Draw(img)

        # Title Header Card
        draw.rectangle([40, 30, width - 40, 100], fill="#313244", outline="#89b4fa", width=2)
        draw.text((60, 50), f"IT Troubleshooting Flowchart: {topic}", fill="#cdd6f4")

        # Render Step Boxes & Arrows
        y_cursor = 130
        for idx, step_text in enumerate(step_list):
            box_top = y_cursor
            box_bottom = y_cursor + card_height

            # Draw step card box
            draw.rectangle([60, box_top, width - 60, box_bottom], fill="#1e1e2e", outline="#a6adc8", width=2)
            # Step badge
            draw.rectangle([75, box_top + 15, 115, box_top + 55], fill="#89b4fa")
            draw.text((90, box_top + 25), str(idx + 1), fill="#11111b")
            # Step text
            draw.text((130, box_top + 25), step_text[:80], fill="#cdd6f4")

            # Connector Arrow if not last step
            if idx < len(step_list) - 1:
                arrow_x = width // 2
                draw.line([(arrow_x, box_bottom), (arrow_x, box_bottom + spacing)], fill="#89b4fa", width=3)
                # Arrowhead
                draw.polygon(
                    [(arrow_x - 8, box_bottom + spacing - 8), (arrow_x + 8, box_bottom + spacing - 8), (arrow_x, box_bottom + spacing)],
                    fill="#89b4fa",
                )

            y_cursor = box_bottom + spacing

        # Save locally as artifact
        topic_slug = re.sub(r"[^\w]+", "_", topic.lower()).strip("_")
        unique_suffix = uuid.uuid4().hex[:6]
        local_filename = f"diagram_{topic_slug}_{unique_suffix}.png"

        # Ensure local artifact directory exists
        artifacts_dir = "/config/.gemini/antigravity/brain/58a08bb8-8cd0-4069-b725-00892e36f6e7"
        os.makedirs(artifacts_dir, exist_ok=True)
        local_path = os.path.join(artifacts_dir, local_filename)

        img.save(local_path, format="PNG")

        # Upload to Google Cloud Storage bucket
        bucket = storage_client.bucket(BUCKET_NAME)
        blob_name = f"diagrams/{local_filename}"
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(local_path, content_type="image/png")

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_name}"

        return (
            f"🖼️ Troubleshooting Diagram generated successfully!\n"
            f"Topic: {topic}\n"
            f"Public GCS URL: {public_url}\n"
            f"Local Artifact: {local_path}\n\n"
            f"![Troubleshooting Diagram]({public_url})"
        )
    except Exception as e:
        return f"Error generating troubleshooting diagram: {str(e)}"


# WRITE: Memory callback sends session events to Vertex AI Memory Bank at turn end
async def generate_memories_callback(callback_context: CallbackContext):
    try:
        await callback_context.add_session_to_memory()
    except ValueError:
        # Gracefully handle local runner contexts where memory service is not attached
        pass
    return None



# Memory Bank Service configuration for Vertex AI Memory Bank instance
MEMORY_BANK_ID = "6162537823556599808"

def memory_bank_service_builder():
    return VertexAiMemoryBankService(
        project=PROJECT_ID,
        location="us-central1",
        agent_engine_id=MEMORY_BANK_ID,
    )


# A2UI Schema Manager setup (v0.8)
schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

a2ui_instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are an IT Service Desk Copilot for support engineers. "
        "You remember user preferences, active team context, and SLA defaults across conversations. "
        "You assist with searching technical knowledge base articles in Firestore, "
        "creating, updating, and tracking support tickets, generating visual troubleshooting diagrams, "
        "and diagnosing system issues."
    ),
    workflow_description="Analyze the user request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=a2ui_instruction,
    tools=[
        PreloadMemoryTool(),
        search_knowledge_base,
        create_support_ticket,
        check_ticket_status,
        list_support_tickets,
        update_ticket_status,
        generate_troubleshooting_diagram,
    ],
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)





