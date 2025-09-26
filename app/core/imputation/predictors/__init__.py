import importlib
import pkgutil

# auto-import all modules inside this package
for loader, module_name, is_pkg in pkgutil.walk_packages(__path__):
    importlib.import_module(f"{__name__}.{module_name}")
