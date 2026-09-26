from abc import ABC, abstractmethod


class BaseTool(ABC):
    @property
    @abstractmethod
    def name(self): pass

    @property
    @abstractmethod
    def description(self): pass

    @property
    @abstractmethod
    def schema(self): pass

    @property
    def requires_approval(self):
        return False

    @abstractmethod
    def execute(self, **kwargs): pass

    def to_openai_schema(self):
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.schema
            }
        }
