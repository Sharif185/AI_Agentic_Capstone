import json
import os
from models.model_client import ModelClient
from rag.pipeline import RAGPipeline
from tools.course_tool import CourseTool
from tools.ticket_tool import TicketTool
from tools.approval_controller import ApprovalController
from tools.tool_executor import ToolExecutor
from dotenv import load_dotenv

load_dotenv()


def load_prompt(version="v1.1"):
    """Load system prompt from file."""
    prompt_path = f"prompts/system-prompt-{version}.txt"
    with open(prompt_path, "r") as f:
        return f.read()


def main():
    print("=" * 60)
    print("Student Support Agent - RAG + Tools")
    print("=" * 60)

    # 1. Load the system prompt
    system_prompt = load_prompt("v1.1")

    # 2. Initialize the RAG pipeline
    model = ModelClient()
    pipeline = RAGPipeline()

    # 3-6. Initialize tools, ApprovalController, and ToolExecutor
    course_tool = CourseTool()
    ticket_tool = TicketTool()
    approval_controller = ApprovalController()
    tool_executor = ToolExecutor(approval_controller)
    tool_executor.register(course_tool)
    tool_executor.register(ticket_tool)

    # 7. Tool schemas the model is offered every turn
    tool_schemas = tool_executor.get_openai_schemas()

    print("\nType 'exit' to quit.\n")

    while True:
        question = input("Student: ").strip()

        if question.lower() == "exit":
            print("Goodbye!")
            break

        if not question:
            print("Assistant: Please ask a question.")
            continue

        # Retrieve relevant documents (RAG context is always available to
        # the model; it's the model's decision whether to answer from it
        # directly or call a tool instead)
        rag_result = pipeline.query(question)
        formatted_prompt = system_prompt.format(
            context=rag_result["context"],
            question=question
        )

        # 8. Let the model decide: answer directly, or call a tool
        result = model.generate(
            system_prompt=formatted_prompt,
            user_message=question,
            tools=tool_schemas
        )

        if result["tool_calls"]:
            calls = result["tool_calls"]

            # Week 4 limit: one tool call per turn. If the model asked for
            # more than one, only the first is executed; the rest are
            # logged and dropped rather than silently ignored.
            if len(calls) > 1:
                print(f"[Notice: model requested {len(calls)} tool calls in one turn; "
                      f"only '{calls[0]['name']}' will be executed, per the "
                      f"one-tool-call-per-turn limit.]")

            call = calls[0]
            print(f"\n[Tool selected: {call['name']}]")
            print(f"[Arguments: {call['arguments']}]")

            # 9. Execute through ToolExecutor (which enforces ApprovalController
            #    for any tool with requires_approval = True)
            tool_result = tool_executor.execute(call["name"], call["arguments"])
            print(f"[Tool result: {json.dumps(tool_result)}]")

            # 10-11. Return the tool result to the model for the final response
            final = model.generate_with_tool_result(
                system_prompt=formatted_prompt,
                user_message=question,
                tool_call=call,
                tool_result=tool_result
            )
            response_text = final["response"]
            usage = final["usage"]
        else:
            response_text = result["response"]
            usage = result["usage"]

        # Display response with sources and token usage
        print(f"\nAssistant: {response_text}")
        print(f"\nSources: {', '.join(rag_result['sources']) if rag_result['sources'] else 'None'}")
        print(f"[Tokens: {usage['total_tokens']}]\n")


if __name__ == "__main__":
    main()
