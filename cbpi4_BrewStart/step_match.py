"""Pure helpers to match an active brew step (no CraftBeerPi imports)."""

from __future__ import annotations

from typing import Any, Optional


def step_matches(step: Any, match_mode: str, match_value: str) -> bool:
    """Return True if the active step matches the configured filter."""
    if step is None:
        return False

    mode = (match_mode or "AnyActive").strip()
    value = (match_value or "").strip().lower()

    if mode == "AnyActive":
        return True

    step_type = str(getattr(step, "type", "") or "")
    step_name = str(getattr(step, "name", "") or "")

    if mode == "TypeContains":
        needle = value or "mash"
        return needle in step_type.lower()

    if mode == "TypeExact":
        if not value:
            return False
        return step_type.lower() == value

    if mode == "NameContains":
        if not value:
            return False
        return value in step_name.lower()

    if mode == "NameExact":
        if not value:
            return False
        return step_name.lower() == value

    return False


def is_matching_step_active(
    step_controller: Any,
    match_mode: str,
    match_value: str,
    active_statuses: Optional[tuple] = None,
) -> bool:
    """Check step controller for an active step matching the filter."""
    if step_controller is None:
        return False

    find = getattr(step_controller, "find_by_status", None)
    if find is None:
        return False

    statuses = active_statuses if active_statuses is not None else ("A",)
    active = None
    for status in statuses:
        try:
            active = find(status)
        except Exception:
            active = None
        if active is not None:
            break

    return step_matches(active, match_mode, match_value)
