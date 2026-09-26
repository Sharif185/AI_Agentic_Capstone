from .base_tool import BaseTool
from .ticket_storage import TicketStorage


class TicketTool(BaseTool):
    def __init__(self, storage=None):
        self.storage = storage or TicketStorage()

    @property
    def name(self):
        return "create_support_ticket"

    @property
    def description(self):
        return (
            "Create a support ticket for a student whose issue cannot be "
            "resolved through available information. Use this when the "
            "student needs human follow-up."
        )

    @property
    def schema(self):
        return {
            "type": "object",
            "properties": {
                "student_name": {"type": "string", "description": "Student's full name"},
                "student_id": {"type": "string", "description": "Student ID number (optional)"},
                "issue_summary": {"type": "string", "description": "Brief description of the issue (max 500 chars)"},
                "priority": {"type": "string", "enum": ["low", "medium", "high"], "default": "medium"},
                "category": {
                    "type": "string",
                    "enum": ["registration", "exams", "fees", "academic", "other"],
                    "default": "other"
                }
            },
            "required": ["student_name", "issue_summary"]
        }

    @property
    def requires_approval(self):
        return True

    def execute(self, student_name=None, issue_summary=None, student_id=None,
                priority="medium", category="other"):
        if not student_name:
            return {"success": False, "error": "student_name is required"}
        if not issue_summary:
            return {"success": False, "error": "issue_summary is required"}
        if len(issue_summary) > 500:
            return {"success": False, "error": "issue_summary exceeds 500 characters"}
        if priority not in ["low", "medium", "high"]:
            return {"success": False, "error": "priority must be low, medium, or high"}
        valid_categories = ["registration", "exams", "fees", "academic", "other"]
        if category not in valid_categories:
            return {"success": False, "error": f"category must be one of: {', '.join(valid_categories)}"}

        try:
            ticket = self.storage.create_ticket(
                student_name=student_name,
                issue_summary=issue_summary,
                student_id=student_id,
                priority=priority,
                category=category
            )
            return {
                "success": True,
                "ticket_id": ticket["ticket_id"],
                "status": ticket["status"],
                "message": f"Ticket {ticket['ticket_id']} created successfully",
                "ticket": ticket
            }
        except Exception as e:
            return {"success": False, "error": f"Ticket system unavailable: {str(e)}"}
