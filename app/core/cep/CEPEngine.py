from abc import ABC, abstractmethod

class CEPEngine(ABC):
    """Abstract base for any CEP engine integration."""

    @abstractmethod
    def start(self, pattern_file: str, output_dir: str):
        """Start the CEP engine with given pattern definitions."""
        pass

    @abstractmethod
    def stop(self):
        """Stop the CEP engine."""
        pass
