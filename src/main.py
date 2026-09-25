import os
import json
from models.model_client import ModelClient
from rag.pipeline import RAGPipeline
from tools.course_tool import CourseTool
from tools.ticket_tool import TicketTool
from dotenv import load_dotenv

class ApprovalController:
  """Manages human approval workflows for write operations and tools."""

  def __init__(self, auto_approve: bool = False, interactive: bool = True):
    self.auto_approve = auto_approve
    self.interactive = interactive

  def request_approval(
      self, tool_name: str, args: Dict[str, Any]
  ) -> bool:
    if self.auto_approve:
      return True

    if not self.interactive:
      return False

    print(
        f"\n[APPROVAL REQUIRED] Tool '{tool_name}' requires human approval"
        " before execution."
    )
    print(f"Proposed Arguments:\n{json.dumps(args, indent=2)}")
    user_input = (
        input("Approve tool execution? (yes/no): ").strip().lower()
    )
    return user_input in ["y", "yes"]


 
load_dotenv()
 
def load_prompt(version="v2.0"):
    prompt_path = f"prompts/system-prompt-{version}.txt"
    with open(prompt_path, "r") as f:
        return f.read()
 
def main():
    print("=" * 60)
    print("Student Support Agent - Tools Enabled")
    print("=" * 60)
    
    # Initialize components
    model = ModelClient()
    pipeline = RAGPipeline()
    tools = [CourseTool(), TicketTool()]
    approval = ApprovalController(auto_approve=False, interactive=True)
    executor = ToolExecutor(tools, approval)
    system_prompt = load_prompt("v2.0")
    
    print("\nAvailable tools:")
    for tool in tools:
        approval_tag = " [requires approval]" if tool.requires_approval else ""
        print(f"  - {tool.name}{approval_tag}")
    print("\nType 'exit' to quit.\n")
    
    while True:
        question = input("Student: ").strip()
        
        if question.lower() == "exit":
            print("Goodbye!")
            break
        
        if not question:
            continue
        
        # 1. Retrieve RAG context
        rag_result = pipeline.query(question)
        
        # 2. Build prompt
        formatted_prompt = system_prompt.format(
            context=rag_result["context"],
            question=question
        )
        
        # 3. Call model WITH tools
        response = model.client.chat.completions.create(
            model=model.model_name,
            messages=[
                {"role": "system", "content": formatted_prompt},
                {"role": "user", "content": question}
            ],
            tools=executor.get_tool_schemas(),
            tool_choice="auto",
            temperature=0.1
        )
        
        message = response.choices[0].message
        
        # 4. Check for tool calls
        if message.tool_calls:
            tool_call = message.tool_calls[0]
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            print(f"\nU0001f527 Calling tool: {tool_name}")
            print(f"   Arguments: {arguments}")
            
            # Execute tool
            exec_result = executor.execute(tool_name, arguments)
            
            # Show result
            if exec_result["success"]:
                print(f"✅ Tool result: {exec_result['result']}")
            else:
                print(f"❌ Tool error: {exec_result.get('error')}")
            
            # Send tool result back to model
            messages = [
                {"role": "system", "content": formatted_prompt},
                {"role": "user", "content": question},
                message,
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(exec_result.get("result", exec_result.get("error")))
                }
            ]
            
            final = model.client.chat.completions.create(
                model=model.model_name,
                messages=messages,
                temperature=0.1
            )
            
            print(f"\nAssistant: {final.choices[0].message.content}\n")
        else:
            # No tool call - direct answer
            print(f"\nAssistant: {message.content}\n")
        
        # Show sources
        if rag_result["sources"]:
            print(f"Sources: {', '.join(rag_result['sources'])}")
 
if __name__ == "__main__":
    main()
