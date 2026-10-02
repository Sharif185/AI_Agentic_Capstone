import os
import time
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()


class VectorStore:
    """Manages the Chroma vector database."""

    def __init__(self, persist_dir="knowledge/vectordb"):
        self.persist_dir = persist_dir
        # Using Google's gemini-embedding-001 so the same GEMINI_API_KEY
        # that drives generation also drives embeddings — no OpenAI key needed.
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=os.getenv("GEMINI_API_KEY")
        )
        self.store = None

    def create(self, chunks):
        """Create a new vector store from chunks, batching to respect rate limits."""
        import shutil
        print(f"Creating vector store with {len(chunks)} chunks...")

        # Clear any partial/stale vectordb before starting fresh
        if os.path.exists(self.persist_dir):
            shutil.rmtree(self.persist_dir)

        # Free tier: keep batches small and pause between them
        BATCH_SIZE = 5
        PAUSE_SECONDS = 90

        total_batches = -(-len(chunks) // BATCH_SIZE)

        # First batch — creates the store
        first_batch = chunks[:BATCH_SIZE]
        print(f"  Batch 1/{total_batches}: chunks 1–{len(first_batch)}")
        self.store = Chroma.from_documents(
            documents=first_batch,
            embedding=self.embeddings,
            persist_directory=self.persist_dir
        )

        # Remaining batches — add to existing store
        for i in range(BATCH_SIZE, len(chunks), BATCH_SIZE):
            batch_num = (i // BATCH_SIZE) + 1
            batch = chunks[i:i + BATCH_SIZE]
            print(f"  Rate limit pause ({PAUSE_SECONDS}s)...")
            time.sleep(PAUSE_SECONDS)
            print(f"  Batch {batch_num}/{total_batches}: chunks {i+1}–{min(i+BATCH_SIZE, len(chunks))}")
            self.store.add_documents(batch)

        print(f"Vector store created at {self.persist_dir}")
        return self.store

    def load(self):
        """Load existing vector store."""
        if not os.path.exists(self.persist_dir):
            raise FileNotFoundError(
                f"Vector store not found at {self.persist_dir}. "
                "Run indexing first."
            )
        self.store = Chroma(
            persist_directory=self.persist_dir,
            embedding_function=self.embeddings
        )
        return self.store

    def similarity_search(self, query, k=5):
        """Search for similar chunks."""
        if self.store is None:
            self.load()
        results = self.store.similarity_search_with_score(query, k=k)
        return results
