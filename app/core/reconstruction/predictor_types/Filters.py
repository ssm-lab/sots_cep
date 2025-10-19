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

        # Initialize filter
        self.kf = FP_KalmanFilter(dim_x=dim_x, dim_z=1)

        # Store intial P
        self.P0_full = self.kf.P.copy()
        self.trace_P0 = float(np.trace(self.P0_full))
        self.P0_scalar = float(self.kf.P[0, 0])

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

        # Build x0 directly from initial value
        x0 = self._default_x(mode, initial_value)

        self.kf.F = np.array(F)
        self.kf.H = np.array(H)
        self.kf.Q = np.array(Q)
        self.kf.R = np.array(R)
        self.kf.P = np.array(P)
        self.kf.x = np.array(x0)

        # Validate shapes
        self._validate_shapes()

    # ------------------------------------------------------------------
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

    def confidence(self) -> float:
        # Identify observed state indices (nonzero columns in H)
        observed_indices = np.where(np.any(self.kf.H != 0, axis=0))[0]
        P_obs = self.kf.P[np.ix_(observed_indices, observed_indices)]
        P0_obs = self.P0_full[np.ix_(observed_indices, observed_indices)]

        # Trace
        trace_current = float(np.trace(P_obs))
        trace_initial = float(np.trace(P0_obs))

        ratio = trace_current / max(trace_initial, 1e-8)
        confidence = 1.0 - ratio

        return float(np.clip(confidence, 0.0, 1.0))



@register_predictor("ParticleFilter")
class ParticleFilter(BasePredictor):
    def __init__(self, num_particles=500, process_std=0.2, meas_std=0.05, initial_value=0.0):
        super().__init__("ParticleFilter")
        self.num_particles = num_particles
        self.particles = np.ones(num_particles) * initial_value
        self.weights = np.ones(num_particles) / num_particles
        self.process_std = process_std
        self.meas_std = meas_std

    def predict(self):
        # Propagate particles with noise
        self.particles += np.random.normal(0, self.process_std, self.num_particles)
        return float(np.mean(self.particles))

    def update(self, observed_value: float):
        # Compute likelihoods
        likelihoods = np.exp(-0.5 * ((self.particles - observed_value) / self.meas_std) ** 2)
        likelihoods += 1e-12  # avoid zeros
        self.weights *= likelihoods
        self.weights /= np.sum(self.weights)

        # Resample
        indices = np.random.choice(self.num_particles, self.num_particles, p=self.weights)
        self.particles = self.particles[indices]
        self.weights.fill(1.0 / self.num_particles)
        return float(np.mean(self.particles))

    def confidence(self):
        variance = np.var(self.particles)
        confidence = 1.0 / (1.0 + np.log1p(variance))
        return max(0.0, min(1.0, confidence))
