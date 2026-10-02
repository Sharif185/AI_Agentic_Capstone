import json
import os
from datetime import datetime, timezone

from tools.base_tool import BaseTool

MAX_ISSUE_SUMMARY_LENGTH = 500
ALLOWED_PRIORITIES = ["low", "medium", "high"]
ALLOWED_CATEGORIES = ["registration", "exams", "fees", "academic", "other"]
DEFAULT_PRIORITY = "medium"
DEFAULT_CATEGORY = "other"


class TicketTool(BaseTool):
    """
    Write tool: create_support_ticket

    Creates a support ticket for a student issue that needs human
    follow-up. This is a WRITE action, so requires_approval = True.
    ToolExecutor is responsible for obtaining human approval via
    ApprovalController BEFORE calling execute() — this tool never
    bypasses that mechanism itself.
    """

    name = "create_support_ticket"
    description = (
        "Create a support ticket for a student issue that cannot be resolved "
        "from available documents or self-service, so a human staff member "
        "can follow up. Requires human approval before the ticket is created."
    )
    schema = {
        "type": "object",
        "properties": {
            "student_name": {"type": "string", "description": "Full name of the student."},
            "student_id": {"type": "string", "description": "Optional student ID, e.g. '2024/BCS/001'."},
            "issue_summary": {
                "type": "string",
                "description": "A concise summary of the student's issue (max 500 characters).",
            },
            "priority": {
                "type": "string",
                "enum": ALLOWED_PRIORITIES,
                "description": f"Ticket priority. Defaults to '{DEFAULT_PRIORITY}' if not given.",
            },
            "category": {
                "type": "string",
                "enum": ALLOWED_CATEGORIES,
                "description": f"Ticket category. Defaults to '{DEFAULT_CATEGORY}' if not given.",
            },
        },
        "required": ["student_name", "issue_summary"],
    }
    requires_approval = True

    def __init__(self, storage_path="data/support_tickets.json"):
        self.storage_path = storage_path

    def execute(self, **kwargs) -> dict:
        student_name = kwargs.get("student_name")
        student_id = kwargs.get("student_id")
        issue_summary = kwargs.get("issue_summary")
        priority = kwargs.get("priority", DEFAULT_PRIORITY)
        category = kwargs.get("category", DEFAULT_CATEGORY)

        # Required field validation
        if not student_name or not isinstance(student_name, str) or not student_name.strip():
            return {"success": False, "error": "Missing or invalid 'student_name'. This field is required."}

        if not issue_summary or not isinstance(issue_summary, str) or not issue_summary.strip():
            return {"success": False, "error": "Missing or invalid 'issue_summary'. This field is required."}

        if len(issue_summary) > MAX_ISSUE_SUMMARY_LENGTH:
            return {
                "success": False,
                "error": f"'issue_summary' is {len(issue_summary)} characters, exceeding the {MAX_ISSUE_SUMMARY_LENGTH}-character limit.",
            }

        if priority not in ALLOWED_PRIORITIES:
            return {
                "success": False,
                "error": f"Invalid 'priority': '{priority}'. Must be one of: {', '.join(ALLOWED_PRIORITIES)}.",
            }

        if category not in ALLOWED_CATEGORIES:
            return {
                "success": False,
                "error": f"Invalid 'category': '{category}'. Must be one of: {', '.join(ALLOWED_CATEGORIES)}.",
            }

        # Load existing tickets (or start a fresh store)
        tickets = []
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                    tickets = existing.get("tickets", [])
            except (json.JSONDecodeError, OSError) as e:
                return {"success": False, "error": f"Ticket storage is unavailable (could not read '{self.storage_path}': {e})."}

        ticket_id = f"TCK-{len(tickets) + 1:04d}"
        ticket = {
            "ticket_id": ticket_id,
            "student_name": student_name.strip(),
            "student_id": student_id.strip() if isinstance(student_id, str) and student_id.strip() else None,
            "issue_summary": issue_summary.strip(),
            "priority": priority,
            "category": category,
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        tickets.append(ticket)

        try:
            os.makedirs(os.path.dirname(self.storage_path) or ".", exist_ok=True)
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump({"tickets": tickets}, f, indent=2)
        except OSError as e:
            return {"success": False, "error": f"Ticket storage is unavailable (could not write '{self.storage_path}': {e})."}

        return {"success": True, "ticket": ticket}
