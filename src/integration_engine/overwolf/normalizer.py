from src.integration_engine.contracts.overwolf_events import (
    NormalizedOverwolfEvent,
    OverwolfEventRequest,
)

_EVENT_CATEGORIES = {
    "game-detected": "lifecycle",
    "features-enabled": "lifecycle",
    "new-info-update": "info",
    "new-game-event": "event",
    "game-exit": "lifecycle",
    "gep-error": "error",
    "error": "error",
}


def normalize_event_kind(kind: str) -> str:
    return kind.strip().lower().replace("_", "-")


def classify_event(kind: str) -> str:
    return _EVENT_CATEGORIES.get(kind, "unknown")


def normalize_overwolf_event(event: OverwolfEventRequest) -> NormalizedOverwolfEvent:
    normalized_kind = normalize_event_kind(event.kind)
    return NormalizedOverwolfEvent(
        captured_at=event.captured_at.strip(),
        kind=normalized_kind,
        game_id=event.game_id,
        category=classify_event(normalized_kind),
        payload=event.args,
    )
