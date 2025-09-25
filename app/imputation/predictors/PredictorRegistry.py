PREDICTOR_REGISTRY = {}

def register_predictor(name: str):
    def decorator(cls):
        PREDICTOR_REGISTRY[name] = cls
        return cls
    return decorator

def get_predictor_class(name: str):
    if name not in PREDICTOR_REGISTRY:
        raise ValueError(f"Predictor '{name}' not found in registry")
    return PREDICTOR_REGISTRY[name]
