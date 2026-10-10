"""
MCP-Style Interface — Week 6

A Model Context Protocol (MCP)-style interface that exposes the agent's
capabilities as well-documented, versioned functions with input/output
schemas, permissions, and error codes.

Four capabilities:
  - query_support       : RAG-based Q&A
  - get_course_info     : Structured course lookup
  - create_ticket       : Support ticket creation (requires approval)
  - check_ticket_status : Ticket status lookup (NEW Week 6)

Author: Noah (DevOps/Documentation Lead)
"""

from typing import Any

from dotenv import load_dotenv

from models.model_client import ModelClient
from rag.pipeline import RAGPipeline
from tools.course_tool import CourseTool
from tools.ticket_tool import TicketTool
from tools.ticket_status_tool import TicketStatusTool
from tools.approval_controller import ApprovalController
from tools.tool_executor import ToolExecutor
from agent.planner import Planner
from agent.agent import StudentSupportAgent
from memory.memory_manager import MemoryManager

load_dotenv()


class StudentSupportInterface:
    """
    MCP-style interface for the University Student-Support Agent.

    Exposes 4 capabilities, each with:
      - Input/output JSON schemas
      - Permissions and rate limits
      - Error codes
      - Consistent success/error response shape

    Usage:
        interface = StudentSupportInterface()
        caps = interface.list_capabilities()
        result = interface.invoke('get_course_info', {'course_code': 'BSE4104'})
    """

    VERSION = "1.0"

    # Capability definitions (schemas, permissions, rate limits)
    CAPABILITIES = {
        "query_support": {
            "description": "Answer student queries using RAG over university documents",
            "permissions": "Public",
            "rate_limit": "10/min",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The student's natural language question",
                        "minLength": 1,
                        "maxLength": 1000,
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Optional session ID for conversation continuity",
                    },
                },
                "required": ["query"],
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "response": {"type": "string"},
                    "sources": {"type": "array", "items": {"type": "string"}},
                    "iterations": {"type": "integer"},
                    "stop_reason": {"type": "string"},
                },
                "required": ["success", "response"],
            },
        },
        "get_course_info": {
            "description": "Retrieve structured course information (prerequisites, credits, schedule)",
            "permissions": "Public",
            "rate_limit": "20/min",
            "input_schema": {
                "type": "object",
                "properties": {
                    "course_code": {
                        "type": "string",
                        "description": "University course code, e.g. 'BSE4104'",
                        "pattern": "^[A-Z]{2,4}[0-9]{3,4}$",
                    },
                    "info_type": {
                        "type": "string",
                        "enum": ["prerequisites", "credits", "schedule", "description", "all"],
                        "default": "all",
                    },
                },
                "required": ["course_code"],
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "course_code": {"type": "string"},
                    "course_name": {"type": "string"},
                    "prerequisites": {"type": "array"},
                    "credits": {"type": "integer"},
                    "schedule": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["success"],
            },
        },
        "create_ticket": {
            "description": "Create a support ticket (requires approval)",
            "permissions": "Requires approval",
            "rate_limit": "5/session",
            "input_schema": {
                "type": "object",
                "properties": {
                    "student_name": {
                        "type": "string",
                        "description": "Full name of the student",
                        "minLength": 1,
                        "maxLength": 100,
                    },
                    "student_id": {
                        "type": "string",
                        "description": "University student ID, e.g. '2024/BCS/001'",
                        "maxLength": 50,
                    },
                    "issue_summary": {
                        "type": "string",
                        "description": "Concise issue description (max 500 chars)",
                        "minLength": 1,
                        "maxLength": 500,
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "default": "medium",
                    },
                    "category": {
                        "type": "string",
                        "enum": ["registration", "exams", "fees", "academic", "other"],
                        "default": "other",
                    },
                },
                "required": ["student_name", "issue_summary"],
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "ticket_id": {"type": "string"},
                    "status": {"type": "string"},
                    "created_at": {"type": "string"},
                },
                "required": ["success"],
            },
        },
        "check_ticket_status": {
            "description": "Retrieve existing ticket status (NEW Week 6)",
            "permissions": "Session",
            "rate_limit": "10/min",
            "input_schema": {
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "string",
                        "description": "Ticket ID to look up, e.g. 'TICKET-0001'",
                        "pattern": "^TICKET-[0-9]{4}$",
                    }
                },
                "required": ["ticket_id"],
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "ticket_id": {"type": "string"},
                    "status": {"type": "string"},
                    "issue_summary": {"type": "string"},
                    "priority": {"type": "string"},
                    "category": {"type": "string"},
                    "created_at": {"type": "string"},
                    "updated_at": {"type": "string"},
                },
                "required": ["success"],
            },
        },
    }

    def __init__(self):
        """
        Initialize the interface with all required components.
        These are instantiated once and reused across invocations.
        """
        self.model = ModelClient()
        self.rag = RAGPipeline()
        self.memory = MemoryManager()

        # Tools
        self.course_tool = CourseTool()
        self.ticket_tool = TicketTool(memory=self.memory)
        self.ticket_status_tool = TicketStatusTool(memory=self.memory)

        # Tool executor with approval
        self.approval_controller = ApprovalController()
        self.tool_executor = ToolExecutor(self.approval_controller)
        self.tool_executor.register(self.course_tool)
        self.tool_executor.register(self.ticket_tool)
        self.tool_executor.register(self.ticket_status_tool)

        # Agent
        self.planner = Planner(self.model)
        self.agent = StudentSupportAgent(
            model_client=self.model,
            rag_pipeline=self.rag,
            tool_executor=self.tool_executor,
            planner=self.planner,
            memory_manager=self.memory,
            max_iterations=5,
            max_tool_calls=3,
            max_rag_calls=2,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_capabilities(self) -> dict:
        """
        Return the interface version and all available capabilities.

        Returns
        -------
        {
          "version": "1.0",
          "capabilities": {
            "query_support": {...schema...},
            "get_course_info": {...schema...},
            ...
          }
        }
        """
        return {"version": self.VERSION, "capabilities": self.CAPABILITIES}

    def invoke(self, capability: str, inputs: dict, session_id: str = None) -> dict:
        """
        Invoke a capability with the given inputs.

        Parameters
        ----------
        capability : str
            One of: query_support, get_course_info, create_ticket, check_ticket_status
        inputs : dict
            Input parameters matching the capability's input_schema
        session_id : str, optional
            Session ID for memory context (user_id derived from session if available)

        Returns
        -------
        Success:
            {"success": True, ...capability-specific fields...}
        Failure:
            {"success": False, "error": "...", "error_code": "INVALID_INPUT|NOT_FOUND|..."}
        """
        if capability not in self.CAPABILITIES:
            return {
                "success": False,
                "error": f"Unknown capability '{capability}'",
                "error_code": "NOT_FOUND",
            }

        # Route to the appropriate handler
        if capability == "query_support":
            return self._query_support(inputs, session_id)
        elif capability == "get_course_info":
            return self._get_course_info(inputs)
        elif capability == "create_ticket":
            return self._create_ticket(inputs)
        elif capability == "check_ticket_status":
            return self._check_ticket_status(inputs)

        return {
            "success": False,
            "error": "Capability not implemented",
            "error_code": "INTERNAL_ERROR",
        }

    # ------------------------------------------------------------------
    # Capability handlers
    # ------------------------------------------------------------------

    def _query_support(self, inputs: dict, session_id: str = None) -> dict:
        """
        query_support: Answer a student query using the RAG-based agent.
        """
        query = inputs.get("query", "").strip()
        if not query:
            return {
                "success": False,
                "error": "'query' is required and must not be empty",
                "error_code": "INVALID_INPUT",
            }

        if len(query) > 1000:
            return {
                "success": False,
                "error": f"'query' exceeds max length of 1000 characters ({len(query)} provided)",
                "error_code": "INVALID_INPUT",
            }

        # Derive user_id from session_id if available (simplified: use session_id as user_id)
        user_id = session_id

        try:
            result = self.agent.run(query, user_id=user_id)
            return {
                "success": True,
                "response": result["response"],
                "sources": [],  # TODO: extract from state.retrieved_documents if needed
                "iterations": result["iterations"],
                "stop_reason": result["stop_reason"],
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Agent execution failed: {e}",
                "error_code": "INTERNAL_ERROR",
            }

    def _get_course_info(self, inputs: dict) -> dict:
        """
        get_course_info: Retrieve structured course information.
        """
        course_code = inputs.get("course_code", "").strip()
        info_type = inputs.get("info_type", "all")

        if not course_code:
            return {
                "success": False,
                "error": "'course_code' is required",
                "error_code": "INVALID_INPUT",
            }

        try:
            result = self.course_tool.execute(course_code=course_code, info_type=info_type)
            if not result.get("success"):
                # Tool returned failure (e.g., course not found)
                return {
                    "success": False,
                    "error": result.get("error", "Course lookup failed"),
                    "error_code": "NOT_FOUND",
                }
            return result
        except Exception as e:
            return {
                "success": False,
                "error": f"Course tool execution failed: {e}",
                "error_code": "INTERNAL_ERROR",
            }

    def _create_ticket(self, inputs: dict) -> dict:
        """
        create_ticket: Create a support ticket (routes through approval).
        """
        student_name = inputs.get("student_name", "").strip()
        issue_summary = inputs.get("issue_summary", "").strip()

        if not student_name:
            return {
                "success": False,
                "error": "'student_name' is required",
                "error_code": "INVALID_INPUT",
            }

        if not issue_summary:
            return {
                "success": False,
                "error": "'issue_summary' is required",
                "error_code": "INVALID_INPUT",
            }

        if len(issue_summary) > 500:
            return {
                "success": False,
                "error": f"'issue_summary' exceeds max length of 500 characters ({len(issue_summary)} provided)",
                "error_code": "INVALID_INPUT",
            }

        try:
            # Tool executor handles approval internally
            result = self.tool_executor.execute("create_support_ticket", inputs)

            if not result.get("success"):
                # Approval denied or tool failure
                if result.get("approved") is False:
                    return {
                        "success": False,
                        "error": "Ticket creation was not approved",
                        "error_code": "UNAUTHORIZED",
                    }
                return {
                    "success": False,
                    "error": result.get("error", "Ticket creation failed"),
                    "error_code": "INTERNAL_ERROR",
                }

            ticket = result.get("ticket", {})
            return {
                "success": True,
                "ticket_id": ticket.get("ticket_id"),
                "status": ticket.get("status"),
                "created_at": ticket.get("created_at"),
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Ticket tool execution failed: {e}",
                "error_code": "INTERNAL_ERROR",
            }

    def _check_ticket_status(self, inputs: dict) -> dict:
        """
        check_ticket_status: Retrieve an existing ticket (NEW Week 6).
        """
        ticket_id = inputs.get("ticket_id", "").strip()

        if not ticket_id:
            return {
                "success": False,
                "error": "'ticket_id' is required",
                "error_code": "INVALID_INPUT",
            }

        try:
            result = self.ticket_status_tool.execute(ticket_id=ticket_id)

            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get("error", "Ticket not found"),
                    "error_code": "NOT_FOUND",
                }

            return result
        except Exception as e:
            return {
                "success": False,
                "error": f"Ticket status tool execution failed: {e}",
                "error_code": "INTERNAL_ERROR",
            }
