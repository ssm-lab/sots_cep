_registry = {}

def register_stream_type(name):
    """Decorator for registering a stream type."""
    def decorator(cls):
        _registry[name] = cls
        return cls
    return decorator

def get_stream_class(name):
    if name not in _registry:
        raise ValueError(f"Unknown stream type: {name}")
    return _registry[name]

def list_stream_types():
    return list(_registry.keys())
