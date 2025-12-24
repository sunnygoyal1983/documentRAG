from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class UploadResponse(BaseModel):
    doc_id: str
    chunks: int


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(3, ge=1, le=20)


class QueryHit(BaseModel):
    id: str
    score: Optional[float] = None
    doc_id: Optional[str] = None
    filename: Optional[str] = None
    chunk_index: Optional[int] = None
    text: str
    metadata: Optional[Dict[str, Any]] = None


class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    hits: List[QueryHit]


class AssistantRequest(BaseModel):
    instruction: str = Field(..., min_length=1)


class AssistantFile(BaseModel):
    path: str
    action: str  # "create" | "modify"
    language: str
    content: str


class AssistantResponse(BaseModel):
    summary: str
    assumptions: List[str]
    files: List[AssistantFile]



