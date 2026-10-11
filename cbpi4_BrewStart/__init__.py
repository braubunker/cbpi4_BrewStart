"""CraftBeerPi4 plugin: schedule brew process start time."""

from .schedule import format_countdown, format_start, resolve_start

__all__ = [
    "format_countdown",
    "format_start",
    "resolve_start",
    "setup",
]


def setup(cbpi):
    """Register plugin types with the CraftBeerPi4 server."""
    from .brew_start import BrewStart
    from .step_status_actor import StepStatusActor

    cbpi.plugin.register("BrewStart", BrewStart)
    cbpi.plugin.register("StepStatusActor", StepStatusActor)
