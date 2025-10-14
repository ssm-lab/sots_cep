_registry = {}

def register_stream_type(name):
    def decorator(cls):
        _registry[name] = cls
        return cls
    return decorator

def get_stream_class(name):
    cls = _registry.get(name)
    if cls is None:
        raise ValueError(f"Unknown stream type: {name}")
    return cls

def list_stream_types():
    return list(_registry.keys())
