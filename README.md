# Enterprise AI Agent - Enterprise AI Document Intelligence System

<div align="center">

![Enterprise AI Agent Logo](https://img.shields.io/badge/AI-Enterprise%20AI%20Agent-ff6b35?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDJMMiAyMkgyMkwxMiAyWiIgZmlsbD0iI2ZmNmIzNSIvPgo8L3N2Zz4=)

**Intelligent Document Analysis with Advanced RAG Technology**

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-0.1+-121212?style=flat)](https://www.langchain.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Architecture](#-architecture) • [Demo](#-demo)

</div>

---

## Overview

**Enterprise AI Agent** is an enterprise-grade AI-powered document intelligence system that enables natural language querying over document collections using Retrieval-Augmented Generation (RAG). Upload your PDFs, ask questions, and get instant, cited answers.

### Key Highlights

- **Advanced RAG Architecture** - Semantic search with GPT-4 powered generation
- **Multi-Document Support** - PDF, TXT, Markdown with intelligent chunking
- **Citation Tracking** - Every answer includes source attribution (99% accuracy)
- **High Performance** - Optimized for speed and accuracy
- **Modern UI** - Beautiful neural network visualization with smooth animations
- **Privacy-First** - Local vector storage, no data leakage
- **Conversational Intelligence** - Natural conversation handling

> 📖 **New!** Read our [Optimization Journey](OPTIMIZATION_JOURNEY.md) to learn about the challenges we faced and how we achieved 99% citation accuracy!

---

## Features

### Core Capabilities

| Feature | Description |
|---------|-------------|
| **Document Ingestion** | Upload PDF, TXT, MD files with automatic text extraction |
| **Semantic Search** | Vector-based retrieval using Sentence Transformers |
| **AI Q&A** | GPT-4 powered answers with conversation memory |
| **Source Citations** | Transparent attribution with similarity scores |
| **Session Management** | Persistent conversations with 24-hour retention |
| **Web Synthesis** | Optional external data integration |
| **Table Generation** | Structured data extraction and formatting |

### Technical Features

- **Modular Architecture** - Clean separation of concerns
- **Async API** - FastAPI with Pydantic validation
- **Vector Database** - ChromaDB for persistent storage
- **Embedding Caching** - LRU cache for 50% latency reduction
- **Batch Processing** - 3x faster document ingestion
- **High-DPI Rendering** - Retina-ready Canvas visualization

---

## Quick Start

### Prerequisites

- Python 3.9 or higher
- OpenAI API key
- 4 GB RAM minimum (8 GB recommended)

### Installation

```bash
# 1. Clone the repository
git clone <your-repo-url> enterprise-ai-agent
cd enterprise-ai-agent

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your OpenAI API key

# 5. Start the backend
python -m uvicorn app.main:app --reload

# 6. Open the frontend
open frontend/index.html # Or double-click the file
```

### First Query

1. **Upload a document** - Drag & drop PDF/TXT/MD file
2. **Ask a question** - Type naturally: "What is the main topic?"
3. **View citations** - See sources with match percentages

---

## Documentation

Comprehensive documentation available in the `docs/` directory:

| Document | Purpose |
|----------|---------|
| [**Project Overview & Interview Guide**](docs/guides/PROJECT_OVERVIEW.md) | Technical deep dive, architecture, interview prep |
| [**Development Timeline**](docs/guides/DEVELOPMENT_TIMELINE.md) | Milestones, transformations, resume bullet points |
| [**Complete User Guide**](docs/guides/USER_GUIDE.md) | Installation, usage, troubleshooting, best practices |

### Quick Links

- **API Documentation**: http://localhost:8000/docs (when server is running)
- **Health Check**: http://localhost:8000/health
- **Project Structure**: See [ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## Architecture

### High-Level System Design

```

 Browser 
 (Frontend) 

 REST API


 FastAPI Backend 

 Ingestion API 
 Query API 






ChromaDB OpenAI 
(Vector) GPT-4 

```

### Technology Stack

**Backend:**
- FastAPI (async web framework)
- LangChain (RAG orchestration)
- ChromaDB (vector database)
- Sentence Transformers (embeddings)
- OpenAI GPT-4 (generation)

**Frontend:**
- Vanilla HTML/CSS/JavaScript
- Canvas API (visualization)
- Fetch API (HTTP requests)

**Data Flow:**
```
Document → Load → Chunk → Embed → Store (ChromaDB)
Query → Embed → Retrieve → Context + Prompt → GPT-4 → Answer + Citations
```

---

## Demo

### Interface Preview

The Enterprise AI Agent interface features:
- **Neural Network Background** - 300 nodes with 3D depth effects
- **Chat Interface** - Clean, modern ChatGPT-style design
- **Citation Display** - Source documents with match percentages
- **Session Management** - Conversation history and context

### Example Interaction

```
 User: "What was the revenue growth in Q4?"

 Enterprise AI Agent: "Revenue grew by 23% in Q4 2024, reaching $4.2M, 
 compared to $3.4M in Q3 2024."

 SOURCES:
 Q4_Financial_Report.pdf (89% MATCH)
 "Q4 revenue reached $4.2M, representing a 23% increase..."
```

---

## Project Structure

```
enterprise-ai-agent/
 app/ # Backend application
 api/ # API endpoints
 ingest.py # Document upload
 query.py # Q&A endpoint
 session.py # Session management
 ingestion/ # Document processing
 loaders.py # PDF/TXT/MD loaders
 chunker.py # Text chunking
 pipeline.py # Ingestion pipeline
 rag/ # RAG implementation
 chain.py # RAG chain
 prompts.py # System prompts
 vectorstore/ # Vector database
 embeddings.py # Embedding generation
 store.py # ChromaDB interface
 retrieval.py # Semantic search
 memory/ # Session & conversation
 models/ # Pydantic models
 tools/ # Agentic tools
 config.py # Configuration
 main.py # FastAPI app
 frontend/ # Web interface
 index.html # Single-page app
 docs/ # Documentation
 01_Project_Overview_Interview_Guide.md
 02_Development_Timeline_Transformations.md
 03_Complete_User_Guide.md
 data/ # Data storage (gitignored)
 chroma_db/ # Vector database
 documents/ # Uploaded files
 sessions/ # Session data
 scripts/ # Utility scripts
 start.sh # Startup script
 tests/ # Unit tests
 .env.example # Environment template
 .gitignore # Git exclusions
 requirements.txt # Python dependencies
 README.md # This file
```

---

## Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-your-key-here

# Optional (defaults shown)
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
CHROMA_PERSIST_DIR=./data/chroma_db
EMBEDDING_MODEL=all-MiniLM-L6-v2
LLM_MODEL=gpt-4-turbo-preview
LLM_TEMPERATURE=0.1
RAG_TOP_K=5
RAG_SIMILARITY_THRESHOLD=0.7
```

### Customization

- **Prompts**: Edit `app/rag/prompts.py`
- **Chunk Size**: Modify `app/ingestion/chunker.py`
- **UI Theme**: Change colors in `frontend/index.html`
- **Models**: Update `.env` configuration

---

## Testing

```bash
# Run unit tests
pytest tests/

# Run with coverage
pytest --cov=app tests/

# Test specific module
pytest tests/test_ingestion.py
```

---

## Deployment

### Local Development

```bash
# Start backend
python -m uvicorn app.main:app --reload

# Open frontend
open frontend/index.html
```

### Production Deployment

See [docs/guides/USER_GUIDE.md](docs/guides/USER_GUIDE.md) for:
- Cloud deployment (AWS, GCP, Azure)
- Docker containerization
- Scaling strategies
- Security hardening

---

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## Author

Saminathan

---

## Acknowledgments

- **OpenAI** - GPT-4 API
- **LangChain** - RAG framework
- **ChromaDB** - Vector database
- **Sentence Transformers** - Embedding models
- **FastAPI** - Web framework

---

<div align="center">

**Built with dedication and optimism by Saminathan**

</div>
