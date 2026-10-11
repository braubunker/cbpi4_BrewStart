# cbpi4_BrewStart

CraftBeerPi4-Plugin mit zwei Bausteinen:

1. **`BrewStart`** – Mash-Step: Brauvorgang zu einer geplanten Startzeit starten  
2. **`StepStatusActor`** – virtueller Actor: ON, solange ein passender Step (z.B. MashStep) aktiv ist — nutzbar als Abhängigkeit mit [cbpi4-DependentActor](https://github.com/PiBrewing/cbpi4-DependentActor)

Als erster Mash-Step in deinem Rezept wartet `BrewStart` bis zur eingestellten Uhrzeit (optional mit Datum), zeigt einen Countdown an und startet danach automatisch den nächsten Step — oder wartet auf deine Bestätigung.

## Installation

Direkt vom GitHub-Repo (auf dem Pi):

```bash
pipx runpip cbpi4 install https://github.com/braubunker/cbpi4_BrewStart/archive/main.zip
sudo systemctl restart craftbeerpi
```

Repo: https://github.com/braubunker/cbpi4_BrewStart

Lokal / editierbar:

```bash
pipx runpip cbpi4 install .
# oder:
pipx runpip cbpi4 install -e /pfad/zu/cbpi4_BrewStart
```

Danach CraftBeerPi4 neu starten (`cbpi start` bzw. Service neu starten).

## Verwendung

1. Rezept / Mash Profile öffnen
2. Als **ersten Step** einen neuen Step vom Typ **`BrewStart`** hinzufügen
3. Parameter setzen:

| Parameter | Bedeutung |
|-----------|-----------|
| **Mode** | `Today` = heute zur Uhrzeit (wenn schon vorbei → morgen). `DateTime` = festes Datum + Uhrzeit. `Daily` = nächste passende Uhrzeit. |
| **StartDate** | Nur bei `DateTime`: z.B. `2026-10-11` oder komplett `2026-10-11 06:00` / `11.10.2026 06:00` |
| **StartTime** | Uhrzeit als `HH:MM`, z.B. `06:00` |
| **NotifyBefore** | Minuten vorher warnen (Standard gedanklich 15; `0` = aus) |
| **AutoNext** | `Yes` = nach Erreichen der Zeit sofort weiter. `No` = Notification mit Button „Next Step“ |

4. Brauprozess starten — der Step wartet und zeigt z.B.  
   `Start 11.10.2026 06:00 · noch 7h 12m 05s`
5. Zur Startzeit geht es weiter mit dem nächsten Mash-/Boil-Step

### Typischer Ablauf

```
BrewStart (warten bis 06:00)
  → MashIn / Aufheizen
  → Maischschritte
  → ...
```

So kannst du abends alles vorbereiten, den Prozess starten und morgens beginnt das eigentliche Brauen zur gewünschten Zeit.

## Step-Status als Actor (Mash / Boil / Whirlpool)

In CraftBeerPi4 können Abhängigkeiten nur über **Actors** laufen (nicht direkt über Steps).  
Diese virtuellen Actors sind **ON**, solange der passende Step aktiv ist:

| Actor-Typ | ON wenn … |
|-----------|-----------|
| **`MashStatusActor`** | MashIn / MashStep (Typ oder Name) |
| **`BoilStatusActor`** | BoilStep / BM_BoilStep |
| **`WhirlpoolStatusActor`** | Step-Typ oder **-Name** enthält Whirlpool (z.B. WaitStep „Whirlpool“) |
| **`StepStatusActor`** | frei konfigurierbar (`StepKind`: Mash / Boil / Whirlpool / Kombinationen / Custom) |

### Einrichten

1. Hardware → Actor → z.B. **`BoilStatusActor`** oder **`WhirlpoolStatusActor`** anlegen (kein Extra-Parameter nötig)
2. Für Whirlpool den Step im Rezept z.B. **WaitStep** nennen: `Whirlpool`
3. Optional DependentActor:

```bash
pipx runpip cbpi4 install https://github.com/PiBrewing/cbpi4-DependentActor/archive/main.zip
```

4. DependentActor:
   - **Base** = echte Pumpe / Ventil / Heizstab  
   - **ActorDependency** = `MashStatusActor` / `BoilStatusActor` / `WhirlpoolStatusActor`  
   - **DependencyType** = `Prerequisite`

Im Kettle / Dashboard den **DependentActor** verwenden.

## Hinweise

- Die Systemzeit des Raspberry Pi / Hosts muss stimmen (Zeitzone prüfen: `timedatectl`).
- Der Step muss **aktiv** sein (Brauprozess gestartet). Im gestoppten Zustand läuft kein Countdown.
- Bei `AutoNext = No` bleibt der Step nach Erreichen der Zeit stehen, bis du in der Notification auf **Next Step** tippst.
- `StepStatusActor` lässt sich nicht manuell schalten — der Status kommt nur vom aktiven Step.

## Entwicklung / Tests

Die Zeit- und Match-Logik ist ohne laufendes CraftBeerPi testbar:

```bash
python -m pip install pytest
python -m pytest -q
```

## Changelog

* **1.2.0** – Mash-/Boil-/Whirlpool-StatusActors + StepKind-Presets (Whirlpool auch per Step-Name)
* **1.1.1** – BrewStart-Fix: Timer wie DatetimeWaitStep, robustere Props, keine kaputte cbpi-Dependency
* **1.1.0** – `StepStatusActor`: aktiver Mash-/Rezept-Step als Actor-Status für DependentActor
* **1.0.0** – Erste Version: Modes Today / DateTime / Daily, Countdown, Vorwarnung, AutoNext

## Troubleshooting BrewStart

Wenn der Step fehlt oder nicht weitergeht:

```bash
# neu installieren
pipx runpip cbpi4 uninstall cbpi4_BrewStart || true
pipx runpip cbpi4 install -e ~/cbpi4_BrewStart
# Plugin geladen?
pipx runpip cbpi4 list | grep -i brew
# Logs
journalctl -u craftbeerpi -n 100 --no-pager
# oder:
cbpi start
```

Im Step müssen **Mode** und **StartTime** (z.B. `06:30`) gesetzt sein.  
DateTime-Modus: Datum in **StartDate** als `11.10.26-06:30` oder `2026-10-11 06:30`.
