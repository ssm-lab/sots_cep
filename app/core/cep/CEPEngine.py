from abc import ABC, abstractmethod

__author__ = "Feyi Adesanya"

class CEPEngine(ABC):
    """
    Abstract base for any CEP engine integration.

    Parameters
    ----------
    pattern_file : str
        Path to the pattern definition file.
    run_dir : str
        Directory for engine output and logs.
    """

    @abstractmethod
    def start(self, pattern_file: str, output_dir: str):
        """Start the CEP engine with given pattern definitions."""
        pass

    @abstractmethod
    def stop(self):
        """Stop the CEP engine."""
        pass
