# HELTEK Maschinenbau – neue Website (heltek.de)

Neubau der bisherigen WordPress-Seite heltek.de: gleiche Inhalte, modern und mit viel Bewegung.
Statisches HTML, CSS und JavaScript ohne Bibliotheken, ohne Cookies und ohne Anfragen an andere Anbieter.

Stand: 05.11.2026, Vorschau. Noch nicht veröffentlicht.

## Aufbau

- `werkzeuge/bauen.py`: erzeugt alle Seiten aus den Daten. Danach liegen die fertigen Seiten im Ordner (index.html, maschinen/, kilia/ …).
- `werkzeuge/maschinen_holen.py`: liest alle Maschinen-Angebote von der alten heltek.de nach `daten/maschinen.json`.
- `werkzeuge/bilder_holen.py`: lädt Fotos, Logos und Seitenbilder der alten Seite und rechnet sie in Webgrößen um. Die Originale landen in `_quellen/` (nicht im Git).
- `werkzeuge/texte_holen.py`: Impressum, AGB, Widerrufsrecht und Haftungsausschluss der alten Seite nach `daten/rechtliches/`.
- `assets/css/site.css`: Gestaltung. `assets/js/site.js`: Bewegung, Menü, Katalogfilter, Galerie, Öffnungszeiten, Anfrageformular.
- `assets/img/rotor.svg`: der Messerkopf aus dem Firmenzeichen als Vektorgrafik, nachgezeichnet aus dem alten Favicon. Er dreht sich im Startbereich und läuft beim Scrollen schneller.
- `assets/fonts/`: Schrift Archivo (SIL Open Font License, liegt bei), direkt auf der Seite, kein Google-Server.

## Bauen und ansehen

```
py werkzeuge\bauen.py            Vorschau: noindex, robots.txt sperrt alles
py werkzeuge\bauen.py --live     für heltek.de: Suchmaschinen erlaubt
py -m http.server 4340           dann http://127.0.0.1:4340
```

Die Seiten benutzen nur relative Links, laufen also unter jeder Adresse und auch in einem Unterordner.

## Seiten

- Start, Maschinen (Katalog mit Filter nach Art und Marke und Suche), eine Seite je Maschine (55), KILIA, KORIMAT, Kundendienst, Kontakt.
- Impressum, AGB, Widerrufsrecht und Haftungsausschluss wörtlich von der alten Seite.
- Datenschutz neu geschrieben, passend zur neuen Technik. Die alte Erklärung beschrieb Cookies und WordPress und enthielt Fehler („info@ex.comheltek.de“, Ort „Dorfmark“).
- Alte WordPress-Adressen leiten weiter: `/project/…` → `/maschinen/…`, `/fleischereimaschinen/` und `/gebrauchtmaschinen/` → `/maschinen/`, `/project_category/…` → gefilterter Katalog, `/datenschutzerklaerung-eu/` und `/cookie-richtlinie-eu/` → `/datenschutz/`.
- Anfrageformular: öffnet das E-Mail-Programm mit fertiger Nachricht an info@heltek.de (mailto). Es wird nichts gespeichert oder übertragen.

## Maschinen aktualisieren

```
py werkzeuge\maschinen_holen.py   (solange die alte Seite noch läuft)
py werkzeuge\bilder_holen.py
py werkzeuge\bauen.py
```

Später, wenn die alte Seite abgeschaltet ist, werden Maschinen direkt in `daten/maschinen.json` gepflegt (Titel, Kategorie, Text, Fotos).

## Offen vor dem Start

- **Hosting:** wohin die Seite kommt (zum Beispiel GitHub Pages wie bei den anderen Seiten). Danach den Anbieter in der Datenschutzerklärung eintragen (`DATENSCHUTZ` in `werkzeuge/bauen.py`).
- **Ersatzteile KORIMAT:** Auf der alten Korimat-Seite geht die Ersatzteil-Mail an `info@hammer-dorfmark.de`. Übernommen wie gehabt, bitte bestätigen oder auf info@heltek.de ändern.
- **Maschinensucher:** Der Link zeigt auf das Händlerprofil „Hammer GmbH & Co. KG“. Übernommen wie gehabt.
- **Bestand:** Alle 55 Angebote der alten Seite sind übernommen. Verkaufte Maschinen bitte nennen, dann fliegen sie raus.
- Eine Maschine („Korimat KA 240 Gas“) hat auf der alten Seite keinen Text.
