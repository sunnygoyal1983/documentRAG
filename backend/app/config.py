import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # App Config
    APP_NAME: str = "AI Codebase Assistant"
    DEBUG: bool = False
    
    # Storage Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR: str = os.path.join(BASE_DIR, "..", "data")
    CHROMA_DIR: str = os.path.join(BASE_DIR, "..", "chroma_db")
    CODEBASE_DIR: str = os.path.join(BASE_DIR, "..", "codebase_db")
    
    # LLM Config
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:14b"
    OLLAMA_TIMEOUT_S: float = 600.0
    TGI_URL: str = ""
    
    # RAG Config
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    EMBEDDING_BATCH_SIZE: int = 16
    CHUNK_MAX_CHARS: int = 2000
    CHUNK_OVERLAP_CHARS: int = 200
    MAX_CHUNKS_PER_DOC: int = 500
    
    # Security & Limits
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]
    MAX_FILE_SIZE_MB: int = 10
    MAX_FILES_PER_REQUEST: int = 10
    
    class Config:
        env_file = ".env"

settings = Settings()
