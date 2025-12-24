import httpx
import logging
from typing import List, Optional, Tuple
from .config import settings

logger = logging.getLogger(__name__)

NOT_IN_DOC_MSG = "The document does not contain this information."

def generate_answer(question: str, contexts: List[str], max_tokens: int = 512) -> str:
    """
    Generates a concise answer based ONLY on provided contexts.
    """
    if not contexts:
        return NOT_IN_DOC_MSG

    prompt = _build_rag_prompt(question, contexts)
    
    # Try Ollama first, then fallback to TGI if configured
    if settings.OLLAMA_URL:
        resp, err = _call_ollama(prompt, max_tokens, settings.OLLAMA_MODEL)
        if not err:
            return resp.strip()
    
    if settings.TGI_URL:
        return _call_tgi(prompt, max_tokens)
        
    return f"[LLM unavailable] Contexts found:\n\n" + "\n\n".join(contexts)

def generate_assistant_response(instruction: str, contexts: List[str]) -> str:
    """
    Generates a structured JSON response for the Codebase Assistant.
    """
    prompt = _build_assistant_system_prompt(instruction, contexts)
    max_tokens = 4096 # High limit for code generation
    
    if settings.OLLAMA_URL:
        resp, err = _call_ollama(prompt, max_tokens, settings.OLLAMA_MODEL)
        if err:
            logger.error(f"Ollama error: {err}")
            raise RuntimeError(f"Ollama inference failed: {err}")
        return resp.strip()
    
    if settings.TGI_URL:
        return _call_tgi(prompt, max_tokens)
        
    raise RuntimeError("No LLM service configured.")

def _build_rag_prompt(question: str, contexts: List[str]) -> str:
    system = (
        "You are a helpful assistant that answers questions strictly using provided excerpts.\n"
        f"If the answer is not in the excerpts, say: '{NOT_IN_DOC_MSG}'\n"
    )
    ctx_str = "\n\n".join([f"Excerpt {i+1}:\n{c}" for i, c in enumerate(contexts)])
    return f"{system}\n\n{ctx_str}\n\nQuestion: {question}\nAnswer:"

def _build_assistant_system_prompt(instruction: str, contexts: List[str]) -> str:
    system = """You are a Staff Software Engineer, Technical Architect, and Database Expert.
Your task is to generate production-ready code and database schemas based on the provided codebase context.

STRICT OPERATIONAL RULES:
1. NO placeholders, NO TODOs, NO skeletons.
2. Generate FULL, working implementations that can be copy-pasted.
3. Follow the existing style and patterns found in the context (if any).
4. If no relevant context exists, design from scratch using industry best practices.
5. Output MUST be a single, valid JSON object.
6. NO conversational text before or after the JSON.

RESPONSIBILITIES:
- Logic: Backend/Frontend implementations.
- Database: SQL schemas, migrations, ORM models, and architecture design (including new projects).
- Architecture: Multi-file changes, infrastructure as code, and system design.

JSON SCHEMA:
{
  "summary": "Technical explanation of the changes and database impact",
  "assumptions": ["List of logical assumptions made"],
  "files": [
    {
      "path": "relative/path/to/file.ext",
      "action": "create" | "modify",
      "language": "python" | "typescript" | "sql" | "json",
      "content": "FULL FILE CONTENT"
    }
  ]
}

SPECIAL INSTRUCTIONS:
- Always check for "DATABASE SCHEMA CONTEXT" in the context excerpts.
- If the user's request involves modifying the current project, strictly refer to the existing schema.
- If the user's request is for a NEW project or feature (e.g., "Design an e-commerce schema"), ignore the existing schema and design a modern, production-ready architecture from scratch.
- For new designs, provide a detailed technical analysis in the "summary" explaining your architectural choices (e.g., normalization, indexing, scaling).
- Propose new files in the "files" array with appropriate paths (e.g., "database/ecommerce.sql").
- Ensure all generated code follows industry best practices for the chosen stack.

Context excerpts from the codebase:
"""
    ctx_str = "\n\n".join([f"Context {i+1}:\n{c}" for i, c in enumerate(contexts)])
    return f"{system}\n{ctx_str}\n\nUser Request: {instruction}\n\nFinal Output (JSON ONLY):"

def _call_ollama(prompt: str, max_tokens: int, model: str) -> Tuple[str, Optional[str]]:
    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": 0.1, # Low temperature for deterministic output
                "top_p": 0.9
            }
        }
        r = httpx.post(f"{settings.OLLAMA_URL}/api/generate", json=payload, timeout=settings.OLLAMA_TIMEOUT_S)
        r.raise_for_status()
        return r.json().get("response", ""), None
    except Exception as e:
        return "", str(e)

def _call_tgi(prompt: str, max_tokens: int) -> str:
    try:
        payload = {"inputs": prompt, "parameters": {"max_new_tokens": max_tokens}}
        r = httpx.post(f"{settings.TGI_URL.rstrip('/')}/v1/generate", json=payload, timeout=settings.OLLAMA_TIMEOUT_S)
        r.raise_for_status()
        data = r.json()
        return data.get("generated_text", str(data))
    except Exception as e:
        logger.error(f"TGI error: {e}")
        return f"[TGI error: {e}]"
