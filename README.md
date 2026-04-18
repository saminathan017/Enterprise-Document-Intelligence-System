# Enterprise Document Intelligence

A full-stack document Q&A system built with FastAPI, React, and RAG (Retrieval-Augmented Generation). Upload your PDFs, Word docs, spreadsheets, or presentations — then ask questions and get answers grounded in your actual documents, with citations showing exactly where the answer came from.

---

## What it does

You upload documents. The system breaks them into chunks, embeds them into a vector database, and uses a hybrid search (BM25 + semantic) to find the most relevant pieces when you ask a question. Those pieces go into a GPT-4o prompt along with instructions to reason step by step and cite sources inline. The answer streams back to the UI token by token.

Beyond basic RAG, there are several layers added on top:

- **CRAG** — before sending chunks to the LLM, each one gets scored for relevance. Low-scoring chunks are dropped. If not enough good chunks survive, it can fall back to a web search.
- **Parent-child chunking** — retrieval uses small 400-char child chunks for precision, but the LLM sees the larger 1200-char parent window for context.
- **Contextual compression** — an optional step where GPT-4o-mini strips each chunk down to only the sentences relevant to the question.
- **Lost-in-the-middle reordering** — the best chunks go at the start and end of the context, not in the middle, since LLMs tend to ignore what's in the middle of long prompts.
- **NLI faithfulness scoring** — after the answer is generated, a DeBERTa cross-encoder checks how well the answer is supported by the retrieved context.

---

## Tech stack

**Backend**
- FastAPI + Uvicorn
- ChromaDB (vector store, persisted to disk)
- BAAI/bge-large-en-v1.5 (1024-dim embeddings, sentence-transformers)
- rank-bm25 (sparse BM25 index, merged with dense via Reciprocal Rank Fusion)
- OpenAI API (GPT-4o for generation, GPT-4o-mini for CRAG/HyDE/compression)
- pdfplumber (PDF parsing with table extraction), PyPDF2 (fallback)
- python-docx, openpyxl/pandas, python-pptx (Word, Excel, PowerPoint)
- bert-score + tiktoken (evaluation and cost tracking)
- slowapi (rate limiting, 120 req/min)

**Frontend**
- React 18 + TypeScript + Vite
- Tailwind CSS
- Zustand (state management)
- TanStack React Query (data fetching + caching)
- Framer Motion (animations)
- Recharts (analytics charts)
- Cytoscape.js (knowledge graph visualization)
- Three.js (3D background)

---

## Project structure

```
├── app/
│   ├── api/              # FastAPI routers
│   │   ├── stream.py     # SSE streaming endpoint (main query path)
│   │   ├── ingest.py     # document upload
│   │   ├── documents.py  # list, delete, knowledge graph, analytics
│   │   ├── feedback.py   # thumbs up/down ratings
│   │   ├── costs.py      # token usage and API cost tracking
│   │   ├── session.py    # session management
│   │   └── evaluate.py   # RAG evaluation metrics
│   ├── ingestion/
│   │   ├── loaders.py    # PDF, DOCX, XLSX, CSV, PPTX parsers
│   │   ├── chunker.py    # parent-child chunking + table preservation
│   │   └── pipeline.py   # async background ingestion with job status
│   ├── vectorstore/
│   │   ├── store.py      # ChromaDB + BM25 hybrid with RRF
│   │   ├── embeddings.py # BGE embeddings with LRU cache
│   │   └── retrieval.py  # score normalization + retrieval logic
│   ├── rag/
│   │   ├── chain.py      # full RAG pipeline orchestration
│   │   ├── crag.py       # corrective RAG relevance filter
│   │   ├── contextual_compression.py
│   │   └── prompts.py    # system prompt, CoT template, HyDE, CRAG prompts
│   ├── evaluation/
│   │   └── metrics.py    # BERTScore, NLI faithfulness, LLM-as-judge
│   ├── memory/
│   │   ├── session_manager.py
│   │   └── conversation_memory.py
│   ├── core/
│   │   └── cost_tracker.py   # tiktoken counting + JSONL cost log
│   └── config.py         # Pydantic Settings (all config via .env)
│
├── frontend/
│   └── src/
│       ├── components/   # ChatView, DocumentsView, AnalyticsView, etc.
│       ├── hooks/        # useStreaming (SSE client)
│       ├── store/        # useStore (Zustand)
│       ├── api/          # client.ts (all API calls in one place)
│       └── types/        # TypeScript interfaces
│
├── tests/                # pytest test suite
├── start_dev.sh          # run backend + frontend dev servers together
├── start_prod.sh         # build frontend, serve everything from port 8000
├── docker-compose.yml
└── requirements.txt
```

---

## Getting started

### Prerequisites

- Python 3.11+
- Node.js 18+
- An OpenAI API key

### Local setup

```bash
# Clone
git clone https://github.com/saminathan017/Enterprise-Document-Intelligence-System.git
cd Enterprise-Document-Intelligence-System

# Copy env file and add your API key
cp .env.example .env
# open .env and set OPENAI_API_KEY=sk-...

# Run everything (creates venv, installs deps, starts both servers)
chmod +x start_dev.sh
./start_dev.sh
```

Then open:
- Frontend: http://localhost:3000
- API docs: http://localhost:8000/api/docs

### Manual setup (if you prefer)

```bash
# Backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

### Docker

```bash
cp .env.example .env
# set OPENAI_API_KEY in .env
docker-compose up --build
```

---

## Configuration

All settings are in `.env`. The important ones:

```env
OPENAI_API_KEY=sk-...

