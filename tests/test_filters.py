import pytest
from app.core.reconstruction.predictor_types.Filters import KalmanFilter

# Run this file directly with:
#   pytest -s tests/test_predictors.py

def test_kalman_filter_confidence_progression():
    # Initialize filter with tuned parameters for visible progression
    predictor = KalmanFilter(Q=0.35, R=0.002, dt=1.0, mode="position")

    # Initial update to establish state
    predictor.update(10.0)
    base_conf = predictor.confidence()
    assert 0.0 <= base_conf <= 1.0

    # --- Missing data: prediction-only intervals ---
    decay_confidences = []
    for _ in range(10):
        predictor.predict()
        decay_confidences.append(predictor.confidence())

    # Confidence should have decreased
    assert decay_confidences[-1] < base_conf

    # --- Recovery: measurements resume ---
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