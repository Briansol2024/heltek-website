# -*- coding: utf-8 -*-
"""Baut die komplette HELTEK-Website als statische Seiten.

    py werkzeuge/bauen.py            Vorschau (noindex, für Testadressen)
    py werkzeuge/bauen.py --live     für heltek.de (Suchmaschinen erlaubt)

Quellen: daten/maschinen.json, daten/rechtliches/*.html, assets/.
Alle Links sind relativ, die Seite läuft also unter jeder Adresse und in jedem Unterordner.
"""
import html, json, re, shutil, sys
from urllib.parse import quote
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
WURZEL = Path(__file__).resolve().parent.parent
LIVE = "--live" in sys.argv
BASIS = "https://www.heltek.de"
HEUTE = date.today()

FIRMA = "HELTEK Maschinenbau GmbH & Co. KG"
STRASSE, PLZ_ORT = "Westendorfer Straße 51", "29683 Bad Fallingbostel"
TEL_ANZEIGE, TEL_LINK = "05163 91000", "+49516391000"
FAX = "05163 720"
MAIL = "info@heltek.de"
LINKS_AUSSEN = {
    "kleinanzeigen": ("Kleinanzeigen", "https://www.kleinanzeigen.de/pro/heltek-maschinenbau"),
    "maschinensucher": ("Maschinensucher", "https://www.maschinensucher.de/Haendler/83784/Hammer-GmbH-Co-KG-Bad-Fallingbostel"),
    "instagram": ("Instagram", "https://www.instagram.com/heltek_maschinenbau/"),
    "youtube": ("YouTube", "https://www.youtube.com/@kilia-Heltek-Maschinenbau"),
}
ROUTE = "https://www.openstreetmap.org/search?query=Westendorfer%20Stra%C3%9Fe%2051%2C%2029683%20Bad%20Fallingbostel"

e = lambda s: html.escape(str(s), quote=True)


# ── Symbole ──────────────────────────────────────────────────────────────────────────
def sym(name, cls=""):
    p = {
        "pfeil": '<path d="M5 12h14M13 6l6 6-6 6"/>',
        "links": '<path d="M15 5l-7 7 7 7"/>',
        "rechts": '<path d="M9 5l7 7-7 7"/>',
        "tel": '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 005 5L15 13l5 2v4a2 2 0 01-2 2A16 16 0 013 6a2 2 0 012-2"/>',
        "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
        "ort": '<path d="M12 21s-7-6.2-7-11.5A7 7 0 0119 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
        "lupe": '<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/>',
        "foto": '<rect x="3" y="6" width="18" height="14" rx="2"/><circle cx="12" cy="13" r="3.5"/><path d="M8 6l1.5-2h5L16 6"/>',
        "zu": '<path d="M6 6l12 12M18 6L6 18"/>',
        "gross": '<path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/>',
        "haken": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
        "aussen": '<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 01-1 1H5a1 1 0 01-1-1V7a1 1 0 011-1h5"/>',
        "instagram": '<rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r=".6" fill="currentColor"/>',
        "youtube": '<rect x="2.5" y="5.5" width="19" height="13" rx="4"/><path d="M10 9.5v5l4.5-2.5z" fill="currentColor"/>',
        "laden": '<path d="M4 9h16l-1.5 10.5a1 1 0 01-1 .5h-11a1 1 0 01-1-.5zM8 9V7a4 4 0 018 0v2"/>',
        "uhr": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    }[name]
    k = f' class="{cls}"' if cls else ""
    return f'<svg{k} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{p}</svg>'


STERN = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 2.8l2.8 5.9 6.4.8-4.7 4.4 1.2 6.3L12 17.1l-5.7 3.1 1.2-6.3L2.8 9.5l6.4-.8z"/></svg>'

# Linienbilder für die Leistungen (werden beim Erscheinen gezeichnet)
LEISTUNG_SYM = {
    "neu": '<path class="strich" style="--l:120" d="M8 22h40v22a4 4 0 01-4 4H12a4 4 0 01-4-4z"/><path class="strich akzent" style="--l:90" d="M28 22c0-8 6-12 12-12M28 22c0-6-4-10-10-10"/><path class="strich" style="--l:60" d="M4 22h48M18 48v4M38 48v4"/>',
    "ueberholt": '<circle class="strich" style="--l:120" cx="28" cy="28" r="17"/><path class="strich akzent" style="--l:80" d="M20 28l6 6 11-12"/><path class="strich" style="--l:70" d="M28 4v5M28 47v5M4 28h5M47 28h5"/>',
    "teile": '<path class="strich" style="--l:160" d="M28 6l4 6 7-1 1 7 6 4-4 6 4 6-6 4-1 7-7-1-4 6-4-6-7 1-1-7-6-4 4-6-4-6 6-4 1-7 7 1z"/><circle class="strich akzent" style="--l:50" cx="28" cy="28" r="7"/>',
    "dienst": '<path class="strich" style="--l:150" d="M36 8a10 10 0 00-12 13L8 37a4 4 0 006 6l16-16a10 10 0 0013-12l-6 6-6-1-1-6z"/><path class="strich akzent" style="--l:30" d="M12 39l2 2"/>',
    "plan": '<rect class="strich" style="--l:170" x="6" y="10" width="44" height="36" rx="3"/><path class="strich akzent" style="--l:110" d="M6 22h20v24M26 30h24M38 30v16"/>',
}


# ── Der Messerkopf (einmal je Seite als Symbol, sonst per <use>) ─────────────────────
_svg = (WURZEL / "assets" / "img" / "rotor.svg").read_text(encoding="utf-8")
_vb = re.search(r'viewBox="([^"]+)"', _svg).group(1)
_pfade = re.findall(r'd="([^"]+)"', _svg)
ROTOR_SPRITE = (
    '<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false"><defs>'
    '<linearGradient id="stahl" x1="0" y1="0" x2="1" y2="1">'
    '<stop offset="0" stop-color="#f4f6f8"/><stop offset=".35" stop-color="#9aa4b0"/><stop offset=".55" stop-color="#e3e8ee"/>'
    '<stop offset=".8" stop-color="#6d7783"/><stop offset="1" stop-color="#c3cad3"/></linearGradient>'
    f'<g id="rk"><path fill-rule="evenodd" d="{_pfade[0]}"/></g>'
    f'<g id="rn"><path fill="#ff0716" fill-rule="evenodd" d="{_pfade[1]}"/></g>'
    '</defs></svg>')


def rotor(cls="rotor", stahl=False):
    fuell = 'url(#stahl)' if stahl else 'currentColor'
    return (f'<div class="{cls}" aria-hidden="true"><svg viewBox="{_vb}">'
            f'<g class="klingen"><use href="#rk" fill="{fuell}"/></g><g class="nabe"><use href="#rn"/></g></svg></div>')


# ── Daten: Maschinen ─────────────────────────────────────────────────────────────────
KATEGORIEN = [  # Schlüssel, Name, alte Namen
    ("kutter", "Kutter", {"Kutter"}),
    ("woelfe", "Fleischwölfe", {"Wolf"}),
    ("autoklaven", "Autoklaven", {"Korimat"}),
    ("fueller", "Füller", {"Füller-Vakuumfüller", "Füller"}),
    ("speckschneider", "Speckschneider", {"Speckschneider"}),
    ("mischer", "Mischer", {"Menger und Mischer"}),
    ("saegen", "Knochensägen", {"Knochensägen"}),
]
KAT_NAME = {k: n for k, n, _ in KATEGORIEN}
MARKEN = [("kilia", "KILIA"), ("korimat", "KORIMAT"), ("frey", "Frey"), ("treif", "TREIF"), ("k+g wetter", "K+G Wetter"),
          ("vemag", "Vemag"), ("seydelmann", "Seydelmann"), ("scharfen", "Scharfen"), ("kolbe", "Kolbe")]


def slug_machen(s):
    s = s.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss").replace("+", "-")
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s)).strip("-")


def text_saeubern(t):
    t = re.sub(r"^(\s*<p>\s*[–-]\s*</p>\s*)+", "", t)
    t = re.sub(r"<p>\s*[–-]\s*</p>", "", t)
    t = re.sub(r"<p>\s*(<br>\s*)*</p>", "", t)
    return t.strip()


def nur_text(t):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t))).strip()


def maschinen_laden():
    roh = json.loads((WURZEL / "daten" / "maschinen.json").read_text(encoding="utf-8"))
    roh = list(reversed(roh))   # Die Sitemap führt die ältesten zuerst, der alte Katalog die neuesten
    alle, vergeben = [], set()
    for m in roh:
        if not m.get("web_bilder"):
            continue
        kat = next((k for k, _, alt in KATEGORIEN if set(m["kategorien"]) & alt), "kutter")
        t = m["titel"].lower()
        marke = next((n for s, n in MARKEN if t.startswith(s)), "")
        slug = m["slug"]
        if slug.isdigit():
            slug = slug_machen(m["titel"])
        basis, n = slug, 2
        while slug in vergeben:
            slug = f"{basis}-{n}"; n += 1
        vergeben.add(slug)
        text = text_saeubern(m["text"])
        alle.append({
            "slug": slug, "alt_slug": m["slug"], "titel": m["titel"], "kat": kat, "marke": marke,
            "bilder": m["web_bilder"], "quelle_slug": m["slug"], "text": text, "kurz": nur_text(text)[:300],
        })
    return alle


