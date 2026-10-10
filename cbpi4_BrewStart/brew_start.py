import asyncio
import logging
from datetime import datetime

from cbpi.api import *
from cbpi.api.dataclasses import NotificationAction, NotificationType
from cbpi.api.step import CBPiStep, StepResult
from cbpi.api.timer import Timer

from .schedule import format_countdown, format_start, resolve_start

logger = logging.getLogger(__name__)


@parameters(
    [
        Property.Select(
            label="Mode",
            options=["Today", "DateTime", "Daily"],
            description=(
                "Today: heute zur Startzeit (sonst morgen). "
                "DateTime: festes Datum + Uhrzeit. "
                "Daily: nächste Uhrzeit (heute/morgen)."
            ),
        ),
        Property.Text(
            label="StartDate",
            configurable=True,
            description="Nur DateTime-Modus: Datum als YYYY-MM-DD oder komplett 'YYYY-MM-DD HH:MM'",
        ),
        Property.Text(
            label="StartTime",
            configurable=True,
            description="Startzeit als HH:MM (z.B. 06:00)",
        ),
        Property.Number(
            label="NotifyBefore",
            configurable=True,
            description="Minuten vorher benachrichtigen (0 = aus, Standard: 15)",
        ),
        Property.Select(
            label="AutoNext",
            options=["Yes", "No"],
            description=(
                "Yes: nach Startzeit automatisch zum nächsten Step. "
                "No: warten auf Bestätigung."
            ),
        ),
    ]
)
class BrewStart(CBPiStep):
    """Wartet bis zur konfigurierten Startzeit und startet dann den Brauvorgang."""

    async def NextStep(self, **kwargs):
        await self.next()

    async def on_timer_done(self, timer):
        self.summary = "Brauzeit erreicht"
        await self.push_update()

        message = f"Geplante Startzeit erreicht ({format_start(self.target_start)})."
        if self.auto_next:
            self.cbpi.notify(self.name, message, NotificationType.INFO)
            await self.next()
        else:
            self.cbpi.notify(
                self.name,
                f"{message} Weiter zum nächsten Step.",
                NotificationType.INFO,
                action=[NotificationAction("Next Step", self.NextStep)],
            )

    async def on_timer_update(self, timer, seconds):
        await self.push_update()

    async def on_start(self):
        self.done = False
        self.pre_notified = False
        self.auto_next = self.props.get("AutoNext", "Yes") == "Yes"

        raw_notify = self.props.get("NotifyBefore", None)
        try:
            if raw_notify is None or raw_notify == "":
                notify_before = 15
            else:
                notify_before = int(float(raw_notify))
        except (TypeError, ValueError):
            notify_before = 15
        self.notify_before_seconds = max(0, notify_before) * 60

        try:
            self.target_start = resolve_start(
                mode=self.props.get("Mode", "Today"),
                start_time=str(self.props.get("StartTime", "06:00") or "06:00"),
                start_date=str(self.props.get("StartDate", "") or ""),
            )
        except ValueError as exc:
            self.summary = f"Fehler: {exc}"
            await self.push_update()
            self.cbpi.notify(self.name, str(exc), NotificationType.ERROR)
            self.target_start = None
            return

        remaining = int((self.target_start - datetime.now()).total_seconds())
        self.summary = (
            f"Start {format_start(self.target_start)} · noch {format_countdown(remaining)}"
        )
        self.cbpi.notify(
            self.name,
            f"Braustart geplant für {format_start(self.target_start)}",
            NotificationType.INFO,
        )

        if self.timer is None:
            self.timer = Timer(1, on_update=self.on_timer_update, on_done=self.on_timer_done)

        await self.push_update()

    async def on_stop(self):
        if self.timer is not None:
            await self.timer.stop()
        self.summary = ""
        await self.push_update()

    async def reset(self):
        self.timer = Timer(1, on_update=self.on_timer_update, on_done=self.on_timer_done)
        self.done = False
        self.pre_notified = False

    async def run(self):
        while self.running is True:
            await asyncio.sleep(1)

            if self.target_start is None or self.done:
                continue

            now = datetime.now()
            remaining = int((self.target_start - now).total_seconds())

            if remaining > 0:
                self.summary = (
                    f"Start {format_start(self.target_start)} · noch {format_countdown(remaining)}"
                )

                if (
                    self.notify_before_seconds > 0
                    and not self.pre_notified
                    and remaining <= self.notify_before_seconds
                ):
                    self.pre_notified = True
                    self.cbpi.notify(
                        self.name,
                        f"Braustart in {format_countdown(remaining)} ({format_start(self.target_start)})",
                        NotificationType.WARNING,
                    )

                if remaining <= 60 or remaining % 30 == 0:
                    await self.push_update()
                continue

            self.done = True
            self.summary = "Brauzeit erreicht"
            await self.push_update()

            if self.timer is not None and self.timer.is_running is not True:
                self.timer.start()
                self.timer.is_running = True

        return StepResult.DONE
