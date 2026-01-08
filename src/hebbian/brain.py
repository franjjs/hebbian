

from hebbian.embedding.local_embedding_store import LocalEmbeddingStore
from hebbian.memory.kuzu_memory_store import KuzuMemoryStore


class HebbianBrain:
    """Main logic for Hebbian clipboard manager."""

    def __init__(self, db_path="./data/hebb_db", read_only=False):
        self.embedding_store = LocalEmbeddingStore(load_model=not read_only)
        self.memory_store = KuzuMemoryStore(db_path=db_path, read_only=read_only)

    def strengthen(self, content, context_name):
        """Add or update memory with embedding and context."""
        from datetime import datetime, timezone
        embedding = self.embedding_store.encode(content)
        embedding_str = self.embedding_store.embedding_to_str(embedding)
        now_utc = datetime.now(timezone.utc)
        self.memory_store.add_memory(content, context_name, embedding_str, now_utc)

    def increment_weight(self, content, context_name):
        """Increment weight for a memory in a context."""
        from datetime import datetime, timezone
        now_utc = datetime.now(timezone.utc)
        self.memory_store.increment_weight(content, context_name, now_utc)

    def recall_smart(self, context_name, limit=15, ttl=None):
        """Recall memories by context, weight, and recency. Purge expired by ttl."""
        if ttl is None:
            try:
                from hebbian.config import load_config
                config = load_config()
                ttl = config.get('settings', {}).get('ttl', None)
            except Exception:
                ttl = None
        return self.memory_store.recall_memories(context_name, limit, ttl)

    def get_full_graph_summary(self):
        """Return full graph summary of memories and contexts."""
        return self.memory_store.get_full_graph_summary()

    def search_globally(self, search_term, limit=10):
        """Search memories globally by term."""
        return self.memory_store.search_globally(search_term, limit)

    def clear_all_memories(self):
        """Clear all memories from the store."""
        self.memory_store.clear_all()
