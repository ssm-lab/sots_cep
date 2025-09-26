from typing import Any, Dict, TypedDict, Optional
import time

class Event(TypedDict, total=False):
    stream_id: str
    event_id: str
    sampled_ts: float
    arrival_ts: Optional[float]
    event_ts: Optional[float]
    datatype: str
    unit: Optional[str]
    value: Optional[float]

    reconstructed_value: Optional[float]
    reconstruction_method: Optional[str]
    confidence: Optional[float]
    reconstruction_flag: Optional[bool]

    # metadata
    status: str
    source: str
    extras: Optional[dict[str, Any]]


def make_event(
    stream_id: str,
    value: Optional[float],
    datatype: str,
    unit: Optional[str] = None,
    sampled_ts: Optional[float] = None,
    event_ts: Optional[float] = None,
    arrival_ts: Optional[float] = None,
    status: str = "observed",
    source: str = "unknown",
    reconstructed_value: Optional[float] = None,
    reconstruction_method: Optional[str] = None,
    confidence: Optional[float] = None,
    reconstruction_flag: Optional[bool] = None,
    extras: Optional[Dict[str, Any]] = None,
) -> Event:
    now = time.time()
    sampled_ts = sampled_ts or now
    event_ts = event_ts or sampled_ts
    arrival_ts = arrival_ts or now

    return {
        "stream_id": stream_id,
        "event_id": f"{stream_id}-{int(event_ts * 1000)}",
        "sampled_ts": sampled_ts,
        "event_ts": event_ts,
        "arrival_ts": arrival_ts,
        "datatype": datatype,
        "unit": unit,
        "value": value,
  
        "reconstructed_value": reconstructed_value,
        "reconstruction_method": reconstruction_method,
        "confidence": confidence,
        "reconstruction_flag": reconstruction_flag,
        # metadata
        "status": status,
        "source": source,
        # always forward extras (at least an empty dict)
        "extras": extras if extras is not None else {},
    }

def update_event_for_reconstruction(event: Event,
                                reconstructed_value: Optional[float],
                                method: str,
                                confidence: float) -> Event:
    updated = dict(event)
    updated["arrival_ts"] = time.time()
    updated["reconstructed_value"] = reconstructed_value
    updated["reconstruction_method"] = method
    updated["confidence"] = confidence
    updated["reconstruction_flag"] = reconstructed_value is not None
    updated["status"] = "reconstructed" if reconstructed_value is not None else "observed"
    updated["value"] = event["value"] if event["value"] is not None else reconstructed_value
    return updated
