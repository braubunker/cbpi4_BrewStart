# cbpi4_BrewStart

CraftBeerPi4-Plugin: **Brauvorgang zu einer geplanten Startzeit starten**.

Als erster Mash-Step in deinem Rezept wartet `BrewStart` bis zur eingestellten Uhrzeit (optional mit Datum), zeigt einen Countdown an und startet danach automatisch den nächsten Step — oder wartet auf deine Bestätigung.

## Installation

Mit pipx (empfohlen, wenn CraftBeerPi4 darüber installiert ist):

```bash
pipx runpip cbpi4 install .
```

Oder aus einem geklonten Repo / Zip:

```bash
pipx runpip cbpi4 install /pfad/zu/cbpi4_BrewStart
# bzw. lokal editierbar:
pipx runpip cbpi4 install -e /pfad/zu/cbpi4_BrewStart
```

Klassisch im cbpi-venv:

```bash
python -m pip install .
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

## Hinweise

- Die Systemzeit des Raspberry Pi / Hosts muss stimmen (Zeitzone prüfen: `timedatectl`).
- Der Step muss **aktiv** sein (Brauprozess gestartet). Im gestoppten Zustand läuft kein Countdown.
- Bei `AutoNext = No` bleibt der Step nach Erreichen der Zeit stehen, bis du in der Notification auf **Next Step** tippst.

## Entwicklung / Tests

Die Zeitlogik ist ohne laufendes CraftBeerPi testbar:

```bash
python -m pip install pytest
python -m pytest -q
```

## Changelog

* **1.0.0** – Erste Version: Modes Today / DateTime / Daily, Countdown, Vorwarnung, AutoNext