MASCHINEN = maschinen_laden()

REZENSIONEN = [
    ("Fleischerei Schiemer", "Wir, die Fleischerei Schiemer sind ein Handwerksbetrieb im Ennepe-Ruhr-Kreis mit 4 Geschäften und dem Schwerpunkt Wurstwaren eigener Herstellung und haben unseren 20 Jahre alten Kilia Kutter Meister plus 50 in Zahlung gegeben und einen 65 er Kutter Meister plus Vario mit Beintaster von Kilia- (Firma Heltek ) als generalüberholte Maschine gekauft. Vorher habe ich mich persönlich in den Geschäftsräumen der Firma Heltek von deren einwandfreiem Arbeitsqualitäten überzeugen dürfen. Der Zustand entspricht einem Neugerät und das bei halben Preis. Solche Geschäfte machen Spaß. Die Maschine möchten wir schon heute nicht mehr missen da sie durch den starken Motor eine hervorragende Schneidleistung hat. Auch die um 30 % größere Kutter Schüssel kommt unseren Chargen sehr entgegen und ist eine Produktions Erleichterung. Kauf Lieferung Montage Rücknahme des Altgerätes alles einwandfrei. Besichtigung bei uns gerne möglich.", "Jochen Michaelsen"),
    ("", "Super Chef der Service ist top und wenn Fragen sind kann man jeder Zeit anrufen haben eine neuen Kutter gekauft bei ihm und läuft einfach spitze kann ich nur jedem empfehlen der auf Qualität achtet", "Jochen Schröder"),
    ("", "Tolle Kommunikation, sehr schnelle Abwicklung, guter Preis für ein echt tolles Gerät! Sind mit dem Wolf echt zufrieden!", "Sascha Dürr"),
    ("", "Hat alles super geklappt. Vom beraten bis zum liefern und aufbauen. Das Verkaufsteam und auch die Techniker sind super nett und hilfsbereit. Gerne wieder", "Martin Eickhoff"),
    ("", "Freundlicher Kundenservice. Ich würde jederzeit wieder einen Kauf tätigen", "Thomas Kling"),
    ("", "Sehr nette und kompetente Fachleute. Reibungslose Kaufabwicklung. Hilfreich bei Inbetriebnahme. Gerne wieder. Kann ich gerne weiterempfehlen.", "Dennis Lorenz"),
    ("", "Sehr guter Service! Selbst am Samstag wurde sich Zeit für eine individuelle Beratung über die Geschäftszeiten hinaus genommen!", "Christian K."),
]

PARTNER = [("partner-1.png", "KILIA – since 1932"), ("partner-2.png", "schau mer mal 24"), ("partner-3.png", "KOMET Vacuum Experts"),
           ("partner-4.png", "FREY Maschinenbau"), ("partner-5.png", "KORIMAT"), ("partner-6.png", "PROCESS-PACK Deutschland")]

NAV = [("maschinen/", "Maschinen"), ("kilia/", "KILIA"), ("korimat/", "KORIMAT"), ("kundendienst/", "Kundendienst"),
       ("#mietkauf", "Mietkauf & Leasing"), ("kontakt/", "Kontakt")]


# ── Seitenrahmen ─────────────────────────────────────────────────────────────────────
def rahmen(pfad, titel, beschreibung, inhalt, aktiv="", kopfbild=None, extra_kopf="", jsonld=None, ohne_index=False):
    tiefe = pfad.count("/")
    r = "../" * tiefe
    url = BASIS + "/" + pfad.replace("index.html", "")
    nav = "".join(
        f'<a href="{r + ("" if z.startswith("#") else "") + z}"{" aria-current=\"page\"" if aktiv == z else ""}>{e(n)}</a>' for z, n in NAV)
    menue_nav = "".join(f'<a href="{(r + z) or "./"}" style="--i:{i}">{e(n)}</a>' for i, (z, n) in enumerate([("", "Start")] + NAV))
    robots = '<meta name="robots" content="noindex, nofollow">' if (not LIVE or ohne_index) else ""
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    seitentitel = titel if "HELTEK" in titel else f"{titel} | HELTEK Maschinenbau"
    og_bild = BASIS + "/assets/img/og.jpg"
    return f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<script>document.documentElement.classList.add("js")</script>
<title>{e(seitentitel)}</title>
<meta name="description" content="{e(beschreibung)}">
{robots}
<link rel="canonical" href="{e(url)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="HELTEK Maschinenbau">
<meta property="og:locale" content="de_DE">
<meta property="og:url" content="{e(url)}">
<meta property="og:title" content="{e(seitentitel)}">
<meta property="og:description" content="{e(beschreibung)}">
<meta property="og:image" content="{og_bild}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{r}assets/img/favicon.svg" type="image/svg+xml">
<link rel="icon" href="{r}assets/img/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="{r}assets/img/apple-touch-icon.png">
<meta name="theme-color" content="#0a0b0d">
<link rel="preload" href="{r}assets/fonts/archivo-latin.woff2" as="font" type="font/woff2" crossorigin>
{extra_kopf}<link rel="stylesheet" href="{r}assets/css/site.css">
{ld}
</head>
<body>
{ROTOR_SPRITE}
<a class="sprung" href="#inhalt">Zum Inhalt springen</a>
<header class="kopf">
  <div class="huelle">
    <a class="logo" href="{r or './'}" aria-label="HELTEK Maschinenbau – zur Startseite"><img src="{r}assets/img/logo-heltek-kilia-600.png" alt="HELTEK Maschinenbau · KILIA" width="600" height="132"></a>
    <nav class="nav" aria-label="Hauptmenü">{nav}</nav>
    <a class="kopf-tel" href="tel:{TEL_LINK}" aria-label="Anrufen: {TEL_ANZEIGE}">{sym("tel")}<span>{TEL_ANZEIGE}</span></a>
    <button class="menue-knopf" type="button" aria-expanded="false" aria-controls="menue" aria-label="Menü öffnen"><span></span><span></span><span></span></button>
  </div>
  <div class="fortschritt" aria-hidden="true"></div>
</header>
<div class="menue" id="menue" aria-hidden="true">
  {rotor("rotor rotor-deko")}
  <nav aria-label="Menü">{menue_nav}</nav>
  <div class="menue-fuss"><a href="tel:{TEL_LINK}">{TEL_ANZEIGE}</a><a href="mailto:{MAIL}">{MAIL}</a><span>Mo–Do 8–17 Uhr · Fr 8–13 Uhr</span></div>
</div>
<main id="inhalt">
{inhalt}
</main>
{fuss(r)}
<script src="{r}assets/js/site.js" defer></script>
</body>
</html>
"""


def fuss(r):
    aussen = "".join(f'<li><a href="{u}" rel="noopener" target="_blank">{e(n)}</a></li>' for n, u in LINKS_AUSSEN.values())
    return f"""<footer class="fuss">
  <div class="huelle">
    <div class="fuss-gitter">
      <div>
        <a class="logo" href="{r or './'}"><img src="{r}assets/img/logo-heltek-kilia-600.png" alt="HELTEK Maschinenbau · KILIA" width="600" height="132" loading="lazy"></a>
        <p>Fleischerei- und Großküchentechnik aus Bad Fallingbostel. Inhaber der Marke KILIA, offizieller Vertriebspartner für KORIMAT.</p>
      </div>
      <div>
        <h4>Seiten</h4>
        <ul><li><a href="{r}maschinen/">Maschinen</a></li><li><a href="{r}kilia/">KILIA</a></li><li><a href="{r}korimat/">KORIMAT</a></li><li><a href="{r}kundendienst/">Kundendienst</a></li><li><a href="{r}#mietkauf">Mietkauf &amp; Leasing</a></li><li><a href="{r}kontakt/">Kontakt</a></li></ul>
      </div>
      <div>
        <h4>Auch bei</h4>
        <ul>{aussen}</ul>
      </div>
      <div>
        <h4>Kontakt</h4>
        <ul>
          <li>{e(FIRMA)}<br>{e(STRASSE)}<br>{e(PLZ_ORT)}</li>
          <li><a href="tel:{TEL_LINK}">Tel. {TEL_ANZEIGE}</a></li>
          <li><a href="mailto:{MAIL}">{MAIL}</a></li>
        </ul>
      </div>
    </div>
    <div class="fuss-wort" aria-hidden="true">HELTEK</div>
    <div class="fuss-unten">
      <span>© {HEUTE.year} {e(FIRMA)}</span>
      <span><a href="{r}impressum/">Impressum</a> · <a href="{r}datenschutz/">Datenschutz</a> · <a href="{r}agb/">AGB</a> · <a href="{r}widerrufsrecht/">Widerrufsrecht</a> · <a href="{r}haftungsausschluss/">Haftungsausschluss</a></span>
    </div>
  </div>
