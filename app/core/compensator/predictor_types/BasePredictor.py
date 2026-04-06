from abc import ABC, abstractmethod

__author__ = "Feyi Adesanya"

class BasePredictor(ABC):
    """
    Abstract predictor interface for handling imputation.
    Returns predictions + confidence for missing values.
    """
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def predict(self) -> float:
        """Generate the next predicted value."""
        pass

    @abstractmethod
    def update(self, observed_value: float) -> float:
        """Update the predictor with an observed value."""
        pass

    @abstractmethod
    def confidence(self) -> float:
        """Return the current confidence of predictions."""
        pass
