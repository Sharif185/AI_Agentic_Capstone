from langchain.text_splitter import RecursiveCharacterTextSplitter


class DocumentChunker:
    """Split documents into chunks for embedding."""

    def __init__(self, chunk_size=600, chunk_overlap=100):
        # 600/100 per the failure-analysis fix in tests/week3-failures.md
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def chunk(self, documents):
        """Split documents into chunks."""
        chunks = self.splitter.split_documents(documents)
        print(f"Split into {len(chunks)} chunks")
        return chunks
