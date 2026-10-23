import re
import json
import os


# Known courses for capability-level lookups (mirrors data/courses.json)
_COURSES_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "..", "data", "courses.json")


def _load_courses():
    """Load course data from disk, return empty dict on failure."""
    try:
        with open(_COURSES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Handle {courses: [...]} wrapper or bare list or dict-keyed-by-code
        if isinstance(data, dict) and "courses" in data:
            data = data["courses"]
        if isinstance(data, list):
            return {c["course_code"]: c for c in data if "course_code" in c}
        return data
    except Exception:
        return {}


class StudentSupportInterface:
    """
    MCP-style interface exposing four capabilities:
      - query_support
      - get_course_info
      - create_ticket
      - check_ticket_status

    Each capability is described as a dict so callers can inspect name,
    description, required_inputs, and auth requirements without invoking.
    """

    VERSION = "1.0"

    # Capability catalogue — dict keyed by name so .keys() works correctly
    CAPABILITY_CATALOGUE = {
        "query_support": {
            "name": "query_support",
            "description": "Answer a student support question using the RAG knowledge base.",
            "required_inputs": ["question"],
            "auth": "public",
            "approval_required": False,
            "rate_limit": "10/min",
            "side_effects": "none",
        },
        "get_course_info": {
            "name": "get_course_info",
            "description": "Return information about a specific course by course code.",
            "required_inputs": ["course_code"],
            "optional_inputs": ["info_type"],
            "auth": "public",
            "approval_required": False,
            "rate_limit": "20/min",
            "side_effects": "none",
        },
        "create_ticket": {
            "name": "create_ticket",
            "description": "Create a support ticket for a student issue.",
            "required_inputs": ["student_name", "issue_summary"],
            "optional_inputs": ["priority", "category"],
            "auth": "session",
            "approval_required": True,
            "rate_limit": "5/session",
            "side_effects": "creates ticket",
        },
        "check_ticket_status": {
            "name": "check_ticket_status",
            "description": "Check the status of an existing support ticket.",
            "required_inputs": ["ticket_id"],
            "auth": "session",
            "approval_required": False,
            "rate_limit": "10/min",
            "side_effects": "none",
        },
    }

    def __init__(self, memory_manager=None):
        self.memory = memory_manager
        self._handlers = {
            "query_support": self._query_support,
            "get_course_info": self._get_course_info,
            "create_ticket": self._create_ticket,
            "check_ticket_status": self._check_ticket_status,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_capabilities(self):
        """Return version and capability catalogue as a dict keyed by name."""
        return {
            "version": self.VERSION,
            "capabilities": self.CAPABILITY_CATALOGUE,
        }

    def invoke(self, capability, inputs, session_id=None):
        """Dispatch a capability call, returning a consistent response shape."""
        if capability not in self._handlers:
            return {
                "success": False,
                "error": f"Unknown capability: '{capability}'",
                "error_code": "NOT_FOUND",
            }
        try:
            return self._handlers[capability](inputs)
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_code": "INTERNAL_ERROR",
            }

    # ------------------------------------------------------------------
    # Capability implementations
    # ------------------------------------------------------------------

    def _query_support(self, inputs):
        question = inputs.get("question", "").strip()
        if not question:
            return {"success": False, "error": "Missing required input: question",
                    "error_code": "INVALID_INPUT"}
        # Lightweight stub — full RAG integration is done via the agent
        return {"success": True, "answer": "Please contact the support office for further help.",
                "sources": []}

    def _get_course_info(self, inputs):
        course_code = inputs.get("course_code", "").strip()
        if not course_code:
            return {"success": False, "error": "Missing required input: course_code",
                    "error_code": "INVALID_INPUT"}

        courses = _load_courses()
        if course_code not in courses:
            return {"success": False,
                    "error": f"Course '{course_code}' not found",
                    "error_code": "NOT_FOUND"}

        course = courses[course_code]
        info_type = inputs.get("info_type", "all")
        if info_type == "all":
            return {"success": True, "course_code": course_code, "data": course}
        if info_type in course:
            return {"success": True, "course_code": course_code, "data": {info_type: course[info_type]}}
        return {"success": True, "course_code": course_code, "data": course}

    def _create_ticket(self, inputs):
        student_name = inputs.get("student_name", "").strip()
        issue_summary = inputs.get("issue_summary", "").strip()
        if not student_name or not issue_summary:
            return {"success": False,
                    "error": "Missing required inputs: student_name and issue_summary",
                    "error_code": "INVALID_INPUT"}
        ticket_id = "TICKET-0001"
        return {"success": True, "ticket_id": ticket_id,
                "message": f"Ticket {ticket_id} created for {student_name}."}

    def _check_ticket_status(self, inputs):
        ticket_id = inputs.get("ticket_id", "").strip()
        if not ticket_id:
            return {"success": False, "error": "Missing required input: ticket_id",
                    "error_code": "INVALID_INPUT"}
        if not re.match(r"^TICKET-\d{4}$", ticket_id):
            return {"success": False, "error": "Malformed ticket ID format. Expected TICKET-NNNN.",
                    "error_code": "INVALID_INPUT"}

        # Look up ticket in the JSON storage (data/tickets.json)
        tickets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                    "..", "data", "tickets.json")
        try:
            if os.path.exists(tickets_path):
                with open(tickets_path, "r", encoding="utf-8") as f:
                    tickets = json.load(f)
                for t in tickets:
                    if t.get("ticket_id") == ticket_id:
                        return {"success": True, "ticket_id": ticket_id,
                                "status": t.get("status", "open"),
                                "issue_summary": t.get("issue_summary", "")}
        except Exception:
            pass

        return {"success": False, "error": f"Ticket '{ticket_id}' not found",
                "error_code": "NOT_FOUND"}
