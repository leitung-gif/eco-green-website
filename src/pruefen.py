"""Prueft einen Bau der Eco-Green-Website ohne Server.

Aufruf:  python pruefen.py                 prueft ../docs (Vorschau, PFAD /eco-green-website/)
         python pruefen.py <ordner> --live prueft einen Live-Probebau (PFAD /)

Prueft: jeder interne Link und jede Datei (href, src, srcset, imagesrcset, Manifest-Icons) zeigt auf eine
vorhandene Datei, URLs ohne Dateiendung wie auf Shopify; kein relativer interner Pfad; JSON-LD jeder Seite
parst, kein AggregateRating, Startseite ohne Article; Sitemap und Atom-Feed nennen nur vorhandene Seiten,
jede Seite steht in der Sitemap; jede <section> traegt data-shopify. Exit-Code 1 bei Fehlern.
"""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json, re, sys
import xml.etree.ElementTree as ET

HIER = Path(__file__).resolve().parent
args = [a for a in sys.argv[1:] if not a.startswith("--")]
ROOT = Path(args[0]).resolve() if args else HIER.parent / "docs"
LIVE = "--live" in sys.argv
PFAD = "/" if LIVE else "/eco-green-website/"
DOMAIN = "https://eco-green.ch/" if LIVE else "https://leitung-gif.github.io/eco-green-website/"
fehler = []


class Leser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.urls, self.ld, self.ids, self._ld, self.sektionen_ohne = [], [], set(), None, 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        for k in ("href", "src"):
            if a.get(k):
                self.urls.append((tag, a[k]))
        for k in ("srcset", "imagesrcset"):
            if a.get(k):
                self.urls += [(tag, t.strip().split(" ")[0]) for t in a[k].split(",") if t.strip()]
        if tag == "script" and a.get("type") == "application/ld+json":
            self._ld = []
        if tag == "section" and "data-shopify" not in a:
            self.sektionen_ohne += 1

    def handle_data(self, data):
        if self._ld is not None:
            self._ld.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self._ld is not None:
            self.ld.append("".join(self._ld))
            self._ld = None


def datei(pfad):
    """Wurzelpfad (ohne PFAD) zu Datei, wie GitHub Pages oder Shopify ausliefert."""
    p = unquote(pfad).lstrip("/")
    if p == "" or p.endswith("/"):
        kand = [p + "index.html"]
    else:
        kand = [p, p + ".html"]
    for k in kand:
        if (ROOT / k).is_file():
            return ROOT / k
    return None


def intern(url):
    """Interne URL zu Wurzelpfad ohne PFAD, sonst None."""
    if url.startswith(("mailto:", "tel:", "data:", "#", "javascript:")):
        return None
    if url.startswith(DOMAIN):
        return "/" + url[len(DOMAIN):]
    if re.match(r"^https?://|^//", url):
        return None
    if not url.startswith("/"):
        return "RELATIV:" + url
    if not url.startswith(PFAD):
        return "FALSCHER-PFAD:" + url
    return "/" + url[len(PFAD):]


seiten = sorted(ROOT.rglob("*.html"))
geprueft = 0
anker = {}
leser = {}
for f in seiten:
    r = f.relative_to(ROOT).as_posix()
    if r.split("/")[0] in ("fonts", "img"):
        continue
    L = Leser()
    L.feed(f.read_text(encoding="utf-8"))
    leser[r] = L
    anker[r] = L.ids
for r, L in leser.items():
    if L.sektionen_ohne:
        fehler.append(f"{r}: {L.sektionen_ohne} <section> ohne data-shopify")
    for tag, url in L.urls:
        i = intern(url)
        if i is None:
            continue
        geprueft += 1
        if i.startswith(("RELATIV:", "FALSCHER-PFAD:")):
            fehler.append(f"{r}: {i} ({tag})")
            continue
        teile = urlsplit(i)
        ziel = datei(teile.path)
        if ziel is None:
            fehler.append(f"{r}: Ziel fehlt {url} ({tag})")
        elif teile.path.endswith(".html"):
            fehler.append(f"{r}: Link mit .html-Endung {url}")
        elif teile.fragment and ziel.suffix == ".html":
            zr = ziel.relative_to(ROOT).as_posix()
            if teile.fragment not in anker.get(zr, set()):
                fehler.append(f"{r}: Anker #{teile.fragment} fehlt in {zr}")
    if not L.ld:
        fehler.append(f"{r}: kein JSON-LD")
    for block in L.ld:
        try:
            d = json.loads(block)
        except json.JSONDecodeError as e:
            fehler.append(f"{r}: JSON-LD parst nicht: {e}")
            continue
        typen = json.dumps(d)
        if "AggregateRating" in typen or "aggregateRating" in typen:
            fehler.append(f"{r}: AggregateRating im JSON-LD")
        if r == "index.html" and re.search(r'"@type": "(Article|BlogPosting|NewsArticle)"', typen):
            fehler.append("index.html: Startseite als Article ausgezeichnet")

# Manifest
man = ROOT / "site.webmanifest"
if man.is_file():
    for ic in json.loads(man.read_text(encoding="utf-8"))["icons"]:
        i = intern(ic["src"])
        if not i or i.startswith(("RELATIV", "FALSCH")) or datei(i) is None:
            fehler.append(f"site.webmanifest: Icon fehlt {ic['src']}")

# Sitemap
ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
baum = ET.parse(ROOT / "sitemap.xml").getroot()
locs = [e.text for e in baum.iterfind(".//s:loc", ns)]
in_karte = set()
for loc in locs:
    i = intern(loc)
    z = datei(i) if i and not i.startswith(("RELATIV", "FALSCH")) else None
    if z is None:
        fehler.append(f"sitemap.xml: URL ohne Datei {loc}")
    else:
        in_karte.add(z.relative_to(ROOT).as_posix())
for lm in baum.iterfind(".//s:lastmod", ns):
    if not re.fullmatch(r"\d{4}-\d\d-\d\d", lm.text or ""):
        fehler.append(f"sitemap.xml: lastmod ungueltig {lm.text}")
for r in leser:
    if r != "404.html" and r not in in_karte:
        fehler.append(f"sitemap.xml: Seite fehlt {r}")

# Atom-Feed
feed = ROOT / "blogs" / "ratgeber.atom"
if feed.is_file():
    a = {"a": "http://www.w3.org/2005/Atom"}
    fb = ET.parse(feed).getroot()
    for l in fb.iterfind(".//a:entry/a:link", a):
        i = intern(l.get("href"))
        if datei(i) is None:
            fehler.append(f"ratgeber.atom: Eintrag ohne Datei {l.get('href')}")

print(f"{len(leser)} Seiten, {geprueft} interne Links und Dateien, {len(locs)} Sitemap-URLs geprueft in {ROOT}")
for f in fehler:
    print("FEHLER", f)
print("0 Fehler" if not fehler else f"{len(fehler)} Fehler")
sys.exit(1 if fehler else 0)
