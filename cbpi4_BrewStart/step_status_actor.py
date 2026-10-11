import asyncio
import logging

from cbpi.api import *
from cbpi.api.step import StepState

from .step_match import is_matching_step_active

logger = logging.getLogger(__name__)


class _StepStatusActorBase(CBPiActor):
    """Shared logic: virtual actor ON while a matching brew step is active."""

    # Subclasses may hardcode a preset; StepStatusActor reads it from props.
    fixed_step_kind = None

    async def on_start(self):
        self.state = False
        self.power = 100
        if self.fixed_step_kind:
            self.step_kind = self.fixed_step_kind
            self.match_mode = "TypeContains"
            self.match_value = ""
        else:
            self.step_kind = self.props.get("StepKind", None) or "Mash"
            self.match_mode = self.props.get("MatchMode", None) or "TypeContains"
            self.match_value = str(self.props.get("MatchValue", "") or "")
        logger.info(
            "%s %s started (kind=%s mode=%s value=%s)",
            self.__class__.__name__,
            self.id,
            self.step_kind,
            self.match_mode,
            self.match_value,
        )

    async def on(self, power=None):
        if power is not None:
            self.power = power
        logger.debug("%s %s: manuelles ON ignoriert", self.__class__.__name__, self.id)

    async def off(self):
        logger.debug("%s %s: manuelles OFF ignoriert", self.__class__.__name__, self.id)

    def get_state(self):
        return self.state

    async def set_power(self, power):
        self.power = power

    async def run(self):
        while self.running is True:
            try:
                active = is_matching_step_active(
                    getattr(self.cbpi, "step", None),
                    self.match_mode,
                    self.match_value,
                    step_kind=self.step_kind,
                    active_statuses=(StepState.ACTIVE, "A"),
                )
            except Exception as exc:
                logger.error("%s status check failed: %s", self.__class__.__name__, exc)
                active = False

            if active != self.state:
                self.state = active
                try:
                    await self.cbpi.actor.actor_update(
                        self.id, self.power if self.state else 0
                    )
                except Exception:
                    try:
                        await self.cbpi.actor.ws_actor_update()
                    except Exception:
                        pass
                logger.info(
                    "%s %s -> %s",
                    self.__class__.__name__,
                    self.id,
                    "ON" if self.state else "OFF",
                )

            await asyncio.sleep(1)


@parameters(
    [
        Property.Select(
            label="StepKind",
            options=[
                "Mash",
                "Boil",
                "Whirlpool",
                "Mash or Boil",
                "Mash+Boil+Whirlpool",
                "AnyActive",
                "Custom",
            ],
            description=(
                "Mash/Boil/Whirlpool: fertige Filter. "
                "Whirlpool erkennt Typ oder Step-Namen (z.B. WaitStep 'Whirlpool'). "
                "Custom: MatchMode + MatchValue nutzen."
            ),
        ),
        Property.Select(
            label="MatchMode",
            options=[
                "TypeContains",
                "TypeOrNameContains",
                "AnyActive",
                "TypeExact",
                "NameContains",
                "NameExact",
            ],
            description="Nur bei StepKind=Custom relevant.",
        ),
        Property.Text(
            label="MatchValue",
            configurable=True,
            description=(
                "Nur Custom: Suchtext, Komma erlaubt (z.B. 'boil,whirlpool'). "
                "Leer bei TypeContains → 'mash'."
            ),
        ),
    ]
)
class StepStatusActor(_StepStatusActorBase):
    """Virtueller Actor für Mash / Boil / Whirlpool (oder Custom-Filter)."""

    fixed_step_kind = None


@parameters([])
class MashStatusActor(_StepStatusActorBase):
    """ON während MashIn-/MashStep (Typ oder Name)."""

    fixed_step_kind = "Mash"


@parameters([])
class BoilStatusActor(_StepStatusActorBase):
    """ON während BoilStep / BM_BoilStep (Typ oder Name)."""

    fixed_step_kind = "Boil"


@parameters([])
class WhirlpoolStatusActor(_StepStatusActorBase):
    """ON während Whirlpool — inkl. benannter Wait/Notification-Steps."""

    fixed_step_kind = "Whirlpool"
