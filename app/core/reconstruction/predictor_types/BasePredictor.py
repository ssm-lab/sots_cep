from abc import ABC, abstractmethod

"""
Predictor: Interface for estimation models.
Implemented by Kalman, etc. for reconstruction.
Returns predictions + confidence for missing values.
"""

class BasePredictor(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def predict(self) -> float:
        pass

    @abstractmethod
    def update(self, observed_value: float) -> float:
        pass

    @abstractmethod
    def confidence(self) -> float:
        pass
