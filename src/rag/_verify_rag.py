"""One-off RAG retrieval verification — delete after use."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rag.pipeline import RAGPipeline

p = RAGPipeline()
for q in [
    "When is the registration deadline?",
    "What are the prerequisites for BSE4104?",
    "What is the exam policy on late submission?",
]:
    r = p.query(q)
    n = len(r["retrieved_chunks"])
    srcs = r["sources"][:2]
    print(f"Q: {q}")
    print(f"   {n} chunks from {srcs}")