from abc import ABC, abstractmethod
 
class BaseTool(ABC):
    """Base class for all tools."""
    
    @property
    @abstractmethod
    def name(self):
        """Tool name used in function calling."""
        pass
    
    @property
    @abstractmethod
    def description(self):
        """Tool description for the model."""
        pass
    
    @property
    @abstractmethod
    def schema(self):
        """JSON schema for tool inputs."""
        pass
    
    @property
    def requires_approval(self):
        """Whether this tool requires human approval."""
        return False
    
    @abstractmethod
    def execute(self, **kwargs):
        """Execute the tool with given parameters."""
        pass
    
    def to_openai_schema(self):
        """Convert to OpenAI tool format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.schema
            }
        }
