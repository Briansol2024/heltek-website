# -*- coding: utf-8 -*-
"""Lädt die Fotos der Maschinen und die Seitenbilder/Logos von der bisherigen heltek.de
und rechnet sie in Webgrößen um.

Originale landen in _quellen/ (nicht veröffentlicht), Webfassungen in assets/.
Mehrfach aufrufbar: was schon geladen ist, wird nicht noch einmal geholt.

    py werkzeuge/bilder_holen.py
"""
import json, sys, time, urllib.request
from pathlib import Path
from PIL import Image, ImageOps

sys.stdout.reconfigure(encoding="utf-8")
WURZEL = Path(__file__).resolve().parent.parent
QUELLEN = WURZEL / "_quellen"
UA = {"User-Agent": "Mozilla/5.0 (Heltek-Umzug)"}
U = "https://www.heltek.de/wp-content/uploads/"

SEITE = {
    # Logos und Marken
    "logo-heltek-kilia.png": U + "2026/11/HELTEK_KILIA_Logo_Header_transparent1.png",
    "logo-kilia.png": U + "2021/01/kilia-logo-500.png",
    "logo-korimat.png": U + "2021/01/Korimat_logo.png",
    "favicon-alt.png": U + "2021/05/cropped-favicon-heltek.png",
    "partner-1.png": U + "2026/05/Gemini_Generated_Image_4gcfkt4gcfkt4gcf.png",
    "partner-2.png": U + "2026/05/Neues-Projekt-1.png",
    "partner-3.png": U + "2026/05/Gemini_Generated_Image_1zuodg1zuodg1zuo.png",
    "partner-4.png": U + "2026/05/Gemini_Generated_Image_y259j5y259j5y259-1.png",
    "partner-5.png": U + "2026/05/Gemini_Generated_Image_1qcviq1qcviq1qcv.png",
    "partner-6.png": U + "2026/05/Gemini_Generated_Image_rh8upgrh8upgrh8u.png",
    # Korimat-Geräte
    "ka160.png": U + "2021/01/KA160_grau.png",
    "ka240.png": U + "2021/01/KA-160-geschliffen.png",
    "ka380.png": U + "2021/01/KA380_grau.png",
    # Große Bilder
    "halle.jpg": U + "2021/02/heltek-slider_1.jpg",
    "sortiment.jpg": U + "2025/08/Maschinen-Sortiment.jpeg",
    "kilia-halle.jpg": U + "2021/01/kilia-slider.jpg",
    "service-werkstatt.jpg": U + "2021/02/WhatsApp-Image-2021-02-12-at-11.35.08.jpeg",
    "service.jpg": U + "2021/02/service2.jpg",
}


def laden(url, ziel):
    if ziel.exists() and ziel.stat().st_size > 0:
        return False
    ziel.parent.mkdir(parents=True, exist_ok=True)
    for versuch in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                daten = r.read()
            ziel.write_bytes(daten)
            time.sleep(0.25)
            return True
        except Exception as e:
            if versuch == 2:
                print("  FEHLER", url, e)
            time.sleep(2)
    return False


def jpg(quelle, ziel, breite, qualitaet=80):
    if ziel.exists():
        return
    im = ImageOps.exif_transpose(Image.open(quelle))
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        grund = Image.new("RGB", im.size, (255, 255, 255))
        grund.paste(im, mask=im.split()[-1])
        im = grund
    else:
        im = im.convert("RGB")
    if im.width > breite:
        im = im.resize((breite, round(im.height * breite / im.width)), Image.LANCZOS)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    im.save(ziel, "JPEG", quality=qualitaet, optimize=True, progressive=True)


def png_klein(quelle, ziel, breite):
    if ziel.exists():
        return
    im = Image.open(quelle).convert("RGBA")
    if im.width > breite:
        im = im.resize((breite, round(im.height * breite / im.width)), Image.LANCZOS)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    im.save(ziel, "PNG", optimize=True)


def main():
    # Seitenbilder
    for name, url in SEITE.items():
        q = QUELLEN / "seite" / name
        neu = laden(url, q)
        if not q.exists():
            continue
        if name.endswith(".png"):
            png_klein(q, WURZEL / "assets" / "img" / name, 1200)
        else:
            jpg(q, WURZEL / "assets" / "img" / name.replace(".jpg", "-2000.jpg"), 2000, 78)
            jpg(q, WURZEL / "assets" / "img" / name.replace(".jpg", "-1000.jpg"), 1000, 78)
        print(("geladen " if neu else "da      ") + name)

    # Maschinen
    daten = json.loads((WURZEL / "daten" / "maschinen.json").read_text(encoding="utf-8"))
    for m in daten:
        web = []
        for n, url in enumerate(m["bilder"], 1):
            endung = Path(url).suffix.lower() or ".jpg"
            q = QUELLEN / "maschinen" / m["slug"] / f"{n:02d}{endung}"
            laden(url, q)
            if not q.exists():
                continue
            try:
                gross = WURZEL / "assets" / "maschinen" / m["slug"] / f"{n:02d}-1600.jpg"
                klein = WURZEL / "assets" / "maschinen" / m["slug"] / f"{n:02d}-720.jpg"
                jpg(q, gross, 1600)
                jpg(q, klein, 720, 76)
                with Image.open(gross) as g:
                    web.append({"nr": n, "b": g.width, "h": g.height})
            except Exception as e:
                print("  BILD KAPUTT", q, e)
        m["web_bilder"] = web
        print(f"{m['slug'][:50]:50s} {len(web)}/{len(m['bilder'])}")
    (WURZEL / "daten" / "maschinen.json").write_text(json.dumps(daten, ensure_ascii=False, indent=1), encoding="utf-8")
    print("fertig")


if __name__ == "__main__":
    main()
