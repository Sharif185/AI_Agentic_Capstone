import time

try:
    from observability.logger import AgentLogger  # type: ignore
except ImportError:  # pragma: no cover
    try:
        from src.observability.logger import AgentLogger  # type: ignore
    except ImportError:
        AgentLogger = None  # type: ignore

from .document_loader import DocumentLoader
from .chunker import DocumentChunker
from .vector_store import VectorStore
from .retriever import Retriever
import time

class RAGPipeline:
    """Complete RAG pipeline.

    Week 7 change: every retrieval emits an `rag_retrieval` event with
    query, result count, source identifiers, latency and outcome. The
    `logs_retrievals = True` marker tells agent.py not to emit a duplicate.
    """

    # Signals to AgentLogger-aware callers (agent.py) that this pipeline
    # already emits its own rag_retrieval events — no fallback needed.
    logs_retrievals = True

    def __init__(
        self,
        corpus_dir="knowledge/corpus",
        persist_dir="knowledge/vectordb",
        logger=None,
    ):
        self.corpus_dir = corpus_dir
        self.persist_dir = persist_dir
        self.vector_store = VectorStore(persist_dir)
        self.retriever = None

        if logger is not None:
            self.logger = logger
        elif AgentLogger is not None:
            self.logger = AgentLogger(log_dir="logs")
        else:
            self.logger = None

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
        start = time.time()

        try:
            if self.retriever is None:
                self.retriever = Retriever(self.vector_store, k=5)

            chunks = self.retriever.retrieve(question)
            context = self.retriever.format_context(chunks)
            latency_ms = (time.time() - start) * 1000.0

            sources = self._extract_sources(chunks)

            self._log_retrieval(
                question=question,
                num_results=len(chunks),
                sources=sources,
                latency_ms=latency_ms,
                success=True,
                error=None,
            )

            return {
                "question": question,
                "retrieved_chunks": chunks,
                "context": context,
                "sources": sources,
            }

        except Exception as e:
            latency_ms = (time.time() - start) * 1000.0
            self._log_retrieval(
                question=question,
                num_results=0,
                sources=[],
                latency_ms=latency_ms,
                success=False,
                error=str(e),
            )
            raise

    # ------------------------------------------------------------------ #
    # internal helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _extract_sources(chunks):
        """Pull source identifiers defensively — a chunk without a 'source'
        key should not break the retrieval log or the returned payload."""
        sources = []
        for c in chunks or []:
            if isinstance(c, dict):
                src = c.get("source")
                if src:
                    sources.append(str(src))
            else:
                src = getattr(c, "source", None)
                if src:
                    sources.append(str(src))
        return sources

    def _log_retrieval(self, question, num_results, sources, latency_ms, success, error=None):
        if self.logger is None:
            return
        try:
            self.logger.log_rag_retrieval(
                query=question,
                num_results=num_results,
                sources=sources,
                latency_ms=latency_ms,
                success=success,
                error=error,
            )
        except Exception:
            # Logging must never break retrieval.
            pass