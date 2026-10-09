**Layers**

1. **User Interface:** CLI (`main.py`)
2. **Application Layer:** Orchestration (`tool_executor`, `approval_controller`, state management)
3. **AI Layer:** Model client (`GPT-4o-mini`), RAG pipeline, prompt management
4. **Tool Layer:** `CourseTool` (read) & `TicketTool` (write, requires approval)
5. **Data Layer:** Vector store (`Chroma`), Courses DB (`courses.json`), Tickets DB (`tickets.db` SQLite)

**Data Flow:** `User -> App -> Model -> [RAG | Tools] -> Response`
