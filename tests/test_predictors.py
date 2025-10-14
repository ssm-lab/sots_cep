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

    predictor.update(10.0)
    base_conf = predictor.confidence()
    assert 0.0 <= base_conf <= 1.0

    # Missing data
    decay_confidences = []
    for _ in range(5):
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

    value = predictor.kf.x[0, 0]
    assert abs(value - 10.0) < 1.0

    print(f"\nInitial confidence: {base_conf:.3f}")
    print("Decay trend:", [round(c, 3) for c in decay_confidences])
    print("Rebound trend:", [round(c, 3) for c in rebound_confidences])