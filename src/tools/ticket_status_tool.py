from .base_tool import BaseTool
 #. The guide’s snippet uses self.memory but never defines __init__, so I added one. Without it the tool would crash on its first call.
 
class TicketStatusTool(BaseTool):
    """Read-only tool: look up the status of a previously created ticket."""
 
    def __init__(self, storage=None, memory=None):
        self.storage = storage or TicketStorage()
        self.memory = memory  # Optional MemoryManager
 
    @property
    def name(self):
        return "check_ticket_status"
 
    @property
    def description(self):
        return (
            "Check the status of a previously created support ticket. "
            "Use when the student asks about a prior ticket."
        )
 
    @property
    def schema(self):
        return {
            "type": "object",
            "properties": {
                "ticket_id": {
                    "type": "string",
                    "description": "The ticket ID (e.g., TICKET-0001)"
                }
            },
            "required": ["ticket_id"]
        }
 
    @property
    def requires_approval(self):
        return False  # read-only, no side effects
 
    def execute(self, ticket_id=None):
        if not ticket_id:
            return {"success": False, "error": "ticket_id is required"}
 
        ticket = self.memory.get_ticket(ticket_id)
        if not ticket:
                        # Persist to memory (optional). A memory failure must not make a
            # successfully created ticket look like it failed.
            if self.memory:
                try:
                    self.memory.save_ticket(ticket)
                except Exception as mem_err:
                    print(f"[warning] ticket created but memory save failed: {mem_err}")
            return {"success": False, "error": f"Ticket {ticket_id} not found"}
 
        return {
            "success": True,
            "ticket_id": ticket["ticket_id"],
            "status": ticket["status"],
            "issue_summary": ticket["issue_summary"],
            "created_at": ticket["created_at"],
            "updated_at": ticket["updated_at"]
        }