</footer>"""


# ── Bausteine ────────────────────────────────────────────────────────────────────────
def mkarte(m, r, lazy=True):
    b = m["bilder"][0]
    such = " ".join([m["titel"], KAT_NAME[m["kat"]], m["marke"], m["kurz"][:160]])
    lade = ' loading="lazy"' if lazy else ""
    return f"""<a class="mkarte" href="{r}maschinen/{m['slug']}/" data-kat="{m['kat']}" data-marke="{e(m['marke'])}" data-suche="{e(such)}">
  <div class="foto"><img src="{r}assets/maschinen/{m['quelle_slug']}/{b['nr']:02d}-720.jpg" alt="{e(m['titel'])}" width="720" height="{round(720 * b['h'] / b['b'])}" decoding="async"{lade}>
    <span class="anzahl">{sym('foto')}{len(m['bilder'])}</span></div>
  <div class="text">
    <div class="etiketten"><span class="etikett">{e(KAT_NAME[m['kat']])}</span>{f'<span class="etikett marke-e">{e(m["marke"])}</span>' if m['marke'] else ''}</div>
    <h3>{e(m['titel'])}</h3>
    <div class="mehr">Ansehen <i>{sym('pfeil')}</i></div>
  </div>
</a>"""


def kartenreihe(r, maschinen, titel, marke_text, alle_link, alle_text, hell=True):
    karten = "\n".join(mkarte(m, r) for m in maschinen)
    return f"""<section class="abschnitt {'hell' if hell else 'weiss'}" data-reihe>
  <div class="huelle">
    <div class="abschnitt-kopf">
      <div><div class="marke">{e(marke_text)}</div><h2 class="wort-auf">{titel}</h2></div>
      <div class="reihe-steuer"><button class="rund" type="button" data-zurueck aria-label="Zurück">{sym('links')}</button><button class="rund" type="button" data-weiter aria-label="Weiter">{sym('rechts')}</button></div>
    </div>
    <div class="karten-reihe" data-staffel=".06">{karten}</div>
    <p style="margin-top:28px"><a class="knopf knopf-rahmen" href="{alle_link}">{e(alle_text)} {sym('pfeil', 'pfeil')}</a></p>
  </div>
</section>"""


def mietkauf(r, mit_id=True):
    vorteile = ["Sofort starten, in festen Raten zahlen", "Liquidität schonen", "Mietkauf: späterer Eigentumserwerb", "Leasing: flexible Laufzeiten"]
    li = "".join(f'<li data-auf style="--d:{i * .08:.2f}s"><span class="haken"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg></span>{e(v)}</li>' for i, v in enumerate(vorteile))
    betreff = "mailto:" + MAIL + "?subject=" + "Anfrage%20Mietkauf%20%2F%20Leasing"
    return f"""<section class="abschnitt dunkel mietkauf"{' id="mietkauf"' if mit_id else ''}>
  {rotor("rotor rotor-deko")}
  <div class="huelle">
    <div>
      <div class="marke">Finanzierung</div>
      <h2 class="wort-auf" style="margin-bottom:26px">Mietkauf <em>&amp;</em> Leasing</h2>
      <p class="einleitung leise" data-auf>Ab sofort bieten wir für alle HELTEK / KILIA Kutter, Wölfe und Korimaten flexible Mietkauf- und Leasingmodelle an.</p>
      <p class="leise" data-auf style="--d:.1s">Jetzt beraten lassen – wir erstellen Ihnen schnell ein passendes Angebot.</p>
      <div class="knopfreihe" data-auf style="--d:.2s;margin-top:30px"><a class="knopf knopf-rot" href="{betreff}">Angebot anfragen {sym('pfeil', 'pfeil')}</a><a class="knopf knopf-rahmen" href="tel:{TEL_LINK}">{sym('tel')} {TEL_ANZEIGE}</a></div>
      <p class="zusatz" data-auf style="--d:.3s">HELTEK Maschinenbau – Wir sind Ihre Finanzierungslösung.</p>
    </div>
    <ul class="vorteile">{li}</ul>
  </div>
</section>"""


def zeiten_liste():
    return ('<dl class="zeiten"><dt data-tag="1,2,3,4">Mo – Do</dt><dd data-tag="1,2,3,4">08:00 – 17:00 Uhr</dd>'
            '<dt data-tag="5">Fr</dt><dd data-tag="5">08:00 – 13:00 Uhr</dd><dt data-tag="6,0">Sa – So</dt><dd data-tag="6,0">geschlossen</dd></dl>')


def kontakt_block(r, ueberschrift="Sprechen Sie mit uns."):
    aussen = "".join(f'<li><a href="{u}" rel="noopener" target="_blank">{sym(k) if k in ("instagram", "youtube") else sym("laden")}{e(n)}</a></li>' for k, (n, u) in LINKS_AUSSEN.items())
    return f"""<section class="abschnitt dunkel kontakt-gross">
  <div class="huelle">
    <div>
      <div class="marke">Kontakt</div>
      <h2 class="wort-auf" style="margin-bottom:22px">{ueberschrift}</h2>
      <p class="leise einleitung" data-auf>Haben Sie Produktanfragen oder Anregungen? Rufen Sie uns an oder schreiben Sie uns eine E-Mail. Wir melden uns umgehend bei Ihnen.</p>
      <a class="telefon-gross" href="tel:{TEL_LINK}" data-auf>{TEL_ANZEIGE}</a>
      <ul class="kontaktliste" data-auf style="--d:.1s">
        <li><span class="t">E-Mail</span><a href="mailto:{MAIL}">{MAIL}</a></li>
        <li><span class="t">Telefax</span><span>{FAX}</span></li>
        <li><span class="t">Öffnungszeiten</span><div><p class="status" data-offen hidden><i></i><span></span></p>{zeiten_liste()}</div></li>
      </ul>
    </div>
    <aside class="ortkarte" data-auf="rechts">
      {rotor("rotor rotor-deko")}
      <h3>Unser Standort</h3>
      <address>{e(FIRMA)}<br>{e(STRASSE)}<br>{e(PLZ_ORT)}</address>
      <div class="knopfreihe"><a class="knopf knopf-rot knopf-klein" href="{ROUTE}" rel="noopener" target="_blank">{sym('ort')} Route planen</a><a class="knopf knopf-rahmen knopf-klein" href="{r}kontakt/#formular">Anfrage schreiben</a></div>
      <div class="auch-bei"><p>Unsere Gebrauchtmaschinen finden Sie auch bei</p><ul>{aussen}</ul></div>
    </aside>
  </div>
</section>"""


def seitenkopf(r, marke_text, titel, einleitung, bild=None, pfad_teile=None, knoepfe=""):
    b = f'<div class="bild" data-tiefe=".18" style="background-image:url({r}assets/img/{bild}-2000.jpg)"></div>' if bild else ""
    pfad = ""
    if pfad_teile:
        teile = [f'<a href="{r or "./"}">Start</a>'] + [f'<a href="{r + z}">{e(n)}</a>' if z else f'<span aria-current="page">{e(n)}</span>' for z, n in pfad_teile]
        pfad = '<nav class="pfad auftritt" aria-label="Brotkrumen">' + ' <span aria-hidden="true">/</span> '.join(teile) + '</nav>'
    return f"""<section class="seitenkopf">
  {b}{rotor("rotor rotor-deko")}
  <div class="huelle">
    {pfad}
    <div class="marke auftritt" style="--d:.05s">{e(marke_text)}</div>
    <h1><span class="zeile"><span>{titel}</span></span></h1>
    {f'<p class="einleitung auftritt" style="--d:.25s">{einleitung}</p>' if einleitung else ''}
    {f'<div class="knopfreihe auftritt" style="--d:.35s">{knoepfe}</div>' if knoepfe else ''}
  </div>
