import re

class StudentSupportInterface:
    VERSION = '1.0'
    
    def __init__(self, memory_manager=None):
        self.memory = memory_manager
        self.capabilities = {
            'query_support': self._query_support,
            'get_course_info': self._get_course_info,
            'create_ticket': self._create_ticket,
            'check_ticket_status': self._check_ticket_status
        }

    def list_capabilities(self):
        return {
            "version": self.VERSION,
            "capabilities": list(self.capabilities.keys())
        }

    def invoke(self, capability, inputs, session_id=None):
        if capability not in self.capabilities:
            return {"success": False, "error": f"Capability '{capability}' not found", "error_code": "NOT_FOUND"}
        
        try:
            return self.capabilities[capability](inputs)
        except Exception as e:
            return {"success": False, "error": str(e), "error_code": "INTERNAL_ERROR"}

    def _get_course_info(self, inputs):
        if "course_code" not in inputs or "info_type" not in inputs:
            return {"success": False, "error": "Missing input tokens", "error_code": "INVALID_INPUT"}
        return {"success": True, "course_code": inputs["course_code"], "data": "Prerequisites: None."}

    def _check_ticket_status(self, inputs):
        ticket_id = inputs.get("ticket_id")
        if not ticket_id or not re.match(r"^TICKET-\d{4}$", ticket_id):
            return {"success": False, "error": "Malformed Ticket format", "error_code": "INVALID_INPUT"}
        return {"success": True, "ticket_id": ticket_id, "status": "open", "issue_summary": "Portal access lock"}

    def _query_support(self, inputs): pass
    def _create_ticket(self, inputs): pass
