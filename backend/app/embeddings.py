from sentence_transformers import SentenceTransformer
import numpy as np
import os


class EmbeddingModel:
    def __init__(self, model_name: str | None = None):
        # Allow switching to a smaller model to avoid Docker OOM (exit 137)
        # Examples:
        #   all-MiniLM-L6-v2 (fast/low memory)
        #   all-mpnet-base-v2 (higher quality, more memory)
        if model_name is None:
            model_name = os.environ.get("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
        # Guard against accidental quoting from docker-compose like "all-MiniLM-L6-v2"
        model_name = model_name.strip().strip('"').strip("'")
        self.model = SentenceTransformer(model_name)
        # typical embedding dim for mpnet is 768
        self.dim = self.model.get_sentence_embedding_dimension()

    def embed_texts(self, texts):
        batch_size = int(os.environ.get("EMBEDDING_BATCH_SIZE", "16"))
        emb = self.model.encode(
            texts,
            show_progress_bar=False,
            convert_to_numpy=True,
            batch_size=batch_size,
        )
        # L2-normalize
        norms = np.linalg.norm(emb, axis=1, keepdims=True) + 1e-12
        return emb / norms

    def embed_text(self, text):
        return self.embed_texts([text])[0]
