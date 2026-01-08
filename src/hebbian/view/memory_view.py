from abc import ABC, abstractmethod

class MemoryView(ABC):
    @abstractmethod
    def select(self, options, context):
        """Show options and return selected index or None."""
        pass

