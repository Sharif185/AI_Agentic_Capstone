"""
Ticket Status Tool — Week 6 Memory Integration

Read-only tool: looks up the status of a previously created support
ticket from the persistent memory store.

This is the new tool introduced in Week 6 to demonstrate that memory
improves the task — the agent can answer "What is the status of my
ticket?" without the student needing to re-explain their issue.

Author: Louis (AI Engineering Lead)
"""

from tools.base_tool import BaseTool


class TicketStatusTool(BaseTool):
    """
    Read-only tool: check_ticket_status

    Retrieves a previously created support ticket from persistent memory
    and returns its current status, issue summary, and timestamps.

    Requires approval: False (read-only, no data written, no side effects)
    """

    name = "check_ticket_status"
    description = (
        "Check the status of a previously created support ticket. "
        "Use when the student asks about a prior ticket — e.g., "
        "'What happened to my registration issue?', 'Is my ticket resolved?', "
        "or 'What is the status of TICKET-0001?'. "
        "Do NOT use for new issues — use create_support_ticket instead."
    )
    schema = {
        "type": "object",
        "properties": {
            "ticket_id": {
                "type": "string",
                "description": (
                    "The ticket ID to look up (e.g., 'TICKET-0001'). "
                    "If the student doesn't know the ID, check the memory context "
                    "in the planning prompt for prior ticket IDs."
                ),
            }
        },
        "required": ["ticket_id"],
    }
    requires_approval = False  # Read-only: no approval needed

    def __init__(self, memory=None):
        """
        Parameters
        ----------
        memory : MemoryManager, optional
            The shared MemoryManager instance. If None, the tool will
            always return 'not found' (graceful degradation — no crash).
        """
        self.memory = memory

    def execute(self, **kwargs) -> dict:
        """
        Look up a ticket by ID from persistent memory.

        Returns
        -------
        Success:
            {
              "success": True,
              "ticket_id": "TICKET-0001",
              "status": "open",
              "issue_summary": "Cannot access registration portal",
              "priority": "high",
              "category": "registration",
              "created_at": "2026-10-05T10:00:00Z",
              "updated_at": "2026-10-05T10:00:00Z"
            }

        Failure:
            {"success": False, "error": "Ticket TICKET-0001 not found"}
        """
        ticket_id = kwargs.get("ticket_id", "").strip()

        if not ticket_id:
            return {
                "success": False,
                "error": "ticket_id is required. Please provide a ticket ID (e.g., 'TICKET-0001').",
            }

        if self.memory is None:
            return {
                "success": False,
                "error": (
                    "Memory is not available in this session. "
                    "Ticket status cannot be retrieved."
                ),
            }

        ticket = self.memory.get_ticket(ticket_id)

        if ticket is None:
            return {
                "success": False,
                "error": (
                    f"Ticket '{ticket_id}' was not found. "
                    "It may have been created in a different session, or the ID may be incorrect. "
                    "Would you like to create a new support ticket instead?"
                ),
            }

        return {
            "success": True,
            "ticket_id": ticket["ticket_id"],
            "status": ticket["status"],
            "issue_summary": ticket["issue_summary"],
            "priority": ticket.get("priority", "medium"),
            "category": ticket.get("category", "other"),
            "student_name": ticket.get("student_name"),
            "created_at": ticket["created_at"],
            "updated_at": ticket["updated_at"],
        }
