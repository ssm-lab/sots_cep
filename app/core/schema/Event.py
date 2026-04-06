from typing import TypedDict, Optional, Any, Literal
import uuid
import json

__author__ = "Feyi Adesanya"

EventStatus = Literal["observed", "validated", "reconstructed"]


class Event(TypedDict, total=False):
    id: str
    type: str
    src: str

    event_ts: Optional[float]
    value: Optional[Any]

    confidence: Any

    event_status: EventStatus
    value_datatype: str
    value_unit: Optional[str]

    extras: dict[str, Any]


def make_event(
    *,
    type: str,
    src: str,
    event_status: EventStatus,
    value: Optional[Any] = None,
    event_ts: Optional[float] = None,
    confidence: Optional[Any] = None,
    value_datatype: str = "unknown",
    value_unit: Optional[str] = None,
    extras: Optional[dict[str, Any]] = None,
    id: Optional[str] = None,
) -> Event:
    if event_status == "reconstructed" and confidence is None:
        raise ValueError("Reconstructed events must include confidence")

    if event_status == "observed" and value is None:
        raise ValueError("Observed events must carry a value")

    event: Event = {
        "id": id or str(uuid.uuid4()),
        "type": type,
        "src": src,
        "event_status": event_status,
        "value_datatype": value_datatype,
    }

    if event_ts is not None:
        event["event_ts"] = event_ts

    if value is not None:
        event["value"] = value

    if confidence is not None:
        event["confidence"] = confidence

    if value_unit is not None:
        event["value_unit"] = value_unit

    if extras is not None:
        event["extras"] = extras

    return event
