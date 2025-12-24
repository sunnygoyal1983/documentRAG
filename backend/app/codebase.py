import os
from typing import List, Dict
from .ingest import chunk_text
from .embeddings import EmbeddingModel
from .vector_store import InMemoryVectorStore

# Directories and files to ignore during codebase indexing
IGNORE_DIRS = {
    "node_modules", ".next", "__pycache__", ".git", "venv", "env", 
    "dist", "build", ".vscode", ".idea", "chroma_db", "data"
}
IGNORE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".pdf", ".zip", 
    ".tar", ".gz", ".exe", ".dll", ".so", ".pyc", ".pyo", ".db", ".sqlite",
    ".bin", ".onnx", ".pkl", ".pt"
}
# Explicitly supported database and config extensions
SUPPORTED_DATA_EXTENSIONS = {
    ".sql", ".prisma", ".dbml", ".yaml", ".yml", ".json", ".xml"
}

class CodebaseAssistant:
    def __init__(self, root_dir: str, embedder: EmbeddingModel):
        self.root_dir = root_dir
        self.embedder = embedder
        # Initialize a separate vector store for the codebase
        # We use a distinct persist_directory to avoid mixing with uploaded documents
        self.persist_dir = os.path.join(os.path.dirname(__file__), '..', 'codebase_db')
        os.makedirs(self.persist_dir, exist_ok=True)
        self.vector_store = InMemoryVectorStore(dim=embedder.dim, persist_directory=self.persist_dir)
        self.is_indexed = False

    def index_codebase(self, force: bool = False):
        if self.is_indexed and not force:
            return

        print(f"Indexing codebase at {self.root_dir}...")
        all_chunks = []
        all_ids = []
        all_metadatas = []

        for root, dirs, files in os.walk(self.root_dir):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in IGNORE_EXTENSIONS:
                    continue

                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.root_dir)

                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        if not content.strip():
                            continue
                        
                        # Add a header to the content so the LLM knows which file it's looking at
                        header = f"File: {rel_path}\n\n"
                        chunks = chunk_text(header + content, max_chars=2000, overlap_chars=200)
                        
                        for i, chunk in enumerate(chunks):
                            chunk_id = f"{rel_path}:{i}"
                            all_chunks.append(chunk)
                            all_ids.append(chunk_id)
                            all_metadatas.append({
                                "path": rel_path,
                                "chunk_index": i,
                                "type": "codebase"
                            })
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

        if all_chunks:
            # Add chunks in batches to avoid OOM or API limits
            batch_size = 100
            for i in range(0, len(all_chunks), batch_size):
                batch_chunks = all_chunks[i:i + batch_size]
                batch_ids = all_ids[i:i + batch_size]
                batch_metadatas = all_metadatas[i:i + batch_size]
                
                embeddings = self.embedder.embed_texts(batch_chunks)
                self.vector_store.add_many(batch_ids, embeddings, batch_chunks, metadatas=batch_metadatas)

        self.is_indexed = True
        print(f"Codebase indexing complete. Indexed {len(all_chunks)} chunks.")

    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        if not self.is_indexed:
            self.index_codebase()
        
        q_emb = self.embedder.embed_texts([query])[0]
        return self.vector_store.search(q_emb, top_k=top_k)