</section>"""


# ── Startseite ───────────────────────────────────────────────────────────────────────
def startseite():
    r = ""
    n = len(MASCHINEN)
    band = "".join(f"<span>{w}</span>" for w in ["Kutter", "Vakuumkutter", "Fleischwölfe", "Autoklaven", "Füller", "Speckschneider", "Mischer", "Ersatzteile", "Kundendienst"])
    zahlen = [("1932", "Tradition der Marke KILIA"), ("2016", "HELTEK übernimmt die Marke KILIA"), ("2021", "Offizieller Vertriebspartner für KORIMAT-Autoklaven"), (str(n), "Maschinen im aktuellen Angebot")]
    zahl_html = "".join(f'<div class="zahl" data-auf style="--d:{i * .1:.1f}s"><div class="zaehlwerk" data-wert="{w}">{w}</div><p>{e(t)}</p></div>' for i, (w, t) in enumerate(zahlen))
    partner = "".join(f'<div class="partnerkachel"><img src="assets/img/{f}" alt="{e(a)}" loading="lazy" height="80"></div>' for f, a in PARTNER)
    partner_kopie = "".join(f'<div class="partnerkachel" aria-hidden="true"><img src="assets/img/{f}" alt="" loading="lazy" height="80"></div>' for f, a in PARTNER)
    leistungen = [
        ("neu", "Neumaschinen", "Hochwertige Kutter, Vakuumkutter und Fleischwölfe unter der Marke HELTEK-KILIA – für Fleischereien, Handwerksbetriebe und die industrielle Lebensmittelverarbeitung."),
        ("ueberholt", "Werksüberholungen", "Professionell überholte Maschinen aus unserer Werkstatt. Neu- und Gebrauchtmaschinen der Marke KILIA führen wir vollständig."),
        ("teile", "Original-Ersatzteile", "Alle Ersatzteile für KILIA-Maschinen und KORIMAT-Autoklaven aus einem großen Ersatzteilsortiment."),
        ("dienst", "Kundendienst", "Reparatur, Montage und Wartung durch unser Fachpersonal. Auch die wiederkehrenden Prüfungen der Autoklaven übernehmen wir."),
        ("plan", "Planung", "Sie planen eine Fleischerei oder Großküche? Wir stellen sie Ihnen zusammen – ganz nach Ihren Erwartungen und Anforderungen."),
    ]
    leist_html = "".join(
        f'<article class="leistung" style="--d:{i * .08:.2f}s"><span class="nr">0{i + 1}</span><svg class="symbol" viewBox="0 0 56 56" aria-hidden="true">{LEISTUNG_SYM[k]}</svg><h3>{e(t)}</h3><p>{e(p)}</p></article>'
        for i, (k, t, p) in enumerate(leistungen))
    stimmen = "".join(
        f'<figure class="stimme" data-auf style="--d:{(i % 3) * .08:.2f}s"><div class="sterne" aria-label="5 von 5 Sternen">{STERN * 5}</div><blockquote>{e(t)}</blockquote><figcaption>{e(name)}</figcaption></figure>'
        for i, (_, t, name) in enumerate(REZENSIONEN))
    inhalt = f"""
<section class="buehne">
  <div class="buehne-bild" data-tiefe=".25" style="background-image:url(assets/img/halle-2000.jpg)"></div>
  <div class="huelle">
    <div>
      <div class="marke auftritt">Fleischerei- &amp; Großküchentechnik<span class="nur-gross">· Bad Fallingbostel</span></div>
      <h1 class="buehne-titel"><span class="zeile"><span>Qualitäts-</span></span><span class="zeile"><span>produkte</span></span><span class="zeile"><span>für <em>Profis.</em></span></span></h1>
      <p class="einleitung auftritt" style="--d:.35s"><strong>HELTEK Maschinenbau</strong> – Ihr Spezialist für KILIA-Fleischereimaschinen und KORIMAT-Autoklaven. Neumaschinen, Werksüberholungen, Original-Ersatzteile und Kundendienst aus einer Hand.</p>
      <div class="knopfreihe auftritt" style="--d:.5s"><a class="knopf knopf-rot" href="maschinen/">Maschinen ansehen {sym('pfeil', 'pfeil')}</a><a class="knopf knopf-rahmen" href="kontakt/">Beratung anfragen</a></div>
    </div>
    <div class="buehne-rotor">
      <span class="ring ring-2" aria-hidden="true"></span><span class="ring ring-1" aria-hidden="true"></span>
      {rotor("rotor", stahl=True)}
      <div class="drehzahl" aria-hidden="true">Messerwelle <b>480</b> UpM</div>
    </div>
  </div>
  <div class="scrollhinweis" aria-hidden="true"><i></i>Scrollen</div>
  <div class="laufband" aria-hidden="true"><div class="laufband-spur">{band}{band}</div></div>
</section>

<section class="dunkel zahlen" aria-label="HELTEK in Zahlen">
  <div class="huelle">{zahl_html}</div>
</section>

<section class="abschnitt hell" id="marken">
  <div class="huelle">
    <div class="abschnitt-kopf">
      <div><div class="marke">Unsere Marken</div><h2 class="wort-auf">Zwei Namen, die Profis kennen.</h2>
      <p class="leise" data-auf>Seit 2016 ist die HELTEK Maschinenbau GmbH &amp; Co. KG Inhaber der traditionsreichen Marke KILIA. Seit 2021 sind wir offizieller Vertriebspartner für KORIMAT-Autoklaven.</p></div>
    </div>
    <div class="marken">
      <a class="markenkarte" href="kilia/" data-auf>
        <div class="bild" style="background-image:url(assets/img/sortiment-1000.jpg)"></div>
        <span class="jahr-gross" aria-hidden="true">1932</span>
        <img class="markenlogo" src="assets/img/logo-kilia.png" alt="KILIA" width="498" height="112">
        <h3>Wir sind KILIA.</h3>
        <p>Wir führen alle Neu- und Gebrauchtmaschinen sowie Original-Ersatzteile der Marke KILIA. Sie suchen etwas Spezielles oder benötigen kompetente Beratung? Unsere Spezialisten unterstützen Sie.</p>
        <ul class="liste-punkte"><li>Kutter</li><li>Vakuumkutter</li><li>Fleischwölfe</li><li>Ersatzteile</li></ul>
        <span class="textlink">Mehr zu KILIA {sym('pfeil')}</span>
      </a>
      <a class="markenkarte" href="korimat/" data-auf style="--d:.12s">
        <div class="bild" style="background-image:url(assets/img/service-werkstatt-1000.jpg)"></div>
        <span class="jahr-gross" aria-hidden="true">2021</span>
        <img class="markenlogo" src="assets/img/logo-korimat.png" alt="KORIMAT" width="600" height="246">
        <h3>Direkter Vertriebspartner.</h3>
        <p>Seit über 60 Jahren haben sich die KORIMAT-Autoklaven in Fleischereien und Großküchen etabliert. Wir führen das gesamte Produktportfolio – vom KA 160 bis zum KA 380.</p>
        <ul class="liste-punkte"><li>KA 160</li><li>KA 240</li><li>KA 380</li><li>Speisetransportbehälter</li></ul>
        <span class="textlink">Mehr zu KORIMAT {sym('pfeil')}</span>
      </a>
    </div>
    <div class="partner">
      <div class="partner-titel">Qualitätsprodukte ausgewählter Partnerfirmen</div>
      <div class="partnerband"><div class="laufband-spur">{partner}{partner_kopie}</div></div>
    </div>
  </div>
</section>

<section class="abschnitt dunkel" id="leistungen">
  <div class="huelle">
    <div class="abschnitt-kopf">
      <div><div class="marke">Leistungen</div><h2 class="wort-auf">Alles aus einer Hand.</h2>
      <p class="leise" data-auf>Mehr Auswahl, perfekt abgestimmte Lösungen und ein zentraler Ansprechpartner für Ihre Technik – von der Beratung über Lieferung und Inbetriebnahme bis zur Wartung.</p></div>
      <a class="knopf knopf-rahmen" href="kundendienst/" data-auf>Zum Kundendienst {sym('pfeil', 'pfeil')}</a>
    </div>
    <div class="leistungen">{leist_html}</div>
  </div>
</section>

{kartenreihe(r, MASCHINEN[:10], "Frisch im Bestand.", "Maschinen", "maschinen/", f"Alle {n} Maschinen ansehen")}

{mietkauf(r)}

<section class="abschnitt hell" id="stimmen">
  <div class="huelle">
    <div class="abschnitt-kopf"><div><div class="marke">Rezensionen</div><h2 class="wort-auf">Was Kunden sagen.</h2></div></div>
    <div class="stimmen">{stimmen}</div>
  </div>
</section>

