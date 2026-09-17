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
        print(f"Creating vector store with {len(chunks)} chunks...")

        # Free tier limit: 100 requests/min. Use batch size of 80 with a
        # 65-second pause between batches to stay safely under the limit.
        BATCH_SIZE = 80
        PAUSE_SECONDS = 65

        if len(chunks) <= BATCH_SIZE:
            # Small enough to do in one shot
            self.store = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=self.persist_dir
            )
        else:
            # First batch — creates the store
            print(f"  Batch 1/{-(-len(chunks)//BATCH_SIZE)}: chunks 1–{BATCH_SIZE}")
            self.store = Chroma.from_documents(
                documents=chunks[:BATCH_SIZE],
                embedding=self.embeddings,
                persist_directory=self.persist_dir
            )
            # Remaining batches — add to existing store
            for i in range(BATCH_SIZE, len(chunks), BATCH_SIZE):
                batch_num = (i // BATCH_SIZE) + 1
                total_batches = -(-len(chunks) // BATCH_SIZE)
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
