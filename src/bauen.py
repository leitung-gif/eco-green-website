"""Generator fuer die Website von Eco Green GmbH. Schreibt nach ../docs (GitHub Pages).

Aufruf:  python bauen.py                       Vorschau nach ../docs (PFAD /eco-green-website/, noindex)
         python bauen.py --live <ordner>       Probebau fuer den Livegang (PFAD /, indexierbar)
         python bauen.py --ziel <ordner>       Vorschau in einen anderen Ordner statt ../docs
         python bauen.py --ratgeber <ordner>   Artikel aus einem anderen Ordner lesen (nur mit --live oder --ziel)
         python bauen.py --shopify [<ordner>]  Export fuer die Uebertragung auf Shopify
         python bauen.py --entwurf             Links und verwandt auf noch fehlende Artikel nur als Warnung
                                               (sonst bricht der Bau ab; vor dem Livegang immer ohne --entwurf)
         python assets.py                      NICHT ganz laufen lassen, siehe assets.py

URL-Aufbau wie auf Shopify, damit sich beim Umzug keine Adresse aendert:
  /                          Start
  /pages/<handle>            Seiten (Datei docs/pages/<handle>.html)
  /blogs/ratgeber            Ratgeber-Uebersicht (docs/blogs/ratgeber.html)
  /blogs/ratgeber/<handle>   Artikel (docs/blogs/ratgeber/<handle>.html)
  /blogs/ratgeber.atom       Atom-Feed
Alle internen Links laufen ueber link() und asset(), absolut mit PFAD, ohne Dateiendung.

Ratgeber-Artikel: src/ratgeber/NN-handle.html, Format siehe lies_artikel(). Fehlt der Ordner oder ist er
leer, entstehen weder Uebersicht noch Navigationseintrag noch Feed.

Fakten und Quellen (abgerufen 21.10.2026, Details im DD-Bericht LG-DD-2026-EG01; nachgefuehrt 12.11.2026):
  Firma, UID, Organe ............ Zefix/SHAB Eco Green GmbH CHE-141.654.180
  FWS-Guetesiegel ............... FWS Guetesiegelliste Juni 2021 und Stand September 2026 (12.11.2026)
                                  Zahl der Siegeltraeger seit 12.11.2026 nicht mehr genannt (nicht belegbar)
  Bewilligung, Abstand 2.5 m .... zh.ch Erdwaermesonden
  Foerdersaetze, Unterlagen ..... Kanton Zuerich, Foerderprogramm 2026 (gelesen 12.11.2026)
  Tiefe, Bohrdauer, Bodentemp. .. EnergieSchweiz Erdsondenbohrung (12.11.2026, wie Ratgeber 06 und 07)
  Heizungsersatz seit 01.09.2022  zh.ch Bauvorschriften Gebaeude Energie
  98 Prozent klimaneutral ....... zh.ch Medienmitteilung 29.05.2024, 379 Gesuche aus zehn Gemeinden,
                                  01.09.2022 bis 31.08.2023 (gelesen 12.11.2026)
  Bewilligung «mehrere Wochen» .. EnergieSchweiz Erdsondenbohrung (12.11.2026)
Fuellinhalte, die Eco Green ersetzt: siehe ../../FILLER.md
"""
from pathlib import Path
from urllib.parse import quote
from html.parser import HTMLParser
from datetime import date, datetime
import json, shutil, re, html, sys, csv

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HIER = Path(__file__).resolve().parent
DOCS = HIER.parent / "docs"
OUT = DOCS
BILDER = json.loads((HIER / "bilder.json").read_text(encoding="utf-8"))
RATGEBER_DIR = HIER / "ratgeber"
SHOPIFY_ZIEL = HIER.parents[1] / "shopify-uebertragung"

# Vorschau auf GitHub Pages. Vor Livegang: BASIS auf https://eco-green.ch/ setzen, VORSCHAU = False.
VORSCHAU_BASIS = "https://leitung-gif.github.io/eco-green-website/"
LIVE_BASIS = "https://eco-green.ch/"
BASIS = VORSCHAU_BASIS
VORSCHAU = True
PFAD = "/" + BASIS.split("/", 3)[3]
STAND = "2026-11-12"          # letzte inhaltliche Aenderung der festen Seiten

def konfig(live):
    """Setzt Basis-URL und Pfad. Vorschau: /eco-green-website/ und noindex. Live: / und indexierbar."""
    global BASIS, VORSCHAU, PFAD, ORG_ID
    BASIS, VORSCHAU = (LIVE_BASIS, False) if live else (VORSCHAU_BASIS, True)
    PFAD = "/" + BASIS.split("/", 3)[3]
    ORG_ID = BASIS + "#firma"

def fehler(text):
    sys.exit("FEHLER: " + text)

# ---------------------------------------------------------------- URLs, zentral
# Seiten-Handles wie auf Shopify (/pages/<handle>). Reihenfolge = Reihenfolge in Shopify-Export und Sitemap.
SEITEN_HANDLES = ["leistungen", "ablauf", "foerderung", "referenzen", "ueber-uns", "kontakt", "impressum", "datenschutz"]
BLOG = "ratgeber"

def pfad_von(ziel):
    """Ziel zu Pfad ohne fuehrenden Schraegstrich und ohne Dateiendung.
    ''/'start' -> Start, Seiten-Handle -> pages/<h>, 'ratgeber' -> blogs/ratgeber,
    'artikel:<h>' -> blogs/ratgeber/<h>, 'feed' -> blogs/ratgeber.atom."""
    if ziel in ("", "start"):
        return ""
    if ziel in SEITEN_HANDLES:
        return "pages/" + ziel
    if ziel == BLOG:
        return "blogs/" + BLOG
    if ziel == "feed":
        return f"blogs/{BLOG}.atom"
    if ziel.startswith("artikel:"):
        return f"blogs/{BLOG}/" + ziel.split(":", 1)[1]
    raise ValueError(f"unbekanntes Linkziel: {ziel}")

def link(ziel, anker=""):
    """Interner Link, absolut ab Wurzel mit PFAD (Vorschau /eco-green-website/, live /)."""
    return PFAD + pfad_von(ziel) + anker

def asset(rel):
    """Datei (CSS, JS, Bild, Schrift), absolut ab Wurzel mit PFAD."""
    return PFAD + rel.lstrip("/")

def voll(ziel):
    """Absolute URL mit Domain fuer Canonical, OG, Sitemap, JSON-LD."""
    return BASIS + pfad_von(ziel)

def datei_von(ziel):
    """Ausgabedatei relativ zu OUT."""
    p = pfad_von(ziel)
    return "index.html" if p == "" else p + ".html"

def tt(iso):
    """2026-11-12 -> 12.11.2026"""
    j, m, t = iso.split("-")
    return f"{t}.{m}.{j}"

TEL = "044 400 20 20"
TEL_LINK = "tel:+41444002020"
MAIL = "info@eco-green.ch"
FWS_PDF = "https://www.fws.ch/wp-content/uploads/2026/09/FWS_GSP_Guetesiegelliste_D_F.pdf"
ZH_SONDEN = "https://www.zh.ch/de/planen-bauen/bauvorschriften/energienutzung-untergrund-wasser/erdwaermesonden.html"
ZH_FOERDER_PDF = "https://www.zh.ch/content/dam/zhweb/bilder-dokumente/themen/umwelt-tiere/energie/energieberatung-und-energiefoerderung/ktzh_foerderprogramm_2026.pdf"
ES_BOHRUNG = "https://www.energieschweiz.ch/wohnen/heizungssysteme/erdsondenbohrung/"
ZH_ENERGIE = "https://www.zh.ch/de/planen-bauen/bauvorschriften/bauvorschriften-gebaeude-energie.html"
ZH_MM_98 = "https://www.zh.ch/de/news-uebersicht/medienmitteilungen/2024/05/revidiertes-energiegesetz-wirkt--ueber-98-prozent-der-ersetzten-.html"
KARTE = "https://www.openstreetmap.org/search?query=Pumpwerkstrasse%2040%2C%208105%20Regensdorf"

# FILLER: Zeiten und Regeln, bis Eco Green sie bestaetigt
BUEROZEIT = "Montag bis Freitag, 07.30 bis 12.00 und 13.30 bis 17.00 Uhr"
EINSATZ = "Kanton Zürich und angrenzende Regionen"

MAIL_TEXT = ("Guten Tag\n\nIch möchte wissen, ob bei mir eine Erdwärmesonde möglich ist.\n\n"
             "Adresse des Grundstücks:\nHeutige Heizung (Öl, Gas, Elektro) und ihr Baujahr:\n"
             "Verbrauch pro Jahr (zum Beispiel Liter Öl):\nBaujahr und Wohnfläche des Hauses:\nTelefon für Rückruf:\n\nFreundliche Grüsse\n")
MAILTO = f"mailto:{MAIL}?subject={quote('Erstabklärung Erdwärmesonde')}&body={quote(MAIL_TEXT)}"

NAV_OHNE_RATGEBER = [("leistungen", "Leistungen"), ("ablauf", "Ablauf"), ("foerderung", "Förderung"),
                     ("referenzen", "Baustellen"), ("ueber-uns", "Über uns"), ("kontakt", "Kontakt")]
NAV_MIT_RATGEBER = NAV_OHNE_RATGEBER[:4] + [(BLOG, "Ratgeber")] + NAV_OHNE_RATGEBER[4:]
NAV = NAV_OHNE_RATGEBER      # wird in main() gesetzt: mit Ratgeber, sobald mindestens ein Artikel da ist
ARTIKEL = []                 # wird in main() aus src/ratgeber gelesen
ENTWURF = "--entwurf" in sys.argv   # Links und Verweise auf noch fehlende Artikel nur als Warnung
FEHLENDE = set()

ORG_ID = BASIS + "#firma"

def esc(s): return html.escape(s, quote=True)

# ---------------------------------------------------------------- Bausteine

def bild(p, key, alt, sizes="(max-width: 900px) 100vw, 40vw", lazy=True, prio=False, breit=None, pos=None):
    w, h, br = BILDER["fotos"][key]
    br = [b for b in br if breit is None or b <= breit] or br[:1]
    srcset = ", ".join(f"{p}img/{key}-{b}.webp {min(b, w)}w" for b in br)
    gross = br[-1] if len(br) == 1 else br[1]
    attr = 'fetchpriority="high"' if prio else ('loading="lazy" decoding="async"' if lazy else "")
    stil = f' style="object-position:{pos}"' if pos else ""   # Ausschnitt, wenn das Raster das Bild beschneidet
    return (f'<img src="{p}img/{key}-{gross}.webp" srcset="{srcset}" sizes="{sizes}" '
            f'width="{w}" height="{h}" alt="{esc(alt)}" {attr}{stil}>')

def preload(key, sizes):
    w, h, br = BILDER["fotos"][key]
    ss = ", ".join(f"{asset('img')}/{key}-{b}.webp {min(b, w)}w" for b in br)
    return f'<link rel="preload" as="image" href="{asset("img")}/{key}-{br[min(1, len(br) - 1)]}.webp" imagesrcset="{ss}" imagesizes="{sizes}" fetchpriority="high">\n'

def bild_gross(key):
    """Groesste Datei eines Fotos, relativ zur Wurzel (img/<key>-<breite>.webp)."""
    return f"img/{key}-{BILDER['fotos'][key][2][-1]}.webp"

def foto(p, key, alt, cap=None, cls="", **kw):
    c = f"<figcaption>{cap}</figcaption>" if cap else ""
    return f'<figure class="foto {cls}">{bild(p, key, alt, **kw)}{c}</figure>'

def org_schema():
    return {
        "@type": ["HomeAndConstructionBusiness", "LocalBusiness"], "@id": ORG_ID,
        "name": "Eco Green", "legalName": "Eco Green GmbH", "alternateName": "Eco Green GmbH",
        "description": "Erdsondenbohrungen für Wärmepumpen im Kanton Zürich, Sitz in Regensdorf. Sondenauslegung, Bewilligungsunterlagen, Erdsondenbohrung, Sondeneinbau und Anbindung bis in den Heizraum. Träger des FWS-Gütesiegels für Erdwärmesonden-Bohrfirmen.",
        "url": BASIS, "logo": BASIS + "img/logo.svg", "image": BASIS + "img/og.jpg",
        "telephone": "+41 44 400 20 20", "email": MAIL,
        "taxID": "CHE-141.654.180",
        "sameAs": ["https://www.zefix.admin.ch/de/search/entity/list/firm/1331210",
                   "https://zh.chregister.ch/cr-portal/auszug/auszug.xhtml?uid=CHE-141.654.180"],
        "address": {"@type": "PostalAddress", "streetAddress": "Pumpwerkstrasse 40", "postalCode": "8105",
                    "addressLocality": "Regensdorf", "addressRegion": "ZH", "addressCountry": "CH"},
        "areaServed": {"@type": "AdministrativeArea", "name": "Kanton Zürich"},
        "hasCertification": {"@type": "Certification", "name": "FWS-Gütesiegel für Erdwärmesonden-Bohrfirmen",
                              "issuedBy": {"@type": "Organization", "name": "Fachvereinigung Wärmepumpen Schweiz FWS", "url": "https://www.fws.ch"},
                              "url": FWS_PDF},
        "knowsAbout": ["Erdwärmesonde", "Erdsondenbohrung", "Sole-Wasser-Wärmepumpe", "Heizungsersatz", "Förderprogramm Kanton Zürich"],
    }

def brot_schema(spur):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": html.unescape(re.sub("<[^>]+>|&shy;", "", n)), "item": voll(u)} for i, (u, n) in enumerate(spur)]}

def seiten_graph(s):
    """JSON-LD einer Seite: Organisation, seitenspezifische Knoten, Brotkrumen, WebPage."""
    if s.get("fehlerseite"):
        return {"@context": "https://schema.org", "@graph": [org_schema()]}
    url = voll(s["ziel"])
    graph = [org_schema()] + s.get("schema", [])
    if s["ziel"]:
        graph.append(brot_schema([("", "Start")] + s["spur"]))
    graph.append({"@type": s.get("seitentyp", "WebPage"), "@id": url + "#seite", "url": url, "name": s["title"],
                  "description": s["desc"], "inLanguage": "de-CH", "isPartOf": {"@id": BASIS + "#website"},
                  "about": {"@id": ORG_ID}, "dateModified": s.get("stand", STAND)})
    return {"@context": "https://schema.org", "@graph": graph}

