# RAG Architecture

## Overview
Our pipeline has two phases. Indexing runs offline and only needs to be
repeated when the corpus changes. Retrieval runs on every student query
and is what produces the grounded, cited answer.

## Phase 1: Indexing (Offline)
Documents of every supported type are loaded, split into overlapping
chunks, converted into embedding vectors, and persisted in a Chroma
database on disk.

Documents (15 source files: PDF, MD, CSV, JSON)
  -> Chunking (Recursive splitter, 600 chars, 100 overlap)
  -> Embedding (OpenAI text-embedding-3-small)
  -> Vector Store (Chroma, persistent on disk)

Run once via `python src/rag/index_corpus.py` — re-run whenever the corpus changes.

## Phase 2: Retrieval (Online)
The student's question is embedded with the same model used at indexing
time, matched against the stored vectors, and the top matches are
assembled into context that the LLM must answer from — and cite.

Student Query -> Query Embedding (same model as indexing)
  -> Similarity Search (Chroma vector search, Top-K = 5)
  -> Retrieved Chunks (text + metadata: source, type, score)
  -> Context Assembly (chunks formatted with [Document n: source])
  -> LLM Generation (GPT-4o-mini, prompt v2.1)
  -> Grounded Answer (answer + source citation)
  -> Student Response (answer, sources, or ticket offer)

If no chunk is relevant, the prompt forces the model to reply:
"I don't have that information in my current documents."

## Component Details

| Component | Technology | Purpose |
|---|---|---|
| Document Loader | PyPDF, markdown, csv | Read all file types |
| Chunker | RecursiveCharacterTextSplitter | Split into chunks with overlap |
| Embedding Model | OpenAI text-embedding-3-small | Convert text to vectors |
| Vector Store | Chroma | Store and search embeddings |
| Retriever | Similarity search (Top-K) | Find relevant chunks |
| Context Builder | Custom Python | Format chunks with metadata |
| LLM | GPT-4o-mini | Generate answer from context |

## Key Design Decisions

**Why 500–600 character chunks?**
- Small enough to be specific
- Large enough to contain complete thoughts
- Fits several chunks comfortably in the context window

**Why 50–100 character overlap?**
- Prevents information loss at chunk boundaries
- Ensures continuity between chunks

**Why Top-K retrieval?**
- Balances context richness with token cost
- Reduces noise from irrelevant documents
- Enough to answer most questions

**Why Chroma?**
- Simple Python API
- Persistent storage
- Good for small corpora (10–50 docs)
- Free and open-source

## Source Grounding Strategy
Every response will include:
- The answer text
- Source document name
- Section/page reference (where available)
- Confidence indicator (if retrieval score is low)