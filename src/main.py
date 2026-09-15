import os
from models.model_client import ModelClient
from dotenv import load_dotenv

load_dotenv()


def load_prompt(version="v1.0"):
    """Load system prompt from file."""
    prompt_path = f"prompts/system-prompt-{version}.txt"
    with open(prompt_path, "r") as f:
        return f.read()


def main():
    print("=" * 50)
    print("Student Support Agent - Baseline (No RAG)")
    print("=" * 50)

    model = ModelClient()
    system_prompt = load_prompt("v1.0")

    print("\nType 'exit' to quit.\n")

    while True:
        question = input("Student: ").strip()

        if question.lower() == "exit":
            print("Goodbye!")
            break

        if not question:
            print("Assistant: Please ask a question.")
            continue

        # Format prompt (no context yet)
        formatted_prompt = system_prompt.format(
            context="No documents loaded yet. Answer from general knowledge only.",
            question=question
        )

        result = model.generate(
            system_prompt=formatted_prompt,
            user_message=question
        )

        print(f"\nAssistant: {result['response']}")
        print(f"[Tokens: {result['usage']['total_tokens']}]\n")


if __name__ == "__main__":
    main()
