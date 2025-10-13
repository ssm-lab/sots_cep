import pytest
from app.core.reconstruction.predictor_types.KalmanFilter import KalmanFilter

# Run with: pytest -s tests/test_predictors.py

def test_kalman_filter_confidence_progression():
    """
    Verify that confidence decreases during consecutive predictions (no observations)
    and recovers after updates, while the state value converges toward the measurement.
    """

    # Initialize filter with moderate noise parameters for visible confidence change
    predictor = KalmanFilter(process_noise=0.05, measurement_noise=0.1)

    # --- Initial update with a known measurement ---
    predictor.update(10.0)
    base_conf = predictor.confidence()
    assert 0.0 <= base_conf <= 1.0

    # --- Simulate missing data (predict-only cycles) ---
    decay_confidences = []
    for _ in range(5):
        predictor.predict()
        decay_confidences.append(predictor.confidence())

    # Confidence should have decreased
    assert decay_confidences[-1] < base_conf

    # --- Simulate recovery once measurements resume ---
    rebound_confidences = []
    for _ in range(5):
        predictor.update(10.0)
        rebound_confidences.append(predictor.confidence())

    # Confidence should have increased again
    assert rebound_confidences[-1] > decay_confidences[-1]

    # --- Sanity check: value should converge toward measurement ---
    if hasattr(predictor, "get_value"):
        value = predictor.get_value()
    elif hasattr(predictor, "state"):
        value = predictor.state[0, 0]
    elif hasattr(predictor, "kf"):
        value = predictor.kf.x[0, 0]
    else:
        raise AttributeError("Predictor has no accessible state value")

    assert abs(value - 10.0) < 1.0

    # --- Optional diagnostic printout ---
    print(f"\nInitial confidence: {base_conf:.3f}")
    print("Decay trend:", [round(c, 3) for c in decay_confidences])
    print("Rebound trend:", [round(c, 3) for c in rebound_confidences])