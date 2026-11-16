"""Serialization helpers for the Cookie Clicker save file.

The save file is plain JSON. This module owns the schema, keeps the
data defensive (a hand-edited or half-written file should never crash
the game) and makes older saves loadable.
"""

from typing import Any, Dict, Mapping, Optional

# Bump when the shape of the save file changes.
#   0 - legacy saves without version/click_level
#   1 - versioned saves with a separate click_level counter
SAVE_VERSION = 1


def _as_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return bool(value)


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, dict) else {}


def serialize_state(*, cookies: float, click_power: float, click_level: int,
                    cps_multiplier: float, buildings: Mapping[str, int],
                    upgrades: Mapping[str, bool], timestamp: float) -> Dict[str, Any]:
    """Build the dict that is written to disk."""
    return {
        "version": SAVE_VERSION,
        "cookies": float(cookies),
        "click_power": float(click_power),
        "click_level": int(click_level),
        "cps_multiplier": float(cps_multiplier),
        "buildings": dict(buildings),
        "upgrades": dict(upgrades),
        "timestamp": float(timestamp),
    }


def deserialize_state(raw: Any) -> Dict[str, Any]:
    """Normalize a loaded save file into the current schema.

    Missing or malformed fields fall back to sensible defaults, and
    invalid numbers are clamped instead of raising.
    """
    if not isinstance(raw, dict):
        raise ValueError("save data must be a JSON object")

    timestamp_value = raw.get("timestamp")
    timestamp: Optional[float] = None
    if timestamp_value is not None:
        parsed_timestamp = _as_float(timestamp_value, 0.0)
        timestamp = parsed_timestamp if parsed_timestamp > 0 else None

    buildings = {
        str(name): max(0, _as_int(count, 0))
        for name, count in _as_mapping(raw.get("buildings")).items()
    }
    upgrades = {
        str(upgrade_id): _as_bool(owned)
        for upgrade_id, owned in _as_mapping(raw.get("upgrades")).items()
    }

    return {
        "version": SAVE_VERSION,
        "cookies": max(0.0, _as_float(raw.get("cookies"), 0.0)),
        "click_power": max(1.0, _as_float(raw.get("click_power"), 1.0)),
        "click_level": max(1, _as_int(raw.get("click_level"), 1)),
        "cps_multiplier": max(1.0, _as_float(raw.get("cps_multiplier"), 1.0)),
        "buildings": buildings,
        "upgrades": upgrades,
        "timestamp": timestamp,
    }
