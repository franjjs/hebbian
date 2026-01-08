from sentence_transformers import SentenceTransformer
import numpy as np
from hebbian.embedding.embedding_store import EmbeddingStore


class LocalEmbeddingStore(EmbeddingStore):
    """Local embedding store using sentence-transformers."""

    def __init__(self, model_name='all-MiniLM-L6-v2', load_model=True):
        self.model = None
        if load_model:
            self.model = SentenceTransformer(model_name)

    def encode(self, text):
        """Encode text to embedding vector."""
        if not self.model:
            return np.zeros(384)
        return self.model.encode(text, show_progress_bar=False)

    def embedding_to_str(self, embedding):
        """Convert embedding vector to string."""
        return ','.join(f"{x:.4f}" for x in embedding.tolist())

    def str_to_embedding(self, emb_str):
        """Convert string to embedding vector."""
        if not emb_str:
            return np.zeros(384)
        return np.array([float(x) for x in emb_str.split(',')])
