_registry = {}

def register_server_type(name):
    def decorator(cls):
        _registry[name] = cls
        return cls
    return decorator

def get_server_class(name):
    cls = _registry.get(name)
    if cls is None:
        raise ValueError(f"Unknown stream type: {name}")
    return cls

def list_server_types():
    return list(_registry.keys())
