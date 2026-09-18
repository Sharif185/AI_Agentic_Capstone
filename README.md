# University Student-Support Case Agent

## Setup

### 1. Clone Repository

git clone [your-repo-url]
cd [repo-name]

### 2. Create Virtual Environment

python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

### 3. Install Dependencies

pip install -r requirements.txt

### 4. Configure Environment

cp .env.example .env

# Edit .env with your API key

### 5. Index the Corpus

python src/rag/index_corpus.py

### 6. Run the Application

python src/main.py

## Project Structure

+-- knowledge/
| +-- corpus/ # Source documents
| +-- vectordb/ # Chroma vector store
| +-- corpus-register.md
+-- src/
| +-- models/ # Model client
| +-- rag/ # RAG pipeline
| +-- main.py
+-- prompts/ # Versioned prompts
+-- tests/ # Test cases and results
+-- docs/ # Documentation

## RAG Pipeline

1. Documents loaded from knowledge/corpus/
2. Chunked into 500-char segments with 50-char overlap
3. Embedded using OpenAI text-embedding-3-small
4. Stored in Chroma vector database
5. Retrieved via similarity search (Top-3)
6. Passed to GPT-4o-mini with system prompt