{kontakt_block(r)}
"""
    ld = {"@context": "https://schema.org", "@type": "LocalBusiness", "name": FIRMA, "url": BASIS + "/", "telephone": "+49 5163 91000",
          "email": MAIL, "image": BASIS + "/assets/img/og.jpg",
          "address": {"@type": "PostalAddress", "streetAddress": STRASSE, "postalCode": "29683", "addressLocality": "Bad Fallingbostel", "addressCountry": "DE"},
          "openingHoursSpecification": [
              {"@type": "OpeningHoursSpecification", "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday"], "opens": "08:00", "closes": "17:00"},
              {"@type": "OpeningHoursSpecification", "dayOfWeek": "Friday", "opens": "08:00", "closes": "13:00"}],
          "sameAs": [u for _, u in LINKS_AUSSEN.values()]}
    vorlade = '<link rel="preload" as="image" href="assets/img/halle-2000.jpg">\n'
    return rahmen("index.html", "HELTEK Maschinenbau | Fleischerei- und Großküchentechnik",
                  "HELTEK Maschinenbau in Bad Fallingbostel: KILIA-Kutter, Vakuumkutter und Fleischwölfe, KORIMAT-Autoklaven, Gebrauchtmaschinen, Ersatzteile, Kundendienst sowie Mietkauf und Leasing.",
                  inhalt, aktiv="", extra_kopf=vorlade, jsonld=ld)


# ── Katalog ──────────────────────────────────────────────────────────────────────────
def katalog():
    r = "../"
    zaehl = {k: sum(1 for m in MASCHINEN if m["kat"] == k) for k, _, _ in KATEGORIEN}
    chips = f'<button class="chip" type="button" data-filter="alle" aria-pressed="true">Alle <small>{len(MASCHINEN)}</small></button>' + "".join(
        f'<button class="chip" type="button" data-filter="{k}" aria-pressed="false">{e(n)} <small>{zaehl[k]}</small></button>' for k, n, _ in KATEGORIEN if zaehl[k])
    marken = sorted({m["marke"] for m in MASCHINEN if m["marke"]}, key=lambda x: (x not in ("KILIA", "KORIMAT"), x.lower()))
    wahl = '<option value="">Alle Marken</option>' + "".join(f'<option value="{e(mk)}">{e(mk)}</option>' for mk in marken)
    karten = "\n".join(mkarte(m, r, lazy=i > 7) for i, m in enumerate(MASCHINEN))
    inhalt = f"""
{seitenkopf(r, "Neu- und Gebrauchtmaschinen", "Maschinen", "Kutter, Fleischwölfe, Füller, Autoklaven und mehr aus unserem Bestand. Sie finden nicht, was Sie suchen? Rufen Sie uns an – wir haben ein umfangreiches Portfolio.", bild="halle", pfad_teile=[("", "Maschinen")])}
<div class="werkzeugleiste">
  <div class="huelle">
    <div class="chips" role="group" aria-label="Nach Art filtern">{chips}</div>
    <select class="markenwahl" id="marke" aria-label="Nach Marke filtern">{wahl}</select>
    <label class="suche"><span class="sr">Maschinen durchsuchen</span>{sym('lupe')}<input id="suche" type="search" placeholder="Suchen, z. B. 65 Liter" autocomplete="off"></label>
    <span class="treffer" id="treffer" aria-live="polite">{len(MASCHINEN)} Maschinen</span>
  </div>
</div>
<section class="katalog hell">
  <div class="huelle">
    <div class="raster" id="raster">{karten}</div>
    <div class="leer" id="leer"><strong>Keine passende Maschine gefunden.</strong>Ändern Sie die Auswahl oder rufen Sie uns an: <a href="tel:{TEL_LINK}">{TEL_ANZEIGE}</a></div>
  </div>
</section>
{mietkauf(r, mit_id=False)}
"""
    return rahmen("maschinen/index.html", "Maschinen: Kutter, Wölfe, Füller, Autoklaven",
                  f"{len(MASCHINEN)} Fleischereimaschinen im Angebot: KILIA-Kutter und Fleischwölfe, KORIMAT-Autoklaven, Frey-Füller, TREIF-Speckschneider und mehr bei HELTEK Maschinenbau.",
                  inhalt, aktiv="maschinen/")


def maschinenseite(m):
    r = "../../"
    bilder = [{"gross": f"{r}assets/maschinen/{m['quelle_slug']}/{b['nr']:02d}-1600.jpg", "alt": f"{m['titel']} – Foto {i + 1}"} for i, b in enumerate(m["bilder"])]
    erstes = bilder[0]
    daumen = "".join(
        f'<button type="button" aria-label="Foto {i + 1} zeigen" aria-current="{"true" if i == 0 else "false"}"><img src="{r}assets/maschinen/{m["quelle_slug"]}/{b["nr"]:02d}-720.jpg" alt="" loading="lazy" decoding="async"></button>'
        for i, b in enumerate(m["bilder"]))
    pfeile = (f'<button class="galerie-pfeil zurueck" type="button" aria-label="Vorheriges Foto">{sym("links")}</button>'
              f'<button class="galerie-pfeil weiter" type="button" aria-label="Nächstes Foto">{sym("rechts")}</button>') if len(bilder) > 1 else ""
    betreff = "mailto:" + MAIL + "?subject=" + quote(f"Anfrage: {m['titel']}")
    verwandt = [x for x in MASCHINEN if x["kat"] == m["kat"] and x is not m][:4]
    if len(verwandt) < 4:
        verwandt += [x for x in MASCHINEN if x is not m and x not in verwandt][:4 - len(verwandt)]
    beschreibung = m["text"] or "<p>Zu dieser Maschine geben wir Ihnen gern telefonisch oder per E-Mail Auskunft.</p>"
    b0 = m["bilder"][0]
    inhalt = f"""
<article class="maschine hell">
  <div class="huelle">
    <nav class="pfad" aria-label="Brotkrumen"><a href="{r}">Start</a> <span aria-hidden="true">/</span> <a href="{r}maschinen/">Maschinen</a> <span aria-hidden="true">/</span> <a href="{r}maschinen/#kategorie={m['kat']}">{e(KAT_NAME[m['kat']])}</a></nav>
    <div class="maschine-gitter">
      <div class="galerie" data-galerie='{e(json.dumps(bilder, ensure_ascii=False))}'>
        <div class="galerie-haupt" role="button" tabindex="0" aria-label="Foto vergrößern">
          <img src="{erstes['gross']}" alt="{e(erstes['alt'])}" width="1600" height="{round(1600 * b0['h'] / b0['b'])}" fetchpriority="high">
          <span class="zaehler">1 / {len(bilder)}</span><span class="vergroessern">{sym('gross')}</span>
        </div>
        {pfeile}
        {'<div class="daumen">' + daumen + '</div>' if len(bilder) > 1 else ''}
      </div>
      <aside class="infokarte">
        <div class="etiketten"><span class="etikett">{e(KAT_NAME[m['kat']])}</span>{f'<span class="etikett marke-e">{e(m["marke"])}</span>' if m['marke'] else ''}</div>
        <h1>{e(m['titel'])}</h1>
        <dl class="fakten">
          <div><dt>Art</dt><dd>{e(KAT_NAME[m['kat']])}</dd></div>
          {f'<div><dt>Marke</dt><dd>{e(m["marke"])}</dd></div>' if m['marke'] else ''}
          <div><dt>Fotos</dt><dd>{len(bilder)}</dd></div>
          <div><dt>Standort</dt><dd>Bad Fallingbostel</dd></div>
        </dl>
        <hr>
        <a class="knopf knopf-rot" href="{betreff}">Anfrage per E-Mail {sym('pfeil', 'pfeil')}</a>
        <a class="knopf knopf-rahmen" href="tel:{TEL_LINK}">{sym('tel')} {TEL_ANZEIGE}</a>
        <p class="klein">Mo–Do 8–17 Uhr, Fr 8–13 Uhr. Fragen Sie auch nach <a href="{r}#mietkauf">Mietkauf &amp; Leasing</a>.</p>
      </aside>
    </div>
    <section class="beschreibung" aria-labelledby="beschreibung-titel">
      <h2 id="beschreibung-titel">Beschreibung</h2>
      <div class="fliesstext">{beschreibung}</div>
    </section>
  </div>
</article>
<section class="verwandt hell" data-reihe>
  <div class="huelle">
    <div class="abschnitt-kopf"><div><div class="marke">Weitere Maschinen</div><h2>Das könnte auch passen.</h2></div>
    <div class="reihe-steuer"><button class="rund" type="button" data-zurueck aria-label="Zurück">{sym('links')}</button><button class="rund" type="button" data-weiter aria-label="Weiter">{sym('rechts')}</button></div></div>
    <div class="karten-reihe">{''.join(mkarte(x, r) for x in verwandt)}</div>
  </div>
</section>
<div class="betrachter" id="betrachter" role="dialog" aria-modal="true" aria-label="Fotos von {e(m['titel'])}" aria-hidden="true">
  <div class="betrachter-kopf"><span class="betrachter-zahl">1 / {len(bilder)}</span><button type="button" data-zu aria-label="Schließen">{sym('zu')}</button></div>
  <div class="betrachter-buehne"><img src="" alt=""></div>
  <div class="betrachter-fuss"><button type="button" data-btz aria-label="Vorheriges Foto">{sym('links')}</button><button type="button" data-btw aria-label="Nächstes Foto">{sym('rechts')}</button></div>
