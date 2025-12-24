import json
import logging
import os
from typing import List, Optional, Dict, Any
from .llm_client import generate_assistant_response
from .schemas import AssistantResponse, AssistantFile
from .config import settings

logger = logging.getLogger(__name__)

class CodeGenerationService:
    """
    Service responsible for orchestrating the code generation process.
    Handles RAG context, LLM interaction, validation, and auto-recovery.
    """
    
    def __init__(self, assistant_rag):
        self.assistant_rag = assistant_rag

    async def generate_code(self, instruction: str, top_k: int = 15) -> AssistantResponse:
        """
        Main entry point for generating code based on a user instruction.
        """
        logger.info(f"Generating code for instruction: {instruction[:100]}...")
        
        # 1. Retrieve context
        results = self.assistant_rag.search(instruction, top_k=top_k)
        contexts = [r.get("text") for r in results]
        
        # 2. Add explicit database context if available
        db_context = self._get_database_context()
        if db_context:
            contexts.insert(0, f"DATABASE SCHEMA CONTEXT:\n{db_context}")
        
        # 3. Generate and validate with retries
        max_retries = 2
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                raw_output = generate_assistant_response(instruction, contexts)
                return self._parse_and_validate(raw_output)
            except Exception as e:
                last_error = e
                logger.warning(f"Generation attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries:
                    # Modify instruction slightly for retry to nudge the LLM
                    instruction += " (Ensure valid JSON output format)"
        
        logger.error(f"All generation attempts failed. Last error: {str(last_error)}")
        raise last_error

    def _parse_and_validate(self, raw_output: str) -> AssistantResponse:
        """
        Extracts JSON from LLM output and validates it against the schema.
        """
        json_str = self._extract_json(raw_output)
        
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}. Raw snippet: {raw_output[:200]}")
            raise ValueError(f"LLM produced invalid JSON: {str(e)}")

        # Normalize common LLM hallucinations
        data = self._normalize_schema(data)
        
        # Validate file paths for security
        self._validate_security(data)
        
        return AssistantResponse(**data)

    def _extract_json(self, text: str) -> str:
        """
        Robustly extracts JSON block from potentially messy LLM output.
        """
        text = text.strip()
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx == -1 or end_idx == -1 or end_idx < start_idx:
            # Fallback: try to find the first balanced brace block
            brace_count = 0
            found_start = False
            extracted = ""
            for char in text:
                if char == '{':
                    brace_count += 1
                    found_start = True
                if found_start:
                    extracted += char
                if char == '}':
                    brace_count -= 1
                    if brace_count == 0 and found_start:
                        return extracted
            raise ValueError("No valid JSON object found in LLM output.")
            
        return text[start_idx : end_idx + 1]

    def _normalize_schema(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fixes common structural errors in LLM output.
        """
        # If LLM returned a different structure (e.g., from a previous prompt version)
        if "files" not in data and "class" in data:
             data = {
                 "summary": "Auto-recovered code generation",
                 "assumptions": ["LLM used legacy/incorrect schema; attempt made to recover content"],
                 "files": [{
                     "path": "generated_code.txt",
                     "action": "create",
                     "language": "text",
                     "content": json.dumps(data, indent=2)
                 }]
             }
        
        # Ensure mandatory top-level fields
        if "summary" not in data: data["summary"] = "Code generated successfully."
        if "assumptions" not in data: data["assumptions"] = []
        if "files" not in data: data["files"] = []
        
        # Normalize individual files
        for file in data["files"]:
            if not isinstance(file, dict):
                continue
                
            # Handle missing 'action'
            if "action" not in file:
                file["action"] = "create"
                
            # Handle missing 'language'
            if "language" not in file:
                path = file.get("path", "")
                file["language"] = self._guess_language(path)
                
            # Handle missing 'content' (unlikely but possible)
            if "content" not in file:
                file["content"] = ""
                
        return data

    def _guess_language(self, path: str) -> str:
        """
        Guesses programming language based on file extension.
        """
        ext = path.split('.')[-1].lower() if '.' in path else ''
        mapping = {
            'py': 'python',
            'ts': 'typescript',
            'tsx': 'typescript',
            'js': 'javascript',
            'jsx': 'javascript',
            'html': 'html',
            'css': 'css',
            'json': 'json',
            'md': 'markdown',
            'sql': 'sql',
            'sh': 'shell',
            'yml': 'yaml',
            'yaml': 'yaml',
            'dockerfile': 'dockerfile'
        }
        return mapping.get(ext, 'text')

    def _get_database_context(self) -> str:
        """
        Reads all SQL and schema files from the database directory to provide explicit context.
        """
        db_dir = os.path.join(settings.BASE_DIR, "database")
        if not os.path.exists(db_dir):
            return ""
            
        context_parts = []
        try:
            for file in os.listdir(db_dir):
                if file.endswith((".sql", ".prisma", ".dbml")):
                    file_path = os.path.join(db_dir, file)
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        context_parts.append(f"--- File: {file} ---\n{content}")
        except Exception as e:
            logger.warning(f"Error reading database context: {str(e)}")
            
        return "\n\n".join(context_parts)

    def _validate_security(self, data: Dict[str, Any]):
        """
        Prevents path traversal and other security issues.
        """
        for file in data.get("files", []):
            path = file.get("path", "")
            # Prevent absolute paths or path traversal
            if path.startswith("/") or ".." in path:
                logger.warning(f"Security blocked: invalid path '{path}'")
                file["path"] = os.path.basename(path) # Sanitize to just filename
            
            # Limit file content size (e.g., 1MB per file)
            content = file.get("content", "")
            if len(content) > 1024 * 1024:
                logger.warning(f"Security: file '{path}' content too large")
                file["content"] = content[:1024 * 1024] + "\n... [TRUNCATED DUE TO SIZE] ..."
