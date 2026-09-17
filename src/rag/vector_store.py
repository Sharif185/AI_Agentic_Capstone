import os
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma


class VectorStore:
    """Manages the Chroma vector database."""

    def __init__(self, persist_dir="knowledge/vectordb"):
        self.persist_dir = persist_dir
        # Embeddings always go through OpenAI (text-embedding-3-small) per
        # the spec, even when MODEL_NAME in .env points main.py at Gemini
        # for generation. OPENAI_API_KEY must be set either way.
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.store = None

    def create(self, chunks):
        """Create a new vector store from chunks."""
        print(f"Creating vector store with {len(chunks)} chunks...")
        self.store = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.persist_dir
        )
        self.store.persist()
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
