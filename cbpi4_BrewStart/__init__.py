"""CraftBeerPi4 plugin: scheduled brew start + step status actor."""

import logging

logger = logging.getLogger(__name__)

try:
    from .schedule import format_countdown, format_start, resolve_start
except Exception:  # pragma: no cover - package import fallback
    format_countdown = format_start = resolve_start = None  # type: ignore

__all__ = [
    "format_countdown",
    "format_start",
    "resolve_start",
    "setup",
]


def setup(cbpi):
    """Register plugin types with the CraftBeerPi4 server."""
    try:
        from .brew_start import BrewStart

        cbpi.plugin.register("BrewStart", BrewStart)
        logger.info("Registered BrewStart step")
    except Exception as exc:
        logger.exception("FAILED to register BrewStart: %s", exc)
        raise

    try:
        from .step_status_actor import StepStatusActor

        cbpi.plugin.register("StepStatusActor", StepStatusActor)
        logger.info("Registered StepStatusActor")
    except Exception as exc:
        # Actor ist optional — Step soll trotzdem laden
        logger.exception("FAILED to register StepStatusActor: %s", exc)
