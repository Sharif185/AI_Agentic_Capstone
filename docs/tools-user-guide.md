# Tools User & Developer Guide

## For Developers

### Adding a New Tool:

1. Create `src/tools/your_tool.py`
2. Extend `BaseTool`
3. Implement `name`, `description`, `schema`, `execute`
4. Set `requires_approval` if needed (write operations)
5. Register in `main.py`: `tools = [CourseTool(), YourTool()]`

### Testing a Tool:

```python
from src.tools.your_tool import YourTool
tool = YourTool()
result = tool.execute(param1="value")
print(result)

## For Users (Students)

### What the Agent Can Do:
* **Answer questions** from university documents (RAG)
* **Look up course info** (prerequisites, credits, schedule)
* **Create support tickets** for unresolved issues

### When a Ticket is Created:
1. **You ask for help** with an unresolved issue
2. **Agent summarizes** the issue
3. **Human supervisor** approves ticket creation
4. **You receive a ticket ID** (e.g., TICKET-0001)
5. **Support staff** follows up

### What the Agent Cannot Do:
* **Change grades**
* **Access real student records**
* **Make admissions decisions**
* **Process fee payments**
* **Make financial commitments**
```
