from abc import ABC, abstractmethod
import numpy as np


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


class KalmanFilter(BasePredictor):
    def __init__(self, initial_value=0.0, initial_rate=0.0,
                 initial_acceleration=0.0, initial_variance=1.0,
                 dt=1.0, process_noise=0.01, measurement_noise=0.1):
        super().__init__(name="kalman")

        self.dt = dt
        dt2 = 0.5 * dt**2

        self.state = np.array([[initial_value],
                               [initial_rate],
                               [initial_acceleration]])
        self.P = np.eye(3) * initial_variance
        self.Q = np.eye(3) * process_noise
        self.H = np.array([[1, 0, 0]])
        self.R = measurement_noise
        self.I = np.eye(3)

        self.F = np.array([
            [1, dt, dt2],
            [0, 1, dt],
            [0, 0, 1]
        ])

    def predict(self) -> float:
        self.state = self.F @ self.state
        self.P = self.F @ self.P @ self.F.T + self.Q
        return self.state[0, 0]

    def update(self, observed_value: float) -> float:
        y = np.array([[observed_value]]) - self.H @ self.state
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T / S
        self.state += K @ y
        self.P = (self.I - K @ self.H) @ self.P
        return self.state[0, 0]

    def confidence(self) -> float:
        variance = self.P[0, 0]
        confidence = 1.0 / (1.0 + variance)
        return max(0.0, min(1.0, confidence))

    def get_value(self): return self.state[0, 0]
    def get_rate(self): return self.state[1, 0]
    def get_acceleration(self): return self.state[2, 0]
    def get_covariance(self): return self.P
