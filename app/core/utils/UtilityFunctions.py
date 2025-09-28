import json

def _load_json(path: str) -> dict:
        with open(path, "r") as f:
            return json.load(f)
        