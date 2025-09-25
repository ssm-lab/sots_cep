import json

from app.schema.Event import Event

# Loading functions
def _load_json(path: str) -> dict:
        with open(path, "r") as f:
            return json.load(f)
        

# Conversion functions
def serialize_event(event: Event) -> str:
    return json.dumps(event)

def deserialize_event(data: str) -> Event:
    return json.loads(data)