import numpy as np
from filterpy.kalman import KalmanFilter as FP_KalmanFilter

from .BasePredictor import BasePredictor
from ..PredictorRegistry import register_predictor


__author__ = "Feyi Adesanya"

# @register_predictor("KalmanFilter")
# class KalmanFilter(BasePredictor):
#     """
#     Kalman Filter using FilterPy's implementation.
#     Supports scalar or per-dimension process noise (Q).
#     """

#     def __init__(self, dt=0.01, process_noise=0.01, measurement_noise=0.1, initial_value=0.0):
#         super().__init__("KalmanFilter")

#         # 3-state constant acceleration model
#         self.kf = FP_KalmanFilter(dim_x=3, dim_z=1)
#         self.dt = dt
#         dt2 = 0.5 * dt**2

#         # State transition and measurement models
#         self.kf.F = np.array([
#             [1, dt, dt2],
#             [0, 1, dt],
#             [0, 0, 1]
#         ])
#         self.kf.H = np.array([[1, 0, 0]])  # observe only position

#         # Covariance and noise matrices
#         self.kf.P *= 1.0
#         self.kf.R = np.array([[measurement_noise]])

#         # Process noise (Q) setup
#         n = self.kf.F.shape[0]
#         if np.isscalar(process_noise):
#             # Same variance for all state dimensions
#             self.kf.Q = np.eye(n) * process_noise
#         elif np.ndim(process_noise) == 1:
#             # Per-state variances (independent)
#             self.kf.Q = np.diag(process_noise)
#         else:
#             # Full covariance matrix provided directly
#             self.kf.Q = np.array(process_noise)

#         # Initial state vector
#         self.kf.x = np.array([[initial_value], [0.0], [0.0]])

#     def predict(self) -> float:
#         """Perform the prediction step and return the predicted position."""
#         self.kf.predict()
#         return float(self.kf.x[0, 0])

#     def update(self, observed_value: float) -> float:
#         """Perform the update step with a new observation."""
#         self.kf.update(np.array([[observed_value]]))
#         return float(self.kf.x[0, 0])

#     def confidence(self) -> float:
#         """Compute a bounded [0,1] confidence measure based on the position variance."""
#         variance = float(self.kf.P[0, 0])
#         confidence = 1.0 / (1.0 + variance)
#         return max(0.0, min(1.0, confidence))

@register_predictor("KalmanFilter")
class KalmanFilter(BasePredictor):
    """
    Kalman Filter using FilterPy's implementation.
    """

    def __init__(
        self,
        dt=0.01,
        process_noise=0.01,
        measurement_noise=0.1,
        initial_value=0.0,
        mode="acceleration",
        F=None,
        H=None,
        Q=None,
        R=None,
        P=None,
        x0=None,
    ):
        super().__init__("KalmanFilter")
        self.dt = dt
        self.mode = mode.lower()

        if self.mode == "position":
            dim_x = 1
        elif self.mode == "velocity":
            dim_x = 2
        elif self.mode == "acceleration":
            dim_x = 3
        else:
            raise ValueError(f"Unknown mode '{mode}'")

        self.kf = FP_KalmanFilter(dim_x=dim_x, dim_z=1)

        # Build defaults if not overridden
        if F is None:
            F = self._default_F(mode, dt)
        if H is None:
            H = self._default_H(mode)
        if Q is None:
            Q = self._make_Q(process_noise, F.shape[0])
        if R is None:
            R = np.array([[measurement_noise]])
        if P is None:
            P = np.eye(F.shape[0]) * 1.0
        if x0 is None:
            x0 = self._default_x(mode, initial_value)

        # 3️⃣ Assign matrices
        self.kf.F = np.array(F)
        self.kf.H = np.array(H)
        self.kf.Q = np.array(Q)
        self.kf.R = np.array(R)
        self.kf.P = np.array(P)
        self.kf.x = np.array(x0)

        # 4️⃣ Validate dimensions
        self._validate_shapes()

    # ------------------------------------------------------------------
    def _default_F(self, mode, dt):
        dt2 = 0.5 * dt**2
        if mode == "position":
            return np.array([[1]])
        elif mode == "velocity":
            return np.array([[1, dt], [0, 1]])
        elif mode == "acceleration":
            return np.array([[1, dt, dt2], [0, 1, dt], [0, 0, 1]])

    def _default_H(self, mode):
        if mode == "position":
            return np.array([[1]])
        elif mode == "velocity":
            return np.array([[1, 0]])
        elif mode == "acceleration":
            return np.array([[1, 0, 0]])

    def _default_x(self, mode, initial_value):
        if mode == "position":
            return np.array([[initial_value]])
        elif mode == "velocity":
            return np.array([[initial_value], [0.0]])
        elif mode == "acceleration":
            return np.array([[initial_value], [0.0], [0.0]])

    def _make_Q(self, process_noise, n):
        if np.isscalar(process_noise):
            return np.eye(n) * process_noise
        elif np.ndim(process_noise) == 1:
            return np.diag(process_noise)
        else:
            return np.array(process_noise)

    def _validate_shapes(self):
        n = self.kf.F.shape[0]
        assert self.kf.Q.shape == (n, n), "Q shape mismatch"
        assert self.kf.P.shape == (n, n), "P shape mismatch"
        assert self.kf.H.shape[1] == n, "H incompatible with state size"

    # ------------------------------------------------------------------
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
