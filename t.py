from app.core.reconstruction.predictor_types.KalmanFilter import KalmanFilter

for q in [0.001, 0.01, 0.05, 0.1]:
    kf = KalmanFilter(dt=0.1, process_noise=q)
    kf.update(10.0)
    confs = []
    for _ in range(5):
        kf.predict()
        confs.append(kf.confidence())
    print(f"Q={q:.3f} -> confidence after 5 predictions: {confs[-1]:.3f}")
