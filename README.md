# AI Tools Suite (Local, Open-Source)

## Why I built this

I built this tool to explore how open-source LLMs can be applied to real developer workflows without relying on paid APIs or hosted services.

This repository contains two complementary AI tools:
- **AI Codebase Assistant** — focused on developer productivity and code understanding  
- **Document Q&A** — a local, privacy-first RAG system for structured document querying  

The goal was to design systems that are practical, secure, and reproducible, rather than demo-only AI experiments.

---

## 🛠️ AI Tools Suite

This repository provides a unified workspace for AI-powered development and document analysis.

---

## 1. AI Codebase Assistant — Code Understanding & Generation

A standalone web tool designed for developers who want AI-assisted code generation and analysis with full control over their data.

The system uses Retrieval-Augmented Generation (RAG) to understand repository context and generate structured, production-oriented outputs. Output quality depends on repository structure and task complexity.

### 🚀 Key Features

- **Codebase RAG**: Semantic indexing of local repositories for contextual understanding.
- **Structured Output**: Deterministic JSON responses with validation and recovery.
- **Production-Oriented Code**: Generates implementation-focused outputs instead of skeletons.
- **Database Design Support**: SQL schemas, migrations, and architecture suggestions.
- **Security-First Design**:
  - Path traversal protection
  - File size limits
  - Sanitization of AI-generated file paths
- **Service-Oriented Architecture**: Clear separation between UI, API, LLM orchestration, and vector storage.

---

## 2. Document Q&A (Local RAG) — Knowledge Management

A local RAG system for interacting with personal or project documents. Upload PDFs, DOCX, or TXT files and ask questions grounded strictly in your data.

### 📚 Key Features

- **Multi-Format Support**: `.pdf`, `.docx`, and `.txt` ingestion.
- **Strict Grounding**: Answers are generated only from retrieved document context.
- **Metadata Transparency**: Visibility into source documents and chunks used.
- **Document Management**: List, manage, and delete indexed documents.
- **Privacy-First**: All embeddings and processing remain on the local machine.

---

## 🏗️ Architecture

The project is designed with maintainability, security, and scalability in mind:

- **Frontend**: Next.js (TypeScript) with modular components and Tailwind CSS.
- **Backend**: FastAPI (Python) following a service-layer architecture.
- **Vector Store**: ChromaDB with local persistence for fast retrieval.
- **LLM Orchestration**: Centralized prompts and robust parsing logic.
- **Configuration**: Environment-based configuration using `pydantic-settings`.

---

## 🛠️ Quick Start

### 1. Requirements
- Docker & Docker Compose
- Ollama (for local LLM inference)

### 2. Setup

```bash
# Start the full stack (frontend + backend + ollama)
docker compose up --build
```

### 3. Usage

1. Open `http://localhost:3000/assistant`
2. Enter a coding or document query
3. Review structured output and source context
4. Copy or export generated results

---

## ⚙️ Configuration

| Variable | Default | Description |
|--------|--------|-------------|
| OLLAMA_URL | http://localhost:11434 | Ollama service URL |
| OLLAMA_MODEL | qwen2.5:14b | LLM model |
| MAX_FILE_SIZE_MB | 10 | Max file size |
| ALLOWED_ORIGINS | http://localhost:3000 | CORS origins |

---

## ⚠️ Known Limitations

- No real-time autocomplete like Copilot or Cursor.
- Inference speed depends on local hardware.
- Generated code must be reviewed before production use.
- Very large or complex repositories may require tuning chunking and indexing strategies.

These trade-offs are intentional to preserve transparency, control, and local-first execution.

---

## 🔒 Security Considerations

- The system **never executes generated code**.
- All file paths are validated and sanitized.
- Strict schema validation for API inputs and outputs.

---

## 🧪 Testing

```bash
cd frontend
npm test
```

---

## 📝 License

MIT