</div>
"""
    kurz = m["kurz"][:150].rsplit(" ", 1)[0] + " …" if len(m["kurz"]) > 150 else m["kurz"]
    besch = f"{m['titel']} – {KAT_NAME[m['kat']]} bei HELTEK Maschinenbau, Bad Fallingbostel. {kurz}".strip()
    return rahmen(f"maschinen/{m['slug']}/index.html", m["titel"], besch[:300], inhalt, aktiv="maschinen/")


# ── KILIA ────────────────────────────────────────────────────────────────────────────
def kilia():
    r = "../"
    km = [m for m in MASCHINEN if m["marke"] == "KILIA"]
    punkte = ["Neumaschinen: Kutter, Vakuumkutter und Fleischwölfe", "Professionelle Werksüberholungen", "Original-Ersatzteile für alle KILIA-Maschinen",
              "Reparaturen und technischer Kundendienst", "Beratung durch unsere Spezialisten", "Mietkauf und Leasing für Kutter und Wölfe"]
    li = "".join(f'<li data-auf style="--d:{i * .06:.2f}s"><span class="haken"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg></span><span>{e(p)}</span></li>' for i, p in enumerate(punkte))
    inhalt = f"""
{seitenkopf(r, "Marke · seit 2016 bei HELTEK", "KILIA", "Seit 2016 ist die HELTEK Maschinenbau GmbH &amp; Co. KG Inhaber der traditionsreichen Marke KILIA. Unter der Marke HELTEK-KILIA bieten wir hochwertige Kutter, Vakuumkutter und Fleischwölfe.", bild="halle", pfad_teile=[("", "KILIA")], knoepfe=f'<a class="knopf knopf-rot" href="{r}maschinen/#marke=KILIA">KILIA-Maschinen ansehen {sym("pfeil", "pfeil")}</a><a class="knopf knopf-rahmen" href="http://www.kilia.de" rel="noopener" target="_blank">kilia.de {sym("aussen")}</a>')}
<section class="abschnitt hell">
  <div class="huelle zweispaltig">
    <div>
      <div class="marke">Qualitätsprodukte für Profis</div>
      <h2 class="wort-auf" style="margin-bottom:24px">Wir sind KILIA.</h2>
      <p class="einleitung" data-auf>KILIA ist eine der führenden Marken im Bereich Fleischerei- und Großküchenmaschinen. Im Jahr 2016 haben wir die Marke übernommen und führen das komplette Sortiment.</p>
      <p class="leise" data-auf style="--d:.1s">Neben den Neu- und Gebrauchtmaschinen finden Sie bei uns alle Ersatzteile der KILIA-Maschinen. Bei Störungen erreichen Sie unseren Kundendienst und unsere Techniker direkt.</p>
    </div>
    <div class="bildrahmen" data-auf="zoom"><img src="{r}assets/img/sortiment-2000.jpg" alt="Das KILIA-Maschinensortiment: Kutter, Vakuumkutter und Fleischwölfe" loading="lazy" data-tiefe=".05"></div>
  </div>
</section>
<section class="abschnitt weiss">
  <div class="huelle">
    <div class="abschnitt-kopf"><div><div class="marke">Geschichte</div><h2 class="wort-auf">Tradition trifft Technik.</h2></div></div>
    <ol class="zeitstrahl">
      <li data-auf><b>1932</b><p>Seit 1932 steht KILIA für Fleischereimaschinen – so steht es bis heute im Markenzeichen.</p></li>
      <li data-auf style="--d:.15s"><b>2016</b><p>Die HELTEK Maschinenbau GmbH &amp; Co. KG wird Inhaber der Marke KILIA.</p></li>
      <li data-auf style="--d:.3s"><b>Heute</b><p>Neumaschinen, Werksüberholungen, Original-Ersatzteile, Reparaturen und Kundendienst aus Bad Fallingbostel.</p></li>
    </ol>
  </div>
</section>
<section class="abschnitt hell">
  <div class="huelle">
    <div class="abschnitt-kopf"><div><div class="marke">Unser Angebot</div><h2 class="wort-auf">Rund um KILIA.</h2></div></div>
    <ul class="leistungsliste">{li}</ul>
  </div>
</section>
{kartenreihe(r, km[:10], "KILIA im Bestand.", "Aus unserem Angebot", f"{r}maschinen/#marke=KILIA", f"Alle {len(km)} KILIA-Maschinen", hell=False)}
{mietkauf(r, mit_id=False)}
{kontakt_block(r, "Fragen zu KILIA?")}
"""
    return rahmen("kilia/index.html", "KILIA: Kutter, Vakuumkutter und Fleischwölfe",
                  "HELTEK Maschinenbau ist seit 2016 Inhaber der Marke KILIA: Neu- und Gebrauchtmaschinen, Werksüberholungen, Original-Ersatzteile und Kundendienst für KILIA-Kutter und Fleischwölfe.",
                  inhalt, aktiv="kilia/")


# ── KORIMAT ──────────────────────────────────────────────────────────────────────────
def korimat():
    r = "../"
    km = [m for m in MASCHINEN if m["marke"] == "KORIMAT"]
    modelle = [("ka160", "KA 160", "ka160.png", "https://korimat-gmbh.de/produkte/korimat/korimat-ka-160/"),
               ("ka240", "KA 240", "ka240.png", "https://korimat-gmbh.de/produkte/korimat/korimat-ka-240/"),
               ("ka380", "KA 380", "ka380.png", "https://korimat-gmbh.de/produkte/korimat/korimat-ka-380/")]
    reiter = "".join(f'<button type="button" role="tab" id="reiter-{k}" aria-controls="tafel-{k}" aria-selected="{"true" if i == 0 else "false"}" tabindex="{0 if i == 0 else -1}" data-modell="{k}">{n}</button>' for i, (k, n, _, _) in enumerate(modelle))
    bilder = "".join(f'<img src="{r}assets/img/{b}" alt="KORIMAT {n}" data-modell="{k}" class="{"an" if i == 0 else ""}" loading="lazy">' for i, (k, n, b, _) in enumerate(modelle))
    tafeln = "".join(f'<div class="modell-text" role="tabpanel" id="tafel-{k}" aria-labelledby="reiter-{k}"{"" if i == 0 else " hidden"}><h3>KORIMAT {n}</h3><p class="leise">Neu- und Gebrauchtgeräte, Ersatzteile und Kundendienst für den KORIMAT {n} – direkt von uns als Vertriebspartner.</p><p><a class="textlink" href="{u}" rel="noopener" target="_blank">Technische Daten beim Hersteller {sym("aussen")}</a></p></div>' for i, (k, n, _, u) in enumerate(modelle))
    punkte = ["Neu- und Gebrauchtgeräte vom KA 160 über KA 240 bis KA 380", "Die altbewährten Speisetransportbehälter", "Alle KORIMAT-Ersatzteile im Sortiment",
              "Kundendienst für alle Geräte", "Wiederkehrende Prüfungen der Autoklaven durch unsere qualifizierten Mitarbeiter", "Mietkauf und Leasing für Korimaten"]
    li = "".join(f'<li data-auf style="--d:{i * .06:.2f}s"><span class="haken"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg></span><span>{e(p)}</span></li>' for i, p in enumerate(punkte))
    inhalt = f"""
{seitenkopf(r, "Vertriebspartner · seit 2021", "KORIMAT", "Seit über 60 Jahren haben sich die KORIMAT-Autoklaven in Fleischereien und Großküchen etabliert – national wie international. Seit 2021 sind wir direkter Vertriebspartner.", bild="service-werkstatt", pfad_teile=[("", "KORIMAT")], knoepfe=f'<a class="knopf knopf-rot" href="{r}kontakt/">Jetzt anfragen {sym("pfeil", "pfeil")}</a><a class="knopf knopf-rahmen" href="{r}maschinen/#kategorie=autoklaven">Autoklaven im Bestand</a>')}
<section class="abschnitt hell" data-modelle>
  <div class="huelle modelle">
    <div class="modell-buehne" data-auf="zoom">{bilder}</div>
    <div>
      <div class="marke">Die Modelle</div>
      <h2 class="wort-auf" style="margin-bottom:28px">Vom KA 160 bis zum KA 380.</h2>
      <div class="modell-reiter" role="tablist" aria-label="KORIMAT-Modelle">{reiter}</div>
      {tafeln}
      <p class="leise" style="margin-top:24px">Die KORIMAT-Autoklaven genießen den allerhöchsten Standard und werden bis heute stetig weiterentwickelt.</p>
    </div>
  </div>
</section>
<section class="abschnitt weiss">
  <div class="huelle">
    <div class="abschnitt-kopf"><div><div class="marke">Unser Angebot</div><h2 class="wort-auf">Alles für Ihren Autoklaven.</h2>
    <p class="leise" data-auf>Selbstverständlich nehmen wir auch gerne Bestellungen für Ersatzteile entgegen: <a href="mailto:info@hammer-dorfmark.de?subject=Anfrage%20Ersatzteile">info@hammer-dorfmark.de</a></p></div></div>
    <ul class="leistungsliste">{li}</ul>
  </div>
