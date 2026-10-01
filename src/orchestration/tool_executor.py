import json
from .approval_controller import ApprovalController
 
class ToolExecutor:
    """Validates and executes tool calls."""
    
    def __init__(self, tools, approval_controller=None):
        """
        Args:
            tools: List of BaseTool instances
            approval_controller: ApprovalController (optional)
        """
        self.tools = {tool.name: tool for tool in tools}
        self.approval = approval_controller or ApprovalController()
        self.execution_log = []
    
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
        log_entry = {
            "tool": tool_name,
            "arguments": arguments,
            "status": "pending"
        }
        
        # 1. Check tool exists
        if tool_name not in self.tools:
            log_entry["status"] = "tool_not_found"
            log_entry["error"] = f"Tool {tool_name} not found"
            self.execution_log.append(log_entry)
            return {
                "success": False,
                "error": f"Tool {tool_name} not found",
                "log": log_entry
            }
        
        tool = self.tools[tool_name]
        
        # 2. Validate arguments against schema
        validation_error = self._validate_arguments(tool, arguments)
        if validation_error:
            log_entry["status"] = "validation_failed"
            log_entry["error"] = validation_error
            self.execution_log.append(log_entry)
            return {
                "success": False,
                "error": validation_error,
                "log": log_entry
            }
        
        # 3. Check approval requirement
        if tool.requires_approval:
            approved = self.approval.request_approval(tool_name, arguments)
            if not approved:
                log_entry["status"] = "approval_denied"
                log_entry["error"] = "Human approval denied"
                self.execution_log.append(log_entry)
                return {
                    "success": False,
                    "error": "Human approval denied",
                    "log": log_entry
                }
            log_entry["approved"] = True
        
        # 4. Execute tool
        try:
            result = tool.execute(**arguments)
            log_entry["status"] = "executed"
            log_entry["result"] = result
            self.execution_log.append(log_entry)
            return {
                "success": result.get("success", False),
                "result": result,
                "log": log_entry
            }
        except Exception as e:
            log_entry["status"] = "exception"
            log_entry["error"] = str(e)
            self.execution_log.append(log_entry)
            return {
                "success": False,
                "error": f"Tool execution failed: {str(e)}",
                "log": log_entry
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