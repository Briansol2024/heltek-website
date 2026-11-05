# -*- coding: utf-8 -*-
"""Liest alle Maschinen-Angebote von der bisherigen heltek.de (WordPress/Divi) aus
und schreibt sie nach daten/maschinen.json. Bilder werden hier nur gesammelt, nicht geladen.

    py werkzeuge/maschinen_holen.py
"""
import json, re, sys, time, html, urllib.request
from html.parser import HTMLParser
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
WURZEL = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "Mozilla/5.0 (Heltek-Umzug)"}


def hole(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
        return r.read().decode("utf-8", "replace")


def groesste(img_tag):
    """Größte Fassung aus srcset, sonst src. Original ohne -BxH bevorzugt."""
    src = re.search(r'\ssrc="([^"]+)"', img_tag)
    kand = []
    for teil in re.findall(r'srcset="([^"]+)"', img_tag):
        for e in teil.split(","):
            e = e.strip().split(" ")
            if len(e) == 2 and e[1].endswith("w"):
                kand.append((int(e[1][:-1]), e[0]))
    url = max(kand)[1] if kand else (src.group(1) if src else "")
    url = url.replace("https://heltek.de/", "https://www.heltek.de/")
    # Original statt verkleinerter Fassung, wenn der Name auf -BxH endet
    return re.sub(r"-\d{2,4}x\d{2,4}(\.(?:jpe?g|png|webp))$", r"\1", url, flags=re.I)


ERLAUBT = {"p", "h2", "h3", "h4", "h5", "ul", "ol", "li", "strong", "b", "em", "i", "br",
           "table", "thead", "tbody", "tr", "td", "th"}
WEG = {"figure", "script", "style", "noscript", "iframe", "form"}


class Saeubern(HTMLParser):
    """Nur einfache Auszeichnung behalten, alle Attribute weg, Bilder/Galerien raus."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.weg = [], 0

    def handle_starttag(self, t, a):
        if t in WEG:
            self.weg += 1
        if self.weg or t not in ERLAUBT:
            return
        t = {"b": "strong", "i": "em", "h2": "h3", "h5": "h4"}.get(t, t)
        self.out.append("<br>" if t == "br" else f"<{t}>")

    def handle_endtag(self, t):
        if t in WEG and self.weg:
            self.weg -= 1
            return
        if self.weg or t not in ERLAUBT or t == "br":
            return
        t = {"b": "strong", "i": "em", "h2": "h3", "h5": "h4"}.get(t, t)
        self.out.append(f"</{t}>")

    def handle_data(self, d):
        if not self.weg:
            self.out.append(html.escape(d, quote=False))


def saeubern(roh):
    p = Saeubern(); p.feed(roh)
    s = "".join(p.out)
    s = re.sub(r"[ \t\r\f\v\u00a0]+", " ", s)
    s = re.sub(r"\s*\n\s*", "\n", s)
    s = re.sub(r"<(p|li|h3|h4|td|th|strong|em)>\s*</\1>", "", s)   # leere Hüllen
    s = re.sub(r"<(p|li|h3|h4|td|th|strong|em)>\s*</\1>", "", s)
    s = re.sub(r"(<br>\s*){3,}", "<br><br>", s)
    return s.strip()


def slug_aus(url):
    return url.rstrip("/").rsplit("/", 1)[-1]


def maschine(url):
    s = hole(url)
    titel = re.search(r'<h1 class="entry-title">(.*?)</h1>', s, re.S)
    titel = re.sub(r"\s+", " ", html.unescape(re.sub("<[^>]+>", "", titel.group(1)))).strip() if titel else ""
    kat = re.search(r'class="et_project_categories">(.*?)</p>', s, re.S)
    kategorien = [html.unescape(k).strip() for k in re.findall(r'rel="tag">([^<]+)</a>', kat.group(1))] if kat else []
    datum = re.search(r'"datePublished":"([^"]+)"', s) or re.search(r'property="article:published_time" content="([^"]+)"', s)
    i = s.find('class="entry-content"')
    ende = s.find('<div id="sidebar"')
    if ende < 0:
        ende = s.find("et_project_meta")
    kopf = s[max(0, i - 6000):i]
    inhalt = s[i:ende if ende > i else len(s)]
    # Ende des Inhalts vor der Projekt-Navigation/Metadaten abschneiden
    for marke in ('class="et_project_meta"', 'class="nav-single', '<div class="et_post_meta_wrapper">'):
        k = inhalt.find(marke)
        if k > 0:
            inhalt = inhalt[:k]
    bilder = []
    titelbild = re.findall(r"<img[^>]+>", kopf)
    if titelbild:
        bilder.append(groesste(titelbild[-1]))
    for tag in re.findall(r"<img[^>]+>", inhalt):
        u = groesste(tag)
        if u and u not in bilder and "/uploads/" in u:
            bilder.append(u)
    text = saeubern(inhalt[inhalt.find(">") + 1:])
    return {"slug": slug_aus(url), "quelle": url, "titel": titel, "kategorien": kategorien,
            "datum": datum.group(1)[:10] if datum else "", "bilder": bilder, "text": text}


def main():
    sm = hole("https://www.heltek.de/wp-sitemap-posts-project-1.xml")
    urls = re.findall(r"<loc>([^<]+)</loc>", sm)
    alle = []
    for n, u in enumerate(urls, 1):
        try:
            m = maschine(u)
            alle.append(m)
            print(f"{n:2d}/{len(urls)} {m['titel'][:60]:60s} {len(m['bilder']):2d} Bilder  {','.join(m['kategorien'])}")
        except Exception as e:
            print(f"{n:2d}/{len(urls)} FEHLER {u}: {e}")
        time.sleep(0.4)
    ziel = WURZEL / "daten" / "maschinen.json"
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(json.dumps(alle, ensure_ascii=False, indent=1), encoding="utf-8")
    print("geschrieben:", ziel, len(alle))


if __name__ == "__main__":
    main()