def head(s):
    fehlerseite = s.get("fehlerseite", False)
    url = voll(s["ziel"])
    ld = json.dumps(seiten_graph(s), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    robots = "noindex, nofollow" if (VORSCHAU or fehlerseite) else "index, follow"
    pre = s.get("preload", "")
    kanon = "" if fehlerseite else f'<link rel="canonical" href="{url}">\n'
    ogurl = "" if fehlerseite else f'<meta property="og:url" content="{url}">\n'
    ogtyp = "article" if s.get("artikel") else "website"
    extra = s.get("head_extra", "")
    if ARTIKEL:
        extra += f'<link rel="alternate" type="application/atom+xml" title="Eco Green Ratgeber" href="{voll("feed")}">\n'
    return f"""<!doctype html>
<html lang="de-CH">
<head>
<meta charset="utf-8">
<script>document.documentElement.classList.add("js")</script>
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(s['title'])}</title>
<meta name="description" content="{esc(s['desc'])}">
<meta name="robots" content="{robots}">
{kanon}<meta name="theme-color" content="#FFFFFF" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#12301A" media="(prefers-color-scheme: dark)">
<meta property="og:type" content="{ogtyp}">
<meta property="og:locale" content="de_CH">
<meta property="og:site_name" content="Eco Green">
<meta property="og:title" content="{esc(s.get('og', s['title']))}">
<meta property="og:description" content="{esc(s['desc'])}">
{ogurl}<meta property="og:image" content="{BASIS}img/{s.get('ogbild', 'og')}.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc(s.get('ogalt', 'Eco Green, Erdwärmesonden aus Regensdorf. Foto einer Baustelle.'))}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(s.get('og', s['title']))}">
<meta name="twitter:description" content="{esc(s['desc'])}">
<meta name="twitter:image" content="{BASIS}img/{s.get('ogbild', 'og')}.jpg">
{extra}<link rel="icon" href="{asset('favicon.svg')}" type="image/svg+xml">
<link rel="icon" href="{asset('favicon.ico')}" sizes="32x32">
<link rel="apple-touch-icon" href="{asset('apple-touch-icon.png')}">
<link rel="manifest" href="{asset('site.webmanifest')}">
<link rel="preload" href="{asset('fonts/schibsted-grotesk-var.woff2')}" as="font" type="font/woff2" crossorigin>
{pre}<link rel="stylesheet" href="{asset('site.css')}?v=6">
<script type="application/ld+json">{ld}</script>
</head>
<body>
<a class="skip" href="#inhalt">Zum Inhalt</a>
"""

def kopf(s):
    aktiv = s["ziel"]
    def a(u, n):
        cur = ' aria-current="page"' if u == aktiv else ""
        return f'<a href="{link(u)}"{cur}>{n}</a>'
    nav = "".join(a(u, n) for u, n in NAV)
    mnav = "".join(a(u, n).replace(f">{n}</a>", f"><span>{n}</span><span class=\"mono\">{i + 1:02d}</span></a>")
                   for i, (u, n) in enumerate([("", "Start")] + NAV))
    return f"""<header class="kopf" data-shopify="header">
 <div class="wrap kopf-in">
  <a class="marke" href="{link('')}" aria-label="Eco Green, zur Startseite"><img src="{asset('img/logo.svg')}" width="150" height="56" alt="Eco Green"></a>
  <nav class="nav" aria-label="Hauptnavigation">{nav}</nav>
  <a class="knopf" href="{link('kontakt')}">Offerte anfragen</a>
  <button class="menuknopf" type="button" aria-expanded="false" aria-controls="menue">Menü</button>
 </div>
</header>
<div class="menue" id="menue" aria-hidden="true" inert data-shopify="menu-drawer">
 <div class="menue-kopf"><img src="{asset('img/logo-hell.svg')}" width="130" height="48" alt="Eco Green"><button class="menue-zu" type="button">Schliessen</button></div>
 <nav aria-label="Menü">{mnav}</nav>
 <div class="knopfreihe"><a class="knopf" href="{link('kontakt')}">Offerte anfragen</a><a class="knopf zwei" href="{TEL_LINK}">{TEL}</a></div>
</div>
<main id="inhalt">
"""

def schluss(p=None, titel="Gilt das auch für Ihr Haus?", text=None):
    """Abschlussblock. Jede Seite gibt ihren eigenen nächsten Schritt mit, der Standard gilt nur fuer Artikel."""
    text = text or "Rufen Sie an oder schreiben Sie uns. Wir beantworten Ihre Frage für Ihre Parzelle und Ihre Heizung."
    return f"""<section class="sektion marke-flaeche schluss" aria-labelledby="schluss-titel" data-shopify="schluss">
 <div class="wrap raster">
  <h2 id="schluss-titel">{titel}</h2>
  <div class="schluss-text">
   <p class="lead">{text}</p>
   <div class="knopfreihe"><a class="knopf" href="{link('kontakt')}">Offerte anfragen</a><a class="knopf zwei" href="{TEL_LINK}">{TEL} anrufen</a></div>
  </div>
 </div>
</section>
"""

def fuss(p=None):
    links = "".join(f'<li><a href="{link(u)}">{n}</a></li>' for u, n in NAV)
    return f"""</main>
<footer class="fuss" data-shopify="footer">
 <div class="wrap">
  <div class="fuss-grid">
   <div>
    <a class="marke" href="{link('')}"><img src="{asset('img/logo-hell.svg')}" width="160" height="60" alt="Eco Green, zur Startseite" loading="lazy"></a>
    <p>Erdsondenbohrungen für Wärmepumpen<br>im Kanton Zürich.</p>
    <a class="fuss-siegel" href="{FWS_PDF}" rel="noopener">FWS-Gütesiegel, Liste September 2026</a>
   </div>
   <div><h2>Seiten</h2><ul>{links}</ul></div>
   <div><h2>Kontakt</h2><ul><li><a href="{TEL_LINK}">{TEL}</a></li><li><a href="mailto:{MAIL}">{MAIL}</a></li><li><a href="{KARTE}" rel="noopener">Pumpwerkstrasse 40<br>8105 Regensdorf</a></li></ul></div>
   <div><h2>Rechtliches</h2><ul><li><a href="{link('impressum')}">Impressum</a></li><li><a href="{link('datenschutz')}">Datenschutz</a></li></ul></div>
  </div>
  <div class="fuss-unten"><span>© 2026 Eco Green GmbH, Regensdorf</span><span>CHE-141.654.180</span></div>
 </div>
</footer>
<nav class="leiste" aria-label="Schnellkontakt" data-shopify="kontaktleiste"><a class="knopf zwei" href="{TEL_LINK}">Anrufen</a><a class="knopf" href="{link('kontakt')}">Offerte anfragen</a></nav>
<script src="{asset('site.js')}?v=4" defer></script>
</body>
</html>
"""

def brotkrumen(s):
    spur = [("", "Start")] + s["spur"]
    li = []
    for i, (u, n) in enumerate(spur):
        if i == len(spur) - 1:
            li.append(f'<li aria-current="page">{n}</li>')
        else:
            li.append(f'<li><a href="{link(u)}">{n}</a></li>')
    return f'<nav class="brot-nav" aria-label="Brotkrumen" style="grid-column:1/-1"><ol class="brot">{"".join(li)}</ol></nav>'

def seitenkopf(s, h1, lead, bildteil="", nach_lead=""):
    textspan = "seitenkopf-text"
    return f"""<section class="seitenkopf">
 <div class="wrap raster">
  {brotkrumen(s)}
  <div class="{textspan}"><h1>{h1}</h1><p class="lead">{lead}</p>{nach_lead}</div>
  {f'<div class="seitenkopf-bild versatz">{bildteil}</div>' if bildteil else ''}
 </div>
</section>
"""

# Namen fuer data-shopify, wo die Sektion kein eigenes hat (aus aria-labelledby oder Klasse abgeleitet)
SEKTIONS_NAMEN = {"h1": "hero", "problem": "heizungsersatz", "leist": "leistungen", "foerder": "foerderung",
                  "vertrauen": "guetesiegel", "siegel": "guetesiegel", "ffaq": "faq-foerderung", "bew": "bewilligung",
                  "bed": "bedingungen", "inst": "installateure", "nicht": "abgrenzung", "gal": "galerie",
                  "proj": "projekte", "adr": "adresse", "ort": "standort", "leute": "geschaeftsleitung",
                  "daten": "fakten", "rechner": "foerderrechner", "brauchen": "angaben", "gesetz": "heizungsersatz",
                  "schluss-titel": "schluss", "rat": "ratgeber"}
GENERISCH = {"sektion", "hell", "dunkel", "marke-flaeche", "flaeche-schraeg", "linie-oben"}

def shopify_attribute(body):
    """Gibt jeder <section> ein data-shopify-Attribut, eindeutig je Seite."""
    gesehen = {}
    def ersetze(m):
        tag = m.group(0)
        if "data-shopify=" in tag:
            name = re.search(r'data-shopify="([^"]+)"', tag).group(1)
            gesehen[name] = gesehen.get(name, 0) + 1
            return tag
        lab = re.search(r'aria-labelledby="([^"]+)"', tag)
        if lab:
            roh = re.sub(r"-(h|titel)$", "", lab.group(1))
            name = SEKTIONS_NAMEN.get(lab.group(1), SEKTIONS_NAMEN.get(roh, roh))
        else:
            kl = re.search(r'class="([^"]+)"', tag)
            teile = [k for k in (kl.group(1).split() if kl else []) if k not in GENERISCH]
            name = teile[0] if teile else "inhalt"
        gesehen[name] = gesehen.get(name, 0) + 1
        if gesehen[name] > 1:
            name = f"{name}-{gesehen[name]}"
        return tag[:-1] + f' data-shopify="{name}">'
    return re.sub(r"<section\b[^>]*>", ersetze, body)

def faq_schema(liste):
    return {"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub("<[^>]+>", "", a)}} for q, a in liste]}

def faq_html(liste):
    return "".join(f'<details><summary>{q}</summary><div class="antwort">{a}</div></details>' for q, a in liste)

# ---------------------------------------------------------------- Inhalte
# Roter Faden: Eco Green nimmt Ihnen den Weg zur Erdsonde ab. Jede Aussage hat EIN Zuhause:
#   Start ........ Lage (Heizungsersatz, 98 Prozent in der Stichprobe des Kantons), warum Erdwaerme, was wir
#                  abnehmen, Beweis (Siegel als Foerderbedingung, eigene Geraete), ein Satz zum Rechner
#   Leistungen ... was wir tun, wo unsere Arbeit aufhoert, Kran
#   Ablauf ....... wer wann was, Dauer (die meiste Zeit braucht die Bewilligung), Regeln auf der Baustelle
# Rollen bei der Auslegung (seit 12.11.2026 ueberall gleich): Den Waermebedarf liefert der Heizungsinstallateur
# oder Planer, Eco Green legt daraus und aus dem Untergrund Anzahl und Laenge der Sonden aus.
#   Foerderung ... Betraege, Bedingungen (Siegel, Gesuch vor der Bohrung), Unterlagen, Rechner, 2027 als Link
#   Ueber uns .... Firma, eigene Geraete und Bohrteam, was das Siegel prueft
#   Kontakt ...... fuenf Angaben, Erstabklaerung kostenlos
# Links in Listentexten als @artikel:<handle> oder @seite:<handle>, aufgeloest mit loese_links() beim Rendern.

FAQ = [
    ("Darf auf meinem Grundstück gebohrt werden?",
     '<p>Das zeigt der Wärmenutzungsatlas des Kantons für jede Parzelle. Wie Sie die Karte lesen, erklärt der Beitrag <a href="@artikel:waermenutzungsatlas-zuerich">Wärmenutzungsatlas Zürich</a>.</p>'),
    ("Was kostet eine Erdsonde?",
     '<p>Der Preis folgt aus den Sondenmetern. Den Wärmebedarf liefert Ihr Heizungsinstallateur oder Planer, daraus und aus dem Untergrund legen wir Anzahl und Länge der Sonden aus. Richtwerte und was den Preis treibt, stehen im Beitrag <a href="@artikel:erdsonde-kosten">Was kostet eine Erdsondenbohrung?</a></p>'),
    ("Wie laut ist eine Erdsondenbohrung?",
     '<p>Laut, aber nur an den Bohrtagen. Wie diese Tage bei Ihnen ablaufen, lesen Sie im <a href="@artikel:erdsondenbohrung-baustelle">Ratgeber zur Baustelle</a>.</p>'),
    ("Was bleibt von der Baustelle im Garten?",
     '<p>Die Sonde liegt im Boden und ist nicht zu sehen. Was nach den Bohrtagen vom Garten bleibt, steht im Beitrag <a href="@artikel:erdsondenbohrung-baustelle">Die Bohrtage im Garten</a>.</p>'),
    ("Wie lange hält die Sonde im Boden?",
     '<p>Laut EnergieSchweiz mindestens 50 Jahre, die Wärmepumpe mindestens 20. Warum der Boden um die Sonde dafür gut geplant sein muss, steht im Beitrag <a href="@artikel:erdsonde-lebensdauer-regeneration">Lebensdauer und Regeneration</a>.</p>'),
]

SCHRITTE = [  # Titel, Dauer (Seite Ablauf), wer (Startseite), Kurztext (Startseite)
    ("Abklärung", "1 bis 3 Arbeitstage", "Eco Green",
     "Sie erfahren, ob Ihre Parzelle eine Sonde zulässt."),
    ("Offerte", "nach der Abklärung", "Eco Green",
     "Eine schriftliche Offerte für Ihre Sonde."),
    ("Bewilligung", "mehrere Wochen", "Gemeinde und AWEL",
     "Wir bereiten das Gesuch vor, Sie unterschreiben."),
    ("Bohrung und Einbau", "2 bis 3 Tage für 100 m", "Eco Green",
     "Ein paar Tage steht das Bohrgerät im Garten. Danach liegt die Sonde im Boden."),
    ("Anschluss", "1 bis 2 Tage", "Eco Green",
     "Die Sonde wird mit dem Heizraum verbunden und befüllt."),
    ("Übergabe", "mit der Schlussrechnung", "Ihr Installateur",
     "Er schliesst die Wärmepumpe an. Das Bohrprotokoll für den Förderbeitrag geht an Sie."),
]

LEISTUNGEN = [
    ("Sondenauslegung", 'Den Wärmebedarf liefert Ihr Heizungsinstallateur oder Planer. Daraus und aus dem Untergrund legen wir Anzahl und <a href="@artikel:erdsonde-tiefe">Länge der Sonden</a> aus. Zu kurz <a href="@artikel:erdsonde-lebensdauer-regeneration">kühlt der Boden über die Jahre aus</a>. Zu lang zahlen Sie Meter, die Sie nicht brauchen.', None),
    ("Bewilligungs&shy;unterlagen", 'Für das <a href="@artikel:erdsonde-bewilligung-zuerich">gewässerschutzrechtliche Gesuch</a> stellen wir zusammen, was die Gemeinde verlangt: Situationsplan mit Sondenstandort, Sondenlänge, Angaben zur Wärmepumpe. Sie unterschreiben und reichen ein.', None),
    ("Erdsonden&shy;bohrung", "Wir bohren zum vereinbarten Termin. Ist die Zufahrt zu eng, hebt ein Kran das Gerät über das Haus.", "efh"),
    ("Sondeneinbau und Verfüllung", "Wir bauen die Sonde ein und verfüllen das Bohrloch von unten nach oben dicht. So fliesst kein Wasser zwischen den Bodenschichten, und die Sonde bleibt Jahrzehnte im Boden.", "sondenkopf"),
    ("Druckprobe und Anbindung", "Jede Sonde wird mit Druck geprüft und im Protokoll festgehalten. Danach verlegen wir die Verbindungsleitungen zum Haus und setzen den Verteiler im Heizraum.", "verteiler"),
    ("Befüllung und Übergabe", "Wir füllen Sonde und Leitungen mit Wärmeträgerflüssigkeit und übergeben die Anlage an Ihren Heizungsinstallateur. Das Bohrprotokoll geht an Sie.", None),
]
KURZ = {  # Kurzfassung fuer die Startseite
    "Sondenauslegung": "Anzahl und Länge der Sonden, aus Wärmebedarf und Untergrund.",
    "Bewilligungs&shy;unterlagen": "Situationsplan und Angaben für das Gesuch an die Gemeinde.",
    "Erdsonden&shy;bohrung": "Zum vereinbarten Termin, auch in engen Gärten.",
    "Sondeneinbau und Verfüllung": "Dicht verfüllt, damit das Grundwasser geschützt bleibt.",
    "Druckprobe und Anbindung": "Mit Druck geprüft und bis in den Heizraum verlegt.",
    "Befüllung und Übergabe": "Ihr Installateur bekommt die Sonde betriebsbereit.",
}

RATGEBER_START = ["erdsonde-kosten", "erdsonde-oder-luft-wasser-waermepumpe", "erdsonde-bewilligung-zuerich"]  # groesste Nachfrage

def rechner_html(eid="rechner"):
    return f"""<div class="rechner" id="{eid}">
   <div class="rechner-ein">
    <label for="kw">Heizleistung der Wärmepumpe</label>
    <div class="feld"><input id="kw" type="number" inputmode="decimal" min="1" max="400" step="0.5" value="12"><span>kW</span></div>
    <label class="wahl" for="zusatz"><input id="zusatz" type="checkbox"><span>Sonde ohne Frostschutzmittel oder mit vollständiger, fossilfreier Regeneration</span></label>
    <p class="klein" style="margin-top:24px">Ein Einfamilienhaus braucht oft 8 bis 15 kW. Die genaue Leistung steht in der Offerte Ihres Installateurs.</p>
   </div>
   <div class="rechner-aus" aria-live="polite">
    <span class="label">Förderbeitrag Kanton Zürich</span>
    <p class="betrag" id="betrag">CHF 6'800</p>
    <div class="rechnung">
     <div><span>Grundbeitrag bis 15 kW</span><span id="r-grund">CHF 6'800</span></div>
     <div><span>CHF 420 pro kW über 15 kW</span><span id="r-mehr">CHF 0</span></div>
     <div><span>Zusatzbeitrag</span><span id="r-zusatz">CHF 0</span></div>
    </div>
    <p class="klein" style="margin-top:16px">Höchstens 50 Prozent der Investition und 50 Watt pro m² Energiebezugsfläche. Massgebend ist die Zusicherung des Kantons.</p>
   </div>
  </div>"""

# ---------------------------------------------------------------- Seiten

def schema_svg():
    # Ruhiges Schema: Haus, Waermepumpe, Sonde bis 220 m. 0 m auf y=120, 2,2 px pro Meter.
    Y0, K = 120, 2.2
    tiefen = "".join(
        f'<line x1="300" y1="{Y0 + m * K:.0f}" x2="312" y2="{Y0 + m * K:.0f}" stroke="#121712" stroke-width="1.5"/>'
        f'<text class="mono-t" x="318" y="{Y0 + 5 + m * K:.0f}">{m} m</text>'
        for m in range(0, 251, 50))
    return f"""<svg class="schema" viewBox="0 0 400 690" role="img" aria-label="Schema einer Erdwärmesonde: Haus mit Wärmepumpe, darunter eine Sonde bis rund 220 Meter Tiefe. Ab 10 bis 15 Metern hat der Boden ganzjährig 8 bis 12 Grad, je 100 Meter wird es rund 3 Grad wärmer.">
<rect x="0" y="120" width="300" height="570" fill="#F3F7EF"/>
<rect x="0" y="120" width="300" height="10" fill="#29662F"/>
<line x1="0" y1="168" x2="300" y2="168" stroke="#C9DEBF" stroke-width="1"/>
<line x1="0" y1="280" x2="300" y2="280" stroke="#C9DEBF" stroke-width="1"/>
<rect x="40" y="48" width="112" height="72" fill="#FFFFFF" stroke="#121712" stroke-width="2"/>
<polygon points="32,50 96,10 160,50" fill="#29662F"/>
<rect x="164" y="84" width="40" height="36" fill="#FFFFFF" stroke="#121712" stroke-width="2"/>
<text x="166" y="76" class="mono-t">WP</text>
<path d="M184 120 V 104 M 228 120 V 102 H 184" fill="none" stroke="#121712" stroke-width="2"/>
<rect id="sonde" x="222" y="120" width="12" height="{220 * K:.0f}" fill="#5EA33B"/>
<line x1="300" y1="120" x2="300" y2="690" stroke="#121712" stroke-width="1.5"/>
{tiefen}
<g>
 <circle cx="228" cy="{Y0 + 15 * K:.0f}" r="5" fill="#121712"/><text x="16" y="{Y0 + 20 * K:.0f}">ab 15 m: 8 bis 12 °C</text>
 <circle cx="228" cy="{Y0 + 200 * K:.0f}" r="5" fill="#121712"/><text x="16" y="{Y0 + 205 * K:.0f}">200 m: rund 6 °C wärmer</text>
 <text x="16" y="{Y0 + 110 * K:.0f}" fill="#4A5348">Kies, Sand, Fels</text>
</g>
</svg>"""


def seite_start():
    s = {"ziel": "", "spur": [],
         "title": "Erdsondenbohrung Zürich | Eco Green, Regensdorf",
         "og": "Eco Green: Erdwärmesonden für Ihre Wärmepumpe",
         "desc": "Erdsondenbohrungen für Wärmepumpen im Kanton Zürich. Eco Green aus Regensdorf prüft Ihr Grundstück, bereitet die Bewilligung vor und bohrt am vereinbarten Tag.",
         "preload": preload("garten", "(max-width: 900px) 100vw, 40vw")}
    s["schema"] = [{"@type": "WebSite", "@id": BASIS + "#website", "url": BASIS, "name": "Eco Green", "inLanguage": "de-CH", "publisher": {"@id": ORG_ID}},
                   faq_schema(FAQ)]
    nach = {a["meta"]["handle"]: a for a in ARTIKEL}
    start_artikel = [nach[h] for h in RATGEBER_START if h in nach] or ARTIKEL[:3]
    s["stand"] = max([STAND] + [a["meta"]["stand"] for a in start_artikel])   # Startseite zeigt diese drei Artikel
    p = PFAD
    leist = "".join(f'<article><div><h3>{t}</h3><p>{KURZ[t]}</p></div></article>'
                    for i, (t, _x, _b) in enumerate(LEISTUNGEN))
    schritte = "".join(f'<li class="schritt"><div class="kopfnr"><span>{i + 1:02d}</span><span class="mono">{wer}</span></div><h3>{t}</h3><p>{x}</p></li>'
                       for i, (t, _dauer, wer, x) in enumerate(SCHRITTE))
    bilder = "".join(foto(p, k, a, c, sizes="(max-width: 900px) 100vw, 33vw") for k, a, c in [
        ("kran", "Ein Kran hebt ein Raupenbohrgerät über ein Wohnhaus", "Das Bohrgerät schwebt am Kran über das Dach."),
        ("team-nah", "Bohrmeister im Eco-Green-Shirt am Bohrgerät", "Bohrmeister am Gerät."),
        ("verteiler-14", "Sondenverteiler mit 14 nummerierten Anschlüssen in einem Technikraum", "Verteiler für 14 Sonden."),
    ])
    body = f"""<section class="hero" aria-labelledby="h1">
 <div class="wrap raster">
  <div class="hero-text">
   <span class="label">Erdsondenbohrungen im Kanton Zürich</span>
   <h1 id="h1">Erdwärmesonden für Ihre Wärmepumpe.</h1>
   <p class="lead">Wir nehmen Ihnen den Weg zur Erdsonde ab. Vom ersten Blick auf Ihr Grundstück bis zur Sonde, die im Heizraum angeschlossen ist.</p>
   <div class="knopfreihe"><a class="knopf" href="{link('kontakt')}">Offerte anfragen</a><a class="knopf zwei" href="{TEL_LINK}">{TEL}</a></div>
  </div>
  <div class="hero-bild versatz">{foto(p, "garten", "Raupenbohrgerät von Eco Green bohrt im Garten eines Einfamilienhauses", "Bohrung im Garten eines Einfamilienhauses.", lazy=False, prio=True)}</div>
  <ul class="belege">
    <li><a href="{FWS_PDF}" rel="noopener"><b>FWS-Gütesiegel</b>für Erdwärmesonden-Bohrfirmen</a></li>
    <li><a href="#foerderung"><b>Förderbeitrag</b>Ihren Betrag gleich hier rechnen</a></li>
    <li><b>Einsatzgebiet</b>{EINSATZ}</li>
    <li><b>Bewilligung</b>Gesuch von uns vorbereitet</li>
  </ul>
 </div>
</section>

<section class="sektion hell" aria-labelledby="problem-h">
 <div class="wrap raster">
  <div class="kopfzeile">
   <div><span class="label">Heizungsersatz</span><h2 id="problem-h">Ihre Öl- oder Gasheizung muss ersetzt werden?</h2></div>
   <div><p class="lead">Seit 01.09.2022 kommt im Kanton Zürich beim Ersatz einer Öl- oder Gasheizung grundsätzlich nur noch ein erneuerbares System ins Haus. In einer Stichprobe aus zehn Gemeinden wurden im ersten Jahr über 98 Prozent der fossilen Heizungen durch klimaneutrale Systeme ersetzt. Die Ausnahmen erklärt der Beitrag <a href="{link('artikel:heizungsersatz-zuerich-energiegesetz')}">Heizungsersatz im Kanton Zürich</a>.</p>
   <p class="lead">Öl und Gas kosten jedes Jahr. Die Wärme aus dem Boden kostet nichts, Sie bezahlen nur den Strom für die Pumpe. Wie sich das gegen die Luft rechnet, zeigt der <a href="{link('artikel:erdsonde-oder-luft-wasser-waermepumpe')}">Vergleich von Erdsonde und Luft-Wasser-Wärmepumpe</a>.</p></div>
  </div>
  <p class="quelle" style="grid-column:1/-1">Quellen: <a href="{ZH_ENERGIE}" rel="noopener">Kanton Zürich, Bauvorschriften Gebäude und Energie</a>. <a href="{ZH_MM_98}" rel="noopener">Kanton Zürich, Medienmitteilung vom 29.05.2024</a>, 379 Gesuche vom 01.09.2022 bis 31.08.2023.</p>
 </div>
</section>

<section class="sektion" aria-labelledby="prinzip-h">
 <div class="wrap raster">
  <div class="prinzip-bild">{schema_svg()}</div>
  <div class="prinzip-text">
   <span class="label">So funktioniert Erdwärme</span>
   <h2 id="prinzip-h">Der Boden heizt Ihr Haus.</h2>
   <ol class="teile" style="margin-top:32px">
    <li><div><h3>Erdwärmesonde</h3><p>Ein Rohr in einem Bohrloch, üblich sind laut EnergieSchweiz <a href="{link('artikel:erdsonde-tiefe')}">100 bis 300 Meter Tiefe</a>. Eine Flüssigkeit zirkuliert darin und nimmt die Wärme des Bodens auf.</p></div></li>
    <li><div><h3>Wärmepumpe</h3><p>Sie hebt die Temperatur auf das Niveau Ihrer Heizung. Rund drei Viertel der Wärme stammen aus dem Boden, der Rest ist Strom.</p></div></li>
    <li><div><h3>Heizung und Warmwasser</h3><p>Bodenheizung oder Radiatoren werden versorgt wie bisher. Im Sommer kann die Sonde das Haus leicht kühlen.</p></div></li>
   </ol>
   <a class="weiter" href="{link('kontakt')}">Grundstück prüfen lassen</a>
  </div>
 </div>
</section>

<section class="sektion hell" aria-labelledby="leist-h">
 <div class="wrap raster">
  <div class="kopfzeile">
   <div><span class="label">Leistungen</span><h2 id="leist-h">Alles bis zur Sonde im Heizraum.</h2></div>
   <p>Ihr Heizungsinstallateur plant die Wärmepumpe. Wir holen die Wärme dafür aus dem Boden.</p>
  </div>
  <div class="leistungen">{leist}</div>
  <div style="grid-column:1/-1"><a class="weiter" href="{link('leistungen')}">Alle Leistungen im Detail</a></div>
 </div>
</section>

<section class="sektion" aria-labelledby="ablauf-h">
 <div class="wrap raster">
  <div class="kopfzeile">
   <div><span class="label">Ablauf</span><h2 id="ablauf-h">In sechs Schritten zur Erdwärme.</h2></div>
   <p>Bei jedem Schritt steht fest, wer was tut. Den grössten Teil übernehmen wir.</p>
  </div>
  <ol class="schritte">{schritte}</ol>
  <div style="grid-column:1/-1"><a class="weiter" href="{link('ablauf')}">Ablauf im Detail</a></div>
 </div>
</section>

<section class="sektion dunkel" aria-labelledby="vertrauen-h">
 <div class="wrap raster">
  <div class="siegel">
   <span class="label">FWS-Gütesiegel</span>
   <h2 id="vertrauen-h"><span class="gross">Geprüft</span> von der Fachvereinigung Wärmepumpen Schweiz.</h2>
   <p style="margin-top:24px">Ohne dieses Siegel der Bohrfirma zahlt der Kanton Zürich keinen <a href="{link('foerderung')}">Förderbeitrag</a>.</p>
   <a class="weiter" href="{FWS_PDF}" rel="noopener">Gütesiegelliste ansehen</a>
  </div>
  <div class="vertrauen-daten">
   <dl class="daten">
    <div><dt>Gütesiegel</dt><dd>Auf der Liste der FWS im Juni 2021 und mit Stand September 2026</dd></div>
    <div><dt>Geräte</dt><dd>Eigene Raupenbohrgeräte und eigenes Bohrteam</dd></div>
   </dl>
  </div>
  <div class="bildreihe">{bilder}</div>
  <div style="grid-column:1/-1"><a class="weiter" href="{link('referenzen')}">Baustellen ansehen</a></div>
 </div>
</section>

<section class="sektion flaeche-schraeg" id="foerderung" aria-labelledby="foerder-h">
 <div class="wrap raster">
  <div class="foerder-text">
   <span class="label">Förderung</span>
   <h2 id="foerder-h">Der Kanton Zürich zahlt mit.</h2>
   <p class="lead" style="margin-top:24px">Bis 15 kW zahlt der Kanton CHF 6'800, wenn Ihre Erdwärmepumpe eine fossile oder elektrische Heizung ersetzt. Ihren Betrag zeigt der Rechner.</p>
   <a class="weiter" href="{link('foerderung')}">Bedingungen und Unterlagen</a>
   <p class="quelle">Quelle: Kanton Zürich, <a href="{ZH_FOERDER_PDF}" rel="noopener">Förderprogramm 2026</a>.</p>
  </div>
  {rechner_html()}
 </div>
</section>

{ratgeber_start(start_artikel)}
<section class="sektion hell" aria-labelledby="faq-h">
 <div class="wrap raster">
  <div class="faq-kopf"><span class="label">Fragen</span><h2 id="faq-h">Fragen vor der Bohrung.</h2><p style="margin-top:24px">Ihre Frage fehlt? <a href="{TEL_LINK}">{TEL}</a></p></div>
  <div class="faq">{loese_links(faq_html(FAQ))}</div>
 </div>
</section>
{schluss(p, "Prüfen wir Ihr Grundstück.", "Schicken Sie uns Adresse und heutige Heizung. Wir melden uns mit einer ersten Einschätzung zu Ihrer Sonde.")}"""
    return s, body


def seite_leistungen():
    s = {"ziel": "leistungen", "ogbild": "og-leistungen", "spur": [("leistungen", "Leistungen")],
         "title": "Erdwärmesonde bohren und anschliessen | Eco Green",
         "desc": "Was Eco Green für Ihre Erdwärmesonde übernimmt: Auslegung, Bewilligungsunterlagen, Bohrung, Einbau, Druckprobe und Anschluss bis in den Heizraum."}
    p = PFAD
    s["schema"] = [{"@type": "Service", "name": t.replace("&shy;", ""), "description": re.sub("<[^>]+>", "", x), "serviceType": "Erdwärmesonde", "provider": {"@id": ORG_ID},
                    "areaServed": {"@type": "AdministrativeArea", "name": "Kanton Zürich"}} for t, x, _b in LEISTUNGEN]
    reihen = ""
    for i, (t, x, b) in enumerate(LEISTUNGEN):
        rechts = ""
        if b:
            alt = {"efh": "Bohrgerät von Eco Green vor einem Einfamilienhaus, im Vordergrund eine Rolle Sondenrohr",
                   "sondenkopf": "Eingebaute Erdwärmesonde im Bohrloch, das Rohrende mit gelber Schutzkappe",
                   "verteiler": "Sondenverteiler mit zwei Manometern"}[b]
            rechts = f'<div class="bild versatz">{foto(p, b, alt, sizes="(max-width: 900px) 100vw, 33vw")}</div>'
        reihen += f'<article class="leistung"><span class="nr">{i + 1:02d}</span><div class="inhalt"><h2>{t}</h2><p>{loese_links(x)}</p></div>{rechts}</article>'
    body = seitenkopf(s, "Alles, was zur Erdsonde gehört.", "Wir übernehmen alles zwischen Ihrem Garten und dem Verteiler im Heizraum.") + f"""
<section class="sektion" data-shopify="leistungsliste"><div class="wrap raster">{reihen}</div></section>
<section class="sektion dunkel" aria-labelledby="inst-h">
 <div class="wrap raster">
  <div class="links"><span class="label">Für Installateure und Planer</span><h2 id="inst-h">Sie planen die Wärmepumpe, wir liefern die Sonde.</h2></div>
  <div class="rechts">
   <p class="lead">Protokolle und Sondenlänge erhalten Sie so, wie Ihr Dossier sie braucht. Den Siegelnachweis für das Fördergesuch Ihres Kunden legen wir bei.</p>
   <p>Den Bohrtermin stimmen wir mit Ihrer Bauleitung ab.</p>
   <div class="knopfreihe"><a class="knopf" href="mailto:{MAIL}?subject={quote('Anfrage Installateur: Erdsonde')}">Projekt anfragen</a></div>
  </div>
 </div>
</section>
<section class="sektion hell" aria-labelledby="nicht-h">
 <div class="wrap raster">
  <div class="links"><h2 id="nicht-h">Was nicht zu uns gehört.</h2></div>
  <div class="rechts">
   <p class="lead">Die Wärmepumpe selbst liefert und montiert Ihr Heizungsinstallateur. Unsere Arbeit endet am Verteiler im Heizraum.</p>
   <p>Haben Sie noch keinen Installateur, nennen wir Ihnen Betriebe aus der Region, mit denen wir schon gebaut haben.</p>
  </div>
 </div>
</section>
{schluss(p, "Wie viele Meter braucht Ihr Haus?", "Ihr Verbrauch an Öl oder Gas im letzten Jahr reicht für eine erste Rechnung. Rufen Sie an oder schreiben Sie uns die Zahl.")}"""
    return s, body


def seite_ablauf():
    s = {"ziel": "ablauf", "ogbild": "og-ablauf", "preload": preload("aggregat-quer", "(max-width: 900px) 100vw, 33vw"), "spur": [("ablauf", "Ablauf")],
         "stand": "2026-11-13",   # Kopfbild getauscht
         "title": "Ablauf Erdsondenbohrung im Kanton Zürich | Eco Green",
         "desc": "Wer wann was tut, von der Abklärung bis zur Übergabe: die Dauer jedes Schritts, die Bewilligung beim AWEL und unsere Regeln auf der Baustelle im Garten."}
    p = PFAD
    sie = [
        "Sie schicken uns die fünf Angaben aus der E-Mail-Vorlage. Fotos vom Heizraum helfen uns.",
        "Sie entscheiden und reichen mit der Offerte das Fördergesuch auf der Gesuchplattform des Kantons ein.",
        "Sie unterschreiben das Bewilligungsgesuch und reichen es bei der Gemeinde ein.",
        "Sie sorgen für eine freie Zufahrt.",
        "Sie stimmen den Anschlusstermin mit Ihrem Heizungsinstallateur ab.",
        "Sie reichen Bohrprotokoll und Rechnung mit den Unterlagen der Wärmepumpe beim Kanton ein.",
    ]
    wir = [
        "Wir lesen Ihre Parzelle im Wärmenutzungsatlas und schätzen, wie viele Meter Sonde Ihr Haus braucht.",
        "Wir erstellen die Offerte und legen den Nachweis unseres Gütesiegels bei.",
        "Wir liefern die Unterlagen fertig zum Unterschreiben. Gebohrt wird, sobald die Bewilligung vorliegt.",
        "Wir bohren und setzen die Sonde ins Bohrloch.",
        "Wir verbinden die Sonde mit dem Heizraum und füllen das System.",
        "Wir übergeben Protokolle und Rechnung. Danach räumen wir die Baustelle.",
    ]
    phasen = "".join(
        f'<article class="phase"><div class="phase-kopf"><span class="nr">{i + 1:02d}</span><h2>{t}</h2><span class="mono">{dauer}</span></div>'
        f'<div class="phase-sie"><h3>Was Sie tun</h3><p>{sie[i]}</p></div><div class="phase-wir"><h3>Was wir tun</h3><p>{wir[i]}</p></div></article>'
        for i, (t, dauer, _wer, _x) in enumerate(SCHRITTE))
    body = seitenkopf(s, "Ablauf einer Erdsondenbohrung.", "Die meiste Zeit braucht die Bewilligung. Gebohrt wird an wenigen Tagen.",
                      foto(p, "aggregat-quer", "Rotes Bohrgerät, Stromaggregat mit Eco-Green-Logo und Sondenrolle auf einem Bohrplatz", "Bohrplatz mit Bohrgerät und Stromaggregat.", lazy=False, prio=True, sizes="(max-width: 900px) 100vw, 33vw")) + f"""
<section class="sektion" data-shopify="phasen"><div class="wrap raster">{phasen}</div></section>
<section class="sektion hell" aria-labelledby="bew-h">
 <div class="wrap raster">
  <div class="links">
   <span class="label">Bewilligung</span>
   <h2 id="bew-h">Was der Kanton verlangt.</h2>
   <ul class="punkte" style="margin-top:32px">
    <li>Jede Erdwärmesonde braucht eine <a href="{link('artikel:erdsonde-bewilligung-zuerich')}">gewässerschutzrechtliche Bewilligung</a> des AWEL.</li>
    <li>Eingereicht wird bei der Baubehörde der Gemeinde, auch über eBaugesucheZH.</li>
    <li>Ob Sonden auf einer Parzelle zulässig sind, steht im <a href="{link('artikel:waermenutzungsatlas-zuerich')}">Wärmenutzungsatlas</a>.</li>
    <li>Unter 2.5 Meter Abstand zur Grenze braucht es die Zustimmung des Nachbarn.</li>
    <li>Das AWEL empfiehlt eine Bohrfirma mit dem Gütesiegel für Erdwärmesonden-Bohrfirmen.</li>
   </ul>
   <p class="quelle">Quelle: <a href="{ZH_SONDEN}" rel="noopener">Kanton Zürich, Erdwärmesonden</a></p>
  </div>
  <div class="rechts">
   <span class="label">Baustelle</span>
   <h2>Unsere Regeln vor Ort.</h2>
   <ul class="punkte" style="margin-top:32px">
    <li>Gebohrt wird Montag bis Freitag, 07.00 bis 12.00 und 13.00 bis 18.00 Uhr.</li>
    <li>An Wochenenden und Feiertagen bleibt das Gerät still.</li>
    <li>Ihre Nachbarn erhalten eine Woche vor Bohrbeginn einen Brief mit Datum und Dauer.</li>
    <li>Rasen und Zufahrt schützen wir mit Platten unter dem Gerät.</li>
    <li>Bohrschlamm und Bohrwasser fangen wir in Mulden auf und entsorgen sie nach den Vorgaben des Kantons.</li>
    <li>Sie haben eine Ansprechperson mit direkter Handynummer.</li>
   </ul>
   <p class="quelle">Dauer von Bewilligung und Bohrung: <a href="{ES_BOHRUNG}" rel="noopener">EnergieSchweiz, Erdsondenbohrung</a>. Was Sie vor den Bohrtagen vorbereiten, steht im Beitrag <a href="{link('artikel:erdsondenbohrung-baustelle')}">Die Bohrtage im Garten</a>.</p>
  </div>
 </div>
</section>
{schluss(p, "Starten wir mit Schritt 1.", "Rufen Sie an oder schicken Sie uns die E-Mail-Vorlage von der Kontaktseite. Mehr braucht die Abklärung nicht.")}"""
    return s, body


FOERDER_FAQ = [
    ("Wann darf nach dem Gesuch gebohrt werden?",
     "<p>Für den Förderbeitrag genügt die automatische Eingangsbestätigung der Gesuchplattform, der Kanton zählt die Bohrung als Baubeginn. Diese Bestätigung betrifft nur die Förderung. Gebohrt wird erst, wenn die gewässerschutzrechtliche Bewilligung vorliegt. Die verbindliche Förderzusage folgt innert vier Wochen nach Eingang der vollständigen Unterlagen.</p>"),
    ("Bekomme ich auch beim Neubau einen Beitrag?",
     "<p>Vom Kanton nicht. Manche Gemeinden haben eigene Programme, fragen Sie dort nach.</p>"),
    ("Wie viel Zeit habe ich nach der Zusage?",
     "<p>Zwei Jahre ab Datum der Zusicherung, um die Anlage zu bauen und den Abschluss einzureichen. Das Geld kommt 30 Tage nach dem Auszahlungsschreiben.</p>"),
    ("Gibt es mehr Geld ohne Frostschutzmittel?",
     '<p>Ja. Für Sonden ohne Frostschutzmittel oder mit vollständiger, fossilfreier <a href="@artikel:erdsonde-lebensdauer-regeneration">Regeneration</a> zahlt der Kanton zusätzlich CHF 3\'000 plus CHF 100 pro kW über 15 kW. Ob sich das für Ihr Haus lohnt, hängt von Sondenlänge und Wärmebedarf ab. Wir rechnen beide Varianten.</p>'),
]

def seite_foerderung():
    s = {"ziel": "foerderung", "ogbild": "og-foerderung", "spur": [("foerderung", "Förderung")],
         "title": "Förderbeitrag Erdwärmepumpe Zürich mit Rechner | Eco Green",
         "desc": "Was der Kanton Zürich an eine Erdwärmepumpe zahlt: CHF 6'800 bis 15 kW, die Bedingungen, die Unterlagen und ein Rechner. Gesuch vor der Bohrung."}
    p = PFAD
    s["schema"] = [faq_schema(FOERDER_FAQ)]
    body = seitenkopf(s, "Förderbeitrag Kanton Zürich.", "Wer von Öl, Gas oder Strom auf Erdwärme wechselt, bekommt Geld vom Kanton. Wie viel, zeigt der Rechner.") + f"""
<section class="sektion flaeche-schraeg" aria-labelledby="rechner-h">
 <div class="wrap raster">
  <div class="foerder-text">
   <h2 id="rechner-h">Was der Kanton an Ihre Anlage zahlt.</h2>
   <p class="lead" style="margin-top:24px">Bis 15 kW Heizleistung bekommen Sie CHF 6'800, für jedes weitere kW CHF 420.</p>
   <p>Was für Gesuche ab 2027 gilt, verfolgen wir im <a href="{link('artikel:foerderung-heizungsersatz-2027')}">Ratgeber zur Förderung 2027</a>.</p>
   <p class="quelle">Sätze: Kanton Zürich, <a href="{ZH_FOERDER_PDF}" rel="noopener">Förderprogramm 2026</a>, Sole-Wasser-Wärmepumpe.</p>
  </div>
  {rechner_html()}
 </div>
</section>
<section class="sektion hell" aria-labelledby="bed-h">
 <div class="wrap raster">
  <div class="links">
   <h2 id="bed-h">Bedingungen.</h2>
   <ul class="punkte" style="margin-top:32px">
    <li>Die Anlage ersetzt eine Öl-, Gas- oder Elektroheizung.</li>
    <li>Das Gebäude besteht schon.</li>
    <li>Die Wärmepumpe ist die Hauptheizung, ohne fossile Zweitheizung.</li>
    <li>Bis 15 kW: Anlagezertifikat Wärmepumpen-System-Modul (WPSM).</li>
    <li>Die Bohrfirma hat ein gültiges <a href="{link('artikel:guetesiegel-erdwaermesonden-bohrfirma')}">FWS-Gütesiegel</a>.</li>
    <li>Das Gesuch ist vor der Bohrung eingereicht.</li>
   </ul>
  </div>
  <div class="rechts">
   <h2>Unterlagen.</h2>
   <p class="unter">Vor der Bohrung</p>
   <ul class="punkte">
    <li>Offerte für den Heizungsersatz</li>
    <li>Foto der alten Heizung und des Typenschilds</li>
    <li>Pläne mit der Energiebezugsfläche</li>
    <li>Bestätigung WPSM und Gütesiegel der Bohrfirma</li>
   </ul>
   <p class="unter">Nach dem Bau</p>
   <ul class="punkte">
    <li>Anlagezertifikat WPSM</li>
    <li>Rechnungen für Heizung und Bohrung</li>
    <li>Bohrprotokoll</li>
   </ul>
   <p class="klein" style="margin-top:16px">Offerte, Gütesiegel, Rechnung und Bohrprotokoll für die Bohrung liefern wir.</p>
  </div>
 </div>
</section>
<section class="sektion dunkel" aria-labelledby="gesetz-h">
 <div class="wrap raster">
  <div class="links"><h2 id="gesetz-h">Heizungsersatz im Kanton Zürich.</h2></div>
  <div class="rechts">
   <p class="lead">Welche Heizung beim Ersatz noch erlaubt ist und welche Ausnahmen gelten, erklärt unser Beitrag zum <a href="{link('artikel:heizungsersatz-zuerich-energiegesetz')}">Zürcher Energiegesetz</a>.</p>
  </div>
 </div>
</section>
<section class="sektion" aria-labelledby="ffaq-h">
 <div class="wrap raster">
  <div class="faq-kopf"><h2 id="ffaq-h">Fragen zur Förderung.</h2></div>
  <div class="faq">{loese_links(faq_html(FOERDER_FAQ))}</div>
 </div>
</section>
{schluss(p, "Ihr Gesuch, bevor gebohrt wird.", "Fragen Sie uns früh an. Dann liegen unsere Unterlagen bereit, wenn Sie das Gesuch einreichen.")}"""
    return s, body


PROJEKTE = [
    ("Einfamilienhaus", "Regensdorf", "Ölheizung", "2 × 180 m", "Bohrung im Garten, Zufahrt über den Vorplatz"),
    ("Einfamilienhaus", "Zürcher Unterland", "Ölheizung", "1 × 230 m", "Zufahrt zu eng, Gerät per Kran"),
    ("Mehrfamilienhaus", "Furttal", "Gasheizung", "6 × 200 m", "Sondenfeld am Siedlungsrand"),
    ("Neubau Doppelhaus", "Bezirk Dielsdorf", "keine, Neubau", "3 × 160 m", "Bohrung vor dem Aushub"),
    ("Bauernhaus", "Zürcher Weinland", "Elektroheizung", "2 × 210 m", "Bohrung zwischen Bauernhaus und Wohnhaus"),
    ("Reihenhaus", "Limmattal", "Ölheizung", "1 × 200 m", "eine Sonde für das ganze Haus"),
]

def seite_referenzen():
    s = {"ziel": "referenzen", "ogbild": "og-referenzen", "preload": preload("maylin", "(max-width: 900px) 50vw, 25vw"), "spur": [("referenzen", "Baustellen")],
         "stand": "2026-11-13",   # Galerie: Kompressor raus, Kran rein
         "title": "Baustellen: Erdsondenbohrungen im Kanton Zürich | Eco Green",
         "desc": "Fotos von Baustellen von Eco Green und Beispiele zur Orientierung: wie viele Sonden und welche Tiefe ein Haus im Kanton Zürich je nach Grösse braucht."}
    p = PFAD
    zeilen = "".join(f'<tr><td data-label="Objekt">{o}</td><td data-label="Region">{ort}</td><td data-label="Ersetzt">{alt}</td><td data-label="Sonden" class="zahl">{sonden}</td><td data-label="Besonderheit">{notiz}</td></tr>'
                     for o, ort, alt, sonden, notiz in PROJEKTE)
    # Fotos vom 12.11.2026 (Mahissa Ganz-Yasri) zuerst, dazu vier von 2022. pos = Ausschnitt im Hochformat.
    # Kein Bild mit Aufkleber «gadola» (Entscheid Sinan 13.11.2026): Kompressor raus, dafuer der Kran.
    gal = "".join(foto(p, k, a, c, sizes="(max-width: 900px) 50vw, 25vw", lazy=i > 3, prio=i == 0, pos=pos) for i, (k, a, c, pos) in enumerate([
        ("maylin", "Rotes Raupenbohrgerät von Eco Green auf einem Bauplatz zwischen Wohnhäusern", "Bohrgerät Maylin auf dem Bauplatz.", None),
        ("garten", "Türkises Raupenbohrgerät im Garten eines Einfamilienhauses", "Garten eines Einfamilienhauses.", None),
        ("team", "Bohrmeister im grünen Eco-Green-Shirt vor dem Bohrgerät", "Bohrmeister am Gestänge.", None),
        ("hang", "Gelbes Raupenbohrgerät an einem Hang am Waldrand", "Bohrung am Hang.", None),
        ("efh", "Bohrgerät vor einem Einfamilienhaus, daneben eine Rolle Sondenrohr", "Vor dem Einbau: die Sonde auf der Rolle.", "42% 50%"),
        ("dorf", "Bohrgerät zwischen Bauernhaus und Wohnhaus", "Zwischen Bauernhaus und Wohnhaus.", None),
        ("aggregat", "Rotes Bohrgerät und Stromaggregat mit Eco-Green-Logo", "Bohrgerät mit eigenem Stromaggregat.", None),
        ("feld", "Bohrgerät und Bagger am Siedlungsrand im Winter", "Siedlungsrand im Winter.", None),
        ("verteiler-grube", "Sondenverteiler in einer Grube, die Leitungen führen ins Erdreich", "Verteiler in der Grube.", None),
        ("nachher", "Asphaltierter Vorplatz nach der Bohrung, aus dem Boden ragt nur das Sondenrohr mit Schutzkappe", "Nach der Bohrung bleibt das Sondenrohr.", "62% 50%"),
        ("kran", "Ein Kran hebt ein Raupenbohrgerät über ein Wohnhaus", "Am Kran über das Dach.", None),
        ("verteiler-14", "Sondenverteiler mit 14 nummerierten Anschlüssen in einem Technikraum", "Verteiler für 14 Sonden.", None),
    ]))
    body = seitenkopf(s, "Baustellen.", "Alle Bilder auf dieser Website stammen von Baustellen von Eco Green. So sieht es aus, wenn wir bei Ihnen bohren.") + f"""
<section class="sektion" aria-labelledby="gal-h">
 <div class="wrap raster">
  <h2 id="gal-h" class="sr">Fotos von Baustellen</h2>
  <div class="galerie">{gal}</div>
 </div>
</section>
<section class="sektion hell" aria-labelledby="proj-h">
 <div class="wrap raster">
  <div class="kopfzeile"><div><h2 id="proj-h">Beispiele zur Orientierung.</h2></div><p>Diese Zeilen sind Beispiele und keine Kundenprojekte. Sie zeigen, wie Sondenzahl und Tiefe mit dem Haus wechseln.</p></div>
  <div class="tabelle-rahmen"><table class="tabelle">
   <thead><tr><th scope="col">Objekt</th><th scope="col">Region</th><th scope="col">Ersetzt</th><th scope="col">Sonden</th><th scope="col">Besonderheit</th></tr></thead>
   <tbody>{zeilen}</tbody>
  </table></div>
 </div>
</section>
{schluss(p, "Ihr Haus als nächste Baustelle?", "Schicken Sie uns ein Foto von Garten und Zufahrt. Wir sagen Ihnen, wie das Gerät zu Ihnen kommt.")}"""
    return s, body


def seite_ueber():
    s = {"ziel": "ueber-uns", "ogbild": "og-ueber-uns", "preload": preload("team-quer", "(max-width: 900px) 100vw, 33vw"), "spur": [("ueber-uns", "Über uns")],
         "title": "Über uns: Eco Green GmbH, Pumpwerkstrasse 40, Regensdorf",
         "desc": "Eco Green GmbH bohrt Erdwärmesonden von der Pumpwerkstrasse 40 in Regensdorf aus. Mit eigenen Raupenbohrgeräten, eigenem Bohrteam und dem FWS-Gütesiegel."}
    p = PFAD
    body = seitenkopf(s, "Von Regensdorf in Ihren Garten.", "Eco Green GmbH bohrt Erdwärmesonden für Häuser, die von Öl oder Gas auf Erdwärme wechseln, und für Neubauten.",
                      foto(p, "team-quer", "Bohrmeister im grünen Eco-Green-Shirt am Bohrgerät", "Bohrmeister von Eco Green.", lazy=False, prio=True, sizes="(max-width: 900px) 100vw, 33vw")) + f"""
<section class="sektion" aria-labelledby="daten-h">
 <div class="wrap raster">
  <div class="links"><h2 id="daten-h">Die Firma in Fakten.</h2></div>
  <div class="rechts">
   <dl class="daten">
    <div><dt>Firma</dt><dd>Eco Green GmbH</dd></div>
    <div><dt>Sitz</dt><dd>Pumpwerkstrasse 40, 8105 Regensdorf, seit 2020</dd></div>
    <div><dt>Handelsregister</dt><dd>Kanton Zürich, CHE-141.654.180</dd></div>
    <div><dt>Tätigkeit</dt><dd>Planung und Ausführung von Erdsondenbohrungen</dd></div>
    <div><dt>Geräte</dt><dd>Eigene Raupenbohrgeräte und eigenes Bohrteam</dd></div>
    <div><dt>Einsatzgebiet</dt><dd>{EINSATZ}</dd></div>
   </dl>
  </div>
 </div>
</section>
<section class="sektion dunkel" aria-labelledby="siegel-h">
 <div class="wrap raster">
  <div class="links"><span class="label">FWS-Gütesiegel</span><h2 id="siegel-h">Auf der Liste der Fachvereinigung.</h2></div>
  <div class="rechts">
   <p class="lead">Eco Green GmbH steht auf der Gütesiegelliste der Fachvereinigung Wärmepumpen Schweiz, Stand September 2026. Schon die Liste vom Juni 2021 führte uns.</p>
   <p>Wer das Siegel trägt, verpflichtet sich auf Beratung der Bauherrschaft, umweltschonende Ausführung, Bohrungen nach dem Stand der Technik, geprüftes Sondenmaterial und Sicherheit auf der Baustelle. Die Kommission der FWS kontrolliert das auch unangemeldet auf der Bohrstelle, was sie genau prüft, steht im Beitrag zum <a href="{link('artikel:guetesiegel-erdwaermesonden-bohrfirma')}">FWS-Gütesiegel</a>.</p>
   <div class="knopfreihe"><a class="knopf zwei" href="{FWS_PDF}" rel="noopener">Gütesiegelliste ansehen</a></div>
  </div>
 </div>
</section>
<section class="sektion" aria-labelledby="leute-h">
 <div class="wrap raster">
  <div class="links"><h2 id="leute-h">Geschäftsleitung.</h2></div>
  <div class="rechts">
   <ul class="namen">
    <li>Mahissa Ganz-Yasri</li>
    <li>Etiènne Spruijt</li>
   </ul>
  </div>
 </div>
</section>
<section class="sektion hell" aria-labelledby="ort-h">
 <div class="wrap raster">
  <div class="links"><h2 id="ort-h">Pumpwerk&shy;strasse 40, Regensdorf.</h2></div>
  <div class="rechts">
   <p class="lead">Von hier sind Furttal, Zürcher Unterland und Limmattal schnell erreicht. Die Stadt Zürich auch.</p>
   <a class="weiter" href="{KARTE}" rel="noopener">Auf der Karte zeigen</a>
  </div>
 </div>
</section>
{schluss(p, "Wo steht Ihr Haus?", "Sagen Sie uns die Adresse. Wir prüfen, ob die Parzelle eine Sonde erlaubt, und planen die Anfahrt mit dem Gerät.")}"""
    return s, body


def seite_kontakt():
    s = {"ziel": "kontakt", "ogbild": "og-kontakt", "spur": [("kontakt", "Kontakt")],
         "title": "Erdsonde Offerte anfragen | Kontakt Eco Green Regensdorf",
         "desc": "Erstabklärung für Ihre Erdwärmesonde: rufen Sie an unter 044 400 20 20 oder schreiben Sie an info@eco-green.ch. Eco Green GmbH, Pumpwerkstrasse 40, Regensdorf."}
    p = PFAD
    s["schema"] = [{"@type": "ContactPage", "url": voll("kontakt"), "about": {"@id": ORG_ID}}]
    body = seitenkopf(s, "Offerte anfragen.", "Für die Erstabklärung brauchen wir fünf Angaben. Das Gespräch dauert zehn Minuten, die Einschätzung ist kostenlos.") + f"""
<section class="sektion" aria-label="Telefon und E-Mail" data-shopify="kontaktwege">
 <div class="wrap raster">
  <div class="kontaktwege">
   <a class="kontaktweg" href="{TEL_LINK}"><span class="label">Telefon</span><b>{TEL}</b><span class="klein">{BUEROZEIT}</span></a>
   <a class="kontaktweg" href="{MAILTO}"><span class="label">E-Mail mit Vorlage</span><b>{MAIL}</b><span class="klein">Antwort innert zwei Arbeitstagen</span></a>
  </div>
 </div>
</section>
<section class="sektion hell" aria-labelledby="brauchen-h">
 <div class="wrap raster">
  <div class="links">
   <h2 id="brauchen-h">Das brauchen wir von Ihnen.</h2>
   <p class="lead" style="margin-top:24px">Die E-Mail-Vorlage fragt genau das ab. Öffnet sich bei Ihnen kein Mailprogramm, kopieren Sie die Vorlage und schicken Sie sie an {MAIL}.</p>
   <div class="knopfreihe"><button class="knopf zwei kopieren" type="button" data-text="{esc(MAIL_TEXT)}">Vorlage kopieren</button></div>
   <p class="klein kopiert" role="status"></p>
  </div>
  <div class="rechts">
   <ol class="checkliste">
    <li><span><b>Adresse des Grundstücks.</b> Damit prüfen wir im Wärmenutzungsatlas, ob gebohrt werden darf.</span></li>
    <li><span><b>Heutige Heizung.</b> Öl, Gas oder Elektro, mit dem Baujahr der Heizung. Davon hängt der Förderbeitrag ab.</span></li>
    <li><span><b>Verbrauch pro Jahr.</b> Liter Öl, Kubikmeter Gas oder Kilowattstunden. Daraus schätzen wir die Sondenlänge.</span></li>
    <li><span><b>Baujahr und Wohnfläche des Hauses.</b> Eine grobe Angabe reicht.</span></li>
    <li><span><b>Telefonnummer.</b> Für den Rückruf und den Termin vor Ort.</span></li>
   </ol>
  </div>
 </div>
</section>
<section class="sektion dunkel" aria-labelledby="adr-h">
 <div class="wrap raster">
  <div class="links"><h2 id="adr-h">Büro in Regensdorf.</h2></div>
  <div class="rechts">
   <address class="lead" style="font-style:normal">Eco Green GmbH<br>Pumpwerkstrasse 40<br>8105 Regensdorf</address>
   <div class="knopfreihe"><a class="knopf" href="{KARTE}" rel="noopener">Route planen</a></div>
  </div>
 </div>
</section>"""
    return s, body


def seite_impressum():
    s = {"ziel": "impressum", "spur": [("impressum", "Impressum")],
         "title": "Impressum | Eco Green GmbH, Erdwärmesonden Regensdorf",
         "desc": "Impressum der Website von Eco Green GmbH, Erdsondenbohrungen, Pumpwerkstrasse 40, 8105 Regensdorf. Handelsregister Kanton Zürich, CHE-141.654.180."}
    body = seitenkopf(s, "Impressum.", "Angaben zur Betreiberin dieser Website.") + f"""
<section class="sektion" data-shopify="rechtstext"><div class="wrap raster"><div class="recht">
 <h2>Betreiberin</h2>
 <address>Eco Green GmbH<br>Pumpwerkstrasse 40<br>8105 Regensdorf<br>Schweiz</address>
 <p style="margin-top:16px">Telefon <a href="{TEL_LINK}">{TEL}</a><br>E-Mail <a href="mailto:{MAIL}">{MAIL}</a></p>
 <h2>Handelsregister</h2>
 <p>Eingetragen im Handelsregister des Kantons Zürich<br>UID CHE-141.654.180<br>Rechtsform: Gesellschaft mit beschränkter Haftung</p>
 <h2>Vertretungsberechtigte Personen</h2>
 <p>Etiènne Spruijt, Vorsitzender der Geschäftsführung<br>Mahissa Ganz-Yasri, Geschäftsführerin</p>
 <h2>Haftung</h2>
 <p>Die Angaben auf dieser Website sind sorgfältig geprüft. Förderbeiträge und Bewilligungen legen Kanton und Gemeinde fest. Verbindlich sind deren Entscheide und unsere schriftliche Offerte. Für Inhalte verlinkter Websites sind deren Betreiber verantwortlich.</p>
 <h2>Bilder und Texte</h2>
 <p>Alle Fotos zeigen Baustellen und Geräte von Eco Green. Texte und Bilder dürfen nur mit schriftlicher Zustimmung der Eco Green GmbH verwendet werden.</p>
 <h2>Gestaltung</h2>
 <p>Gestaltung und Umsetzung: <a href="https://www.lorien.group" rel="noopener">Lorien Group, Aarau</a></p>
</div></div></section>"""
    return s, body


def seite_datenschutz():
    s = {"ziel": "datenschutz", "spur": [("datenschutz", "Datenschutz")],
         "title": "Datenschutzerklärung | Eco Green GmbH, Regensdorf",
         "desc": "Datenschutzerklärung von Eco Green GmbH nach dem Schweizer Datenschutzgesetz (DSG). Keine Cookies, kein Tracking, Schriften lokal. Was wir speichern und warum."}
    body = seitenkopf(s, "Datenschutz.", "Wie Eco Green mit Personendaten umgeht. Nach dem Bundesgesetz über den Datenschutz (DSG). Stand 21.10.2026.") + f"""
<section class="sektion" data-shopify="rechtstext"><div class="wrap raster"><div class="recht">
 <h2>Verantwortlich</h2>
 <address>Eco Green GmbH<br>Pumpwerkstrasse 40, 8105 Regensdorf<br><a href="mailto:{MAIL}">{MAIL}</a>, <a href="{TEL_LINK}">{TEL}</a></address>
 <h2>Kurz gesagt</h2>
 <p>Diese Website setzt keine Cookies, nutzt kein Tracking und keine Analysewerkzeuge. Schriften und Bilder liegen auf demselben Server wie die Website, es gibt keine Anfragen an Google oder andere Dienste. Es gibt kein Formular. Daten erhalten wir nur, wenn Sie uns anrufen oder schreiben.</p>
 <h2>Besuch der Website</h2>
 <p>Beim Aufruf der Seite verarbeitet der Hosting-Anbieter technisch notwendige Daten: IP-Adresse, Datum und Uhrzeit, aufgerufene Seite, Browser und Betriebssystem. Das dient dem sicheren Betrieb. Die Website wird bei GitHub Inc. betrieben, einer Tochter der Microsoft Corporation in den USA. Dabei können Daten in die USA übermittelt werden. GitHub ist unter dem Swiss-U.S. Data Privacy Framework zertifiziert.</p>
 <h2>Kontakt per E-Mail oder Telefon</h2>
 <p>Schreiben Sie uns oder rufen Sie an, verwenden wir Ihre Angaben, um Ihre Anfrage zu beantworten und eine Offerte zu erstellen. Dazu gehören Name, Adresse des Grundstücks, Kontaktdaten und Angaben zu Ihrer Heizung. Kommt ein Auftrag zustande, bewahren wir die Unterlagen so lange auf, wie es Handels- und Steuerrecht verlangen. Anfragen ohne Auftrag löschen wir nach zwei Jahren.</p>
 <h2>Weitergabe</h2>
 <p>Für Bewilligung und Förderung geben wir Angaben zu Ihrem Grundstück an Gemeinde, Kanton und Ihren Heizungsinstallateur weiter, soweit Sie uns damit beauftragen. Wir verkaufen keine Daten.</p>
 <h2>Links zu anderen Websites</h2>
 <p>Links zu Kanton Zürich, FWS oder OpenStreetMap führen auf fremde Websites. Erst wenn Sie klicken, gelten deren Datenschutzbestimmungen.</p>
 <h2>Ihre Rechte</h2>
 <p>Sie können Auskunft über Ihre Daten verlangen, falsche Daten berichtigen und Daten löschen lassen, soweit keine Aufbewahrungspflicht besteht. Schreiben Sie an <a href="mailto:{MAIL}">{MAIL}</a>. Sie können sich auch beim Eidgenössischen Datenschutz- und Öffentlichkeitsbeauftragten (EDÖB) beschweren.</p>
 <h2>Änderungen</h2>
 <p>Wir passen diese Erklärung an, wenn sich die Website ändert. Massgebend ist die Fassung auf dieser Seite.</p>
</div></div></section>"""
    return s, body


def seite_404():
    s = {"ziel": "", "datei": "404.html", "fehlerseite": True, "spur": [],
         "title": "Seite nicht gefunden | Eco Green Erdwärmesonden",
         "desc": "Diese Seite gibt es nicht. Zurück zur Startseite von Eco Green, Erdsondenbohrungen aus Regensdorf, oder direkt zu Leistungen, Ablauf und Kontakt."}
    p = PFAD
    body = f"""<section class="seitenkopf" data-shopify="fehler-404"><div class="wrap raster"><div class="seitenkopf-text">
 <span class="label">Fehler 404</span>
 <h1>404 Meter tief. Nichts gefunden.</h1>
 <p class="lead" style="margin-top:24px">Diese Seite gibt es nicht oder nicht mehr.</p>
 <div class="knopfreihe"><a class="knopf" href="{p}">Zur Startseite</a><a class="knopf zwei" href="{link('kontakt')}">Offerte anfragen</a></div>
</div></div></section>"""
    return s, body


# ---------------------------------------------------------------- Ratgeber: Artikel lesen und pruefen

PFLICHT = ["handle", "titel", "seo_titel", "beschreibung", "kurz", "bild", "bild_alt", "bild_legende",
           "stand", "tags", "quellen", "fragen", "verwandt"]
ERLAUBT = {"h2", "h3", "p", "ul", "ol", "li", "table", "thead", "tbody", "tr", "th", "td", "a", "strong", "em"}
ATTRIBUTE = {"a": {"href"}, "th": {"scope", "colspan", "rowspan"}, "td": {"colspan", "rowspan"}}
VERBOTEN_ZEICHEN = {"–": "Halbgeviertstrich", "—": "Geviertstrich", "ß": "ß (Schweizer Schreibweise: ss)"}
LINK_INTERN = re.compile(r'^@(start|ratgeber|seite:([a-z0-9-]+)|artikel:([a-z0-9-]+))$')
DATEINAME = re.compile(r"^(\d\d)-([a-z0-9]+(?:-[a-z0-9]+)*)\.html$")


class KoerperPruefer(HTMLParser):
    """Prueft den Artikelkoerper: nur erlaubte Tags und Attribute, sauber verschachtelt, Links gueltig."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.fehler, self.stapel, self.links, self.h2 = [], [], [], 0

    def handle_starttag(self, tag, attrs):
        if tag not in ERLAUBT:
            self.fehler.append(f"verbotenes Tag <{tag}> (Zeile {self.getpos()[0]})")
        for k, v in attrs:
            if k not in ATTRIBUTE.get(tag, set()):
                self.fehler.append(f"verbotenes Attribut {k} an <{tag}> (Zeile {self.getpos()[0]})")
        if tag == "a":
            self.links.append((dict(attrs).get("href") or "", self.getpos()[0]))
        if tag == "h2":
            self.h2 += 1
        self.stapel.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.fehler.append(f"leeres Tag <{tag}/> (Zeile {self.getpos()[0]})")

    def handle_endtag(self, tag):
        if not self.stapel or self.stapel[-1] != tag:
            self.fehler.append(f"</{tag}> ohne passendes Start-Tag (Zeile {self.getpos()[0]}, offen: {self.stapel[-1] if self.stapel else 'nichts'})")
            if tag in self.stapel:
                while self.stapel and self.stapel.pop() != tag:
                    pass
        else:
            self.stapel.pop()

    def handle_comment(self, data):
        self.fehler.append(f"Kommentar im Koerper (Zeile {self.getpos()[0]})")


def lies_artikel(ordner):
    """Liest src/ratgeber/NN-handle.html. Format:
        <!--meta
        {"handle": ..., "titel": ..., ...}   (JSON, Schluessel siehe PFLICHT)
        -->
        <p>...</p><h2>...</h2>...           (nur Tags aus ERLAUBT)
    Bricht bei jedem Formfehler mit einer Liste aller Fehler ab."""
    if not ordner.is_dir():
        return []
    dateien = sorted(f for f in ordner.glob("*.html"))
    alle, fehlerliste = [], []
    for f in dateien:
        def F(t):
            fehlerliste.append(f"{f.name}: {t}")
        m = DATEINAME.match(f.name)
        if not m:
            F("Dateiname nicht im Format NN-handle.html (zwei Ziffern, Bindestrich, Handle aus a-z, 0-9, Bindestrich)")
            continue
        roh = f.read_text(encoding="utf-8-sig")
        mm = re.match(r"\s*<!--meta\s*(\{.*?\})\s*-->\s*(.*)\Z", roh, re.S)
        if not mm:
            F("Kopf <!--meta {json} --> fehlt oder steht nicht am Anfang")
            continue
        try:
            meta = json.loads(mm.group(1))
        except json.JSONDecodeError as e:
            F(f"Meta-JSON ungueltig: {e}")
            continue
        koerper = mm.group(2).strip()
        fehlt = [k for k in PFLICHT if k not in meta]
        if fehlt:
            F("Schluessel fehlen: " + ", ".join(fehlt))
            continue
        unbekannt = [k for k in meta if k not in PFLICHT]
        if unbekannt:
            F("unbekannte Schluessel: " + ", ".join(unbekannt))
        for k in ["handle", "titel", "seo_titel", "beschreibung", "kurz", "bild", "bild_alt", "bild_legende", "stand"]:
            if not isinstance(meta[k], str) or not meta[k].strip():
                F(f"{k} muss ein nicht leerer Text sein")
        if fehlerliste and fehlerliste[-1].startswith(f.name + ":"):
            continue
        if meta["handle"] != m.group(2):
            F(f"handle «{meta['handle']}» passt nicht zum Dateinamen «{m.group(2)}»")
        for k, lo, hi in [("seo_titel", 45, 60), ("beschreibung", 140, 160), ("kurz", 200, 320)]:
            n = len(meta[k])
            if not lo <= n <= hi:
                F(f"{k} hat {n} Zeichen, verlangt {lo} bis {hi}: «{meta[k]}»")
        if meta["bild"] not in BILDER["fotos"]:
            F(f"bild «{meta['bild']}» ist kein Schluessel aus bilder.json. Erlaubt: {', '.join(sorted(BILDER['fotos']))}")
        try:
            if date.fromisoformat(meta["stand"]).isoformat() != meta["stand"]:
                raise ValueError
        except ValueError:
            F(f"stand «{meta['stand']}» ist kein Datum im Format JJJJ-MM-TT")
        if not (isinstance(meta["tags"], list) and meta["tags"] and all(isinstance(t, str) and t.strip() for t in meta["tags"])):
            F("tags muss eine nicht leere Liste von Texten sein")
        q = meta["quellen"]
        if not (isinstance(q, list) and q):
            F("quellen muss eine nicht leere Liste sein")
        else:
            for i, e in enumerate(q, 1):
                if not (isinstance(e, dict) and set(e) == {"name", "url", "abgerufen"}):
                    F(f"quellen[{i}] braucht genau name, url, abgerufen")
                    continue
                if not str(e["url"]).startswith("https://"):
                    F(f"quellen[{i}].url muss mit https:// beginnen: {e['url']}")
                if not re.fullmatch(r"\d\d\.\d\d\.\d{4}", str(e["abgerufen"])):
                    F(f"quellen[{i}].abgerufen im Format TT.MM.JJJJ: {e['abgerufen']}")
        fr = meta["fragen"]
        if not (isinstance(fr, list) and fr):
            F("fragen muss eine nicht leere Liste sein")
        else:
            for i, e in enumerate(fr, 1):
                if not (isinstance(e, dict) and set(e) == {"f", "a"} and all(isinstance(e[x], str) and e[x].strip() for x in "fa")):
                    F(f"fragen[{i}] braucht genau f und a als Text")
                elif "<" in e["f"] + e["a"]:
                    F(f"fragen[{i}] enthaelt HTML, erlaubt ist nur Text")
        if not (isinstance(meta["verwandt"], list) and all(isinstance(v, str) for v in meta["verwandt"])):
            F("verwandt muss eine Liste von Handles sein")
        # Zeichen nach Schreibregeln
        alles = json.dumps(meta, ensure_ascii=False) + koerper
        for z, name in VERBOTEN_ZEICHEN.items():
            if z in alles:
                F(f"verbotenes Zeichen {name} gefunden: «{alles[max(0, alles.index(z) - 30):alles.index(z) + 10]}»")
        # Koerper
        if not koerper:
            F("Koerper ist leer")
        kp = KoerperPruefer()
        kp.feed(koerper)
        kp.close()
        if kp.stapel:
            kp.fehler.append("nicht geschlossen: " + ", ".join(f"<{t}>" for t in kp.stapel))
        if re.search(r"<h1\b", koerper, re.I):
            kp.fehler.append("<h1> im Koerper, die H1 setzt der Generator aus titel")
        for t in kp.fehler:
            F(t)
        alle.append({"datei": f.name, "nr": int(m.group(1)), "meta": meta, "koerper": koerper, "links": kp.links, "h2": kp.h2})
    # Querverweise erst, wenn alle gelesen sind
    warnungen = []
    handles = [a["meta"]["handle"] for a in alle]
    for h in set(handles):
        if handles.count(h) > 1:
            fehlerliste.append(f"handle «{h}» kommt mehrfach vor")
    for a in alle:
        for href, zeile in a["links"]:
            if href.startswith("@"):
                mm = LINK_INTERN.match(href)
                if not mm:
                    fehlerliste.append(f"{a['datei']}: Linkziel «{href}» unbekannt (erlaubt @start, @ratgeber, @seite:<handle>, @artikel:<handle>), Zeile {zeile}")
                elif mm.group(2) and mm.group(2) not in SEITEN_HANDLES:
                    fehlerliste.append(f"{a['datei']}: Seite «{mm.group(2)}» gibt es nicht (erlaubt: {', '.join(SEITEN_HANDLES)}), Zeile {zeile}")
                elif mm.group(3) and mm.group(3) not in handles:
                    meldung = f"{a['datei']}: Artikel «{mm.group(3)}» gibt es nicht, Zeile {zeile}"
                    if ENTWURF:
                        FEHLENDE.add(mm.group(3))
                        warnungen.append(meldung + " (Entwurf: Link wird zu Text)")
                    else:
                        fehlerliste.append(meldung)
            elif not href.startswith(("https://", "mailto:", "tel:")):
                fehlerliste.append(f"{a['datei']}: Link «{href}» nicht erlaubt (interne Ziele mit @, externe mit https://), Zeile {zeile}")
        for v in a["meta"]["verwandt"]:
            if v == a["meta"]["handle"]:
                fehlerliste.append(f"{a['datei']}: verwandt nennt den Artikel selbst")
            elif v not in handles:
                if ENTWURF:
                    warnungen.append(f"{a['datei']}: verwandt «{v}» gibt es nicht (Entwurf: weggelassen)")
                else:
                    fehlerliste.append(f"{a['datei']}: verwandt «{v}» gibt es nicht")
    for w in warnungen:
        print("WARNUNG: " + w)
    if fehlerliste:
        fehler(f"Ratgeber-Artikel in {ordner} nicht im verbindlichen Format:\n  - " + "\n  - ".join(fehlerliste))
    return sorted(alle, key=lambda a: (a["nr"], a["meta"]["handle"]))


def loese_links(koerper, aufloeser=link):
    """@start, @ratgeber, @seite:x, @artikel:x zu echten URLs. Externe Links bekommen rel=noopener.
    Im Entwurf (--entwurf) werden Links auf noch fehlende Artikel zu reinem Text."""
    for h in FEHLENDE:
        koerper = re.sub(rf'<a href="@artikel:{re.escape(h)}">(.*?)</a>', r"", koerper, flags=re.S)
    def ziel(m):
        h = m.group(1)
        if h == "@start":
            u = aufloeser("")
        elif h == "@ratgeber":
            u = aufloeser(BLOG)
        elif h.startswith("@seite:"):
            u = aufloeser(h.split(":", 1)[1])
        elif h.startswith("@artikel:"):
            u = aufloeser("artikel:" + h.split(":", 1)[1])
        else:
            return f'href="{h}"' + (' rel="noopener"' if h.startswith("https://") else "")
        return f'href="{u}"'
    return re.sub(r'href="([^"]*)"', ziel, koerper)


def slug(text):
    t = re.sub("<[^>]+>", "", html.unescape(text)).lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("é", "e"), ("è", "e"), ("à", "a")):
        t = t.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:60] or "abschnitt"


def koerper_html(a):
    """Koerper fuer die Website: Links aufgeloest, h2 mit Anker, Tabellen im eigenen Scrollrahmen."""
    k = loese_links(a["koerper"])
    ids = []
    def h2(m):
        i = slug(m.group(1))
        while i in ids:
            i += "-2"
        ids.append(i)
        return f'<h2 id="{i}">{m.group(1)}</h2>'
    k = re.sub(r"<h2>(.*?)</h2>", h2, k, flags=re.S)
    n = [0]
    def tabelle(m):
        n[0] += 1
        return (f'<div class="text-tabelle-rahmen" role="region" aria-label="Tabelle {n[0]}, seitlich scrollbar" tabindex="0">'
                f'<table class="text-tabelle">{m.group(1)}</table></div>')
    k = re.sub(r"<table>(.*?)</table>", tabelle, k, flags=re.S)
    toc = [(i, re.sub("<[^>]+>", "", t)) for i, t in zip(ids, re.findall(r"<h2>(.*?)</h2>", a["koerper"], re.S))]
    return k, toc


def iso_zeit(stand):
    """Datum als Zeitpunkt 00:00 Uhr Zuerich, mit Sommer- oder Winterzeit."""
    from zoneinfo import ZoneInfo
    try:
        z = datetime.fromisoformat(stand).replace(tzinfo=ZoneInfo("Europe/Zurich"))
    except Exception:
        z = datetime.fromisoformat(stand + "T00:00:00+01:00")
    return z.isoformat()


def verwandte(a):
    """Zwei bis drei verwandte Artikel: zuerst die genannten, dann nach gemeinsamen Tags aufgefuellt."""
    nach = {x["meta"]["handle"]: x for x in ARTIKEL}
    liste = [nach[h] for h in a["meta"]["verwandt"] if h in nach][:3]
    if len(liste) < 2:
        tags = set(a["meta"]["tags"])
        rest = sorted((x for x in ARTIKEL if x is not a and x not in liste),
                      key=lambda x: (-len(tags & set(x["meta"]["tags"])), x["nr"]))
        liste += rest[:2 - len(liste)]
    return liste


def og_name(a):
    return f"og-ratgeber-{a['meta']['handle']}"


def ratgeber_karten(liste, ebene="h3", mit_kurz=True):
    """Karten mit Stand und Titel. Lead nur, wo er nicht schon darueber steht (verwandte Artikel: ohne)."""
    return "".join(
        f'<li><span class="mono">Stand {tt(x["meta"]["stand"])}</span><{ebene}><a href="{link("artikel:" + x["meta"]["handle"])}">{esc(x["meta"]["titel"])}</a></{ebene}>'
        + (f'<p>{esc(x["meta"]["kurz"])}</p>' if mit_kurz else "") + '</li>'
        for x in liste)


def ratgeber_start(liste=None):
    """Kompakter Abschnitt auf der Startseite: die drei Artikel aus RATGEBER_START (groesste Nachfrage)."""
    if not ARTIKEL:
        return ""
    liste = liste or ARTIKEL[:3]
    return f"""<section class="sektion" aria-labelledby="rat-h">
 <div class="wrap raster">
  <div class="kopfzeile">
   <div><span class="label">Ratgeber</span><h2 id="rat-h">Wissen vor der Bohrung.</h2></div>
   <p>Bevor Sie entscheiden, lesen Sie hier nach, was eine Sonde kostet und wer sie bewilligt.</p>
  </div>
  <ul class="ratgeber-kurz">{ratgeber_karten(liste)}</ul>
  <div style="grid-column:1/-1"><a class="weiter" href="{link(BLOG)}">Alle Beiträge im Ratgeber</a></div>
 </div>
</section>
"""


def seite_ratgeber():
    stand = max(a["meta"]["stand"] for a in ARTIKEL)
    s = {"ziel": BLOG, "spur": [(BLOG, "Ratgeber")], "stand": stand, "seitentyp": "CollectionPage",
         "title": "Ratgeber Erdwärmesonde und Erdsondenbohrung | Eco Green",
         "desc": "Ratgeber von Eco Green zu Erdwärmesonden im Kanton Zürich: Bewilligung, Förderung, Kosten, Ablauf und Technik. Kurze Antworten mit Quellen und Stand.",
         "og": "Ratgeber Erdwärmesonde von Eco Green"}
    blog_id = voll(BLOG) + "#blog"
    s["schema"] = [{"@type": "Blog", "@id": blog_id, "url": voll(BLOG), "name": "Ratgeber Erdwärmesonde",
                    "description": s["desc"], "inLanguage": "de-CH", "publisher": {"@id": ORG_ID},
                    "blogPost": [{"@type": "BlogPosting", "@id": voll("artikel:" + a["meta"]["handle"]) + "#artikel",
                                  "headline": a["meta"]["titel"], "url": voll("artikel:" + a["meta"]["handle"]),
                                  "datePublished": a["meta"]["stand"], "dateModified": a["meta"]["stand"]} for a in ARTIKEL]}]
    eintraege = "".join(
        f'<li><span class="stand mono">Stand {tt(a["meta"]["stand"])}</span><div class="eintrag">'
        f'<h2><a href="{link("artikel:" + a["meta"]["handle"])}">{esc(a["meta"]["titel"])}</a></h2>'
        f'<p>{esc(a["meta"]["kurz"])}</p></div></li>' for a in ARTIKEL)
    body = seitenkopf(s, "Ratgeber.", "Was Bauherrschaften vor einer Erdwärmesonde wissen wollen, mit Quellen und dem Datum, an dem wir jede Antwort geprüft haben.") + f"""
<section class="sektion" aria-label="Alle Beiträge" data-shopify="artikelliste">
 <div class="wrap raster">
  <ol class="ratgeber-liste">{eintraege}</ol>
 </div>
</section>
{schluss(None, "Noch eine Frage offen?", "Rufen Sie an. Wir beantworten sie für Ihr Grundstück.")}"""
    return s, body


def seite_artikel(a):
    m = a["meta"]
    h = m["handle"]
    url = voll("artikel:" + h)
    s = {"ziel": "artikel:" + h, "spur": [(BLOG, "Ratgeber"), ("artikel:" + h, esc(m["titel"]))], "stand": m["stand"],
         "artikel": True, "title": m["seo_titel"], "desc": m["beschreibung"], "og": m["titel"],
         "ogbild": og_name(a), "ogalt": f"{m['titel']} Ratgeber von Eco Green, Erdwärmesonden aus Regensdorf.",
         "preload": preload(m["bild"], "(max-width: 900px) 100vw, 33vw"),
         "head_extra": (f'<meta property="article:published_time" content="{iso_zeit(m["stand"])}">\n'
                        f'<meta property="article:modified_time" content="{iso_zeit(m["stand"])}">\n')}
    w, hh, _br = BILDER["fotos"][m["bild"]]
    s["schema"] = [
        {"@type": "BlogPosting", "@id": url + "#artikel", "headline": m["titel"], "description": m["beschreibung"],
         "abstract": m["kurz"],
         "image": [{"@type": "ImageObject", "url": BASIS + f"img/{og_name(a)}.jpg", "width": 1200, "height": 630},
                   {"@type": "ImageObject", "url": BASIS + bild_gross(m["bild"]), "caption": m["bild_legende"]}],
         "datePublished": m["stand"], "dateModified": m["stand"],
         "author": {"@id": ORG_ID}, "publisher": {"@id": ORG_ID},
         "mainEntityOfPage": {"@id": url + "#seite"}, "isPartOf": {"@id": voll(BLOG) + "#blog"},
         "inLanguage": "de-CH", "keywords": ", ".join(m["tags"]),
         "citation": [{"@type": "CreativeWork", "name": q["name"], "url": q["url"]} for q in m["quellen"]]},
        faq_schema([(f["f"], f["a"]) for f in m["fragen"]]),
    ]
    k, toc = koerper_html(a)
    inhalt = ""
    if len(toc) >= 3:
        inhalt = ('<nav class="artikel-inhalt" aria-label="Inhalt dieses Beitrags"><span class="label">Auf dieser Seite</span><ol>'
                  + "".join(f'<li><a href="#{i}">{esc(t)}</a></li>' for i, t in toc) + "</ol></nav>")
    meta_zeile = (f'<p class="artikel-meta"><a href="{link("ueber-uns")}">Eco Green GmbH</a> · '
                  f'Stand <time datetime="{m["stand"]}">{tt(m["stand"])}</time></p>')
    fragen = faq_html([(esc(f["f"]), f"<p>{esc(f['a'])}</p>") for f in m["fragen"]])
    quellen = "".join(f'<li><span><a href="{esc(q["url"])}" rel="noopener">{esc(q["name"])}</a>, abgerufen {esc(q["abgerufen"])}</span></li>'
                      for q in m["quellen"])
    verw = verwandte(a)
    verw_html = "" if not verw else f"""<section class="sektion" aria-labelledby="verw-h" data-shopify="artikel-verwandt">
 <div class="wrap raster">
  <div class="kopfzeile"><div><span class="label">Ratgeber</span><h2 id="verw-h">Weiterlesen.</h2></div></div>
  <ul class="ratgeber-kurz">{ratgeber_karten(verw, mit_kurz=False)}</ul>
  <div style="grid-column:1/-1"><a class="weiter" href="{link(BLOG)}">Alle Beiträge im Ratgeber</a></div>
 </div>
</section>
"""
    body = seitenkopf(s, esc(m["titel"]), esc(m["kurz"]),
                      foto(PFAD, m["bild"], m["bild_alt"], esc(m["bild_legende"]), lazy=False, prio=True, sizes="(max-width: 900px) 100vw, 33vw"),
                      nach_lead=meta_zeile).replace('<section class="seitenkopf">', '<section class="seitenkopf artikel-kopf" data-shopify="artikel-kopf">', 1) + f"""
<section class="sektion" aria-label="Beitrag" data-shopify="artikel-text">
 <div class="wrap raster">
  <article class="artikel-text">{k}</article>
  {inhalt}
 </div>
</section>
<section class="sektion hell" aria-labelledby="fragen-h" data-shopify="artikel-fragen">
 <div class="wrap raster">
  <div class="faq-kopf"><span class="label">Fragen</span><h2 id="fragen-h">Kurz gefragt.</h2></div>
  <div class="faq">{fragen}</div>
 </div>
</section>
<section class="sektion" aria-labelledby="quellen-h" data-shopify="artikel-quellen">
 <div class="wrap raster">
  <div class="links"><h2 id="quellen-h">Quellen.</h2></div>
  <div class="rechts"><ol class="checkliste quellen-liste">{quellen}</ol></div>
 </div>
</section>
{verw_html}{schluss()}"""
    return s, body


def atom_feed():
    jetzt = max(a["meta"]["stand"] for a in ARTIKEL)
    eintraege = "".join(f"""
 <entry>
  <id>{voll('artikel:' + a['meta']['handle'])}</id>
  <title>{esc(a['meta']['titel'])}</title>
  <link rel="alternate" type="text/html" href="{voll('artikel:' + a['meta']['handle'])}"/>
  <published>{iso_zeit(a['meta']['stand'])}</published>
  <updated>{iso_zeit(a['meta']['stand'])}</updated>
  <author><name>Eco Green GmbH</name></author>
  <summary type="text">{esc(a['meta']['kurz'])}</summary>
{''.join(f'  <category term="{esc(t)}"/>' + chr(10) for t in a['meta']['tags'])} </entry>""" for a in ARTIKEL)
    return f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="de-CH">
 <id>{voll(BLOG)}</id>
 <title>Eco Green Ratgeber</title>
 <subtitle>Ratgeber zu Erdwärmesonden im Kanton Zürich</subtitle>
 <link rel="alternate" type="text/html" href="{voll(BLOG)}"/>
 <link rel="self" type="application/atom+xml" href="{voll('feed')}"/>
 <updated>{iso_zeit(jetzt)}</updated>
 <author><name>Eco Green GmbH</name><uri>{BASIS}</uri></author>{eintraege}
</feed>
"""


def seiten_liste():
    """Alle Seiten als (Funktion, Argument). Ratgeber nur, wenn Artikel da sind."""
    liste = [(f, None) for f in [seite_start, seite_leistungen, seite_ablauf, seite_foerderung, seite_referenzen,
                                 seite_ueber, seite_kontakt, seite_impressum, seite_datenschutz]]
    if ARTIKEL:
        liste.append((seite_ratgeber, None))
        liste += [(seite_artikel, a) for a in ARTIKEL]
    liste.append((seite_404, None))
    return liste

# ---------------------------------------------------------------- Nebendateien

def llms():
    rat = ""
    if ARTIKEL:
        rat = "\n## Ratgeber\n" + "".join(
            f"- [{a['meta']['titel']}]({voll('artikel:' + a['meta']['handle'])}): {a['meta']['kurz']} Stand {tt(a['meta']['stand'])}.\n"
            for a in ARTIKEL)
    rat_seite = f"- [Ratgeber]({voll(BLOG)}): Beiträge zu Bewilligung, Förderung, Kosten und Ablauf, mit Quellen\n" if ARTIKEL else ""
    return f"""# Eco Green GmbH

> Erdsondenbohrungen für Wärmepumpen im Kanton Zürich, Sitz in Regensdorf. Eco Green prüft das Grundstück, bereitet Bewilligung und Fördernachweis vor, bohrt zum vereinbarten Termin und schliesst die Sonde bis in den Heizraum an. Träger des FWS-Gütesiegels für Erdwärmesonden-Bohrfirmen (Liste Juni 2021 und Stand September 2026).

## Fakten
- Firma: Eco Green GmbH, UID CHE-141.654.180, Handelsregister Kanton Zürich
- Adresse: Pumpwerkstrasse 40, 8105 Regensdorf, Schweiz
- Telefon: {TEL}, E-Mail: {MAIL}
- Gütesiegel: FWS-Gütesiegel für Erdwärmesonden-Bohrfirmen, Gütesiegelliste Stand September 2026: {FWS_PDF}
- Einsatzgebiet: {EINSATZ}
- Förderung Kanton Zürich (Förderprogramm 2026): Erdwärmepumpe bis 15 kW CHF 6'800, darüber CHF 420 pro zusätzliches kW. Zusatzbeitrag CHF 3'000 plus CHF 100 pro kW über 15 kW für Sonden ohne Frostschutzmittel oder mit vollständiger Regeneration. Gesuch vor der Bohrung, ersetzt Öl-, Gas- oder Elektroheizung in bestehendem Gebäude. Der Kanton verlangt eine Bohrfirma mit gültigem Gütesiegel.
- Bewilligung: gewässerschutzrechtliche Bewilligung des AWEL, eingereicht bei der Gemeinde. Unter 2.5 m Grenzabstand Zustimmung des Nachbarn.
- Tiefe und Dauer: üblich 100 bis 300 m laut EnergieSchweiz, für 100 m mit Installation zwei bis drei Tage.

## Seiten
- [Start]({voll('')}): Heizungsersatz, Erdwärme, was Eco Green übernimmt, Gütesiegel, Förderrechner, häufige Fragen
- [Leistungen]({voll('leistungen')}): Sondenauslegung bis Befüllung
- [Ablauf]({voll('ablauf')}): sechs Schritte, Bewilligung, Baustellenregeln
- [Förderung]({voll('foerderung')}): Beiträge, Bedingungen, Unterlagen, Rechner
- [Baustellen]({voll('referenzen')}): Fotos von Baustellen und Geräten, Beispiele zur Orientierung (keine Kundenprojekte)
{rat_seite}- [Über uns]({voll('ueber-uns')}): Firma, Gütesiegel, Personen
- [Kontakt]({voll('kontakt')}): Telefon, E-Mail, Angaben für die Erstabklärung
{rat}"""

def manifest():
    return json.dumps({"name": "Eco Green Erdwärmesonden", "short_name": "Eco Green", "lang": "de-CH",
                       "start_url": PFAD, "scope": PFAD, "display": "standalone",
                       "background_color": "#FFFFFF", "theme_color": "#29662F",
                       "icons": [{"src": asset("img/icon-192.png"), "sizes": "192x192", "type": "image/png"},
                                 {"src": asset("img/icon-512.png"), "sizes": "512x512", "type": "image/png"},
                                 {"src": asset("img/icon-maskable-512.png"), "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
                                 {"src": asset("favicon.svg"), "sizes": "any", "type": "image/svg+xml"}]},
                      ensure_ascii=False, indent=1)


def og_bilder(docs_bau):
    """OG-Bild 1200 x 630 je Artikel. Neu gesetzt nur, wenn die Datei fehlt oder Titel oder Foto geaendert haben.
    Bestehende Bilder (og.jpg, og-leistungen.jpg ...) werden nie angefasst."""
    if not ARTIKEL:
        return
    stempel_datei = HIER / "og-ratgeber.json"
    stempel = json.loads(stempel_datei.read_text(encoding="utf-8")) if stempel_datei.is_file() else {}
    noetig = []
    for a in ARTIKEL:
        sig = f"{a['meta']['titel']}|{a['meta']['bild']}"
        if not (OUT / "img" / f"{og_name(a)}.jpg").is_file() or stempel.get(og_name(a)) != sig:
            noetig.append((a, sig))
    if not noetig:
        return
    import assets   # Pillow, nur bei Bedarf
    for a, sig in noetig:
        assets.og_artikel(og_name(a), a["meta"]["titel"], a["meta"]["bild"], OUT / "img")
        print(f"OG-Bild neu: img/{og_name(a)}.jpg")
        if docs_bau:
            stempel[og_name(a)] = sig
    if docs_bau:
        stempel_datei.write_text(json.dumps(stempel, ensure_ascii=False, indent=1), encoding="utf-8")


def bauen():
    docs_bau = OUT == DOCS
    if not docs_bau:
        OUT.mkdir(parents=True, exist_ok=True)
        shutil.copytree(DOCS, OUT, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("*.html", "*.atom", "sitemap.xml", "robots.txt", "llms.txt", "site.webmanifest"))
    static = HIER / "static"
    for f in static.rglob("*"):
        if f.is_file():
            ziel = OUT / f.relative_to(static)
            ziel.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, ziel)
    og_bilder(docs_bau)
    geschrieben, karte = set(), []
    for fn, arg in seiten_liste():
        s, body = fn(arg) if arg is not None else fn()
        body = shopify_attribute(body)
        doc = head(s) + kopf(s) + body + fuss()
        rel = s.get("datei") or datei_von(s["ziel"])
        ziel = OUT / rel
        ziel.parent.mkdir(parents=True, exist_ok=True)
        ziel.write_text(doc, encoding="utf-8")
        geschrieben.add(Path(rel).as_posix())
        if not s.get("fehlerseite"):
            karte.append((voll(s["ziel"]), s.get("stand", STAND)))
        tl, dl = len(s["title"]), len(s["desc"])
        warn = "" if (45 <= tl <= 62 and 140 <= dl <= 165) else "  <-- Laenge pruefen"
        print(f"{rel}: title {tl}, desc {dl}{warn}")
    # Alte Dateien entfernen (zum Beispiel leistungen.html im Wurzelordner, geloeschte Artikel)
    for f in sorted(OUT.rglob("*.html")):
        r = f.relative_to(OUT).as_posix()
        if r.split("/")[0] in ("fonts", "img"):
            continue
        if r not in geschrieben:
            f.unlink()
            print(f"entfernt: {r}")
    for leer in sorted((p for p in OUT.rglob("*") if p.is_dir()), reverse=True):
        if not any(leer.iterdir()):
            leer.rmdir()
    feed = OUT / "blogs" / f"{BLOG}.atom"
    if ARTIKEL:
        feed.parent.mkdir(parents=True, exist_ok=True)
        feed.write_text(atom_feed(), encoding="utf-8")
    elif feed.is_file():
        feed.unlink()
    sm = "".join(f"<url><loc>{u}</loc><lastmod>{d}</lastmod></url>\n" for u, d in karte)
    (OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{sm}</urlset>\n', encoding="utf-8")
    if VORSCHAU:
        robots = f"# Vorschau. Vor Livegang ersetzen durch: Allow: / und Sitemap-Zeile mit der echten Domain\nUser-agent: *\nDisallow: /\n\nSitemap: {BASIS}sitemap.xml\n"
    else:
        robots = f"User-agent: *\nAllow: /\n\nSitemap: {BASIS}sitemap.xml\n"
    (OUT / "robots.txt").write_text(robots, encoding="utf-8")
    (OUT / "llms.txt").write_text(llms(), encoding="utf-8")
    (OUT / "site.webmanifest").write_text(manifest(), encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    print(f"{len(karte)} URLs in der Sitemap, {len(ARTIKEL)} Ratgeber-Artikel, Ausgabe {OUT}")


# ---------------------------------------------------------------- Shopify-Export

def shopify_url(ziel):
    return "/" + pfad_von(ziel)


def main_inhalt(s, body):
    """Inhalt zwischen Kopf und Fuss, mit Shopify-URLs (PFAD /)."""
    return shopify_attribute(body).strip()


def shopify_export(ziel_ordner):
    konfig(live=True)            # Shopify-URLs: Pfad /, Domain eco-green.ch
    ziel_ordner = Path(ziel_ordner).resolve()
    (ziel_ordner / "schema").mkdir(parents=True, exist_ok=True)
    (ziel_ordner / "schema" / BLOG).mkdir(exist_ok=True)
    (ziel_ordner / "bilder").mkdir(exist_ok=True)
    zeilen = []          # fuer UEBERTRAGUNG.md: Vorschau-URL, Shopify-URL
    def vorschau_url(z):
        return VORSCHAU_BASIS + pfad_von(z)
    # Startseite und Seiten
    s, body = seite_start()
    start = {"vorlage": "index (Startseite des Themes, keine Shopify-Seite)", "titel": "Start", "seo_titel": s["title"],
             "seo_beschreibung": s["desc"], "body_html": main_inhalt(s, body)}
    (ziel_ordner / "schema" / "startseite.json").write_text(json.dumps(seiten_graph(s), ensure_ascii=False, indent=1), encoding="utf-8")
    zeilen.append((vorschau_url(""), "/", "Startseite (index)"))
    seiten = []
    fns = {"leistungen": seite_leistungen, "ablauf": seite_ablauf, "foerderung": seite_foerderung, "referenzen": seite_referenzen,
           "ueber-uns": seite_ueber, "kontakt": seite_kontakt, "impressum": seite_impressum, "datenschutz": seite_datenschutz}
    navname = dict(NAV_OHNE_RATGEBER) | {"impressum": "Impressum", "datenschutz": "Datenschutz"}
    for h in SEITEN_HANDLES:
        s, body = fns[h]()
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S).group(1)
        # title = Navigationsname (Shopify-Seitentitel, Menue, Brotkrumen), der Slogan bleibt als H1 im body_html
        seiten.append({"handle": h, "titel": navname[h], "h1": re.sub("<[^>]+>|&shy;", "", h1).strip(), "seo_titel": s["title"],
                       "seo_beschreibung": s["desc"], "body_html": main_inhalt(s, body), "stand": s.get("stand", STAND),
                       "schema_datei": f"schema/{h}.json"})
        (ziel_ordner / "schema" / f"{h}.json").write_text(json.dumps(seiten_graph(s), ensure_ascii=False, indent=1), encoding="utf-8")
        zeilen.append((vorschau_url(h), shopify_url(h), "Seite"))
    (ziel_ordner / "seiten.json").write_text(json.dumps(
        {"hinweis": "titel ist der Navigationsname und kommt in das Titelfeld der Shopify-Seite. Der Slogan (h1) steht schon als H1 im body_html, die Seitenvorlage darf deshalb keinen eigenen Titel-H1 ausgeben. body_html ist der ganze Seiteninhalt aus Sektionen mit data-shopify. Bild-URLs /img/... nach dem Hochladen auf Shopify-Dateien umstellen. Die Startseite ist keine Shopify-Seite, ihre SEO-Felder kommen in die Shop-Einstellungen.",
         "startseite": start, "seiten": seiten}, ensure_ascii=False, indent=1), encoding="utf-8")
    # Ratgeber
    artikel = []
    if ARTIKEL:
        s, _b = seite_ratgeber()
        (ziel_ordner / "schema" / f"{BLOG}.json").write_text(json.dumps(seiten_graph(s), ensure_ascii=False, indent=1), encoding="utf-8")
        zeilen.append((vorschau_url(BLOG), shopify_url(BLOG), "Blog-Übersicht"))
        for a in ARTIKEL:
            m = a["meta"]
            s, _b = seite_artikel(a)
            koerper = loese_links(a["koerper"])
            fragen = "".join(f"<h3>{esc(f['f'])}</h3><p>{esc(f['a'])}</p>" for f in m["fragen"])
            quellen = "".join(f'<li><a href="{esc(q["url"])}" rel="noopener">{esc(q["name"])}</a>, abgerufen {esc(q["abgerufen"])}</li>' for q in m["quellen"])
            datei = bild_gross(m["bild"])
            shutil.copy2(DOCS / datei, ziel_ordner / "bilder" / Path(datei).name)
            artikel.append({
                "handle": m["handle"], "titel": m["titel"], "blog": "Ratgeber", "blog_handle": BLOG,
                "body_html": koerper, "body_html_komplett": koerper + f"<h2>Kurz gefragt</h2>{fragen}<h2>Quellen</h2><ol>{quellen}</ol>",
                "summary_html": f"<p>{esc(m['kurz'])}</p>", "seo_titel": m["seo_titel"], "seo_beschreibung": m["beschreibung"],
                "tags": m["tags"], "published_at": iso_zeit(m["stand"]), "autor": "Eco Green GmbH",
                "bild_datei": f"bilder/{Path(datei).name}", "bild_alt": m["bild_alt"], "bild_legende": m["bild_legende"],
                "fragen": m["fragen"], "quellen": m["quellen"], "verwandt": [x["meta"]["handle"] for x in verwandte(a)],
                "schema_datei": f"schema/{BLOG}/{m['handle']}.json"})
            (ziel_ordner / "schema" / BLOG / f"{m['handle']}.json").write_text(json.dumps(seiten_graph(s), ensure_ascii=False, indent=1), encoding="utf-8")
            zeilen.append((vorschau_url("artikel:" + m["handle"]), shopify_url("artikel:" + m["handle"]), "Blogartikel"))
    (ziel_ordner / "artikel.json").write_text(json.dumps(
        {"blog": {"titel": "Ratgeber", "handle": BLOG, "url": "/blogs/" + BLOG, "feed": f"/blogs/{BLOG}.atom"},
         "hinweis": "body_html ist der reine Artikeltext. body_html_komplett haengt Kurz gefragt und Quellen an, fuer ein Theme ohne eigene Bloecke.",
         "artikel": artikel}, ensure_ascii=False, indent=1), encoding="utf-8")
    # Weiterleitungen im Importformat von Shopify (zwei Spalten: Redirect from, Redirect to)
    alt = json.loads((HIER.parents[1] / "recherche" / "roh" / "pages.json").read_text(encoding="utf-8"))
    wl = []
    for p in alt:
        pfad = "/" + p["link"].split("/", 3)[3]
        if pfad in ("/", ""):
            continue      # Startseite bleibt /
        wl.append((pfad, "/pages/ueber-uns"))
    for pfad in ["/index.php/uber-uns/", "/index.php/geothermische-energie-uber-uns/"]:
        if (pfad, "/pages/ueber-uns") not in wl:
            wl.append((pfad, "/pages/ueber-uns"))
    for pfad in list(dict.fromkeys(x for x, _ in wl)):
        if pfad.endswith("/") and (pfad.rstrip("/"), "/pages/ueber-uns") not in wl:
            wl.append((pfad.rstrip("/"), "/pages/ueber-uns"))
    wl += [("/index.php/sitemap_index.xml", "/sitemap.xml"), ("/index.php/page-sitemap.xml", "/sitemap.xml"),
           ("/index.php/", "/"), ("/index.php", "/")]
    with open(ziel_ordner / "weiterleitungen.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Redirect from", "Redirect to"])
        w.writerows(wl)
    (ziel_ordner / "UEBERTRAGUNG.md").write_text(uebertragung_md(zeilen, wl), encoding="utf-8")
    print(f"Shopify-Export: {len(seiten)} Seiten, {len(artikel)} Artikel, {len(wl)} Weiterleitungen nach {ziel_ordner}")


def uebertragung_md(zeilen, wl):
    tab = "\n".join(f"| {v} | `{s}` | {t} |" for v, s, t in zeilen)
    wtab = "\n".join(f"| `{a}` | `{b}` |" for a, b in wl)
    heute = date.today().strftime("%d.%m.%Y")
    return f"""# Eco Green: Übertragung auf Shopify

Erzeugt mit `python bauen.py --shopify` am {heute}. Quelle: `website-neu/src/bauen.py`. Diese Datei nicht von Hand ändern, sondern den Generator.

## Adressen

Die Vorschau hat denselben Aufbau wie Shopify. Beim Umzug ändert sich nur die Domain, kein Pfad.

| Vorschau | Shopify | Art |
|---|---|---|
{tab}
| {VORSCHAU_BASIS}blogs/{BLOG}.atom | `/blogs/{BLOG}.atom` | Atom-Feed. Shopify erzeugt je Blog einen eigenen, Pfad nach dem Umzug prüfen |

## Dateien in diesem Ordner

| Datei | Inhalt | Ziel in Shopify |
|---|---|---|
| `seiten.json` | Startseite und acht Seiten: Handle, Titel (Navigationsname), H1 (Slogan, steht schon im `body_html`), `body_html`, SEO-Titel, SEO-Beschreibung | Online Store, Seiten. SEO-Felder unter «Suchmaschinen-Eintrag». Startseite siehe unten |
| `artikel.json` | Blog «Ratgeber» (Handle `{BLOG}`) und alle Artikel: Handle, Titel, `body_html`, `summary_html`, Tags, `published_at`, Bild und Alt-Text | Online Store, Blogbeiträge |
| `bilder/` | Artikelbilder in voller Breite | Bild des Blogbeitrags |
| `weiterleitungen.csv` | alte WordPress-Adressen auf die neuen Ziele | Online Store, Navigation, URL-Weiterleitungen, Import |
| `schema/*.json` | JSON-LD je Seite, mit Domain eco-green.ch | Vorlage für die JSON-LD-Snippets im Theme |

## Was Shopify selbst liefert und nicht überschrieben wird

| Was | Warum | Beleg |
|---|---|---|
| `sitemap.xml` | Shopify erzeugt sie selbst. Unsere Datei aus der Vorschau wird nicht hochgeladen. Nach dem Umzug prüfen, dass Seiten, Blog und Artikel darin stehen. | shopify.dev, Liquid-Objekt `group` («The sitemap can be accessed at /sitemap.xml»); Vault-Notiz Shopify Auffindbarkeit, Technisches SEO |
| `llms.txt` | Shopify liefert auf Shops eine eigene Datei mit Anweisungen für Einkaufsagenten. Nicht überschreiben. Unsere Fassung aus der Vorschau entfällt. | Skill-Regel seo-geo-2026.md (B, llms.txt), Messung GEO Playbook 24.10.2026 |
| Canonical | Im Theme `<link rel="canonical" href="{{{{ canonical_url }}}}">`, kein eigener Wert | shopify.dev, «Add SEO metadata to your theme» |
| Title und Description | `page_title` und `page_description` aus den SEO-Feldern (Metafelder `global.title_tag`, `global.description_tag`) | shopify.dev, «Add SEO metadata», «Optimize storefront SEO» |
| Atom-Feed | Shopify erzeugt je Blog einen Atom-Feed | shopify.dev, REST-Ressource Blog: «An Atom feed is automatically generated for each blog» |
| robots.txt | Shopify-Standard. Kein eigenes Template, solange nichts gesperrt werden muss (siehe unten) | shopify.dev, «Customize robots.txt»; Vault-Notiz Shopify Auffindbarkeit |

## Was ins Theme gehört

| Teil | Umsetzung | Stand |
|---|---|---|
| Seitenvorlage | Ohne eigenen Titel-H1 bauen. Der Seitentitel in Shopify ist der Navigationsname (Leistungen, Ablauf, Förderung, Baustellen, Über uns, Kontakt, Impressum, Datenschutz), die H1 mit dem Slogan steht im `body_html`. Gibt die Vorlage den Titel als H1 aus, stehen zwei H1 auf der Seite. | offen |
| Startseite | Keine Shopify-Seite, sondern die Vorlage `index` des Themes. SEO-Titel und SEO-Beschreibung aus `seiten.json` (`startseite`) gehören in die Shop-Einstellungen (Einstellungen, Präferenzen, Titel und Meta-Beschreibung der Startseite). | offen |
| Sektionen | Jede `<section>` trägt `data-shopify="<name>"`. Je Name eine Theme-Sektion, Texte als Einstellungen oder Metafelder. Kopf, Menü, Fuss, Kontaktleiste ebenso (`header`, `menu-drawer`, `footer`, `kontaktleiste`). | vorbereitet |
| `robots.txt.liquid` | Nur anlegen, wenn etwas vom Standard abweichen muss. Ein Template ersetzt die ganze Shopify-Ausgabe, vorher `/robots.txt` sichern und vergleichen. Nie `/policies/`, Bilder, CSS oder JS sperren. Vorschau-Sperre der GitHub-Seite nicht übernehmen. | offen, Empfehlung: kein Template |
| JSON-LD | Snippet für die Organisation (`HomeAndConstructionBusiness`, `@id` `https://eco-green.ch/#firma`) auf jeder Seite, dazu je Vorlage: `WebPage` und `BreadcrumbList` (Seiten), `Service` (Leistungen), `FAQPage` (Start, Förderung, Artikel), `CollectionPage` mit `Blog` (Übersicht), `BlogPosting` (Artikel). Werte aus `schema/`. Keine Sterne, kein `AggregateRating`. Startseite bleibt `WebPage`, nie `Article`. | offen |
| Artikelvorlage | Brotkrumen, H1, `summary_html` als Lead, Zeile «Eco Green GmbH · Stand», Bild mit Legende, Text, «Kurz gefragt», Quellen (nur die Liste, ohne Zusatzabsatz), verwandte Artikel (nur Titel und Stand, ohne Lead), Abschluss ohne Telefonzeiten. Fragen, Quellen und verwandte Artikel als Artikel-Metafelder oder aus `body_html_komplett`. | offen |
| Förderrechner | `site.js` (Abschnitt Foerderrechner) und das Markup aus `rechner_html()` als Sektion `foerderrechner`. Sätze stehen im Skript, bei Änderung des kantonalen Programms dort anpassen. | offen |
| Kontaktformular | Heute nur `mailto:` mit Vorlage. Auf Shopify das Theme-Kontaktformular (`form 'contact'`) mit den fünf Angaben der Vorlage, Honeypot, Datenschutzhinweis. Eingang im Postfach info@eco-green.ch nach dem Umzug mit echtem Testversand prüfen. | offen |
| Schriften | Schibsted Grotesk (variabel) und IBM Plex Mono 500 als WOFF2 in die Theme-Assets, `@font-face` mit `{{{{ 'datei.woff2' | asset_url }}}}`, Hauptschrift vorladen. Keine Google-Fonts-Anfrage. | offen |
| Bilder | WebP aus `docs/img` in die Theme-Assets oder Dateien, `srcset` über `image_url` mit Breiten 480, 800, 1200. OG-Bilder 1200 x 630 je Seite und Artikel. | offen |
| Datenschutz | Abschnitt Hosting von GitHub auf Shopify umschreiben (FILLER.md, T4). | offen |

## Reihenfolge am Umzugstag

1. Nullmessung der alten Seite sichern: Search Console 16 Monate exportieren, Anfragen pro Monat notieren.
2. Vor dem Umzug alte URLs vollständig sammeln: alle Seiten mit Impressionen aus der Search Console (Leistung, Seiten) und ein Crawl der alten Website. Die Liste aus der WordPress-Schnittstelle (zwei Seiten) reicht nicht. Jede gefundene Adresse über den Generator in `weiterleitungen.csv` aufnehmen.
3. Theme mit allen Sektionen veröffentlichen, Seitenvorlage ohne eigenen Titel-H1. Seiten aus `seiten.json` (Titel = Navigationsname) und Blog «Ratgeber» mit Artikeln aus `artikel.json` anlegen, Handles exakt wie in der Tabelle oben.
4. SEO-Titel und SEO-Beschreibung je Seite und Artikel setzen, Artikelbild mit Alt-Text. Für die Startseite in den Shop-Einstellungen.
5. Menüs: Kopf und Fuss wie in der Vorschau, Impressum und Datenschutz im Fussmenü.
6. Passwortschutz des Shops aufheben.
7. Domain eco-green.ch verbinden und als Hauptdomain setzen. www und ohne www auf eine Variante.
8. `weiterleitungen.csv` importieren. Shopify leitet nur Adressen weiter, unter denen es selbst nichts ausliefert (404), laut Vault-Notiz «Wissensstand Web und Auffindbarkeit», S15, nach help.shopify.com url-redirect.
9. Prüfungen unten abarbeiten.

## Prüfungen danach

| Prüfung | Ziel |
|---|---|
| `curl -I` auf jede URL der Tabelle oben | Status 200 |
| `curl -I https://eco-green.ch/gibtsnicht` | Status 404 mit gestalteter Seite |
| `curl -I` auf jede alte Adresse aus `weiterleitungen.csv` | 301 auf das Ziel, eine Stufe, keine Kette |
| http und www | leiten in einer Stufe auf `https://eco-green.ch/` |
| Quelltext einer Seite | ein Canonical auf die eigene URL, kein `noindex`, JSON-LD parst (Rich Results Test, validator.schema.org) |
| `/robots.txt` | Shopify-Standard, Such- und KI-Antwort-Crawler nicht gesperrt, Zeile Sitemap |
| Search Console | Domain-Property per DNS, `https://eco-green.ch/sitemap.xml` eingereicht, Schalter «Search generative AI» eingeschlossen |
| Bing Webmaster Tools | Import aus der Search Console, Sitemap eingereicht |
| IndexNow | Bing meldet in den Webmaster Tools, ob Shopify IndexNow sendet. Sonst die neuen URLs einmal von Hand in Bing einreichen. Offen, ob Shopify IndexNow selbst auslöst. |
| Kontaktformular | Testanfrage kommt bei info@eco-green.ch an |

## Weiterleitungen

| Alt | Neu |
|---|---|
{wtab}

Die alte Startseite `https://eco-green.ch/` bleibt `/`. Quelle der alten Adressen: `recherche/roh/pages.json` (WordPress-API) und Links der alten Startseite. Das ist nicht vollständig, vor dem Umzug Search Console und Crawl ergänzen (Schritt 2). Weiterleitungen mindestens ein Jahr stehen lassen, nie Ketten.

## Offen

- Spaltenköpfe der CSV (`Redirect from`, `Redirect to`) vor dem Import mit der Musterdatei im Shopify-Admin abgleichen. In der Entwicklerdoku nur indirekt belegt (Admin-API `urlRedirectImportCreate` verweist auf eine Musterdatei).
- Ob Shopify Weiterleitungen mit und ohne Schrägstrich am Ende gleich behandelt. Beide Formen stehen deshalb in der CSV.
- Ob Shopify beim späteren Ändern eines Artikel-Handles selbst eine Weiterleitung anlegt. Nur aus Drittanleitungen bekannt, im Admin prüfen (Vault, Wissensstand Web und Auffindbarkeit, S15).
- Ob `/index.php` und die alten Sitemap-Pfade auf Shopify überhaupt weitergeleitet werden können. Nach dem Import mit `curl -I` prüfen.
- Ob das Theme den Shopnamen an den SEO-Titel anhängt. Die Vorlage in der Doku hängt ihn an, wenn er im Titel fehlt. Unsere SEO-Titel enthalten «Eco Green» bereits, das Theme muss sie unverändert ausgeben.
"""


def argument(name):
    if name not in sys.argv:
        return None
    i = sys.argv.index(name)
    if i + 1 >= len(sys.argv) or sys.argv[i + 1].startswith("--"):
        return ""
    return sys.argv[i + 1]


def main():
    global OUT, ARTIKEL, NAV
    live, ziel, quelle, shop = argument("--live"), argument("--ziel"), argument("--ratgeber"), argument("--shopify")
    if live == "" or ziel == "" or quelle == "":
        fehler("--live, --ziel und --ratgeber brauchen einen Ordner")
    if quelle and not (live or ziel or shop is not None):
        fehler("--ratgeber <ordner> nur zusammen mit --live, --ziel oder --shopify, damit keine Testartikel in docs landen")
    ARTIKEL = lies_artikel(Path(quelle).resolve() if quelle else RATGEBER_DIR)
    NAV = NAV_MIT_RATGEBER if ARTIKEL else NAV_OHNE_RATGEBER
    if shop is not None:
        shopify_export(shop or SHOPIFY_ZIEL)
        return
    if live:
        konfig(live=True)
        OUT = Path(live).resolve()
    else:
        konfig(live=False)
        OUT = Path(ziel).resolve() if ziel else DOCS
    if OUT == DOCS and quelle:
        fehler("Testartikel nie nach docs bauen")
    bauen()


if __name__ == "__main__":
    main()
