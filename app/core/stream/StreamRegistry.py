_registry = {}

def register_stream_type(name, experimental=False):
    def decorator(cls):
        cls._experimental = experimental
        _registry[name] = cls
        return cls
    return decorator

def get_stream_class(name, allow_experimental=False):
    cls = _registry.get(name)
    if cls is None:
        raise ValueError(f"Unknown stream type: {name}")

    if getattr(cls, "_experimental", False) and not allow_experimental:
        raise ValueError(f"Stream type {name} is experimental")

    return cls

def list_stream_types(allow_experimental=False):
    return [
        name for name, cls in _registry.items()
        if allow_experimental or not getattr(cls, "_experimental", False)
    ]
