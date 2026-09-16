"""
run_rag_evaluation.py
---------------------
Author  : Imaan (Quality/Security Lead)
Date    : 15th September 2026
Purpose : Run all 15 RAG test questions through the pipeline and save
          results to tests/week3-rag-results.json for review.
"""

import sys
import os
import json
from datetime import datetime

# Allow imports from the project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag.pipeline import RAGPipeline
from src.models.model_client import ModelClient


def load_prompt(version="v2.0"):
    """Load a versioned system prompt from the prompts directory."""
    prompt_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "prompts",
        f"system-prompt-{version}.txt"
    )
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# Test cases — 15 questions across 3 categories
# ---------------------------------------------------------------------------
TEST_CASES = [
    # ------------------------------------------------------------------
    # Category 1: Answerable (8) — full answer should exist in corpus
    # ------------------------------------------------------------------
    {
        "id": "R01",
        "category": "answerable",
        "question": "When is the registration deadline for Semester 1 2026/2027?",
        "expected_source": "Academic Calendar 2026/2027",
        "expected_outcome": "Specific date provided",
    },
    {
        "id": "R02",
        "category": "answerable",
        "question": "What are the prerequisites for BSE4104?",
        "expected_source": "Course Handbook 2026/2027",
        "expected_outcome": "Course codes listed",
    },
    {
        "id": "R03",
        "category": "answerable",
        "question": "How many credits does BSE4104 have?",
        "expected_source": "Course Handbook 2026/2027",
        "expected_outcome": "Credit number stated",
    },
    {
        "id": "R04",
        "category": "answerable",
        "question": "What is the procedure for applying for study leave?",
        "expected_source": "Study Leave Policy",
        "expected_outcome": "Step-by-step procedure listed",
    },
    {
        "id": "R05",
        "category": "answerable",
        "question": "What are the examination regulations regarding late submission?",
        "expected_source": "Examination Regulations",
        "expected_outcome": "Policy on late submission described",
    },
    {
        "id": "R06",
        "category": "answerable",
        "question": "What support services are available for students?",
        "expected_source": "Student Support Services Brochure",
        "expected_outcome": "List of available services",
    },
    {
        "id": "R07",
        "category": "answerable",
        "question": "What is the fee structure for Year 4 BSE?",
        "expected_source": "Fee Structure 2026/2027",
        "expected_outcome": "Fee amounts stated",
    },
    {
        "id": "R08",
        "category": "answerable",
        "question": "What is the academic integrity policy on plagiarism?",
        "expected_source": "Academic Integrity Policy",
        "expected_outcome": "Plagiarism policy summarised",
    },

    # ------------------------------------------------------------------
    # Category 2: Partially Answerable (4) — some info in corpus, some not
    # ------------------------------------------------------------------
    {
        "id": "R09",
        "category": "partial",
        "question": "Can I register late for courses?",
        "expected_source": "Registration Guidelines",
        "expected_outcome": "Late registration policy stated; specific dates flagged as missing",
    },
    {
        "id": "R10",
        "category": "partial",
        "question": "How do I get a transcript?",
        "expected_source": "Registration Guidelines",
        "expected_outcome": "General procedure described; specific office location flagged as missing",
    },
    {
        "id": "R11",
        "category": "partial",
        "question": "What are the requirements for graduation?",
        "expected_source": "Course Handbook 2026/2027",
        "expected_outcome": "Credit requirements described; specific GPA rules flagged as missing",
    },
    {
        "id": "R12",
        "category": "partial",
        "question": "How do I appeal a grade?",
        "expected_source": "Examination Regulations",
        "expected_outcome": "Appeal process described; specific timelines flagged as missing",
    },

    # ------------------------------------------------------------------
    # Category 3: Unanswerable (3) — not in corpus; model must refuse
    # ------------------------------------------------------------------
    {
        "id": "R13",
        "category": "unanswerable",
        "question": "What is the VC's phone number?",
        "expected_source": None,
        "expected_outcome": "Model says: I don't have that information in my current documents.",
    },
    {
        "id": "R14",
        "category": "unanswerable",
        "question": "How many students failed BSE4104 last year?",
        "expected_source": None,
        "expected_outcome": "Model says: I don't have that information in my current documents.",
    },
    {
        "id": "R15",
        "category": "unanswerable",
        "question": "What is the recipe for matooke?",
        "expected_source": None,
        "expected_outcome": "Model says: I don't have that information in my current documents.",
    },
]


def run_rag_evaluation():
    """
    Run all 15 RAG test questions through the pipeline.

    Steps per question:
        1. Retrieve relevant chunks from the vector store.
        2. Format the system prompt with retrieved context.
        3. Generate a response via the model client.
        4. Record all metadata for later review.

    Output:
        tests/week3-rag-results.json
    """

    print("=" * 60)
    print("RAG EVALUATION — Week 3")
    print(f"Run date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Questions: {len(TEST_CASES)}")
    print("=" * 60)

    # ------------------------------------------------------------------
    # Initialise pipeline and model
    # ------------------------------------------------------------------
    pipeline = RAGPipeline()
    pipeline.retriever = None  # Will load vector store lazily on first query
    model = ModelClient()
    system_prompt = load_prompt("v2.0")

    results = []

    for tc in TEST_CASES:
        print(f"\n{'=' * 60}")
        print(f"[{tc['id']}] ({tc['category'].upper()}) {tc['question']}")
        print("-" * 60)

        # 1. Retrieve relevant chunks
        rag_result = pipeline.query(tc["question"])
        sources = rag_result["sources"]
        num_chunks = len(rag_result["retrieved_chunks"])

        print(f"  Chunks retrieved : {num_chunks}")
        print(f"  Sources          : {sources}")

        # 2. Build prompt with context
        formatted_prompt = system_prompt.format(
            context=rag_result["context"],
            question=tc["question"]
        )

        # 3. Generate response
        model_result = model.generate(formatted_prompt, tc["question"])
        response_text = model_result["response"]
        tokens_used = model_result["usage"]["total_tokens"]

        print(f"  Response (preview): {response_text[:200]}...")
        print(f"  Tokens used       : {tokens_used}")

        # 4. Collect result record
        results.append({
            "id": tc["id"],
            "category": tc["category"],
            "question": tc["question"],
            "expected_source": tc["expected_source"],
            "expected_outcome": tc["expected_outcome"],
            "retrieved_chunks": num_chunks,
            "sources_retrieved": sources,
            "response": response_text,
            "tokens_used": tokens_used,
            "run_timestamp": datetime.now().isoformat(),
        })

    # ------------------------------------------------------------------
    # Save results
    # ------------------------------------------------------------------
    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "week3-rag-results.json"
    )
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    answerable  = [r for r in results if r["category"] == "answerable"]
    partial     = [r for r in results if r["category"] == "partial"]
    unanswerable = [r for r in results if r["category"] == "unanswerable"]

    print("\n" + "=" * 60)
    print("EVALUATION COMPLETE")
    print("=" * 60)
    print(f"  Answerable questions  : {len(answerable)}/8")
    print(f"  Partial questions     : {len(partial)}/4")
    print(f"  Unanswerable questions: {len(unanswerable)}/3")
    print(f"  Total                 : {len(results)}/15")
    print(f"\n  Results saved to: {output_path}")

    return results


if __name__ == "__main__":
    run_rag_evaluation()
