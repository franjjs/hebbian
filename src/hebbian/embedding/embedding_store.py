
from abc import ABC, abstractmethod
import numpy as np


class EmbeddingStore(ABC):
    """Abstract base class for embedding storage."""

    @abstractmethod
    def encode(self, text):
        """Encode text to embedding vector."""
        pass

    @abstractmethod
    def embedding_to_str(self, embedding):
        """Convert embedding vector to string."""
        pass

    @abstractmethod
    def str_to_embedding(self, emb_str):
        """Convert string to embedding vector."""
        pass

    @staticmethod
    def parse_embedding(emb_str, ref_emb):
        if not emb_str:
            return np.zeros_like(ref_emb)
        return np.array([float(x) for x in emb_str.split(',')])

    @staticmethod
    def cosine_sim(a, b):
        if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
            return -1
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def similarity(self, ref_emb, emb_str):
        emb = self.str_to_embedding(emb_str)
        return self.cosine_sim(ref_emb, emb)
