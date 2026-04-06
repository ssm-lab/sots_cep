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
    def __init__(
        self,
        dt=0.01,
        Q=0.01,
        R=0.1,
        initial_value=0.0,
        mode="acceleration",
        F=None,
        H=None,
        P=None,
        alpha=0.25,
    ):
        super().__init__("KalmanFilter")
        self.dt = dt
        self.mode = mode.lower()
        
        # Determine state dimensionality
        if self.mode == "position":
            dim_x = 1
        elif self.mode == "velocity":
            dim_x = 2
        elif self.mode == "acceleration":
            dim_x = 3
        else:
            raise ValueError(f"Unknown mode '{mode}'")

        self.kf = FP_KalmanFilter(dim_x=dim_x, dim_z=1)

        self.alpha = alpha
        self.last_confidence = 1.0
        self.last_trace = float(np.trace(self.kf.P))

        # Build defaults if not provided
        if F is None:
            F = self._default_F(mode, dt)
        if H is None:
            H = self._default_H(mode)
        if np.isscalar(Q):
            Q = np.eye(dim_x) * Q
        if np.isscalar(R):
            R = np.array([[R]])
        if P is None:
            P = np.eye(dim_x) * 1.0

        x0 = self._default_x(mode, initial_value)

        self.kf.F = np.array(F)
        self.kf.H = np.array(H)
        self.kf.Q = np.array(Q)
        self.kf.R = np.array(R)
        self.kf.P = np.array(P)
        self.kf.x = np.array(x0)

        # Validate shapes
        self._validate_shapes()

    def _default_F(self, mode, dt):
        dt2 = 0.5 * dt**2
        if mode == "position":
            return np.array([[1]])
        elif mode == "velocity":
            return np.array([[1, dt], [0, 1]])
        elif mode == "acceleration":
            return np.array([[1, dt, dt2],
                             [0, 1, dt],
                             [0, 0, 1]])

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

    # def confidence(self, observed_value=None):
    #     kf = self.kf
    #     # Compute predicted measurement and innovation covariance
    #     z_pred = float((kf.H @ kf.x)[0])
    #     S = float((kf.H @ kf.P @ kf.H.T + kf.R)[0, 0])

    #     # Case 1: measurement available → innovation-based confidence  
    #     if observed_value is not None:
    #         # Predicted measurement
    #         z_pred = float((kf.H @ kf.x)[0])

    #         # Innovation residual and covariance
    #         v = observed_value - z_pred
    #         S = float((kf.H @ kf.P @ kf.H.T + kf.R)[0, 0])

    #         # Normalized Innovation Squared (NIS)
    #         nis = (v ** 2) / (S + 1e-12)
    #         c_meas = max(np.exp(-0.5 * nis), 1e-3)
    #         c = c_meas

    #         self.last_confidence = float(np.clip(c, 1e-6, 1.0))
    #         self.last_trace = float(np.trace(kf.P))
    #         return self.last_confidence
    #     # Case 2: missing measurement → covariance-based decay
    #     else:        
    #         current_trace = float(np.trace(kf.P))
    #         prev_trace = getattr(self, "last_trace", current_trace)

    #         # Ratio of current to previous uncertainty (bounded)
    #         ratio = min(current_trace / (prev_trace + 1e-8), 1.5)

    #         decay = np.exp(-self.alpha * (ratio - 1.0))

    #         prev_conf = getattr(self, "last_confidence", 1.0)
    #         c = prev_conf * decay

    #         self.last_confidence = float(np.clip(c, 1e-6, 1.0))
    #         self.last_trace = current_trace
    #         return self.last_confidence
    def confidence(self, observed_value=None):
        kf = self.kf

        # Predicted measurement and innovation covariance
        z_pred = float((kf.H @ kf.x)[0])
        S = float((kf.H @ kf.P @ kf.H.T + kf.R)[0, 0])

        # Case 1: measurement available → NIS-based confidence
        if observed_value is not None:
            v = observed_value - z_pred

            # Normalized Innovation Squared (NIS)
            nis = (v ** 2) / (S + 1e-12)
            c = 1.0 / (1.0 + nis)

            self.last_confidence = float(np.clip(c, 1e-6, 1.0))
            self.last_trace = float(np.trace(kf.P))
            return self.last_confidence

        # Case 2: no measurement → decay based on covariance growth
        else:
            current_trace = float(np.trace(kf.P))
            prev_trace = getattr(self, "last_trace", current_trace)

            # Growth ratio of uncertainty
            ratio = min(current_trace / (prev_trace + 1e-8), 1.5)

            decay = np.exp(-self.alpha * (ratio - 1.0))

            prev_conf = getattr(self, "last_confidence", 1.0)
            c = prev_conf * decay

            self.last_confidence = float(np.clip(c, 1e-6, 1.0))
            self.last_trace = current_trace
            return self.last_confidence