import os
from typing import List, Dict, Optional

try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions
    CHROMADB_AVAILABLE = True
except Exception:
    CHROMADB_AVAILABLE = False


class InMemoryVectorStore:
    def __init__(self, dim: int, persist_directory: str = None):
        self.dim = dim
        self.persist_directory = persist_directory
        # runtime chroma flag (avoid mutating module-global)
        self.use_chroma = CHROMADB_AVAILABLE
        if self.use_chroma:
            # try to initialize chroma client; fall back to in-memory on any error
            try:
                settings = Settings(chroma_db_impl="duckdb+parquet", persist_directory=persist_directory)
                self.client = chromadb.Client(settings=settings)
                self.collection = self.client.get_or_create_collection(name="documents")
            except Exception as e:
                # avoid crashing the whole app for configuration/migration issues
                import logging
                logging.warning("Chroma initialization failed, falling back to in-memory store: %s", e)
                self._init_inmemory()
                # disable chroma for this instance
                self.use_chroma = False
        else:
            self._init_inmemory()

    def _init_inmemory(self):
        self.ids: List[str] = []
        self.vectors: List[List[float]] = []
        self.texts: List[str] = []
        self.metadatas: List[Dict] = []

    def add_many(self, ids: List[str], vectors: List, texts: List[str], metadatas: Optional[List[Dict]] = None):
        if metadatas is None:
            metadatas = [{} for _ in ids]
        if self.use_chroma:
            self.collection.add(
                ids=ids,
                embeddings=[v.tolist() for v in vectors],
                metadatas=metadatas,
                documents=texts,
            )
            if self.persist_directory:
                self.client.persist()
        else:
            for i, vid in enumerate(ids):
                self.ids.append(vid)
                self.vectors.append(vectors[i].tolist() if hasattr(vectors[i], 'tolist') else vectors[i])
                self.texts.append(texts[i])
                self.metadatas.append(metadatas[i])

    def search(self, query_vector, top_k: int = 5) -> List[Dict]:
        if self.use_chroma:
            res = self.collection.query(query_embeddings=[query_vector.tolist()], n_results=top_k, include=['documents','metadatas','distances'])
            results = []
            docs = res.get('documents', [[]])[0]
            metadatas = res.get('metadatas', [[]])[0]
            distances = res.get('distances', [[]])[0]
            ids = res.get('ids', [[]])[0]
            for i in range(len(docs)):
                results.append({"id": ids[i], "score": float(1 - distances[i]) if distances and distances[i] is not None else None, "text": docs[i], "metadata": metadatas[i]})
            return results
        else:
            if len(self.vectors) == 0:
                return []
            import numpy as np
            mats = np.array(self.vectors)
            sims = mats.dot(query_vector)
            idx = np.argsort(-sims)[:top_k]
            results = []
            for i in idx:
                results.append({"id": self.ids[i], "score": float(sims[i]), "text": self.texts[i], "metadata": self.metadatas[i]})
            return results

    def delete_doc(self, doc_id: str) -> int:
        """
        Delete all vectors/chunks belonging to a document id.
        Returns number of deleted chunks (best-effort for Chroma).
        """
        if not doc_id:
            return 0

        if self.use_chroma:
            # Chroma supports deleting by metadata filter.
            try:
                # NOTE: depending on Chroma version, where filter may vary.
                self.collection.delete(where={"doc_id": doc_id})
                if self.persist_directory:
                    self.client.persist()
                return 0
            except Exception:
                # fall back to best-effort id-based delete if available
                try:
                    # attempt to find ids then delete
                    res = self.collection.get(where={"doc_id": doc_id}, include=[])
                    ids = res.get("ids") or []
                    if ids:
                        self.collection.delete(ids=ids)
                        if self.persist_directory:
                            self.client.persist()
                        return len(ids)
                except Exception:
                    pass
                return 0

        # In-memory delete
        keep_ids = []
        keep_vectors = []
        keep_texts = []
        keep_metas = []
        deleted = 0
        for i in range(len(self.ids)):
            md = self.metadatas[i] or {}
            if md.get("doc_id") == doc_id:
                deleted += 1
                continue
            keep_ids.append(self.ids[i])
            keep_vectors.append(self.vectors[i])
            keep_texts.append(self.texts[i])
            keep_metas.append(self.metadatas[i])
        self.ids = keep_ids
        self.vectors = keep_vectors
        self.texts = keep_texts
        self.metadatas = keep_metas
        return deleted
