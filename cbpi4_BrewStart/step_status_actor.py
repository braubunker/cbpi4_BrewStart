import asyncio
import logging

from cbpi.api import *
from cbpi.api.step import StepState

from .step_match import is_matching_step_active

logger = logging.getLogger(__name__)


@parameters(
    [
        Property.Select(
            label="MatchMode",
            options=["TypeContains", "AnyActive", "TypeExact", "NameContains", "NameExact"],
            description=(
                "Wann der Actor ON ist: "
                "TypeContains = Step-Typ enthält Text (Standard: mash). "
                "AnyActive = irgendein aktiver Step. "
                "TypeExact/NameExact = exakter Typ bzw. Name."
            ),
        ),
        Property.Text(
            label="MatchValue",
            configurable=True,
            description=(
                "Suchtext je nach MatchMode. "
                "Bei TypeContains z.B. 'Mash', 'Boil', 'DatetimeWait'. "
                "Leer bei TypeContains → 'mash'."
            ),
        ),
    ]
)
class StepStatusActor(CBPiActor):
    """
    Virtueller Actor: ON, solange ein passender Mash-/Rezept-Step aktiv ist.

    Damit kannst du z.B. mit cbpi4-DependentActor Abhängigkeiten bauen:
    Pumpe nur wenn MashStep läuft (Prerequisite = dieser Actor).
    """

    async def on_start(self):
        self.state = False
        self.power = 100
        self.match_mode = self.props.get("MatchMode", "TypeContains")
        self.match_value = str(self.props.get("MatchValue", "") or "")
        logger.info(
            "StepStatusActor %s started (mode=%s value=%s)",
            self.id,
            self.match_mode,
            self.match_value,
        )

    async def on(self, power=None):
        # Status kommt nur vom aktiven Step — manuelles Einschalten wird ignoriert
        if power is not None:
            self.power = power
        logger.debug("StepStatusActor %s: manuelles ON ignoriert", self.id)

    async def off(self):
        logger.debug("StepStatusActor %s: manuelles OFF ignoriert", self.id)

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
                    active_statuses=(StepState.ACTIVE, "A"),
                )
            except Exception as exc:
                logger.error("StepStatusActor status check failed: %s", exc)
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
                    "StepStatusActor %s -> %s",
                    self.id,
                    "ON" if self.state else "OFF",
                )

            await asyncio.sleep(1)
