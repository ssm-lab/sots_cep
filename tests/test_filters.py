import pytest
import numpy as np
from app.core.reconstruction.predictor_types.Filters import KalmanFilter, ParticleFilter

# Run this file directly with:
#   pytest -s tests/test_predictors.py

def test_kalman_filter_confidence_progression():
    predictor = KalmanFilter(Q=0.35, R=0.002, dt=1.0, mode="position")

    # Initial update to establish state
    predictor.update(10.0)
    base_conf = predictor.confidence()
    assert 0.0 <= base_conf <= 1.0

    # Missing data: prediction-only
    decay_confidences = []
    for _ in range(10):
        predictor.predict()
        decay_confidences.append(predictor.confidence())

    # Confidence should have decreased
    assert decay_confidences[-1] < base_conf

    # Recovery
    rebound_confidences = []
    for _ in range(5):
        predictor.update(10.0)
        rebound_confidences.append(predictor.confidence())

    # Confidence should have increased again
    assert rebound_confidences[-1] > decay_confidences[-1]

    # Verify convergence of state estimate
    value = predictor.kf.x[0, 0]
    assert abs(value - 10.0) < 1.0

    print("\n--- Confidence Progression Test ---")
    print(f"Initial confidence: {base_conf:.3f}")
    print("Decay trend:   ", [round(c, 3) for c in decay_confidences])
    print("Rebound trend: ", [round(c, 3) for c in rebound_confidences])


def test_particle_filter_confidence_progression():
    """
    Verify that the Particle Filter's confidence decreases when predictions are made
    without observations and increases once updates resume.
    """

    predictor = ParticleFilter(num_particles=500, process_std=0.2, meas_std=0.05, initial_value=10.0)

    # Initial update
    predictor.update(10.0)
    base_conf = predictor.confidence()
    assert 0.0 <= base_conf <= 1.0

    decay_confidences = []
    for _ in range(10):
        predictor.predict()
        decay_confidences.append(predictor.confidence())

    # Should decay (though may fluctuate slightly)
    assert np.mean(decay_confidences[-3:]) < base_conf

    rebound_confidences = []
    for _ in range(5):
        predictor.update(10.0)
        rebound_confidences.append(predictor.confidence())

    # Should recover
    assert rebound_confidences[-1] > np.mean(decay_confidences[-3:])

    final_estimate = np.mean(predictor.particles)
    assert abs(final_estimate - 10.0) < 1.0

    print("\n--- ParticleFilter Confidence Progression ---")
    print(f"Initial confidence: {base_conf:.3f}")
    print("Decay trend:   ", [round(float(c), 3) for c in decay_confidences])
    print("Rebound trend: ", [round(float(c), 3) for c in rebound_confidences])
