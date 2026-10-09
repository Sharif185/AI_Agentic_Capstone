import json


class ToolExecutor:
    """
    Registers tools and executes them safely:
      - unknown tool name -> structured error, never a crash
      - malformed arguments -> structured error
      - requires_approval tools -> ALWAYS routed through ApprovalController
        first; execute() is never called on a denied or unapproved action
      - unexpected internal errors in a tool -> caught and returned as a
        structured error, never allowed to crash the application
    """

    def __init__(self, approval_controller):
        self.approval_controller = approval_controller
        self._tools = {}

    def register(self, tool):
        self._tools[tool.name] = tool

    def get_openai_schemas(self):
        """Return all registered tools' schemas, for passing to the model."""
        return [tool.to_openai_schema() for tool in self._tools.values()]

    def execute(self, tool_name: str, arguments) -> dict:
        # Unknown tool
        tool = self._tools.get(tool_name)
        if tool is None:
            return {"success": False, "error": f"Unknown tool requested: '{tool_name}'."}

        # Arguments may arrive as a JSON string from the model — normalize to dict
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments) if arguments.strip() else {}
            except json.JSONDecodeError:
                return {"success": False, "error": f"Tool '{tool_name}' received malformed (non-JSON) arguments."}

        if arguments is None:
            arguments = {}

        if not isinstance(arguments, dict):
            return {"success": False, "error": f"Tool '{tool_name}' received unexpected argument format: {type(arguments).__name__}."}

        # Reject parameters the tool's schema doesn't declare, rather than
        # silently swallowing them via **kwargs
        allowed_keys = set(tool.schema.get("properties", {}).keys())
        if allowed_keys:
            unexpected = set(arguments.keys()) - allowed_keys
            if unexpected:
                return {
                    "success": False,
                    "error": f"Tool '{tool_name}' received unexpected parameter(s): {', '.join(sorted(unexpected))}.",
                }

        # Human approval gate — never skipped for a tool that requires it
        if tool.requires_approval:
            approved = self.approval_controller.approve(tool_name, arguments)
            if not approved:
                return {"success": False, "error": "Human approval denied", "approved": False}

        # Execute, catching unexpected internal errors (tools already
        # handle expected/validation errors themselves and return structured
        # {"success": False, ...} dicts for those)
        try:
            result = tool.execute(**arguments)
        except TypeError as e:
            # e.g. tool.execute() got an argument it doesn't accept
            return {"success": False, "error": f"Tool '{tool_name}' received unexpected parameters: {e}"}
        except Exception as e:
            return {"success": False, "error": f"Tool '{tool_name}' failed unexpectedly: {e}"}

        if tool.requires_approval:
            result = dict(result)
            result["approved"] = True

        return result
