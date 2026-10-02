from abc import ABC, abstractmethod


class BaseTool(ABC):
    """
    Base class for all agent tools.

    Every tool exposes:
      - name              : unique string identifier the model uses to call it
      - description       : tells the model what the tool does and when to use it
      - schema             : JSON Schema for the tool's input parameters
      - requires_approval  : True if a human must approve before execute() runs
      - execute(**kwargs)  : runs the tool and returns a structured result dict
      - to_openai_schema() : the tool's schema in OpenAI function-calling format

    Subclasses (CourseTool, TicketTool, ...) implement `execute()` and set
    `name`, `description`, `schema`, and `requires_approval` in __init__.

    execute() must never raise for expected/user-facing problems (bad input,
    missing data, etc.) — it should catch those and return
    {"success": False, "error": "..."} so the model can recover gracefully,
    per the project's safe-failure requirement. Unexpected internal errors
    may still raise; ToolExecutor is responsible for catching those.
    """

    name: str = ""
    description: str = ""
    schema: dict = {}
    requires_approval: bool = False

    @abstractmethod
    def execute(self, **kwargs) -> dict:
        """
        Run the tool with the given (already-validated-by-the-tool) arguments.

        Returns a JSON-serializable dict. Convention used across this project:
          success case:  {"success": True, ...tool-specific fields...}
          failure case:  {"success": False, "error": "human-readable reason"}
        """
        raise NotImplementedError

    def to_openai_schema(self) -> dict:
        """
        Return this tool's definition in OpenAI function-calling format.
        This is the canonical schema format for the project; ModelClient is
        responsible for translating it into the active provider's expected
        shape (e.g. Gemini's FunctionDeclaration) when needed.
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.schema,
            },
        }
