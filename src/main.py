import os
import sys
from dotenv import load_dotenv

# Resolve project root regardless of where the script is called from
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from models.model_client import ModelClient
from rag.pipeline import RAGPipeline

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def load_prompt(version="v2.0"):
    """Load system prompt from file."""
    prompt_path = os.path.join(PROJECT_ROOT, "prompts", f"system-prompt-{version}.txt")
    with open(prompt_path, "r") as f:
        return f.read()


def main():
    print("=" * 60)
    print("Student Support Agent - RAG Enabled")
    print("=" * 60)

    # Initialize components using absolute paths
    model = ModelClient()
    pipeline = RAGPipeline(
        corpus_dir=os.path.join(PROJECT_ROOT, "knowledge", "corpus"),
        persist_dir=os.path.join(PROJECT_ROOT, "knowledge", "vectordb")
    )
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

        # 3. Generate response with retry on server errors
        result = None
        for attempt in range(4):
            try:
                result = model.generate(
                    system_prompt=formatted_prompt,
                    user_message=question
                )
                break
            except Exception as e:
                err = str(e)
                if attempt < 3 and ("503" in err or "429" in err or "UNAVAILABLE" in err or "ConnectError" in err):
                    wait = 20 * (attempt + 1)
                    print(f"(Server busy, retrying in {wait}s...)")
                    import time; time.sleep(wait)
                else:
                    print(f"\nAssistant: Sorry, the AI service is temporarily unavailable. Please try again in a moment.")
                    result = None
                    break

        if result is None:
            continue

        # 4. Display response with sources
        print(f"\nAssistant: {result['response']}")
        print(f"\nSources: {', '.join(rag_result['sources']) if rag_result['sources'] else 'None'}")
        print(f"[Tokens: {result['usage']['total_tokens']}]\n")


if __name__ == "__main__":
    main()
