from typing import Any, Dict, TypedDict, Optional
import time

__author__ = "Feyi Adesanya"

class Event(TypedDict, total=False):
    stream_id: str
    event_id: str
    sampled_ts: float
    arrival_ts: Optional[float]
    event_ts: Optional[float]
    datatype: str
    unit: Optional[str]
    value: Optional[float]
    origin: str

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
    event_id: str,
    value: Optional[float],
    datatype: str,
    origin: str,
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
    event_ts = event_ts or sampled_ts
    arrival_ts = arrival_ts or now

    return {
        "stream_id": stream_id,
        "event_id": event_id,
        "sampled_ts": sampled_ts,
        "event_ts": event_ts,
        "arrival_ts": arrival_ts,
        "datatype": datatype,
        "unit": unit,
        "value": value,
        "origin": origin,
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