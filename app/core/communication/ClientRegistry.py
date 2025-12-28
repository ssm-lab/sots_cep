_registry = {}

def register_client_type(name):
    def decorator(cls):
        _registry[name] = cls
        return cls
    return decorator

def get_client_class(name):
    cls = _registry.get(name)
    if cls is None:
        raise ValueError(f"Unknown stream type: {name}")
    return cls

def list_client_types():
    return list(_registry.keys())