</section>
{kartenreihe(r, km[:10], "KORIMAT im Bestand.", "Aus unserem Angebot", f"{r}maschinen/#kategorie=autoklaven", f"Alle {len(km)} Autoklaven")}
{kontakt_block(r, "Fragen zu KORIMAT?")}
"""
    return rahmen("korimat/index.html", "KORIMAT-Autoklaven KA 160, KA 240, KA 380",
                  "HELTEK Maschinenbau ist direkter Vertriebspartner für KORIMAT-Autoklaven: KA 160, KA 240, KA 380, Speisetransportbehälter, Ersatzteile, Kundendienst und wiederkehrende Prüfungen.",
                  inhalt, aktiv="korimat/")


# ── Kundendienst ─────────────────────────────────────────────────────────────────────
def kundendienst():
    r = "../"
    punkte = ["Reparatur von Fleischereimaschinen und Großküchengeräten", "Montage und Inbetriebnahme", "Wartung durch unser Fachpersonal",
              "Großes Ersatzteilsortiment", "Wiederkehrende Prüfungen für KORIMAT-Autoklaven", "Beratung bei Ihren Planungen"]
    li = "".join(f'<li data-auf style="--d:{i * .06:.2f}s"><span class="haken"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg></span><span>{e(p)}</span></li>' for i, p in enumerate(punkte))
    schritte = [("Melden", "Rufen Sie uns an oder schreiben Sie uns, was die Maschine macht – oder eben nicht mehr macht."),
                ("Klären", "Unsere Techniker grenzen den Fehler ein und sagen Ihnen, welches Ersatzteil oder welcher Einsatz nötig ist."),
                ("Instandsetzen", "Wir reparieren, montieren und warten – mit Original-Ersatzteilen aus unserem Lager."),
                ("Weiterarbeiten", "Ihre Maschine läuft wieder. Für Wartungen und Prüfungen sind wir auch danach für Sie da.")]
    sch = "".join(f'<li data-auf style="--d:{i * .1:.1f}s"><h3>{e(t)}</h3><p>{e(p)}</p></li>' for i, (t, p) in enumerate(schritte))
    inhalt = f"""
{seitenkopf(r, "Service", "Kundendienst", "Für die von uns gelieferten Geräte und Maschinen übernehmen unsere Servicemitarbeiter den Kundendienst. Ihre Anforderung ist unsere Herausforderung.", bild="service-werkstatt", pfad_teile=[("", "Kundendienst")], knoepfe=f'<a class="knopf knopf-rot" href="tel:{TEL_LINK}">{sym("tel")} {TEL_ANZEIGE}</a><a class="knopf knopf-rahmen" href="{r}kontakt/">Anfrage schreiben</a>')}
<section class="abschnitt hell">
  <div class="huelle zweispaltig">
    <div>
      <div class="marke">Was wir tun</div>
      <h2 class="wort-auf" style="margin-bottom:24px">Wir halten Ihre Produktion am Laufen.</h2>
      <p class="einleitung" data-auf>Wir verfügen über ein großes Ersatzteilsortiment. Mit unserem Fachpersonal reparieren, montieren und warten wir Ihre Fleischereimaschinen und Großküchengeräte.</p>
      <p class="leise" data-auf style="--d:.1s">Unsere Arbeit umfasst die Beratung bei Ihren Planungen, die Lieferung und die Inbetriebnahme der Geräte. Für Wartungs- und Reparaturarbeiten steht Ihnen unser Kundendienst zur Verfügung.</p>
    </div>
    <ul class="leistungsliste" style="grid-template-columns:1fr">{li}</ul>
  </div>
</section>
<section class="abschnitt weiss">
  <div class="huelle">
    <div class="abschnitt-kopf"><div><div class="marke">So läuft es</div><h2 class="wort-auf">In vier Schritten zurück in Betrieb.</h2></div></div>
    <ol class="schritte">{sch}</ol>
  </div>
</section>
{mietkauf(r, mit_id=False)}
{kontakt_block(r, "Störung? Rufen Sie an.")}
"""
    return rahmen("kundendienst/index.html", "Kundendienst: Reparatur, Wartung, Ersatzteile",
                  "Kundendienst von HELTEK Maschinenbau: Reparatur, Montage und Wartung von Fleischereimaschinen und Großküchengeräten, großes Ersatzteilsortiment, wiederkehrende Prüfungen für KORIMAT-Autoklaven.",
                  inhalt, aktiv="kundendienst/")


# ── Kontakt ──────────────────────────────────────────────────────────────────────────
def kontakt():
    r = "../"
    anliegen = ["Maschine kaufen", "Ersatzteile", "Kundendienst / Reparatur", "Mietkauf & Leasing", "Planung", "Sonstiges"]
    opt = "".join(f"<option>{e(a)}</option>" for a in anliegen)
    inhalt = f"""
{seitenkopf(r, "Wir sind für Sie da", "Kontakt", "Haben Sie Produktanfragen oder Anregungen? Schreiben Sie uns eine E-Mail oder rufen Sie uns an. Wir melden uns umgehend bei Ihnen.", pfad_teile=[("", "Kontakt")])}
{kontakt_block(r, "Rufen Sie uns an.")}
<section class="abschnitt hell" id="formular">
  <div class="huelle zweispaltig" style="align-items:start">
    <div>
      <div class="marke">Ihre Anfrage</div>
      <h2 class="wort-auf" style="margin-bottom:22px">Schreiben Sie uns.</h2>
      <p class="einleitung" data-auf>Füllen Sie die Felder aus und tippen Sie auf „E-Mail erstellen“. Ihr E-Mail-Programm öffnet sich mit der fertigen Nachricht an {MAIL} – Sie schicken sie selbst ab.</p>
      <p class="leise" data-auf style="--d:.1s">Auf dieser Website wird dabei nichts gespeichert oder übertragen.</p>
    </div>
    <form class="formular" id="anfrage" data-auf>
      <div class="feld"><label for="f-name">Name *</label><input id="f-name" name="name" required autocomplete="name"></div>
      <div class="feld"><label for="f-firma">Firma</label><input id="f-firma" name="firma" autocomplete="organization"></div>
      <div class="feld"><label for="f-tel">Telefon</label><input id="f-tel" name="telefon" type="tel" autocomplete="tel"></div>
      <div class="feld"><label for="f-mail">E-Mail</label><input id="f-mail" name="email" type="email" autocomplete="email"></div>
      <div class="feld ganz"><label for="f-anliegen">Anliegen</label><select id="f-anliegen" name="anliegen">{opt}</select></div>
      <div class="feld ganz"><label for="f-nachricht">Nachricht *</label><textarea id="f-nachricht" name="nachricht" required></textarea></div>
      <div class="ganz"><button class="knopf knopf-rot" type="submit">E-Mail erstellen {sym('pfeil', 'pfeil')}</button></div>
      <p class="hinweis ganz" id="anfrage-hinweis" aria-live="polite"></p>
    </form>
  </div>
</section>
"""
    ld = {"@context": "https://schema.org", "@type": "ContactPage", "name": "Kontakt – HELTEK Maschinenbau", "url": BASIS + "/kontakt/"}
    return rahmen("kontakt/index.html", "Kontakt",
                  "Kontakt zu HELTEK Maschinenbau in Bad Fallingbostel: Telefon 05163 91000, info@heltek.de, Westendorfer Straße 51. Mo–Do 8–17 Uhr, Fr 8–13 Uhr.",
                  inhalt, aktiv="kontakt/", jsonld=ld)


# ── Rechtliches ──────────────────────────────────────────────────────────────────────
def alt_rechtstext(name):
    t = (WURZEL / "daten" / "rechtliches" / f"{name}.html").read_text(encoding="utf-8")
    t = t.split("<p>Unsere Gebrauchtmaschinen finden Sie bei:</p>")[0]
    t = t.split("Interesse an dem Produkt")[0]
    t = re.sub(r"^\s*<h2>[^<]*</h2>\s*", "", t)       # Überschrift kommt aus dem Seitenkopf
    t = re.sub(r"<a href=\"[^\"]*\">\s*</a>", "", t)
    return t.strip()


def rechtsseite(pfad, titel, text, beschreibung):
    r = "../"
    inhalt = f"""
{seitenkopf(r, "Rechtliches", titel, "", pfad_teile=[("", titel)])}
<section class="abschnitt hell"><div class="huelle"><div class="rechtstext">{text}</div></div></section>
"""
    return rahmen(pfad, titel, beschreibung, inhalt, ohne_index=pfad.startswith(("impressum", "datenschutz")))


DATENSCHUTZ = f"""
<h2>1. Verantwortlicher</h2>
<p>{e(FIRMA)}<br>{e(STRASSE)}<br>{e(PLZ_ORT)}<br>Telefon: {TEL_ANZEIGE}<br>E-Mail: <a href="mailto:{MAIL}">{MAIL}</a></p>
<p>Vertreten durch die persönlich haftende Gesellschafterin Herold Verwaltungs-GmbH, diese vertreten durch den Geschäftsführer Lars Herold.</p>
<h2>2. Das Wichtigste in Kürze</h2>
<p>Diese Website setzt keine Cookies, verwendet keine Analyse- oder Werbedienste und lädt keine Inhalte von anderen Anbietern nach. Schriften und Bilder liegen auf unserem eigenen Webspace. Es gibt kein Kundenkonto und kein Formular, das Daten an uns überträgt.</p>
<h2>3. Bereitstellung der Website und Server-Protokolle</h2>
<p>Beim Aufruf dieser Website verarbeitet unser Hosting-Anbieter technisch notwendige Daten, die Ihr Browser übermittelt: IP-Adresse, Datum und Uhrzeit, aufgerufene Seite, übertragene Datenmenge, die zuvor besuchte Seite sowie Browser und Betriebssystem. Das ist nötig, um die Seite auszuliefern und ihre Sicherheit zu gewährleisten. Rechtsgrundlage ist Art. 6 Abs. 1 lit. f DSGVO.</p>
<p>Hosting-Anbieter: <strong>[wird vor dem Start eingetragen]</strong></p>
<h2>4. Kontakt per E-Mail und Telefon</h2>
<p>Wenn Sie uns per E-Mail oder Telefon kontaktieren, verarbeiten wir Ihre Angaben (zum Beispiel Name, Firma, Kontaktdaten und den Inhalt Ihrer Anfrage), um Ihr Anliegen zu bearbeiten. Rechtsgrundlage ist Art. 6 Abs. 1 lit. b DSGVO, soweit es um einen Vertrag oder dessen Anbahnung geht, sonst Art. 6 Abs. 1 lit. f DSGVO.</p>
<p>Das Anfrageformular auf der Kontaktseite überträgt keine Daten. Es öffnet lediglich Ihr eigenes E-Mail-Programm mit einer vorbereiteten Nachricht, die Sie selbst abschicken.</p>
<p>Wir löschen Ihre Angaben, sobald Ihr Anliegen erledigt ist und keine gesetzlichen Aufbewahrungspflichten (zum Beispiel nach Handels- und Steuerrecht) entgegenstehen.</p>
<h2>5. Links zu anderen Anbietern</h2>
<p>Unsere Seite enthält Links zu Kleinanzeigen, Maschinensucher, Instagram, YouTube, kilia.de, korimat-gmbh.de und OpenStreetMap. Diese Inhalte sind nicht eingebettet. Erst wenn Sie einen Link anklicken, gelangen Sie zum jeweiligen Anbieter, und dessen Datenschutzbestimmungen gelten.</p>
<h2>6. Ihre Rechte</h2>
<p>Sie haben das Recht auf Auskunft (Art. 15 DSGVO), Berichtigung (Art. 16), Löschung (Art. 17), Einschränkung der Verarbeitung (Art. 18), Datenübertragbarkeit (Art. 20) und Widerspruch gegen Verarbeitungen auf Grundlage von Art. 6 Abs. 1 lit. f DSGVO (Art. 21). Wenden Sie sich dazu einfach an die oben genannten Kontaktdaten.</p>
<p>Sie können sich außerdem bei einer Datenschutz-Aufsichtsbehörde beschweren. Für uns zuständig ist: Die Landesbeauftragte für den Datenschutz Niedersachsen, Prinzenstraße 5, 30159 Hannover.</p>
<p>Stand: {HEUTE.strftime('%m/%Y')}</p>
"""


# ── 404 und Weiterleitungen alter Adressen ───────────────────────────────────────────
def nicht_gefunden():
    inhalt = f"""<section class="nichtda dunkel"><div>
  {rotor("rotor", stahl=True)}
  <div class="marke" style="justify-content:center">Fehler 404</div>
  <h1 style="font-size:clamp(36px,6vw,72px);margin-bottom:18px">Leerlauf.</h1>
  <p class="leise" style="max-width:44ch;margin:0 auto 28px">Diese Seite gibt es nicht (mehr). Vielleicht finden Sie, was Sie suchen, unter unseren Maschinen.</p>
  <div class="knopfreihe" style="justify-content:center"><a class="knopf knopf-rot" href="/maschinen/">Zu den Maschinen {sym('pfeil', 'pfeil')}</a><a class="knopf knopf-rahmen" href="/">Zur Startseite</a></div>
