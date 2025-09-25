from abc import ABC, abstractmethod
import numpy as np
from ..PredictorRegistry import register_predictor

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
