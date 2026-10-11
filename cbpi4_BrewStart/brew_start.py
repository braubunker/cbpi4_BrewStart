import asyncio
import logging
from datetime import datetime

from cbpi.api import *
from cbpi.api.dataclasses import NotificationAction, NotificationType
from cbpi.api.step import CBPiStep, StepResult
from cbpi.api.timer import Timer

try:
    from .schedule import format_countdown, format_start, resolve_start
except ImportError:
    from cbpi4_BrewStart.schedule import format_countdown, format_start, resolve_start

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
            description=(
                "Nur DateTime: Datum YYYY-MM-DD, oder komplett "
                "'YYYY-MM-DD HH:MM' / '11.10.26-06:00'"
            ),
        ),
        Property.Text(
            label="StartTime",
            configurable=True,
            description="Startzeit HH:MM (Pflicht bei Today/Daily), z.B. 06:00",
        ),
        Property.Number(
            label="NotifyBefore",
            configurable=True,
            description="Minuten vorher benachrichtigen (0 = aus, leer = 15)",
        ),
        Property.Select(
            label="AutoNext",
            options=["Yes", "No"],
            description=(
                "Yes: nach Startzeit automatisch weiter. "
                "No: auf Bestätigung warten."
            ),
        ),
    ]
)
class BrewStart(CBPiStep):
    """Wartet bis zur konfigurierten Startzeit (wie DatetimeWaitStep, mit Countdown)."""

    async def NextStep(self, **kwargs):
        await self.next()

    async def on_timer_done(self, timer):
        self.summary = "Brauzeit erreicht"
        await self.push_update()

        message = "Geplante Startzeit erreicht."
        if getattr(self, "target_start", None) is not None:
            message = f"Geplante Startzeit erreicht ({format_start(self.target_start)})."

        if self.auto_next:
            self.cbpi.notify(self.name, message, NotificationType.SUCCESS)
            await self.next()
        else:
            self.cbpi.notify(
                self.name,
                f"{message} Weiter zum nächsten Step.",
                NotificationType.INFO,
                action=[NotificationAction("Next Step", self.NextStep)],
            )

    async def on_timer_update(self, timer, seconds):
        try:
            secs = int(seconds)
        except (TypeError, ValueError):
            secs = 0

        if getattr(self, "target_start", None) is not None:
            self.summary = (
                f"Start {format_start(self.target_start)} · noch {format_countdown(secs)}"
            )
        else:
            self.summary = Timer.format_time(secs)

        # Vorwarnung
        if (
            getattr(self, "notify_before_seconds", 0) > 0
            and not getattr(self, "pre_notified", False)
            and 0 < secs <= self.notify_before_seconds
        ):
            self.pre_notified = True
            self.cbpi.notify(
                self.name,
                f"Braustart in {format_countdown(secs)}",
                NotificationType.WARNING,
            )

        await self.push_update()

    def _read_props(self):
        mode = self.props.get("Mode", None) or "Today"
        start_time = self.props.get("StartTime", None)
        start_date = self.props.get("StartDate", None)
        start_time = "" if start_time is None else str(start_time).strip()
        start_date = "" if start_date is None else str(start_date).strip()

        # Häufiger Fehler: StartTime leer gelassen
        if not start_time and mode != "DateTime":
            start_time = "06:00"
        if mode == "DateTime" and not start_date and start_time:
            # Erlaubt: kompletter Zeitstempel nur in StartTime
            start_date = start_time
            start_time = ""

        raw_notify = self.props.get("NotifyBefore", None)
        try:
            if raw_notify is None or raw_notify == "":
                notify_before = 15
            else:
                notify_before = int(float(raw_notify))
        except (TypeError, ValueError):
            notify_before = 15

        auto_next = (self.props.get("AutoNext", None) or "Yes") == "Yes"
        return mode, start_time, start_date, max(0, notify_before), auto_next

    async def on_start(self):
        self.pre_notified = False
        mode, start_time, start_date, notify_before, self.auto_next = self._read_props()
        self.notify_before_seconds = notify_before * 60

        try:
            self.target_start = resolve_start(
                mode=mode,
                start_time=start_time,
                start_date=start_date,
            )
        except ValueError as exc:
            logger.error("BrewStart config error: %s", exc)
            self.summary = f"Fehler: {exc}"
            await self.push_update()
            self.cbpi.notify(self.name, str(exc), NotificationType.ERROR)
            # Kurzer Timer, dann stehen bleiben (kein Auto-Next bei Fehler)
            self.auto_next = False
            self.timer = Timer(1, on_update=self.on_timer_update, on_done=self.on_timer_done)
            return

        seconds = int((self.target_start - datetime.now()).total_seconds())
        if seconds <= 0:
            self.summary = "Brauzeit erreicht"
            await self.push_update()
            self.cbpi.notify(
                self.name,
                f"Startzeit bereits erreicht ({format_start(self.target_start)}).",
                NotificationType.SUCCESS,
            )
            if self.auto_next:
                await self.next()
            else:
                self.cbpi.notify(
                    self.name,
                    "Weiter zum nächsten Step.",
                    NotificationType.INFO,
                    action=[NotificationAction("Next Step", self.NextStep)],
                )
            self.timer = Timer(1, on_update=self.on_timer_update, on_done=self.on_timer_done)
            return

        self.summary = (
            f"Start {format_start(self.target_start)} · noch {format_countdown(seconds)}"
        )
        self.cbpi.notify(
            self.name,
            f"Braustart geplant für {format_start(self.target_start)}",
            NotificationType.INFO,
        )
        await self.push_update()

        # Bewährtes CBPi-Muster (wie DatetimeWaitStep): ein Timer über die gesamte Wartezeit
        self.timer = Timer(
            seconds, on_update=self.on_timer_update, on_done=self.on_timer_done
        )
        self.timer.start()
        logger.info(
            "BrewStart waiting %s seconds until %s",
            seconds,
            format_start(self.target_start),
        )

    async def on_stop(self):
        if getattr(self, "timer", None) is not None:
            try:
                await self.timer.stop()
            except Exception as exc:
                logger.warning("BrewStart timer stop: %s", exc)
        self.summary = ""
        await self.push_update()

    async def reset(self):
        mode, start_time, start_date, notify_before, self.auto_next = self._read_props()
        self.notify_before_seconds = notify_before * 60
        self.pre_notified = False
        try:
            self.target_start = resolve_start(
                mode=mode, start_time=start_time, start_date=start_date
            )
            seconds = max(
                1, int((self.target_start - datetime.now()).total_seconds())
            )
        except ValueError:
            seconds = 1
            self.target_start = None
        self.timer = Timer(
            seconds, on_update=self.on_timer_update, on_done=self.on_timer_done
        )

    async def run(self):
        while self.running is True:
            await asyncio.sleep(1)
        return StepResult.DONE