</div></section>"""
    s = rahmen("404.html", "Seite nicht gefunden", "Diese Seite gibt es nicht.", inhalt, ohne_index=True)
    # 404 liegt an der Wurzel, wird aber unter jeder Adresse ausgeliefert: dort absolute Pfade
    return s.replace('href="assets/', 'href="/assets/').replace('src="assets/', 'src="/assets/').replace('href="maschinen/', 'href="/maschinen/') \
        .replace('href="kilia/', 'href="/kilia/').replace('href="korimat/', 'href="/korimat/').replace('href="kundendienst/', 'href="/kundendienst/') \
        .replace('href="kontakt/', 'href="/kontakt/').replace('href="impressum/', 'href="/impressum/').replace('href="datenschutz/', 'href="/datenschutz/') \
        .replace('href="agb/', 'href="/agb/').replace('href="widerrufsrecht/', 'href="/widerrufsrecht/').replace('href="haftungsausschluss/', 'href="/haftungsausschluss/') \
        .replace('href="#mietkauf"', 'href="/#mietkauf"').replace('href="./"', 'href="/"')


def weiterleitung(alt, neu):
    tiefe = alt.count("/")
    ziel = "../" * tiefe + neu
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><title>Weiterleitung</title>
<meta name="robots" content="noindex"><link rel="canonical" href="{BASIS}/{neu}"><meta http-equiv="refresh" content="0; url={ziel}">
<script>location.replace({json.dumps(ziel)}+location.hash)</script></head>
<body><p>Diese Seite ist umgezogen: <a href="{ziel}">weiter</a>.</p></body></html>"""


# ── Schreiben ────────────────────────────────────────────────────────────────────────
GENERIERT = ["index.html", "404.html", "maschinen", "kilia", "korimat", "kundendienst", "kontakt", "impressum", "datenschutz", "agb",
             "widerrufsrecht", "haftungsausschluss", "project", "project_category", "fleischereimaschinen", "gebrauchtmaschinen",
             "datenschutzerklaerung-eu", "cookie-richtlinie-eu", "sitemap.xml", "robots.txt"]


def schreiben(pfad, text):
    z = WURZEL / pfad
    z.parent.mkdir(parents=True, exist_ok=True)
    z.write_text(text, encoding="utf-8")


def main():
    # Alles Generierte vorher entfernen (Bilder, Schriften, Werkzeuge bleiben)
    for g in GENERIERT:
        p = WURZEL / g
        if p.is_dir():
            shutil.rmtree(p)
        elif p.exists():
            p.unlink()
    seiten = {"index.html": startseite(), "maschinen/index.html": katalog(), "kilia/index.html": kilia(), "korimat/index.html": korimat(),
              "kundendienst/index.html": kundendienst(), "kontakt/index.html": kontakt(), "404.html": nicht_gefunden()}
    for m in MASCHINEN:
        seiten[f"maschinen/{m['slug']}/index.html"] = maschinenseite(m)
    seiten["impressum/index.html"] = rechtsseite("impressum/index.html", "Impressum", alt_rechtstext("impressum"), "Impressum der HELTEK Maschinenbau GmbH & Co. KG, Bad Fallingbostel.")
    seiten["datenschutz/index.html"] = rechtsseite("datenschutz/index.html", "Datenschutz", DATENSCHUTZ, "Datenschutzerklärung der HELTEK Maschinenbau GmbH & Co. KG.")
    seiten["agb/index.html"] = rechtsseite("agb/index.html", "AGB", alt_rechtstext("agb"), "Allgemeine Geschäftsbedingungen der HELTEK Maschinenbau GmbH & Co. KG.")
    seiten["widerrufsrecht/index.html"] = rechtsseite("widerrufsrecht/index.html", "Widerrufsrecht", alt_rechtstext("widerrufsrecht"), "Widerrufsbelehrung der HELTEK Maschinenbau GmbH & Co. KG.")
    seiten["haftungsausschluss/index.html"] = rechtsseite("haftungsausschluss/index.html", "Haftungsausschluss", alt_rechtstext("haftungsausschluss"), "Haftungsausschluss der HELTEK Maschinenbau GmbH & Co. KG.")
    # Alte WordPress-Adressen leiten weiter
    alt = {"fleischereimaschinen/index.html": "maschinen/", "gebrauchtmaschinen/index.html": "maschinen/",
           "datenschutzerklaerung-eu/index.html": "datenschutz/", "cookie-richtlinie-eu/index.html": "datenschutz/"}
    for m in MASCHINEN:
        alt[f"project/{m['alt_slug']}/index.html"] = f"maschinen/{m['slug']}/"
    katalt = {"kutter": "kutter", "wolf": "woelfe", "korimat": "autoklaven", "fueller": "fueller", "fueller-vakuumfueller": "fueller",
              "speckschneider": "speckschneider", "menger-und-mischer": "mischer", "knochensaegen": "saegen"}
    for a, n in katalt.items():
        alt[f"project_category/{a}/index.html"] = f"maschinen/#kategorie={n}"
    for p, s in seiten.items():
        schreiben(p, s)
    for p, ziel in alt.items():
        schreiben(p, weiterleitung(p.replace("index.html", ""), ziel))
    # sitemap und robots
    urls = [p.replace("index.html", "") for p in seiten if p not in ("404.html",) and not p.startswith(("impressum", "datenschutz"))]
    sm = "".join(f"<url><loc>{BASIS}/{u}</loc><lastmod>{HEUTE.isoformat()}</lastmod></url>" for u in urls)
    schreiben("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>\n')
    if LIVE:
        schreiben("robots.txt", f"User-agent: *\nDisallow: /werkzeuge/\nDisallow: /daten/\nDisallow: /LIESMICH.md\n\nSitemap: {BASIS}/sitemap.xml\n")
    else:
        schreiben("robots.txt", "# Vorschau: nicht für Suchmaschinen\nUser-agent: *\nDisallow: /\n")
    print(f"{'LIVE' if LIVE else 'Vorschau'}: {len(seiten)} Seiten, {len(alt)} Weiterleitungen, {len(MASCHINEN)} Maschinen")


if __name__ == "__main__":
    main()