# Models
LLM_MODEL=gpt-4o                    # main generation model
HELPER_MODEL=gpt-4o-mini            # used for CRAG, HyDE, compression
OCR_MODEL=gpt-4o                    # used for scanned PDF OCR
EMBEDDING_MODEL=BAAI/bge-large-en-v1.5

# RAG
TOP_K_RETRIEVAL=5
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Storage
CHROMA_PERSIST_DIR=./data/chroma_db
SESSION_PERSIST_DIR=./data/sessions
```

---

## API endpoints

| Method | Path | What it does |
|--------|------|-------------|
| POST | `/api/v1/ingest` | Upload a document (PDF, DOCX, XLSX, CSV, PPTX, TXT) |
| POST | `/api/v1/stream/query` | Ask a question — streams back SSE events |
| GET | `/api/v1/documents` | List all ingested documents |
| DELETE | `/api/v1/documents/{id}` | Delete a document and all its chunks |
| POST | `/api/v1/knowledge-graph` | Build entity/relationship graph from docs |
| GET | `/api/v1/analytics` | Query counts, session stats, chunk counts |
| POST | `/api/v1/feedback` | Submit thumbs up/down on an answer |
| GET | `/api/v1/feedback/summary` | Positive/negative rate across all feedback |
| GET | `/api/v1/costs` | Total token usage and API spend by model |
| GET | `/api/v1/jobs/{job_id}` | Check status of a background ingestion job |
| GET | `/health` | Health check with embedding model info |
| GET | `/api/docs` | Swagger UI |

The SSE stream emits JSON events with `type` fields: `step`, `token`, `citations`, `metrics`, `done`, `error`. The frontend handles each type — step events update the pipeline progress bar, token events append to the message, and citations/metrics arrive at the end.

---

## How the query pipeline works

When you send a question, this is what happens on the backend:

1. **HyDE** (optional) — GPT-4o-mini generates a hypothetical answer document. That document gets embedded and used alongside your original query for retrieval, which tends to improve recall.

2. **Hybrid retrieval** — your query hits both the BM25 sparse index and the ChromaDB dense index. Results from both are merged using Reciprocal Rank Fusion (RRF) and ranked by a combined score.

3. **CRAG filter** — each retrieved chunk gets a 0–1 relevance score from GPT-4o-mini. Chunks scoring below 0.4 are dropped. If fewer than 2 chunks pass, all originals are kept.

4. **Parent expansion** — child chunk IDs are swapped out for their parent chunks, giving the LLM a wider context window per document section.

5. **Lost-in-the-middle reorder** — highest-scoring chunks go to positions 0 and -1 in the context array.

6. **Contextual compression** (optional, off by default) — GPT-4o-mini strips each chunk to only the relevant sentences.

7. **Generation** — GPT-4o streams the response with chain-of-thought reasoning and [^N] inline citations.

8. **NLI faithfulness** — DeBERTa cross-encoder scores the answer against the context (0–1). This score is sent to the frontend with the `metrics` SSE event.

9. **Cost tracking** — tiktoken counts input/output tokens, calculates cost, appends to `data/cost_log.jsonl`.

---

## Document support

| Format | How it's parsed |
|--------|----------------|
| PDF | pdfplumber extracts text and tables separately; PyPDF2 as fallback; GPT-4o Vision for scanned/image pages |
| DOCX | python-docx, element-level (paragraphs + tables as Markdown) |
| XLSX / XLS | pandas reads each sheet, outputs as Markdown tables |
| CSV | native csv module, outputs as Markdown table |
| PPTX | python-pptx, extracts text from each slide + speaker notes |
| TXT / MD | read directly |

Tables are detected and kept as atomic chunks — they never get split mid-row.

---

## Frontend features

- **Chat** — streaming Q&A with pipeline step indicators (retrieval → CRAG → generation), inline citations, copy button, processing time, thumbs up/down feedback
- **Voice input** — Web Speech API, works in Chrome/Edge
- **Export** — exports the full conversation to a printable HTML page (browser print → PDF)
- **Documents** — upload by drag-and-drop, see chunk count per file, delete individual documents
- **Knowledge Graph** — force-directed graph of entities and relationships extracted from your documents, built on Cytoscape.js
- **Analytics** — query activity chart, session distribution, satisfaction bar from feedback ratings, cost breakdown by model
- **Command palette** — Cmd+K to navigate between views

---

## Evaluation

There are three ways the system evaluates answer quality:

- **NLI faithfulness** — runs on every query automatically. Uses `cross-encoder/nli-deberta-v3-base` to check if the answer is entailed by the retrieved context.
- **BERTScore** — semantic precision/recall/F1 using contextual embeddings. Available via the `/api/v1/evaluate` endpoint.
- **LLM-as-judge** — GPT-4o-mini returns JSON scores for faithfulness, answer relevancy, and completeness. Used for batch evaluation of test sets.

Feedback from users (thumbs up/down) gets appended to `data/feedback.jsonl` and the summary is visible in the Analytics view.

---

## Running tests

```bash
source venv/bin/activate
pytest tests/ -v
```

---

## Notes

- The first startup takes a few minutes — it downloads the BAAI/bge-large-en-v1.5 model (~1.3GB) from HuggingFace.
- Scanned PDF support (GPT-4o Vision OCR) requires `pdf2image` and Poppler. Install with `brew install poppler` on Mac, then uncomment `pdf2image` in requirements.txt.
- ChromaDB data persists in `./data/chroma_db`. Delete that folder to reset the vector store.
- Session history persists as JSON files in `./data/sessions`.
- Cost logs write to `./data/cost_log.jsonl`. Feedback writes to `./data/feedback.jsonl`.

---

## License

MIT
