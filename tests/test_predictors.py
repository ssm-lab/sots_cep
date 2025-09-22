import pytest
from app.imputation.predictors.Predictor import KalmanFilter

def test_kalman_filter_stability():
    predictor = KalmanFilter()

    initial_pred = predictor.predict()
    assert isinstance(initial_pred, float)

    updated = predictor.update(5.0)
    assert isinstance(updated, float)

    conf = predictor.confidence()
    assert 0.0 <= conf <= 1.0

    # After a few cycles, state should move toward measurement
    for _ in range(10):
        predictor.predict()
        predictor.update(5.0)

    value = predictor.get_value()
    assert abs(value - 5.0) < 1.0  # something close to this
