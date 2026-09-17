import os
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document


class DocumentLoader:
    """Load documents from the corpus directory."""

    def __init__(self, corpus_dir="knowledge/corpus"):
        self.corpus_dir = Path(corpus_dir)

    def load_all(self):
        """Load all supported documents from corpus."""
        documents = []

        if not self.corpus_dir.exists():
            print(f"Corpus directory not found: {self.corpus_dir}")
            return documents

        for file_path in self.corpus_dir.iterdir():
            if not file_path.is_file():
                continue
            suffix = file_path.suffix.lower()
            if suffix == ".pdf":
                documents.extend(self._load_pdf(file_path))
            elif suffix in (".md", ".txt"):
                documents.extend(self._load_text(file_path))
            elif suffix == ".csv":
                documents.extend(self._load_csv(file_path))
            elif suffix == ".json":
                documents.extend(self._load_json(file_path))

        print(f"Loaded {len(documents)} document segments")
        return documents

    def _load_pdf(self, file_path):
        """Load a PDF file."""
        loader = PyPDFLoader(str(file_path))
        docs = loader.load()
        for doc in docs:
            doc.metadata["source"] = file_path.name
            doc.metadata["type"] = "pdf"
        return docs

    def _load_text(self, file_path):
        """Load a text or markdown file."""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return [Document(
            page_content=content,
            metadata={"source": file_path.name, "type": "text"}
        )]

    def _load_csv(self, file_path):
        """Load a CSV file as text."""
        import csv
        rows = []
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                rows.append(", ".join(row))
        content = "\n".join(rows)
        return [Document(
            page_content=content,
            metadata={"source": file_path.name, "type": "csv"}
        )]

    def _load_json(self, file_path):
        """Load a JSON file as text."""
        import json
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        content = json.dumps(data, indent=2)
        return [Document(
            page_content=content,
            metadata={"source": file_path.name, "type": "json"}
        )]
