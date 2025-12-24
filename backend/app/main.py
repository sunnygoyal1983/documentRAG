import os
import uuid
import json
import logging
import threading
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .ingest import extract_text, chunk_text
from .embeddings import EmbeddingModel
from .vector_store import InMemoryVectorStore
from .llm_client import generate_answer
from .schemas import QueryRequest, QueryResponse, UploadResponse, QueryHit, AssistantRequest, AssistantResponse
from .codebase import CodebaseAssistant
from .services import CodeGenerationService

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description="Production-ready AI Codebase Assistant with RAG capabilities."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency Injection / Singleton patterns for core components
embedder = EmbeddingModel()
os.makedirs(settings.CHROMA_DIR, exist_ok=True)
os.makedirs(settings.DATA_DIR, exist_ok=True)

# Document RAG store (Legacy/Upload-based)
doc_vector_store = InMemoryVectorStore(dim=embedder.dim, persist_directory=settings.CHROMA_DIR)
doc_index = {} # metadata store: id -> {filename, path, chunks}

# Codebase RAG store
assistant_rag = CodebaseAssistant(root_dir=settings.BASE_DIR, embedder=embedder)
code_gen_service = CodeGenerationService(assistant_rag)

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.APP_NAME}...")
    # Background indexing for the codebase
    threading.Thread(target=assistant_rag.index_codebase, daemon=True).start()

# --- AI Codebase Assistant Endpoints ---

@app.post("/assistant/query", response_model=AssistantResponse)
async def assistant_query(body: AssistantRequest):
    """
    Primary endpoint for the AI Codebase Assistant.
    Generates production-ready code based on codebase analysis.
    """
    try:
        return await code_gen_service.generate_code(body.instruction)
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error during code generation")
        raise HTTPException(status_code=500, detail="Internal server error during code generation.")

# --- Document RAG Endpoints (Legacy/Reference) ---

@app.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and index a document for the generic RAG tool.
    """
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".txt", ".pdf", ".docx"]:
        raise HTTPException(status_code=400, detail="Unsupported file type. Use .txt, .pdf, or .docx")
    
    doc_id = str(uuid.uuid4())
    save_path = os.path.join(settings.DATA_DIR, f"{doc_id}{ext}")
    
    try:
        contents = await file.read()
        if len(contents) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"File too large (max {settings.MAX_FILE_SIZE_MB}MB)")
            
        with open(save_path, "wb") as f:
            f.write(contents)

        text = extract_text(save_path)
        if not (text or "").strip():
            raise HTTPException(status_code=400, detail="No extractable text found in document.")

        chunks = chunk_text(text, max_chars=settings.CHUNK_MAX_CHARS, overlap_chars=settings.CHUNK_OVERLAP_CHARS)
        if len(chunks) > settings.MAX_CHUNKS_PER_DOC:
             raise HTTPException(status_code=400, detail="Document exceeds maximum allowed chunks.")

        embeddings = embedder.embed_texts(chunks)
        ids = [f"{doc_id}:{i}" for i in range(len(chunks))]
        metadatas = [{"doc_id": doc_id, "chunk_index": i, "filename": file.filename} for i in range(len(chunks))]
        
        doc_vector_store.add_many(ids, embeddings, chunks, metadatas=metadatas)
        doc_index[doc_id] = {"filename": file.filename, "path": save_path, "chunks": len(chunks)}
        
        return UploadResponse(doc_id=doc_id, chunks=len(chunks))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Upload failed for {file.filename}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def query_documents(body: QueryRequest):
    """
    Generic RAG query against uploaded documents.
    """
    try:
        q_emb = embedder.embed_texts([body.query])[0]
        results = doc_vector_store.search(q_emb, top_k=body.top_k)
        
        contexts = [r.get("text") for r in results]
        sources = list(set([r.get("metadata", {}).get("doc_id") for r in results]))
        answer = generate_answer(body.query, contexts)
        
        hits = [
            QueryHit(
                id=r.get("id", ""),
                score=r.get("score"),
                doc_id=r.get("metadata", {}).get("doc_id"),
                filename=r.get("metadata", {}).get("filename"),
                chunk_index=r.get("metadata", {}).get("chunk_index"),
                text=r.get("text") or "",
                metadata=r.get("metadata") or {}
            ) for r in results
        ]
        
        return QueryResponse(answer=answer, sources=sources, hits=hits)
    except Exception as e:
        logger.exception("Query failed")
        raise HTTPException(status_code=500, detail="Search operation failed.")

@app.get("/documents")
async def list_documents():
    return doc_index

@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    meta = doc_index.get(doc_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        doc_vector_store.delete_doc(doc_id)
        if os.path.exists(meta["path"]):
            os.remove(meta["path"])
        doc_index.pop(doc_id)
        return {"status": "deleted", "doc_id": doc_id}
    except Exception as e:
        logger.error(f"Delete failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete document")
