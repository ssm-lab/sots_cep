from app.core.reconstruction.predictor_types.KalmanFilter import KalmanFilter

for q in [0.00001, 0.0001, 0.001, 0.01, 0.05, 0.1]:
    kf = KalmanFilter(dt=0.05, process_noise=q, mode="acceleration")
    kf.update(10.0)
    kf.predict()
    kf.update(11)
    kf.predict()
    kf.update(12)
    kf.predict()
    kf.update(12.23)
    kf.predict()
    kf.update(12.45)
    confs = []
    print(f"Q = {q}")
    for _ in range(5):
        predic = kf.predict()
        print(f"Prediction: {predic}")
        confs.append(kf.confidence())
        print(f"Confidence: {confs[-1]}")
    print(f"Q={q:.3f} -> confidence after 5 predictions: {confs[-1]:.3f}")
