from .document_loader import DocumentLoader
from .chunker import DocumentChunker
from .vector_store import VectorStore
from .retriever import Retriever


class RAGPipeline:
    """Complete RAG pipeline."""

    def __init__(self, corpus_dir="knowledge/corpus", persist_dir="knowledge/vectordb"):
        self.corpus_dir = corpus_dir
        self.persist_dir = persist_dir
        self.vector_store = VectorStore(persist_dir)
        self.retriever = None

    def index(self):
        """Index all documents in the corpus. Run offline, re-run when corpus changes."""
        print("=" * 50)
        print("INDEXING CORPUS")
        print("=" * 50)

        # 1. Load documents
        loader = DocumentLoader(self.corpus_dir)
        documents = loader.load_all()

        # 2. Chunk documents
        chunker = DocumentChunker(chunk_size=600, chunk_overlap=100)
        chunks = chunker.chunk(documents)

        # 3. Create vector store
        self.vector_store.create(chunks)

        # 4. Initialize retriever
        self.retriever = Retriever(self.vector_store, k=5)

        print("\n✅ Indexing complete!")
        return len(chunks)

    def query(self, question):
        """Query the RAG pipeline: retrieve + format context for a question."""
        if self.retriever is None:
            self.retriever = Retriever(self.vector_store, k=5)

        chunks = self.retriever.retrieve(question)
        context = self.retriever.format_context(chunks)

        return {
            "question": question,
            "retrieved_chunks": chunks,
            "context": context,
            "sources": [c["source"] for c in chunks]
        }
