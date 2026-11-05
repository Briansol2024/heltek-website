/* HELTEK Maschinenbau – Bewegung und Bedienung. Ohne Bibliotheken, ohne Cookies, ohne Anfragen an Dritte. */
(function () {
  'use strict';
  var d = document, w = window, html = d.documentElement, body = d.body;
  var ruhig = w.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var $ = function (s, r) { return (r || d).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || d).querySelectorAll(s)); };

  /* ── Start: Auftritt nach dem ersten Bild ─────────────────────────── */
  function bereit() { requestAnimationFrame(function () { requestAnimationFrame(function () { body.classList.add('bereit'); }); }); }
  if (d.fonts && d.fonts.ready) { Promise.race([d.fonts.ready, new Promise(function (r) { setTimeout(r, 900); })]).then(bereit); } else { bereit(); }

  /* ── Kopf: fest, aus- und einblenden, Fortschritt ─────────────────── */
  var kopf = $('.kopf'), letzteY = w.scrollY, geplant = false;
  function kopfZeichnen() {
    geplant = false;
    var y = w.scrollY, max = Math.max(1, html.scrollHeight - w.innerHeight);
    if (kopf) {
      kopf.classList.toggle('fest', y > 24 || !$('.buehne, .seitenkopf'));
      var runter = y > letzteY;
      kopf.classList.toggle('weg', runter && y > 520 && !body.classList.contains('menue-offen'));
      kopf.style.setProperty('--p', (y / max).toFixed(4));
    }
    letzteY = y;
  }
  w.addEventListener('scroll', function () { if (!geplant) { geplant = true; requestAnimationFrame(kopfZeichnen); } }, { passive: true });
  kopfZeichnen();

  /* ── Menü am Handy ────────────────────────────────────────────────── */
  var mk = $('.menue-knopf'), menue = $('#menue');
  function menueSetzen(auf) {
    body.classList.toggle('menue-offen', auf);
    if (mk) { mk.setAttribute('aria-expanded', auf ? 'true' : 'false'); mk.setAttribute('aria-label', auf ? 'Menü schließen' : 'Menü öffnen'); }
    if (menue) menue.setAttribute('aria-hidden', auf ? 'false' : 'true');
    body.style.overflow = auf ? 'hidden' : '';
    if (auf && kopf) kopf.classList.remove('weg');
  }
  if (mk) mk.addEventListener('click', function () { menueSetzen(!body.classList.contains('menue-offen')); });
  if (menue) $$('a', menue).forEach(function (a) { a.addEventListener('click', function () { menueSetzen(false); }); });
  d.addEventListener('keydown', function (e) { if (e.key === 'Escape' && body.classList.contains('menue-offen')) { menueSetzen(false); if (mk) mk.focus(); } });

  /* ── Wörter für die Wort-Animation zerlegen ───────────────────────── */
  $$('.wort-auf').forEach(function (el) {
    var i = 0;
    (function zerlegen(knoten) {
      Array.prototype.slice.call(knoten.childNodes).forEach(function (k) {
        if (k.nodeType === 3) {
          var teile = k.textContent.split(/(\s+)/), frag = d.createDocumentFragment();
          teile.forEach(function (t) {
            if (!t) return;
            if (/^\s+$/.test(t)) { frag.appendChild(d.createTextNode(t)); return; }
            var a = d.createElement('span'); a.className = 'w';
            var b = d.createElement('span'); b.textContent = t; b.style.setProperty('--i', i++);
            a.appendChild(b); frag.appendChild(a);
          });
          k.parentNode.replaceChild(frag, k);
        } else if (k.nodeType === 1 && k.tagName !== 'BR') { zerlegen(k); }
      });
    })(el);
    el.setAttribute('aria-label', el.textContent.replace(/\s+/g, ' ').trim());
  });

  /* ── Zählwerk: Ziffern rollen wie an einer Maschine ───────────────── */
  $$('.zaehlwerk').forEach(function (el) {
    var wert = String(el.getAttribute('data-wert') || el.textContent).trim();
    el.setAttribute('aria-label', wert); el.textContent = '';
    wert.split('').forEach(function (z, n) {
      var stelle = d.createElement('span'); stelle.className = 'stelle'; stelle.setAttribute('aria-hidden', 'true');
      var band = d.createElement('span'); band.className = 'band';
      for (var k = 0; k < 20; k++) { var i = d.createElement('i'); i.textContent = k % 10; band.appendChild(i); }
      band.dataset.ziel = String(10 + Number(z));
      band.style.setProperty('--d', (n * 0.12) + 's');
      stelle.appendChild(band); el.appendChild(stelle);
    });
  });
  function zaehlwerkStarten(el) {
    $$('.band', el).forEach(function (b) { b.style.transform = 'translateY(-' + b.dataset.ziel + 'em)'; });
  }

  /* ── Erscheinen beim Scrollen ─────────────────────────────────────── */
  $$('[data-staffel]').forEach(function (g) {
    var schritt = parseFloat(g.getAttribute('data-staffel')) || 0.08;
    Array.prototype.slice.call(g.children).forEach(function (k, i) { if (!k.style.getPropertyValue('--d')) k.style.setProperty('--d', (i * schritt).toFixed(2) + 's'); });
  });
  var beobachtet = $$('[data-auf], .wort-auf, .zahl, .leistung, .zeitstrahl, .vorteile li');
  if (ruhig || !('IntersectionObserver' in w)) {
    beobachtet.forEach(function (el) { el.classList.add('sichtbar'); });
    $$('.zaehlwerk').forEach(zaehlwerkStarten);
  } else {
    var io = new IntersectionObserver(function (eintraege) {
      eintraege.forEach(function (e) {
        if (!e.isIntersecting) return;
        e.target.classList.add('sichtbar');
        $$('.zaehlwerk', e.target).forEach(zaehlwerkStarten);
        io.unobserve(e.target);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.12 });
    beobachtet.forEach(function (el) { io.observe(el); });
  }

  /* ── Der Messerkopf: läuft beim Scrollen hoch ─────────────────────── */
  var klingen = $('.buehne-rotor .klingen'), anzeige = $('.drehzahl b');
  if (klingen && !ruhig && klingen.getAnimations) {
    var anim = null, tempo = 1, ziel = 1, schub = 0, letztesY = w.scrollY, ueber = false;
    var holen = function () { if (!anim) anim = klingen.getAnimations()[0] || null; return anim; };
    w.addEventListener('scroll', function () { var y = w.scrollY; schub += Math.abs(y - letztesY); letztesY = y; }, { passive: true });
    var rotorHuelle = $('.buehne-rotor');
    if (rotorHuelle) {
      rotorHuelle.addEventListener('pointerenter', function () { ueber = true; });
      rotorHuelle.addEventListener('pointerleave', function () { ueber = false; });
    }
    (function lauf() {
      ziel = 1 + Math.min(schub * 0.06, 9) + (ueber ? 2.5 : 0);
      schub *= 0.88;
      tempo += (ziel - tempo) * 0.06;
      var a = holen(); if (a) a.playbackRate = tempo;
      if (anzeige) anzeige.textContent = String(Math.min(5000, Math.round(tempo * 480 / 10) * 10)).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
      requestAnimationFrame(lauf);
    })();
  }

  /* ── Leichte Tiefe beim Scrollen ──────────────────────────────────── */
  var tiefe = $$('[data-tiefe]');
  if (tiefe.length && !ruhig) {
    var tiefeGeplant = false;
    var tiefeZeichnen = function () {
      tiefeGeplant = false;
      var h = w.innerHeight;
      tiefe.forEach(function (el) {
        var r = el.getBoundingClientRect(); if (r.bottom < -200 || r.top > h + 200) return;
        var f = parseFloat(el.getAttribute('data-tiefe')) || 0.2;
        var mitte = (r.top + r.height / 2 - h / 2);
        el.style.setProperty('--py', (mitte * -f).toFixed(1) + 'px');
      });
    };
    w.addEventListener('scroll', function () { if (!tiefeGeplant) { tiefeGeplant = true; requestAnimationFrame(tiefeZeichnen); } }, { passive: true });
    w.addEventListener('resize', tiefeZeichnen); tiefeZeichnen();
  }

  /* ── Karten folgen dem Zeiger ─────────────────────────────────────── */
  if (!ruhig && w.matchMedia('(hover: hover)').matches) {
    $$('.markenkarte').forEach(function (k) {
      k.addEventListener('pointermove', function (e) {
        var r = k.getBoundingClientRect(), x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
        k.style.setProperty('--mx', (x * 100).toFixed(1) + '%'); k.style.setProperty('--my', (y * 100).toFixed(1) + '%');
        k.style.setProperty('--ry', ((x - 0.5) * 6).toFixed(2) + 'deg'); k.style.setProperty('--rx', ((0.5 - y) * 5).toFixed(2) + 'deg');
      });
      k.addEventListener('pointerleave', function () { k.style.setProperty('--rx', '0deg'); k.style.setProperty('--ry', '0deg'); });
    });
  }

  /* ── Kartenreihe: ziehen und blättern ─────────────────────────────── */
  $$('[data-reihe]').forEach(function (bereich) {
    var reihe = $('.karten-reihe', bereich), zur = $('[data-zurueck]', bereich), vor = $('[data-weiter]', bereich);
    if (!reihe) return;
    var schritt = function () { var k = reihe.firstElementChild; return k ? k.getBoundingClientRect().width + 20 : 300; };
    var knoepfe = function () {
      if (zur) zur.disabled = reihe.scrollLeft < 8;
      if (vor) vor.disabled = reihe.scrollLeft > reihe.scrollWidth - reihe.clientWidth - 8;
    };
    if (zur) zur.addEventListener('click', function () { reihe.scrollBy({ left: -schritt(), behavior: 'smooth' }); });
    if (vor) vor.addEventListener('click', function () { reihe.scrollBy({ left: schritt(), behavior: 'smooth' }); });
    reihe.addEventListener('scroll', knoepfe, { passive: true }); knoepfe();
    var unten = false, startX = 0, startL = 0, bewegt = 0;
    reihe.addEventListener('pointerdown', function (e) { if (e.pointerType !== 'mouse') return; unten = true; bewegt = 0; startX = e.clientX; startL = reihe.scrollLeft; });
    w.addEventListener('pointermove', function (e) {
      if (!unten) return; var dx = e.clientX - startX; bewegt = Math.max(bewegt, Math.abs(dx));
      if (bewegt > 6) { reihe.classList.add('ziehen'); reihe.scrollLeft = startL - dx; }
    });
    w.addEventListener('pointerup', function () { if (!unten) return; unten = false; setTimeout(function () { reihe.classList.remove('ziehen'); }, 0); });
  });

  /* ── Katalog: Filter, Marke, Suche ────────────────────────────────── */
  var raster = $('#raster');
  if (raster) {
    var karten = $$('.mkarte', raster), chips = $$('.chip'), markeWahl = $('#marke'), suche = $('#suche'), treffer = $('#treffer'), leer = $('#leer');
    var kategorie = 'alle';
    var aus = function (s) { return s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/ß/g, 'ss'); };
    var anwenden = function (animiert) {
      var marke = markeWahl ? markeWahl.value : '', q = suche ? aus(suche.value.trim()) : '';
      var vorher = new Map(); if (animiert && !ruhig) karten.forEach(function (k) { if (!k.hidden) vorher.set(k, k.getBoundingClientRect()); });
      var n = 0;
      karten.forEach(function (k) {
        var ok = (kategorie === 'alle' || k.dataset.kat === kategorie) && (!marke || k.dataset.marke === marke) && (!q || aus(k.dataset.suche).indexOf(q) > -1);
        k.hidden = !ok; if (ok) n++;
      });
      if (treffer) treffer.textContent = n === 1 ? '1 Maschine' : n + ' Maschinen';
      if (leer) leer.classList.toggle('da', n === 0);
      if (animiert && !ruhig && raster.animate) {
        karten.forEach(function (k) {
          if (k.hidden) return;
          var alt = vorher.get(k), neu = k.getBoundingClientRect();
          if (alt) {
            var dx = alt.left - neu.left, dy = alt.top - neu.top;
            if (dx || dy) k.animate([{ transform: 'translate(' + dx + 'px,' + dy + 'px)' }, { transform: 'none' }], { duration: 650, easing: 'cubic-bezier(.2,.75,.15,1)' });
          } else {
            k.animate([{ opacity: 0, transform: 'scale(.92) translateY(16px)' }, { opacity: 1, transform: 'none' }], { duration: 600, easing: 'cubic-bezier(.2,.75,.15,1)', delay: Math.min(300, Math.random() * 200) });
          }
        });
      }
      var teile = [];
      if (kategorie !== 'alle') teile.push('kategorie=' + kategorie);
      if (marke) teile.push('marke=' + encodeURIComponent(marke));
      history.replaceState(null, '', location.pathname + (teile.length ? '#' + teile.join('&') : ''));
    };
    chips.forEach(function (c) {
      c.addEventListener('click', function () {
        kategorie = c.dataset.filter;
        chips.forEach(function (x) { x.setAttribute('aria-pressed', x === c ? 'true' : 'false'); });
        anwenden(true);
      });
    });
    if (markeWahl) markeWahl.addEventListener('change', function () { anwenden(true); });
    if (suche) { var t; suche.addEventListener('input', function () { clearTimeout(t); t = setTimeout(function () { anwenden(true); }, 140); }); }
    var h = new URLSearchParams(location.hash.slice(1));
    if (h.get('kategorie') && chips.some(function (c) { return c.dataset.filter === h.get('kategorie'); })) {
      kategorie = h.get('kategorie');
      chips.forEach(function (x) { x.setAttribute('aria-pressed', x.dataset.filter === kategorie ? 'true' : 'false'); });
    }
    if (h.get('marke') && markeWahl) markeWahl.value = h.get('marke');
    anwenden(false);
  }

  /* ── Galerie und Bildbetrachter ───────────────────────────────────── */
  var galerie = $('[data-galerie]');
  if (galerie) {
    var bilder = JSON.parse(galerie.getAttribute('data-galerie')), akt = 0;
    var haupt = $('.galerie-haupt img', galerie), zaehl = $('.galerie-haupt .zaehler', galerie), daumen = $$('.daumen button', galerie);
    var zeigen = function (i) {
      akt = (i + bilder.length) % bilder.length;
      haupt.classList.add('raus');
      var neu = new Image(); neu.src = bilder[akt].gross;
      var tauschen = function () { haupt.src = bilder[akt].gross; haupt.alt = bilder[akt].alt; haupt.classList.remove('raus'); };
      if (neu.decode) neu.decode().then(tauschen, tauschen); else neu.onload = tauschen;
      if (zaehl) zaehl.textContent = (akt + 1) + ' / ' + bilder.length;
      daumen.forEach(function (b, n) { b.setAttribute('aria-current', n === akt ? 'true' : 'false'); });
      var aktDaumen = daumen[akt]; if (aktDaumen) aktDaumen.scrollIntoView({ block: 'nearest', inline: 'nearest', behavior: ruhig ? 'auto' : 'smooth' });
    };
    daumen.forEach(function (b, n) { b.addEventListener('click', function () { zeigen(n); }); });
    var gz = $('.galerie-pfeil.zurueck', galerie), gw = $('.galerie-pfeil.weiter', galerie);
    if (gz) gz.addEventListener('click', function () { zeigen(akt - 1); });
    if (gw) gw.addEventListener('click', function () { zeigen(akt + 1); });

    var bt = $('#betrachter'), btBild = bt && $('img', bt), btZahl = bt && $('.betrachter-zahl', bt), zuvor = null;
    var btZeigen = function (i, richtung) {
      akt = (i + bilder.length) % bilder.length;
      if (btBild) {
        if (richtung && btBild.animate && !ruhig) btBild.animate([{ opacity: 0, transform: 'translateX(' + (richtung * 40) + 'px)' }, { opacity: 1, transform: 'none' }], { duration: 380, easing: 'cubic-bezier(.2,.75,.15,1)' });
        btBild.src = bilder[akt].gross; btBild.alt = bilder[akt].alt;
      }
      if (btZahl) btZahl.textContent = (akt + 1) + ' / ' + bilder.length;
    };
    var btAuf = function () { if (!bt) return; zuvor = d.activeElement; btZeigen(akt); bt.classList.add('offen'); bt.setAttribute('aria-hidden', 'false'); body.style.overflow = 'hidden'; $('[data-zu]', bt).focus(); };
    var btZu = function () { if (!bt) return; bt.classList.remove('offen'); bt.setAttribute('aria-hidden', 'true'); body.style.overflow = ''; zeigen(akt); if (zuvor) zuvor.focus(); };
    var hauptFlaeche = $('.galerie-haupt', galerie);
    if (hauptFlaeche) { hauptFlaeche.addEventListener('click', btAuf); hauptFlaeche.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); btAuf(); } }); }
    if (bt) {
      $('[data-zu]', bt).addEventListener('click', btZu);
      $('[data-btz]', bt).addEventListener('click', function () { btZeigen(akt - 1, -1); });
      $('[data-btw]', bt).addEventListener('click', function () { btZeigen(akt + 1, 1); });
      d.addEventListener('keydown', function (e) {
        if (!bt.classList.contains('offen')) return;
        if (e.key === 'Escape') btZu();
        if (e.key === 'ArrowLeft') btZeigen(akt - 1, -1);
        if (e.key === 'ArrowRight') btZeigen(akt + 1, 1);
        if (e.key === 'Tab') { var f = $$('button', bt); var i = f.indexOf(d.activeElement); e.preventDefault(); f[(i + (e.shiftKey ? -1 : 1) + f.length) % f.length].focus(); }
      });
      var sx = null;
      bt.addEventListener('pointerdown', function (e) { sx = e.clientX; });
      bt.addEventListener('pointerup', function (e) { if (sx === null) return; var dx = e.clientX - sx; sx = null; if (Math.abs(dx) > 50) btZeigen(akt + (dx < 0 ? 1 : -1), dx < 0 ? 1 : -1); });
    }
  }

  /* ── Öffnungszeiten: jetzt geöffnet? (Zeit in Deutschland) ────────── */
  var ZEITEN = { 1: [8, 17], 2: [8, 17], 3: [8, 17], 4: [8, 17], 5: [8, 13] };
  var TAGE = ['Sonntag', 'Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag'];
  function jetztInDeutschland() {
    try {
      var t = new Intl.DateTimeFormat('de-DE', { timeZone: 'Europe/Berlin', weekday: 'short', hour: '2-digit', minute: '2-digit', hour12: false }).formatToParts(new Date());
      var g = {}; t.forEach(function (p) { g[p.type] = p.value; });
      var tag = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'].indexOf(g.weekday.replace('.', ''));
      return { tag: tag, min: Number(g.hour) * 60 + Number(g.minute) };
    } catch (e) { var n = new Date(); return { tag: n.getDay(), min: n.getHours() * 60 + n.getMinutes() }; }
  }
  var jetzt = jetztInDeutschland();
  $$('[data-offen]').forEach(function (el) {
    var z = ZEITEN[jetzt.tag], auf = z && jetzt.min >= z[0] * 60 && jetzt.min < z[1] * 60, text;
    if (auf) { text = 'Jetzt geöffnet · bis ' + z[1] + ':00 Uhr'; }
    else {
      var t = jetzt.tag, n = 0;
      if (z && jetzt.min < z[0] * 60) { text = 'Geschlossen · öffnet heute ' + String(z[0]).padStart(2, '0') + ':00 Uhr'; }
      else {
        do { t = (t + 1) % 7; n++; } while (!ZEITEN[t] && n < 8);
        text = 'Geschlossen · öffnet ' + (n === 1 ? 'morgen' : TAGE[t]) + ' ' + String(ZEITEN[t][0]).padStart(2, '0') + ':00 Uhr';
      }
    }
    el.classList.toggle('ja', !!auf);
    var s = $('span', el); if (s) s.textContent = text;
    el.hidden = false;
  });
  $$('[data-tag]').forEach(function (el) {
    var tage = el.getAttribute('data-tag').split(',').map(Number);
    if (tage.indexOf(jetzt.tag) > -1) el.classList.add('heute');
  });

  /* ── Korimat-Modelle ──────────────────────────────────────────────── */
  $$('[data-modelle]').forEach(function (bereich) {
    var reiter = $$('[role="tab"]', bereich);
    var waehlen = function (r, fokus) {
      reiter.forEach(function (x) {
        var an = x === r; x.setAttribute('aria-selected', an ? 'true' : 'false'); x.tabIndex = an ? 0 : -1;
        var p = d.getElementById(x.getAttribute('aria-controls')); if (p) p.hidden = !an;
        var b = $('[data-modell="' + x.dataset.modell + '"]', bereich); if (b) b.classList.toggle('an', an);
      });
      if (fokus) r.focus();
    };
    reiter.forEach(function (r, i) {
      r.addEventListener('click', function () { waehlen(r); });
      r.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowRight') waehlen(reiter[(i + 1) % reiter.length], true);
        if (e.key === 'ArrowLeft') waehlen(reiter[(i - 1 + reiter.length) % reiter.length], true);
      });
    });
  });

  /* ── Anfrage: öffnet das Mailprogramm, hier wird nichts gespeichert ─ */
  var form = $('#anfrage');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (!form.reportValidity()) return;
      var f = new FormData(form), wert = function (k) { return String(f.get(k) || '').trim(); };
      var betreff = 'Anfrage über heltek.de: ' + (wert('anliegen') || 'Allgemein');
      var zeilen = [wert('nachricht'), '', '—', 'Name: ' + wert('name')];
      if (wert('firma')) zeilen.push('Firma: ' + wert('firma'));
      if (wert('telefon')) zeilen.push('Telefon: ' + wert('telefon'));
      if (wert('email')) zeilen.push('E-Mail: ' + wert('email'));
      location.href = 'mailto:info@heltek.de?subject=' + encodeURIComponent(betreff) + '&body=' + encodeURIComponent(zeilen.join('\n'));
      var h = $('#anfrage-hinweis'); if (h) h.textContent = 'Ihr E-Mail-Programm öffnet sich mit der fertigen Nachricht. Falls nicht, schreiben Sie bitte direkt an info@heltek.de.';
    });
    var vorgabe = new URLSearchParams(location.search).get('maschine');
    if (vorgabe) {
      var feld = form.querySelector('[name="nachricht"]'), sel = form.querySelector('[name="anliegen"]');
      if (feld && !feld.value) feld.value = 'Ich interessiere mich für: ' + vorgabe + '\n\n';
      if (sel) sel.value = 'Maschine kaufen';
    }
  }
})();
