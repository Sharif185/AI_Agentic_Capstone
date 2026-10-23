import time

try:
    from observability.logger import AgentLogger  # type: ignore
except ImportError:  # pragma: no cover
    try:
        from src.observability.logger import AgentLogger  # type: ignore
    except ImportError:
        AgentLogger = None  # type: ignore

from .approval_controller import ApprovalController


class ToolExecutor:
    """Validates and executes tool calls."""
 
    def __init__(self, tools, approval_controller=None, logger=None):

        """
        Args:
            tools: List of BaseTool instances
            approval_controller: ApprovalController (optional)
            logger: AgentLogger instance (optional; a default is created
                    so logging works out of the box)
        """
        self.tools = {tool.name: tool for tool in tools}
        self.approval = approval_controller or ApprovalController()
        self.execution_log = []
        self.logger = logger
    
    def get_tool_schemas(self):
        """Return OpenAI-compatible tool schemas."""
        return [tool.to_openai_schema() for tool in self.tools.values()]

    def execute(self, tool_name, arguments):
        """
        Execute a tool call.

        Args:
            tool_name: Name of tool to execute
            arguments: Dict of arguments

        Returns:
            dict with 'success', 'result'/'error', and 'log' info
        """
        arguments = arguments or {}
        start = time.time()

        log_entry = {
            "tool": tool_name,
            "arguments": arguments,
            "status": "pending",
        }

        # 1. Check tool exists
        if tool_name not in self.tools:
            log_entry["status"] = "tool_not_found"
            log_entry["error"] = f"Tool {tool_name} not found"
            self.execution_log.append(log_entry)
            self._log_tool_call(
                tool_name=tool_name,
                arguments=arguments,
                success=False,
                result_preview=None,
                latency_ms=(time.time() - start) * 1000.0,
                error=log_entry["error"],
            )
            return {
                "success": False,
                "error": f"Tool {tool_name} not found",
                "log": log_entry,
            }

        tool = self.tools[tool_name]

        # 2. Validate arguments against schema
        validation_error = self._validate_arguments(tool, arguments)
        if validation_error:
            log_entry["status"] = "validation_failed"
            log_entry["error"] = validation_error
            self.execution_log.append(log_entry)
            self._log_tool_call(
                tool_name=tool_name,
                arguments=arguments,
                success=False,
                result_preview=None,
                latency_ms=(time.time() - start) * 1000.0,
                error=validation_error,
            )
            return {
                "success": False,
                "error": validation_error,
                "log": log_entry,
            }

        # 3. Check approval requirement
        approved_flag = None
        if tool.requires_approval:
            approved = self.approval.request_approval(tool_name, arguments)
            approved_flag = bool(approved)
            self._log_approval(
                tool_name=tool_name,
                arguments=arguments,
                approved=approved_flag,
                mode=self.approval_mode,
                outcome="allowed" if approved else "denied",
            )
            if not approved:
                log_entry["status"] = "approval_denied"
                log_entry["error"] = "Human approval denied"
                self.execution_log.append(log_entry)
                self._log_tool_call(
                    tool_name=tool_name,
                    arguments=arguments,
                    success=False,
                    result_preview=None,
                    latency_ms=(time.time() - start) * 1000.0,
                    error="Human approval denied",
                )
                return {
                    "success": False,
                    "error": "Human approval denied",
                    "approved": False,
                    "log": log_entry,
                }
            log_entry["approved"] = True

        # 4. Execute tool
        try:
            result = tool.execute(**arguments)
            log_entry["status"] = "executed"
            log_entry["result"] = result
            self.execution_log.append(log_entry)

            latency_ms = (time.time() - start) * 1000.0
            success = bool(
                result.get("success", False) if isinstance(result, dict) else False
            )
            preview = result.get("result") if isinstance(result, dict) else result

            self._log_tool_call(
                tool_name=tool_name,
                arguments=arguments,
                success=success,
                result_preview=preview,
                latency_ms=latency_ms,
                error=result.get("error") if isinstance(result, dict) else None,
            )

            response = {
                "success": success,
                "result": result,
                "log": log_entry,
            }
            # Surface approval so the tracer (and any caller) can record it.
            if approved_flag is not None:
                response["approved"] = approved_flag
            return response

        except Exception as e:
            log_entry["status"] = "exception"
            log_entry["error"] = str(e)
            self.execution_log.append(log_entry)
            self._log_tool_call(
                tool_name=tool_name,
                arguments=arguments,
                success=False,
                result_preview=None,
                latency_ms=(time.time() - start) * 1000.0,
                error=str(e),
            )
            return {
                "success": False,
                "error": f"Tool execution failed: {str(e)}",
                "log": log_entry,
            }

    def _validate_arguments(self, tool, arguments):
        """Basic schema validation."""
        schema = tool.schema
        required = schema.get("required", [])

        for param in required:
            if param not in arguments or arguments[param] is None:
                return f"{param} is required"

        allowed = set(schema.get("properties", {}).keys())
        for key in arguments:
            if key not in allowed:
                pass

        return None

    def get_execution_log(self):
        """Return full execution log."""
        return self.execution_log

    # ------------------------------------------------------------------ #
    # Week 7: logging helpers
    # ------------------------------------------------------------------ #
    @property
    def approval_mode(self):
        """Best-effort probe for the approval controller's mode.

        ApprovalController implementations vary between projects; probe
        the common attribute names and fall back to "unknown" rather than
        guessing or hard-coding.
        """
        for attr in ("mode", "approval_mode", "default_mode"):
            value = getattr(self.approval, attr, None)
            if isinstance(value, str) and value:
                return value
        # Common convention: auto_approve / interactive flags.
        if getattr(self.approval, "auto_approve", False):
            return "auto"
        if getattr(self.approval, "interactive", False):
            return "interactive"
        return "unknown"

    def _log_tool_call(self, tool_name, arguments, success, result_preview,
                       latency_ms, error=None):
        if self.logger is None:
            return
        try:
            self.logger.log_tool_call(
                tool_name=tool_name,
                arguments=arguments,
                success=success,
                result_preview=result_preview,
                latency_ms=latency_ms,
                error=error,
            )
        except Exception:
            # Logging must never break execution.
            pass

    def _log_approval(self, tool_name, arguments, approved, mode, outcome=None):
        if self.logger is None:
            return
        try:
            self.logger.log_approval(
                tool_name=tool_name,
                arguments=arguments,
                approved=approved,
                mode=mode,
                outcome=outcome,
            )
        except Exception:
            pass