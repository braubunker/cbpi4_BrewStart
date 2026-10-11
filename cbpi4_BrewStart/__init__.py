"""CraftBeerPi4 plugin: scheduled brew start + step status actors."""

import logging

logger = logging.getLogger(__name__)

try:
    from .schedule import format_countdown, format_start, resolve_start
except Exception:  # pragma: no cover
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
        from .step_status_actor import (
            BoilStatusActor,
            MashStatusActor,
            StepStatusActor,
            WhirlpoolStatusActor,
        )

        cbpi.plugin.register("StepStatusActor", StepStatusActor)
        cbpi.plugin.register("MashStatusActor", MashStatusActor)
        cbpi.plugin.register("BoilStatusActor", BoilStatusActor)
        cbpi.plugin.register("WhirlpoolStatusActor", WhirlpoolStatusActor)
        logger.info("Registered StepStatusActor / Mash / Boil / Whirlpool")
    except Exception as exc:
        logger.exception("FAILED to register StepStatus actors: %s", exc)
