import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.pipeline import RAGPipeline

if __name__ == "__main__":
    pipeline = RAGPipeline()
    num_chunks = pipeline.index()
    print(f"\nTotal chunks indexed: {num_chunks}")
