# Garmin Designer

Wandelt Designs aus dem Zifferblatt-Editor (JSON) in Garmin-Zifferblätter (`.prg`) für die Venu X1 um.

**Webseite:** https://jorgepnt-design.github.io/garmindesigner/

## So geht's

1. Auf der Webseite einmalig einen GitHub-Schlüssel speichern (die Seite erklärt jeden Schritt).
2. Die JSON-Datei hochladen und prüfen, wie die Vorschau aussieht.
3. Auf **In .prg umwandeln** tippen. Nach 1–2 Minuten erscheint der Download.
4. Uhr per USB anschließen, die `.prg` in den Ordner **`GARMIN/APPS`** kopieren,
   dann auf der Uhr das Zifferblatt lange drücken und auswählen.

Alle fertigen Dateien liegen auch unter **Releases → neueste**.

## Einmalige Einrichtung (schon erledigt)

- Secrets `GARMIN_USERNAME` und `GARMIN_PASSWORD` unter *Settings → Secrets and variables → Actions*.
  Damit lädt der Bau das Connect IQ SDK und die Gerätedaten von Garmin.
- *Settings → Pages → Source:* **GitHub Actions**.

## Was der Konverter kann

| Typ im JSON | Anzeige |
|---|---|
| `hours`, `minutes`, `seconds`, `time`, `ampm` | Uhrzeit (12/24 h wie in der Uhr eingestellt) |
| `date`, `weekday`, `day`, `month`, `year` | Datum in der Sprache der Uhr |
| `battery` | Akku in % |
| `temperature` | aktuelle Temperatur |
| `distance` | heutige Strecke in km bzw. Meilen |
| `steps`, `heartRate`, `calories`, `floors`, `activeMinutes` | Aktivitätswerte |
| `notifications`, `alarmCount`, `alarmStatus` | Benachrichtigungen, Wecker |
| `text` | fester Text |
| `image` | eingebettetes Bild (`data:image/...;base64`, Größe aus `width`/`height`) |
| `icon` | Icons (Sonne, Läufer, Wecker, Herz, Glocke, Flamme, Akku, Bluetooth, Schritte, Mond, Wolke, Kalender) und Formen (`line`, `rect`, `circle`, `ring`, `dot`) |

Unbekannte Typen und Icons werden weggelassen; die Webseite zeigt dann einen Hinweis.
Die Liste steht in [`web/support.json`](web/support.json).

Optional im JSON: `"width"`/`"height"` (Größe der Design-Fläche, Standard 448 × 486) und
`"devices"` (Liste von Connect-IQ-Geräten, Standard `["venux1"]`).

## Aufbau

- `designs/` – hochgeladene Designs; jedes wird zu `<name>-venux1.prg`
- `tools/build_face.py` – erzeugt aus einem Design ein Connect-IQ-Projekt (Schriften, Icons, Monkey C, Vorschau)
- `tools/template/` – fester Monkey-C-Code (App, Datenquellen)
- `tools/fonts/` – Cormorant Garamond (Ziffern: lining/tabular), Inter (beide SIL Open Font License) und Roboto Condensed Bold (Apache 2.0)
- `tools/icons/` – Icon-Masken aus `web/icons.json` (Material Icons, Apache 2.0)
- `web/` – die Webseite
- `ElegantFace/`, `design/` – das erste, von Hand abgestimmte Zifferblatt „Elegant“
