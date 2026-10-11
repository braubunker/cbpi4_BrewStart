"""Pure helpers to match an active brew step (no CraftBeerPi imports)."""

from __future__ import annotations

from typing import Any, Iterable, Optional, Sequence, Tuple

# Presets for common brew phases.
# Whirlpool has no built-in CBPi step type — usually Wait/Notification named "Whirlpool".
STEP_KIND_PRESETS = {
    "Mash": {
        "type_contains": ("mash",),
        "name_contains": ("mash", "maische", "einmaischen", "mashin"),
    },
    "Boil": {
        "type_contains": ("boil",),
        "name_contains": ("boil", "kochen", "würzekochen", "wurzekochen"),
    },
    "Whirlpool": {
        "type_contains": ("whirlpool", "whirl"),
        "name_contains": ("whirlpool", "whirl", "whirl pool"),
    },
}


def _contains_any(text: str, needles: Iterable[str]) -> bool:
    lowered = (text or "").lower()
    return any(n.lower() in lowered for n in needles if n)


def step_matches_preset(step: Any, kinds: Sequence[str]) -> bool:
    """True if step type or name matches any of the given kind presets."""
    if step is None:
        return False

    step_type = str(getattr(step, "type", "") or "")
    step_name = str(getattr(step, "name", "") or "")

    for kind in kinds:
        rules = STEP_KIND_PRESETS.get(kind)
        if not rules:
            continue
        if _contains_any(step_type, rules.get("type_contains", ())):
            return True
        if _contains_any(step_name, rules.get("name_contains", ())):
            return True
    return False


def parse_step_kind(step_kind: str) -> Tuple[str, ...]:
    """Map UI StepKind value to one or more preset keys."""
    kind = (step_kind or "Mash").strip()
    mapping = {
        "Mash": ("Mash",),
        "Boil": ("Boil",),
        "Whirlpool": ("Whirlpool",),
        "Mash or Boil": ("Mash", "Boil"),
        "Mash+Boil+Whirlpool": ("Mash", "Boil", "Whirlpool"),
        "Custom": (),
        "AnyActive": (),
    }
    return mapping.get(kind, ("Mash",))


def step_matches(step: Any, match_mode: str, match_value: str, step_kind: str = "Custom") -> bool:
    """Return True if the active step matches the configured filter."""
    if step is None:
        return False

    kind = (step_kind or "Custom").strip()
    if kind == "AnyActive":
        return True

    presets = parse_step_kind(kind)
    if presets:
        return step_matches_preset(step, presets)

    # Custom modes
    mode = (match_mode or "TypeContains").strip()
    value = (match_value or "").strip().lower()

    if mode == "AnyActive":
        return True

    step_type = str(getattr(step, "type", "") or "")
    step_name = str(getattr(step, "name", "") or "")

    if mode == "TypeContains":
        # Comma-separated list supported: "boil,whirlpool"
        needles = [n.strip() for n in value.split(",") if n.strip()] or ["mash"]
        return _contains_any(step_type, needles)

    if mode == "TypeExact":
        if not value:
            return False
        return step_type.lower() == value

    if mode == "NameContains":
        needles = [n.strip() for n in value.split(",") if n.strip()]
        if not needles:
            return False
        return _contains_any(step_name, needles)

    if mode == "NameExact":
        if not value:
            return False
        return step_name.lower() == value

    if mode == "TypeOrNameContains":
        needles = [n.strip() for n in value.split(",") if n.strip()]
        if not needles:
            return False
        return _contains_any(step_type, needles) or _contains_any(step_name, needles)

    return False


def is_matching_step_active(
    step_controller: Any,
    match_mode: str,
    match_value: str,
    step_kind: str = "Custom",
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

    return step_matches(active, match_mode, match_value, step_kind=step_kind)
