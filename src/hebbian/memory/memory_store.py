from abc import ABC, abstractmethod

class MemoryStore(ABC):
    @abstractmethod
    def add_memory(self, content, context_name, embedding, last_seen):
        pass

    @abstractmethod
    def associate_context(self, content, context_name):
        pass

    @abstractmethod
    def increment_weight(self, content, context_name, last_seen):
        pass

    @abstractmethod
    def recall_memories(self, context_name, limit, ttl):
        pass

    @abstractmethod
    def delete_memory(self, content):
        pass

    @abstractmethod
    def clear_all(self):
        pass
