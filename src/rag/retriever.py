class Retriever:
    """Retrieve relevant chunks for a query."""

    def __init__(self, vector_store, k=5):
        # Top-K = 5 per the failure-analysis fix (was 3)
        self.vector_store = vector_store
        self.k = k

    def retrieve(self, query):
        """
        Retrieve top-k chunks for a query.

        Returns:
            list of dicts with 'content', 'source', 'type', 'score'
        """
        results = self.vector_store.similarity_search(query, k=self.k)
        retrieved = []
        for doc, score in results:
            retrieved.append({
                "content": doc.page_content,
                "source": doc.metadata.get("source", "Unknown"),
                "type": doc.metadata.get("type", "unknown"),
                "score": float(score)
            })
        return retrieved

    def format_context(self, retrieved_chunks):
        """Format retrieved chunks into a context string."""
        if not retrieved_chunks:
            return "No relevant documents found."

        context_parts = []
        for i, chunk in enumerate(retrieved_chunks, 1):
            context_parts.append(
                f"[Document {i}: {chunk['source']}]\n"
                f"{chunk['content']}\n"
            )
        return "\n---\n".join(context_parts)
