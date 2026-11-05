# -*- coding: utf-8 -*-
"""Rechtstexte der bisherigen heltek.de als einfaches HTML nach daten/rechtliches/.

    py werkzeuge/texte_holen.py
"""
import re, sys, html, urllib.request
from html.parser import HTMLParser
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
WURZEL = Path(__file__).resolve().parent.parent
SEITEN = ["impressum", "agb", "widerrufsrecht", "haftungsausschluss", "datenschutzerklaerung-eu"]
ERLAUBT = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "strong", "b", "em", "i", "br", "a",
           "table", "tbody", "tr", "td", "th"}
WEG = {"script", "style", "noscript", "iframe", "form", "header", "footer", "nav", "svg", "figure"}
UMBENENNEN = {"b": "strong", "i": "em", "h1": "h2", "h5": "h4", "h6": "h4"}


class S(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.out = []; self.weg = 0

    def handle_starttag(self, t, a):
        if t in WEG: self.weg += 1
        if self.weg or t not in ERLAUBT: return
        t = UMBENENNEN.get(t, t)
        if t == "br": self.out.append("<br>"); return
        if t == "a":
            href = dict(a).get("href") or ""
            if re.match(r"^(https?:|mailto:|tel:)", href):
                self.out.append(f'<a href="{html.escape(href)}">'); return
            self.out.append("<a>"); return
        self.out.append(f"<{t}>")

    def handle_endtag(self, t):
        if t in WEG and self.weg: self.weg -= 1; return
        if self.weg or t not in ERLAUBT or t == "br": return
        self.out.append(f"</{UMBENENNEN.get(t, t)}>")

    def handle_data(self, d):
        if not self.weg: self.out.append(html.escape(d, quote=False))


for name in SEITEN:
    roh = urllib.request.urlopen(urllib.request.Request(f"https://www.heltek.de/{name}/", headers={"User-Agent": "Mozilla/5.0"}), timeout=40).read().decode("utf-8", "replace")
    i = roh.find('<div id="main-content"'); j = roh.find('<footer')
    teil = roh[i:j if j > i else len(roh)]
    s = S(); s.feed(teil)
    t = "".join(s.out)
    t = re.sub(r"[ \t\r\f\v ]+", " ", t)
    t = re.sub(r"\s*\n\s*", "\n", t)
    for _ in range(3):
        t = re.sub(r"<(p|li|h2|h3|h4|strong|em|a)>\s*</\1>", "", t)
    t = re.sub(r"<a>(.*?)</a>", r"\1", t, flags=re.S)
    ziel = WURZEL / "daten" / "rechtliches" / f"{name}.html"
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(t.strip(), encoding="utf-8")
    print(f"{name:28s} {len(t):6d} Zeichen")
