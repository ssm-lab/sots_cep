import numpy as np
from filterpy.kalman import KalmanFilter as FP_KalmanFilter

from .BasePredictor import BasePredictor
from ..PredictorRegistry import register_predictor


__author__ = "Feyi Adesanya"

@register_predictor("KalmanFilter")
class KalmanFilter(BasePredictor):
    """
    Kalman Filter using FilterPy's implementation.
    """

    def __init__(self, dt=1.0, process_noise=0.01, measurement_noise=0.1, initial_value=0.0):
        super().__init__("KalmanFilter")

        # 3-state constant acceleration model
        self.kf = FP_KalmanFilter(dim_x=3, dim_z=1)
        self.dt = dt
        dt2 = 0.5 * dt**2

        self.kf.F = np.array([
            [1, dt, dt2],
            [0, 1, dt],
            [0, 0, 1]
        ])

        self.kf.H = np.array([[1, 0, 0]])  # observe only position
        self.kf.P *= 1.0
        self.kf.R = np.array([[measurement_noise]])
        self.kf.Q = np.diag([process_noise, process_noise * 2, process_noise * 4]) ## Increasing noise across value, rate, acceleration responsive tracking

        self.kf.x = np.array([[initial_value], [0.0], [0.0]])

    def predict(self) -> float:
        self.kf.predict()
        return float(self.kf.x[0, 0])

    def update(self, observed_value: float) -> float:
        self.kf.update(np.array([[observed_value]]))
        return float(self.kf.x[0, 0])

    def confidence(self) -> float:
        variance = float(self.kf.P[0, 0])
        confidence = 1.0 / (1.0 + variance)
        return max(0.0, min(1.0, confidence))




# @register_predictor("KalmanFilter")
# class KalmanFilter(BasePredictor):
#     def __init__(self, initial_value=0.0, initial_rate=0.0,
#                  initial_acceleration=0.0, initial_variance=1.0,
#                  dt=1.0, process_noise=0.01, measurement_noise=0.1):
#         super().__init__(name="KalmanFilter")

#         self.dt = dt
#         dt2 = 0.5 * dt**2

#         self.state = np.array([[initial_value],
#                                [initial_rate],
#                                [initial_acceleration]])
#         self.P = np.eye(3) * initial_variance
#         self.Q = np.eye(3) * process_noise
#         self.H = np.array([[1, 0, 0]])
#         self.R = measurement_noise
#         self.I = np.eye(3)

#         self.F = np.array([
#             [1, dt, dt2],
#             [0, 1, dt],
#             [0, 0, 1]
#         ])

#     def predict(self) -> float:
#         self.state = self.F @ self.state
#         self.P = self.F @ self.P @ self.F.T + self.Q
#         return self.state[0, 0]

#     def update(self, observed_value: float) -> float:
#         y = np.array([[observed_value]]) - self.H @ self.state
#         S = self.H @ self.P @ self.H.T + self.R
#         K = self.P @ self.H.T / S
#         self.state += K @ y
#         self.P = (self.I - K @ self.H) @ self.P
#         return self.state[0, 0]

#     def confidence(self) -> float:
#         variance = self.P[0, 0]
#         confidence = 1.0 / (1.0 + variance)
#         return max(0.0, min(1.0, confidence))

#     def get_value(self): return self.state[0, 0]
#     def get_rate(self): return self.state[1, 0]
#     def get_acceleration(self): return self.state[2, 0]
#     def get_covariance(self): return self.P
