import os
from models.model_client import ModelClient
from rag.pipeline import RAGPipeline
from dotenv import load_dotenv

load_dotenv()


def load_prompt(version="v2.0"):
    """Load system prompt from file."""
    prompt_path = f"prompts/system-prompt-{version}.txt"
    with open(prompt_path, "r") as f:
        return f.read()


def main():
    print("=" * 60)
    print("Student Support Agent - RAG Enabled")
    print("=" * 60)

    # Initialize components
    model = ModelClient()
    pipeline = RAGPipeline()
    system_prompt = load_prompt("v2.0")

    print("\nType 'exit' to quit.\n")

    while True:
        question = input("Student: ").strip()

        if question.lower() == "exit":
            print("Goodbye!")
            break

        if not question:
            print("Assistant: Please ask a question.")
            continue

        # 1. Retrieve relevant documents
        rag_result = pipeline.query(question)

        # 2. Build prompt with context
        formatted_prompt = system_prompt.format(
            context=rag_result["context"],
            question=question
        )

        # 3. Generate response
        result = model.generate(
            system_prompt=formatted_prompt,
            user_message=question
        )

        # 4. Display response with sources
        print(f"\nAssistant: {result['response']}")
        print(f"\nSources: {', '.join(rag_result['sources']) if rag_result['sources'] else 'None'}")
        print(f"[Tokens: {result['usage']['total_tokens']}]\n")


if __name__ == "__main__":
    main()
