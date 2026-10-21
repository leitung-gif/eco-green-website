"""Generator fuer die Website von Eco Green GmbH. Schreibt nach ../docs (GitHub Pages).

Aufruf:  python assets.py   (einmal, Bilder und Icons)
         python bauen.py    (Seiten, Sitemap, robots, llms.txt)

Fakten und Quellen (alle abgerufen 21.10.2026, Details im DD-Bericht LG-DD-2026-EG01):
  Firma, UID, Organe ............ Zefix/SHAB Eco Green GmbH CHE-141.654.180
  FWS-Guetesiegel ............... FWS Guetesiegelliste Juni 2021 und Juli 2026
  Bewilligung, Abstand 2,5 m .... zh.ch Erdwaermesonden
  Foerdersaetze, Unterlagen ..... Kanton Zuerich, Foerderprogramm 2025 Heizung ersetzen, S. 16 f.
  Programm 2026 unveraendert .... zh.ch Mitteilung 24.10.2025
  Heizungsersatz seit 01.09.2022  zh.ch Bauvorschriften Gebaeude Energie
Fuellinhalte, die Eco Green ersetzt: siehe ../../FILLER.md
"""
from pathlib import Path
from urllib.parse import quote
import json, shutil, re, html

HIER = Path(__file__).resolve().parent
OUT = HIER.parent / "docs"
BILDER = json.loads((HIER / "bilder.json").read_text(encoding="utf-8"))

# Vorschau auf GitHub Pages. Vor Livegang: BASIS auf https://eco-green.ch/ setzen, VORSCHAU = False.
import sys
BASIS = "https://leitung-gif.github.io/eco-green-website/"
VORSCHAU = True
if "--live" in sys.argv:          # Probe fuer den Livegang: python bauen.py --live <ordner>
    BASIS, VORSCHAU = "https://eco-green.ch/", False
    OUT = Path(sys.argv[sys.argv.index("--live") + 1]).resolve()
PFAD = "/" + BASIS.split("/", 3)[3]
STAND = "2026-10-21"

TEL = "044 400 20 20"
TEL_LINK = "tel:+41444002020"
MAIL = "info@eco-green.ch"
FWS_PDF = "https://www.fws.ch/wp-content/uploads/2026/07/072026_FWS_GSP_Guetesiegelliste_D_F.pdf"
ZH_SONDEN = "https://www.zh.ch/de/planen-bauen/bauvorschriften/energienutzung-untergrund-wasser/erdwaermesonden.html"
ZH_FOERDER_PDF = "https://zh.ch/content/dam/zhweb/bilder-dokumente/themen/umwelt-tiere/energie/energieberatung-und-energiefoerderung/ktzh_foerderprogramm_2025_heizung_ersetzen.pdf"
ZH_2026 = "https://www.zh.ch/de/news-uebersicht/mitteilungen/2025/umwelt-tiere/energie/foerderprogramm-energie-geht-2026-unveraendert-weiter.html"
ZH_ENERGIE = "https://www.zh.ch/de/planen-bauen/bauvorschriften/bauvorschriften-gebaeude-energie.html"
KARTE = "https://www.openstreetmap.org/search?query=Pumpwerkstrasse%2040%2C%208105%20Regensdorf"

# FILLER: Zeiten und Regeln, bis Eco Green sie bestaetigt
BUEROZEIT = "Montag bis Freitag, 07.30 bis 12.00 und 13.30 bis 17.00 Uhr"
EINSATZ = "Kanton Zürich und angrenzende Regionen"

MAIL_TEXT = ("Guten Tag\n\nIch möchte wissen, ob bei mir eine Erdwärmesonde möglich ist.\n\n"
             "Adresse des Grundstücks:\nHeutige Heizung (Öl, Gas, Elektro) und ihr Baujahr:\n"
             "Verbrauch pro Jahr (zum Beispiel Liter Öl):\nBaujahr und Wohnfläche des Hauses:\nTelefon für Rückruf:\n\nFreundliche Grüsse\n")
MAILTO = f"mailto:{MAIL}?subject={quote('Erstabklärung Erdwärmesonde')}&body={quote(MAIL_TEXT)}"

NAV = [("leistungen", "Leistungen"), ("ablauf", "Ablauf"), ("foerderung", "Förderung"),
       ("referenzen", "Baustellen"), ("ueber-uns", "Über uns"), ("kontakt", "Kontakt")]

ORG_ID = BASIS + "#firma"

def esc(s): return html.escape(s, quote=True)

# ---------------------------------------------------------------- Bausteine

def bild(p, key, alt, sizes="(max-width: 900px) 100vw, 40vw", lazy=True, prio=False, breit=None):
    w, h, br = BILDER["fotos"][key]
    br = [b for b in br if breit is None or b <= breit] or br[:1]
    srcset = ", ".join(f"{p}img/{key}-{b}.webp {min(b, w)}w" for b in br)
    gross = br[-1] if len(br) == 1 else br[1]
    attr = 'fetchpriority="high"' if prio else ('loading="lazy" decoding="async"' if lazy else "")
    return (f'<img src="{p}img/{key}-{gross}.webp" srcset="{srcset}" sizes="{sizes}" '
            f'width="{w}" height="{h}" alt="{esc(alt)}" {attr}>')

def preload(key, sizes):
    w, h, br = BILDER["fotos"][key]
    ss = ", ".join(f"img/{key}-{b}.webp {min(b, w)}w" for b in br)
    return f'<link rel="preload" as="image" href="img/{key}-{br[min(1, len(br) - 1)]}.webp" imagesrcset="{ss}" imagesizes="{sizes}" fetchpriority="high">\n'

def foto(p, key, alt, cap=None, cls="", **kw):
    c = f"<figcaption>{cap}</figcaption>" if cap else ""
    return f'<figure class="foto {cls}">{bild(p, key, alt, **kw)}{c}</figure>'

def org_schema():
    return {
        "@type": ["HomeAndConstructionBusiness", "LocalBusiness"], "@id": ORG_ID,
        "name": "Eco Green", "legalName": "Eco Green GmbH", "alternateName": "Eco Green GmbH",
        "description": "Bohrfirma für Erdwärmesonden in Regensdorf ZH. Sondenauslegung, Erdsondenbohrung, Sondeneinbau und Anbindung an die Wärmepumpe. Träger des FWS-Gütesiegels für Erdwärmesonden-Bohrfirmen.",
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
        {"@type": "ListItem", "position": i + 1, "name": n, "item": BASIS + u} for i, (u, n) in enumerate(spur)]}

def head(s):
    p = s["p"]
    url = BASIS + s["slug"]
    graph = [org_schema()] + s.get("schema", [])
    if s["slug"]:
        graph.append(brot_schema([("", "Start")] + s["spur"]))
    graph.append({"@type": "WebPage", "@id": url + "#seite", "url": url, "name": s["title"],
                  "description": s["desc"], "inLanguage": "de-CH", "isPartOf": {"@id": BASIS + "#website"},
                  "about": {"@id": ORG_ID}, "dateModified": STAND})
    ld = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":"))
    robots = "noindex, nofollow" if VORSCHAU else "index, follow"
    pre = s.get("preload", "")
    return f"""<!doctype html>
<html lang="de-CH">
<head>
<meta charset="utf-8">
<script>document.documentElement.classList.add("js")</script>
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(s['title'])}</title>
<meta name="description" content="{esc(s['desc'])}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{url}">
<meta name="theme-color" content="#F2EEE3" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#14140F" media="(prefers-color-scheme: dark)">
<meta property="og:type" content="website">
<meta property="og:locale" content="de_CH">
<meta property="og:site_name" content="Eco Green">
<meta property="og:title" content="{esc(s.get('og', s['title']))}">
<meta property="og:description" content="{esc(s['desc'])}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{BASIS}img/{s.get('ogbild', 'og')}.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc(s.get('ogalt', 'Eco Green, Erdwärmesonden aus Regensdorf. Schwarzweissfoto einer Baustelle.'))}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(s.get('og', s['title']))}">
<meta name="twitter:description" content="{esc(s['desc'])}">
<meta name="twitter:image" content="{BASIS}img/{s.get('ogbild', 'og')}.jpg">
<link rel="icon" href="{p}favicon.svg" type="image/svg+xml">
<link rel="icon" href="{p}favicon.ico" sizes="32x32">
<link rel="apple-touch-icon" href="{p}apple-touch-icon.png">
<link rel="manifest" href="{p}site.webmanifest">
<link rel="preload" href="{p}fonts/schibsted-grotesk-var.woff2" as="font" type="font/woff2" crossorigin>
{pre}<link rel="stylesheet" href="{p}site.css?v=1">
<script type="application/ld+json">{ld}</script>
</head>
<body>
<a class="skip" href="#inhalt">Zum Inhalt</a>
"""

def kopf(s):
    p, aktiv = s["p"], s["slug"]
    def a(u, n, extra=""):
        cur = ' aria-current="page"' if u == aktiv else ""
        return f'<a href="{(p + u) or "./"}"{cur}>{extra}{n}</a>'
    nav = "".join(a(u, n) for u, n in NAV)
    mnav = "".join(a(u, n, "") .replace(f">{n}</a>", f"><span>{n}</span><span class=\"mono\">{i + 1:02d}</span></a>")
                   for i, (u, n) in enumerate([("", "Start")] + NAV))
    start = p if p else "./"
    return f"""<header class="kopf">
 <div class="wrap kopf-in">
  <a class="marke" href="{start}" aria-label="Eco Green, zur Startseite"><img src="{p}img/logo.svg" width="170" height="63" alt="Eco Green"></a>
  <nav class="nav" aria-label="Hauptnavigation">{nav}</nav>
  <a class="knopf" href="{TEL_LINK}"><span class="lang">Anrufen </span>{TEL}</a>
  <button class="menuknopf" type="button" aria-expanded="false" aria-controls="menue">Menü</button>
 </div>
</header>
<div class="menue" id="menue" aria-hidden="true" inert>
 <div class="menue-kopf"><img src="{p}img/logo-hell.svg" width="120" height="45" alt="Eco Green"><button class="menue-zu" type="button">Schliessen</button></div>
 <nav aria-label="Menü">{mnav}</nav>
 <a class="knopf" href="{TEL_LINK}">{TEL} anrufen</a>
</div>
<main id="inhalt">
"""

def schluss(p, titel="Schicken Sie uns Ihre Adresse.", text=None, flaeche="gruen-flaeche"):
    text = text or "Wir prüfen, ob auf Ihrem Grundstück gebohrt werden darf, und melden uns mit einer ersten Einschätzung zu Sonde und Förderbeitrag."
    return f"""<section class="schluss {flaeche}" aria-labelledby="schluss-titel">
 <div class="wrap">
  <h2 id="schluss-titel">{titel}</h2>
  <p class="lead">{text}</p>
  <div class="knopfreihe"><a class="knopf" href="{MAILTO}">Anfrage per E-Mail <span class="pfeil">→</span></a><a class="knopf weiss" href="{TEL_LINK}">{TEL}</a></div>
  <div class="schluss-zeile"><span>{BUEROZEIT}</span><span>Pumpwerkstrasse 40, 8105 Regensdorf</span></div>
 </div>
</section>
"""

def fuss(p):
    links = "".join(f'<li><a href="{p}{u}">{n}</a></li>' for u, n in NAV)
    start = p if p else "./"
    return f"""</main>
<footer class="fuss">
 <div class="wrap">
  <div class="fuss-grid">
   <div>
    <a class="marke" href="{start}"><img src="{p}img/logo-hell.svg" width="170" height="63" alt="Eco Green, zur Startseite" loading="lazy"></a>
    <p>Erdwärmesonden für Häuser im Kanton Zürich.<br>Bohrfirma mit FWS-Gütesiegel.</p>
    <a class="fuss-siegel" href="{FWS_PDF}" rel="noopener">FWS-Gütesiegelliste, Stand Juli 2026</a>
   </div>
   <div><h2>Seiten</h2><ul>{links}</ul></div>
   <div><h2>Kontakt</h2><ul><li><a href="{TEL_LINK}">{TEL}</a></li><li><a href="mailto:{MAIL}">{MAIL}</a></li><li><a href="{KARTE}" rel="noopener">Pumpwerkstrasse 40<br>8105 Regensdorf</a></li></ul></div>
   <div><h2>Rechtliches</h2><ul><li><a href="{p}impressum">Impressum</a></li><li><a href="{p}datenschutz">Datenschutz</a></li></ul></div>
  </div>
  <div class="fuss-unten"><span>© 2026 Eco Green GmbH, Regensdorf</span><span>CHE-141.654.180</span></div>
 </div>
</footer>
<nav class="leiste" aria-label="Schnellkontakt"><a href="{TEL_LINK}">Anrufen</a><a href="{MAILTO}">E-Mail</a></nav>
<script src="{p}site.js?v=1" defer></script>
</body>
</html>
"""

def seitenkopf(s, h1, lead, extra=""):
    p = s["p"]
    spur = [("", "Start")] + s["spur"]
    li = []
    for i, (u, n) in enumerate(spur):
        if i == len(spur) - 1:
            li.append(f'<li aria-current="page">{n}</li>')
        else:
            li.append(f'<li><a href="{p}{u}" >{n}</a></li>' if u else f'<li><a href="{p or "./"}">{n}</a></li>')
    return f"""<section class="seitenkopf raster">
 <div class="wrap seitenkopf-in">
  <nav aria-label="Brotkrumen"><ol class="brot">{''.join(li)}</ol></nav>
  {extra if extra else f'<h1>{h1}</h1><p class="lead">{lead}</p>'}
 </div>
</section>
"""

# ---------------------------------------------------------------- Inhalte

FAQ = [
    ("Darf auf meinem Grundstück gebohrt werden?",
     "<p>Das zeigt der Wärmenutzungsatlas des Kantons Zürich für jede Parzelle. Wir prüfen das vor der Offerte. Liegt eine Sonde näher als 2,5 Meter an der Grundstücksgrenze, braucht es die Zustimmung Ihres Nachbarn.</p>"),
    ("Wie tief wird gebohrt?",
     "<p>Das hängt vom Wärmebedarf und vom Untergrund ab. Ein Einfamilienhaus braucht oft eine oder zwei Sonden von 150 bis 250 Metern. Im Kanton Zürich reichen Erdwärmesonden meist bis höchstens 500 Meter.</p>"),
    ("Wie lange dauert die Bohrung?",
     "<p>Pro Sonde meist ein bis zwei Tage. Dazu kommen ein Tag für Aufbau und Abbau und die Arbeiten für den Anschluss ans Haus. Den genauen Plan erhalten Sie mit der Offerte.</p>"),
    ("Wer reicht die Bewilligung ein?",
     "<p>Jede Erdwärmesonde braucht eine gewässerschutzrechtliche Bewilligung des AWEL. Eingereicht wird bei der Baubehörde Ihrer Gemeinde, auch über eBaugesucheZH. Wir stellen die Unterlagen für Sie zusammen.</p>"),
    ("Was bedeutet das FWS-Gütesiegel?",
     "<p>Die Fachvereinigung Wärmepumpen Schweiz vergibt es an Bohrfirmen, die Beratung, Sondenmaterial, Ausführung und Sicherheit auf der Baustelle nach ihren Vorgaben erfüllen. Das AWEL empfiehlt Bauherrschaften solche Firmen. Für den Förderbeitrag verlangt der Kanton eine Bohrfirma mit gültigem Gütesiegel.</p>"),
    ("Muss ich meine Ölheizung ersetzen?",
     "<p>Solange sie läuft, nicht. Wird sie ersetzt, darf im Kanton Zürich seit 01.09.2022 grundsätzlich nur noch ein erneuerbares System eingebaut werden. Eine Ausnahme gibt es, wenn die erneuerbare Lösung über die Lebensdauer mehr als 5 Prozent teurer ist.</p>"),
]

def faq_schema(liste):
    return {"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub("<[^>]+>", "", a)}} for q, a in liste]}

def faq_html(liste):
    return "".join(f'<details><summary>{q}</summary><div class="antwort">{a}</div></details>' for q, a in liste)

SCHRITTE = [
    ("Abklärung", "1 bis 3 Arbeitstage",
     "Sie schicken uns Adresse und heutigen Verbrauch. Wir prüfen im Wärmenutzungsatlas des Kantons, ob auf Ihrer Parzelle gebohrt werden darf, und schätzen Anzahl und Tiefe der Sonden."),
    ("Bewilligung und Förderung", "4 bis 8 Wochen",
     "Das Bewilligungsgesuch geht über Ihre Gemeinde an das AWEL. Gleichzeitig reichen Sie das Fördergesuch beim Kanton ein. Gebohrt wird erst, wenn beides steht."),
    ("Bohrung", "1 bis 2 Tage pro Sonde",
     "Das Raupengerät fährt auf Ihr Grundstück oder kommt mit dem Kran über das Haus. Bohrwasser und Bohrschlamm fangen wir in Mulden auf und führen sie ab."),
    ("Sonde einbauen", "am Tag der Bohrung",
     "In das Bohrloch kommt die Sonde aus Kunststoffrohr. Den Raum rundherum füllen wir mit einer Zement-Bentonit-Mischung, damit kein Wasser zwischen den Bodenschichten fliesst."),
    ("Druckprobe und Anschluss", "1 bis 2 Tage",
     "Jede Sonde wird mit Druck geprüft. Wir verlegen die Leitungen bis in den Heizraum, setzen den Verteiler und füllen das System mit Wärmeträgerflüssigkeit."),
    ("Übergabe", "mit der Schlussrechnung",
     "Sie erhalten das Bohrprotokoll und die Rechnung für die Bohrung. Beides verlangt der Kanton für die Auszahlung des Förderbeitrags. Ihr Heizungsinstallateur schliesst die Wärmepumpe an."),
]

LEISTUNGEN = [
    ("Sondenauslegung", "Aus Wärmebedarf und Untergrund berechnen wir, wie viele Sonden Ihr Haus braucht und wie tief sie gehen. Zu kurz kühlt der Boden über die Jahre aus. Zu lang zahlen Sie Meter, die Sie nicht brauchen.", None),
    ("Bewilligungs&shy;unterlagen", "Für das gewässerschutzrechtliche Gesuch stellen wir zusammen, was die Gemeinde verlangt: Situationsplan mit Sondenstandort, Sondenlänge, Angaben zur Wärmepumpe. Sie unterschreiben und reichen ein.", None),
    ("Erdsonden&shy;bohrung", "Mit eigenen Raupenbohrgeräten und eigenem Bohrteam, an dem Tag, der in der Offerte steht. Ist die Zufahrt zu eng, hebt ein Kran das Gerät über das Haus.", "garten"),
    ("Sondeneinbau und Verfüllung", "Wir bauen die Sonde ein und verfüllen das Bohrloch von unten nach oben dicht. So fliesst kein Wasser zwischen den Bodenschichten, und die Sonde bleibt Jahrzehnte im Boden.", None),
    ("Druckprobe und Anbindung", "Jede Sonde wird mit Druck geprüft und im Protokoll festgehalten. Danach verlegen wir die Verbindungsleitungen zum Haus und setzen den Verteiler im Heizraum.", "verteiler"),
    ("Befüllung und Übergabe", "Wir füllen Sonde und Leitungen mit Wärmeträgerflüssigkeit und übergeben die Anlage an Ihren Heizungsinstallateur. Bohrprotokoll und Rechnung für das Fördergesuch erhalten Sie mit.", None),
]

# ---------------------------------------------------------------- Seiten

def schnitt_svg():
    # Schema eines Bodenschnitts, 400 x 700. 0 m auf y=130, 2,2 px pro Meter.
    Y0, K = 130, 2.2
    ticks = "".join(
        f'<line x1="330" y1="{Y0 + m * K:.0f}" x2="352" y2="{Y0 + m * K:.0f}" stroke="#14140F" stroke-width="3"/>'
        f'<text x="358" y="{Y0 + 5 + m * K:.0f}">{m if m else "0 m"}</text>'
        for m in range(0, 251, 50))
    return f"""<svg viewBox="0 0 400 700" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Schema eines Bodenschnitts: Haus mit Wärmepumpe, darunter Humus, Kies und Fels. Die Erdwärmesonde wächst beim Scrollen in die Tiefe.">
<defs>
 <pattern id="kies" width="16" height="16" patternUnits="userSpaceOnUse"><rect width="16" height="16" fill="#E7D7AE"/><circle cx="4" cy="4" r="2.2" fill="#14140F"/><circle cx="12" cy="11" r="1.5" fill="#14140F"/></pattern>
 <pattern id="fels" width="20" height="20" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="20" height="20" fill="#B8BBA8"/><line x1="0" y1="0" x2="0" y2="20" stroke="#14140F" stroke-width="2"/></pattern>
</defs>
<rect x="34" y="52" width="118" height="78" fill="#F2EEE3" stroke="#14140F" stroke-width="4"/>
<polygon points="24,56 93,10 162,56" fill="#29662F" stroke="#14140F" stroke-width="4"/>
<rect x="58" y="88" width="26" height="42" fill="#14140F"/>
<rect x="110" y="72" width="26" height="22" fill="#FBF9F4" stroke="#14140F" stroke-width="3"/>
<rect x="168" y="96" width="42" height="34" fill="#F0B23E" stroke="#14140F" stroke-width="4"/>
<text class="svg-text" x="172" y="88">WP</text>
<rect x="2" y="130" width="328" height="14" fill="#29662F" stroke="#14140F" stroke-width="4"/>
<rect x="2" y="144" width="328" height="26" fill="#C98B4A" stroke="#14140F" stroke-width="4"/>
<rect x="2" y="170" width="328" height="92" fill="url(#kies)" stroke="#14140F" stroke-width="4"/>
<rect x="2" y="262" width="328" height="436" fill="url(#fels)" stroke="#14140F" stroke-width="4"/>
<g class="svg-text">
 <rect x="14" y="196" width="112" height="26" fill="#FBF9F4" stroke="#14140F" stroke-width="2.5"/><text x="23" y="214">Kies, Sand</text>
 <rect x="14" y="300" width="58" height="26" fill="#FBF9F4" stroke="#14140F" stroke-width="2.5"/><text x="23" y="318">Fels</text>
</g>
<path d="M189 130 V 112 H 248 V 130" fill="none" stroke="#14140F" stroke-width="5"/>
<rect x="238" y="130" width="20" height="0" id="sonde" fill="#F0B23E" stroke="#14140F" stroke-width="4"/>
<g id="bohrkopf"><polygon points="235,130 261,130 248,150" fill="#14140F"/></g>
<line x1="330" y1="130" x2="330" y2="700" stroke="#14140F" stroke-width="3"/>
<rect id="parzelle" x="4" y="124" width="324" height="26" fill="none" stroke="#F0B23E" stroke-width="6" stroke-dasharray="14 8" opacity="0"/>
<g id="stempel" opacity="0" transform="rotate(-4 286 60)"><rect x="222" y="40" width="128" height="40" fill="#F0B23E" stroke="#14140F" stroke-width="4"/><text class="svg-text" x="234" y="66" style="font-size:17px;font-weight:500">BEWILLIGT</text></g>
<g class="svg-text">{ticks}</g>
</svg>"""


def seite_start():
    s = {"slug": "", "p": "", "spur": [],
         "title": "Erdsondenbohrung Zürich | Eco Green, Regensdorf",
         "og": "Eco Green: Wir bohren nach Wärme.",
         "desc": "Erdwärmesonden für Häuser im Kanton Zürich. Bohrfirma mit FWS-Gütesiegel aus Regensdorf, von der Abklärung bis zur befüllten Sonde. Jetzt Grundstück prüfen.",
         "preload": preload("kran", "(max-width: 1320px) 100vw, 1240px")}
    s["schema"] = [{"@type": "WebSite", "@id": BASIS + "#website", "url": BASIS, "name": "Eco Green", "inLanguage": "de-CH", "publisher": {"@id": ORG_ID}},
                   faq_schema(FAQ)]
    p = ""
    schritte = "".join(
        f'<li class="schritt"><div class="nr"><span>{i + 1:02d}</span><span class="mono">{dauer}</span></div><h3>{t}</h3><p>{x}</p></li>'
        for i, (t, dauer, x) in enumerate(SCHRITTE))
    streifen = "".join(foto(p, k, a, c, sizes="(max-width: 640px) 78vw, 360px") for k, a, c in [
        ("garten", "Türkises Raupenbohrgerät im Garten eines Einfamilienhauses", "Bohrung im Garten eines Einfamilienhauses."),
        ("verteiler", "Zwei Sondenrohre mit Manometern während der Druckprobe", "Druckprobe an zwei Sonden."),
        ("rot-logo", "Antriebseinheit des roten Bohrgeräts mit Eco-Green-Beschriftung", "Das rote Gerät auf einer Neubaustelle."),
        ("feld", "Bohrgerät und Bagger am Siedlungsrand im Winter", "Bohrung am Siedlungsrand."),
        ("mast", "Bohrmast von unten gegen den Himmel", "Der Bohrmast, von unten."),
        ("rot-grube", "Raupenbohrgerät neben der Baugrube eines Neubaus", "Neubau, Bohrung vor dem Aushub."),
    ])
    body = f"""<section class="hero raster" aria-labelledby="h1">
 <div class="wrap">
  <div class="hero-kopf">
   <h1 id="h1">Wir bohren nach Wärme.</h1>
   <div class="hero-text">
    <p class="lead">Eco Green bohrt Erdwärmesonden für Häuser im Kanton Zürich. Mit eigenen Geräten, bis die Leitung in Ihrem Heizraum ankommt.</p>
    <div class="knopfreihe"><a class="knopf" href="kontakt">Grundstück prüfen lassen <span class="pfeil">→</span></a><a class="knopf hell" href="{TEL_LINK}">{TEL}</a></div>
   </div>
  </div>
  {foto(p, "kran", "Ein Kran hebt ein Raupenbohrgerät über ein Wohnhaus im Schnee", "Zu eng für die Zufahrt. Das Bohrgerät kommt mit dem Kran über das Haus.", cls="hero-band", lazy=False, prio=True, sizes="(max-width: 1320px) 100vw, 1240px")}
 </div>
</section>
<section class="fakten" aria-label="Eco Green auf einen Blick">
 <div class="wrap"><div class="fakten-in">
  <a class="fakt fakt-siegel" href="{FWS_PDF}" rel="noopener"><span class="label">FWS-Gütesiegel</span><b>1 von 45</b><p>Bohrfirmen in der Schweiz mit dem Gütesiegel für Erdwärmesonden. Eco Green steht seit 2021 auf der Liste.</p></a>
  <div class="fakt"><span class="label">Standort</span><b>Regensdorf ZH</b><p>Pumpwerkstrasse 40, im Furttal. Einsatz im {EINSATZ}.</p></div>
  <a class="fakt" href="{TEL_LINK}"><span class="label">Telefon</span><b>{TEL}</b><p>{BUEROZEIT}.</p></a>
 </div></div>
</section>
<section class="sektion" id="schnitt" aria-labelledby="schnitt-h">
 <div class="wrap">
  <div class="kopfzeile"><h2 id="schnitt-h">Was unter Ihrem Rasen passiert.</h2><p class="lead" style="max-width:28em">Ab etwa 15 Metern ist der Boden das ganze Jahr rund 10 Grad warm. Pro 100 Meter kommen etwa 3 Grad dazu. Diese Wärme holt die Sonde ins Haus.</p></div>
  <div class="schnitt-grid">
   <div class="buehne">
    <div class="anzeige"><div><span class="label">Tiefe</span><output data-tiefe>000 m</output></div><div><span class="label">Boden</span><output data-temp>10,0 °C</output></div></div>
    {schnitt_svg()}
    <p class="klein">Schema. Schichten und Tiefe sind an jedem Ort anders.</p>
   </div>
   <div>
    <div class="tiefenleiste" aria-hidden="true"><span data-tiefe>000 m</span><span class="balken"><i></i></span><span data-temp>10,0 °C</span></div>
    <ol class="schritte">{schritte}</ol>
    <div class="knopfreihe" style="margin-top:40px"><a class="knopf hell" href="ablauf">Ablauf im Detail <span class="pfeil">→</span></a><a class="knopf hell" href="leistungen">Alle Leistungen <span class="pfeil">→</span></a></div>
   </div>
  </div>
 </div>
</section>
<section class="sektion ocker-flaeche" aria-labelledby="foerder-h">
 <div class="wrap foerder-grid">
  <p class="riesig auf"><small>Förderbeitrag ab</small>CHF 6'800</p>
  <div>
   <h2 id="foerder-h">Das Fördergesuch kommt vor der Bohrung.</h2>
   <p class="lead" style="margin-top:24px">So viel zahlt der Kanton Zürich an eine Erdwärmepumpe bis 15 kW, die eine Öl-, Gas- oder Elektroheizung ersetzt. Darüber kommen CHF 420 pro kW dazu. Als Baubeginn gilt die Bohrung. Wer vorher bohrt, verliert den Beitrag.</p>
   <p>Im Gesuch verlangt der Kanton eine Bohrfirma mit gültigem Gütesiegel. Eco Green hat es.</p>
   <div class="knopfreihe"><a class="knopf weiss" href="foerderung">Förderbeitrag berechnen <span class="pfeil">→</span></a></div>
   <p class="quelle">Quelle: Kanton Zürich, <a href="{ZH_FOERDER_PDF}" rel="noopener">Förderprogramm Heizung ersetzen</a>, Sole-Wasser-Wärmepumpe. Das Programm läuft <a href="{ZH_2026}" rel="noopener">2026 unverändert</a> weiter.</p>
  </div>
 </div>
</section>
<section class="sektion dunkel" aria-labelledby="bau-h">
 <div class="wrap bau-grid">
  {foto(p, "bohrmeister", "Bohrmeister im grünen Eco-Green-Shirt am Bohrgerät, daneben Bohrgestänge", "Bohrmeister am Gerät.", cls="auf")}
  <div>
   <h2 id="bau-h">Bohren ist laut. Das sagen wir vorher.</h2>
   <p class="lead" style="margin-top:24px">Bohrgerät und Kompressor hört man in der Nachbarschaft. Darum arbeiten wir zu festen Zeiten und reden mit Ihren Nachbarn, bevor das Gerät kommt.</p>
   <dl class="regeln">
    <div><dt>Arbeitszeit</dt><dd>Montag bis Freitag, 07.00 bis 12.00 und 13.00 bis 18.00 Uhr.</dd></div>
    <div><dt>Wochenende</dt><dd>Am Wochenende und an Feiertagen bohren wir nicht.</dd></div>
    <div><dt>Nachbarn</dt><dd>Brief mit Datum und Dauer eine Woche vor Bohrbeginn.</dd></div>
    <div><dt>Bohrschlamm</dt><dd>In Mulden aufgefangen und fachgerecht entsorgt. Rasen und Zufahrt schützen wir mit Platten.</dd></div>
    <div><dt>Ansprechperson</dt><dd>Eine Person für die ganze Baustelle, mit direkter Handynummer.</dd></div>
   </dl>
  </div>
 </div>
</section>
<section class="sektion raster" aria-labelledby="bilder-h">
 <div class="wrap">
  <div class="kopfzeile"><h2 id="bilder-h">Baustellen</h2><a class="textlink" href="referenzen">Alle Bilder und Projektbeispiele</a></div>
  <div class="streifen" tabindex="0" aria-label="Fotos von Baustellen, seitlich scrollbar">{streifen}</div>
 </div>
</section>
<section class="sektion papier" aria-labelledby="faq-h">
 <div class="wrap faq-grid">
  <div><h2 id="faq-h">Was Haus&shy;besitzer zuerst fragen.</h2><p style="margin-top:24px">Ihre Frage fehlt? Rufen Sie an: <a href="{TEL_LINK}">{TEL}</a>.</p></div>
  <div class="faq">{faq_html(FAQ)}</div>
 </div>
</section>
{schluss(p)}"""
    return s, body


def seite_leistungen():
    s = {"slug": "leistungen", "p": "", "ogbild": "og-leistungen", "spur": [("leistungen", "Leistungen")],
         "title": "Erdwärmesonde bohren: Leistungen | Eco Green Regensdorf",
         "desc": "Sondenauslegung, Bewilligungsunterlagen, Erdsondenbohrung, Sondeneinbau, Druckprobe und Anbindung an die Wärmepumpe. Alles von einer Bohrfirma mit Gütesiegel."}
    p = s["p"]
    s["schema"] = [{"@type": "Service", "name": t, "description": x, "serviceType": "Erdwärmesonde", "provider": {"@id": ORG_ID},
                    "areaServed": {"@type": "AdministrativeArea", "name": "Kanton Zürich"}} for t, x, _b in LEISTUNGEN]
    for d in s["schema"]:
        d["name"] = d["name"].replace("&shy;", "")
    reihen = ""
    for i, (t, x, b) in enumerate(LEISTUNGEN):
        rechts = ""
        if b:
            alt = {"garten": "Raupenbohrgerät bohrt im Garten eines Einfamilienhauses", "verteiler": "Sondenverteiler mit zwei Manometern"}[b]
            rechts = foto(p, b, alt, sizes="(max-width: 900px) 100vw, 36vw")
        reihen += f'<article class="leistung auf{" mit-bild" if b else ""}"><span class="gross-nr">{i + 1:02d}</span><div><h2>{t}</h2><p class="lead">{x}</p></div>{f"<div>{rechts}</div>" if rechts else ""}</article>'
    body = seitenkopf(s, "Alles bis zur Hauswand.", "Eco Green bohrt Erdwärmesonden und schliesst sie an. Sie haben eine Ansprechperson vom ersten Anruf bis zum Bohrprotokoll.") + f"""
<section class="sektion"><div class="wrap">{reihen}</div></section>
<section class="sektion gruen-flaeche" aria-labelledby="inst-h">
 <div class="wrap zwei">
  <div><h2 id="inst-h">Für Installateure und Planer.</h2></div>
  <div>
   <p class="lead">Sie planen die Wärmepumpe, wir liefern die Sonde. Für Anlagen bis 15 kW verlangt der Kanton das Wärmepumpen-System-Modul, für die Förderung eine Bohrfirma mit Gütesiegel. Sondenlänge, Druckprotokoll und Bohrprotokoll erhalten Sie so, wie Ihr Dossier sie braucht.</p>
   <p>Sie erhalten einen festen Bohrtermin und eine Ansprechperson, die auch Ihren Bauleiter kennt.</p>
   <div class="knopfreihe"><a class="knopf weiss" href="mailto:{MAIL}?subject={quote('Anfrage Installateur: Erdsonde')}">Projekt anfragen <span class="pfeil">→</span></a></div>
  </div>
 </div>
</section>
<section class="sektion papier" aria-labelledby="nicht-h">
 <div class="wrap zwei">
  <h2 id="nicht-h">Was nicht zu uns gehört.</h2>
  <div class="textspalte">
   <p class="lead">Die Wärmepumpe selbst liefert und montiert Ihr Heizungsinstallateur. Wir arbeiten mit ihm zusammen und übergeben ihm die befüllte Sonde.</p>
   <p>Haben Sie noch keinen Installateur, nennen wir Ihnen Betriebe aus der Region, mit denen wir schon gebaut haben.</p>
  </div>
 </div>
</section>
{schluss(p, "Wie viele Meter braucht Ihr Haus?", "Schicken Sie uns Adresse und heutigen Verbrauch. Sie erhalten eine erste Einschätzung zu Anzahl und Länge der Sonden.")}"""
    return s, body


def seite_ablauf():
    s = {"slug": "ablauf", "p": "", "ogbild": "og-ablauf", "preload": preload("feld2", "(max-width: 900px) 100vw, 40vw"), "spur": [("ablauf", "Ablauf")],
         "title": "Erdsonde Bewilligung Zürich: Ablauf | Eco Green",
         "desc": "Von der Abklärung im Wärmenutzungsatlas bis zur Übergabe: so läuft eine Erdsondenbohrung im Kanton Zürich ab. Mit Bewilligung, Förderung und Baustellenregeln."}
    p = s["p"]
    sie = [
        "Sie schicken uns die fünf Angaben aus der E-Mail-Vorlage. Fotos vom Heizraum helfen.",
        "Sie unterschreiben das Bewilligungsgesuch und reichen es bei der Gemeinde ein. Das Fördergesuch reichen Sie auf der Gesuchplattform des Kantons ein, vor der Bohrung.",
        "Sie sorgen für Strom und Wasser auf dem Grundstück und eine freie Zufahrt.",
        "Nichts. Sie können zuschauen.",
        "Sie stimmen den Anschlusstermin mit Ihrem Heizungsinstallateur ab.",
        "Sie reichen Bohrprotokoll und Rechnung zusammen mit den Unterlagen der Wärmepumpe beim Kanton ein.",
    ]
    wir = [
        "Wir prüfen im Wärmenutzungsatlas, ob gebohrt werden darf, und schätzen Anzahl und Tiefe der Sonden. Danach kommt die Offerte.",
        "Wir stellen die Unterlagen für das Bewilligungsgesuch zusammen und liefern Ihnen alles, was der Kanton für das Fördergesuch von der Bohrfirma verlangt, auch den Nachweis des Gütesiegels.",
        "Wir informieren Ihre Nachbarn schriftlich, stellen das Gerät auf und schützen Rasen und Zufahrt.",
        "Wir bohren, bauen die Sonde ein und verfüllen das Bohrloch. Bohrschlamm und Bohrwasser fangen wir auf.",
        "Wir prüfen jede Sonde mit Druck, verlegen die Leitungen bis in den Heizraum und füllen das System.",
        "Wir übergeben Protokolle und Rechnung. Danach räumen wir die Baustelle.",
    ]
    phasen = "".join(
        f'<article class="phase auf"><div class="phase-kopf"><span class="gross-nr">{i + 1:02d}</span><h2 style="font-size:clamp(1.6rem,2.6vw,2.2rem)">{t}</h2><span class="mono">{dauer}</span></div>'
        f'<div class="phase-inhalt"><div><h3 class="label">Was Sie tun</h3><p>{sie[i]}</p></div><div><h3 class="label">Was wir tun</h3><p>{wir[i]}</p></div></div></article>'
        for i, (t, dauer, _x) in enumerate(SCHRITTE))
    body = seitenkopf(s, "", "", extra=f"""<div class="split">
  <div><h1>Sechs Schritte bis zur warmen Stube.</h1><p class="lead">Von der ersten Anfrage bis zur Übergabe vergehen meist zwei bis drei Monate. Die meiste Zeit braucht die Bewilligung. Die Bohrung selbst dauert wenige Tage.</p></div>
  {foto(p, "feld2", "Bohrgerät mit Bagger auf einer Wiese am Dorfrand", "Bohrung am Dorfrand im Winter.", lazy=False, prio=True, sizes="(max-width: 900px) 100vw, 40vw")}
 </div>""") + f"""
<section class="sektion"><div class="wrap">{phasen}</div></section>
<section class="sektion raster" aria-labelledby="bew-h">
 <div class="wrap zwei">
  <div class="kasten auf">
      <h2 id="bew-h" style="font-size:clamp(1.8rem,3vw,2.6rem)">Was der Kanton verlangt.</h2>
   <ul>
    <li>Jede Erdwärmesonde braucht eine gewässerschutzrechtliche Bewilligung des AWEL.</li>
    <li>Eingereicht wird bei der Baubehörde der Gemeinde, auch über eBaugesucheZH.</li>
    <li>Der Wärmenutzungsatlas zeigt für jede Parzelle, ob Sonden zulässig sind.</li>
    <li>Unter 2,5 Meter Abstand zur Grenze braucht es die Zustimmung des Nachbarn.</li>
    <li>Das AWEL empfiehlt eine Bohrfirma mit dem Gütesiegel für Erdwärmesonden-Bohrfirmen.</li>
   </ul>
   <p class="quelle">Quelle: <a href="{ZH_SONDEN}" rel="noopener">Kanton Zürich, Erdwärmesonden</a></p>
  </div>
  <div class="kasten kasten-ocker auf">
      <h2 style="font-size:clamp(1.8rem,3vw,2.6rem)">Unsere Regeln vor Ort.</h2>
   <ul>
    <li>Gebohrt wird Montag bis Freitag, 07.00 bis 12.00 und 13.00 bis 18.00 Uhr.</li>
    <li>An Wochenenden und Feiertagen bleibt das Gerät still.</li>
    <li>Ihre Nachbarn erhalten eine Woche vor Bohrbeginn einen Brief mit Datum und Dauer.</li>
    <li>Bohrschlamm und Bohrwasser fangen wir in Mulden auf. Nichts läuft in die Kanalisation.</li>
    <li>Sie haben eine Ansprechperson mit direkter Handynummer.</li>
   </ul>
  </div>
 </div>
</section>
{schluss(p)}"""
    return s, body


FOERDER_FAQ = [
    ("Was zahlt der Kanton Zürich an eine Erdwärmepumpe?",
     "<p>Bis 15 kW Heizleistung CHF 6'800, darüber CHF 420 pro zusätzliches kW. Bedingung ist, dass die Anlage eine Öl-, Gas- oder Elektroheizung in einem bestehenden Gebäude ersetzt. Das Gesuch muss vor der Bohrung eingereicht sein.</p>"),
    ("Wann muss ich das Fördergesuch einreichen?",
     "<p>Vor der Bohrung. Der Kanton zählt die Bohrung der Erdwärmesonde als Baubeginn. Sobald die automatische Eingangsbestätigung da ist, darf gebohrt werden. Die verbindliche Zusage folgt innert vier Wochen nach Eingang der vollständigen Unterlagen.</p>"),
    ("Bekomme ich auch beim Neubau einen Beitrag?",
     "<p>Vom Kanton nicht. Gefördert wird der Ersatz einer Öl-, Gas- oder Elektroheizung in einem bestehenden Gebäude. Manche Gemeinden haben eigene Programme, fragen Sie dort nach.</p>"),
    ("Wie viel Zeit habe ich nach der Zusage?",
     "<p>Zwei Jahre ab Datum der Zusicherung, um die Anlage zu bauen und den Abschluss einzureichen. Das Geld kommt 30 Tage nach dem Auszahlungsschreiben.</p>"),
    ("Gibt es mehr Geld ohne Frostschutzmittel?",
     "<p>Ja. Für Sonden ohne Frostschutzmittel oder mit vollständiger, fossilfreier Regeneration zahlt der Kanton zusätzlich CHF 3'000 plus CHF 100 pro kW über 15 kW. Ob das bei Ihrem Haus sinnvoll ist, hängt von Sondenlänge und Wärmebedarf ab. Wir rechnen beide Varianten.</p>"),
]

def seite_foerderung():
    s = {"slug": "foerderung", "p": "", "ogbild": "og-foerderung", "spur": [("foerderung", "Förderung")],
         "title": "Förderung Erdwärmepumpe Kanton Zürich | Eco Green",
         "desc": "Der Kanton Zürich zahlt ab CHF 6'800 an eine Erdwärmepumpe, die Öl, Gas oder Strom ersetzt. Bedingungen, Unterlagen, Rechner. Gesuch vor der Bohrung einreichen."}
    p = s["p"]
    s["schema"] = [faq_schema(FOERDER_FAQ)]
    body = seitenkopf(s, "CHF 6'800 vom Kanton Zürich.", "Der Kanton Zürich fördert den Ersatz von Öl-, Gas- und Elektroheizungen durch eine Erdwärmepumpe. Das Gesuch muss eingereicht sein, bevor wir bohren.") + f"""
<section class="sektion" aria-labelledby="rechner-h">
 <div class="wrap">
  <div class="kopfzeile"><h2 id="rechner-h">Was der Kanton an Ihre Anlage zahlt.</h2></div>
  <div class="rechner auf" id="rechner">
   <div class="rechner-ein">
    <label for="kw">Heizleistung der Wärmepumpe</label>
    <div class="feld"><input id="kw" type="number" inputmode="decimal" min="1" max="400" step="0.5" value="12"><span>kW</span></div>
    <label class="wahl" for="zusatz"><input id="zusatz" type="checkbox"><span>Sonde ohne Frostschutzmittel oder mit vollständiger Regeneration</span></label>
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
    <p class="klein" style="color:var(--tinte);margin-top:16px">Der Beitrag ist auf 50 Prozent der Investition und auf 50 Watt pro m² Energiebezugsfläche begrenzt. Massgebend ist die Zusicherung des Kantons.</p>
   </div>
  </div>
  <p class="quelle">Sätze: Kanton Zürich, <a href="{ZH_FOERDER_PDF}" rel="noopener">Förderprogramm Heizung ersetzen</a>, Sole-Wasser-Wärmepumpe. <a href="{ZH_2026}" rel="noopener">Programm 2026 unverändert.</a></p>
 </div>
</section>
<section class="sektion papier" aria-labelledby="bed-h">
 <div class="wrap zwei">
  <div class="kasten auf">
   <h2 id="bed-h" style="font-size:clamp(1.8rem,3vw,2.6rem)">Bedingungen.</h2>
   <ul>
    <li>Die Anlage ersetzt eine Öl-, Gas- oder Elektroheizung.</li>
    <li>Das Gebäude besteht schon. Neubauten fördert der Kanton nicht.</li>
    <li>Die Wärmepumpe ist die Hauptheizung und liefert mindestens 50 Prozent der Wärme.</li>
    <li>Bis 15 kW: Anlagezertifikat Wärmepumpen-System-Modul (WPSM).</li>
    <li>Die Bohrfirma hat ein gültiges Gütesiegel.</li>
    <li>Das Gesuch ist vor der Bohrung eingereicht.</li>
   </ul>
  </div>
  <div class="kasten auf">
   <h2 style="font-size:clamp(1.8rem,3vw,2.6rem)">Unterlagen.</h2>
   <h3 class="label" style="margin:18px 0 8px">Vor der Bohrung</h3>
   <ul>
    <li>Offerte für den Heizungsersatz</li>
    <li>Foto der alten Heizung und des Typenschilds</li>
    <li>Pläne mit der Energiebezugsfläche</li>
    <li>Bestätigung WPSM und Gütesiegel der Bohrfirma</li>
   </ul>
   <h3 class="label" style="margin:18px 0 8px">Nach dem Bau</h3>
   <ul>
    <li>Anlagezertifikat WPSM</li>
    <li>Rechnungen für Heizung und Bohrung</li>
    <li>Bohrprotokoll</li>
   </ul>
   <p class="klein">Rechnung und Bohrprotokoll für die Bohrung liefern wir.</p>
  </div>
 </div>
</section>
<section class="sektion dunkel" aria-labelledby="gesetz-h">
 <div class="wrap zwei">
  <h2 id="gesetz-h">Heizungsersatz im Kanton Zürich.</h2>
  <div>
   <p class="lead">Im Kanton Zürich darf eine Öl- oder Gasheizung in einem bestehenden Haus seit 01.09.2022 grundsätzlich nur noch durch ein erneuerbares System ersetzt werden.</p>
   <p>Eine Ausnahme gilt, wenn die erneuerbare Lösung über die ganze Lebensdauer mehr als 5 Prozent teurer ist. Im ersten Jahr wurden über 98 Prozent der ersetzten fossilen Heizungen durch klimaneutrale Systeme ersetzt.</p>
   <p class="quelle">Quelle: <a href="{ZH_ENERGIE}" rel="noopener" style="color:inherit">Kanton Zürich, Bauvorschriften Gebäude und Energie</a></p>
  </div>
 </div>
</section>
<section class="sektion" aria-labelledby="ffaq-h">
 <div class="wrap faq-grid">
  <h2 id="ffaq-h">Fragen zur Förderung.</h2>
  <div class="faq">{faq_html(FOERDER_FAQ)}</div>
 </div>
</section>
{schluss(p, "Unterlagen für Ihr Fördergesuch.", "Sie erhalten von uns die Offerte für die Bohrung und den Nachweis unseres Gütesiegels. Damit ist Ihr Gesuch vollständig, bevor das Gerät kommt.", "ocker-flaeche")}"""
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
    s = {"slug": "referenzen", "p": "", "ogbild": "og-referenzen", "preload": preload("garten", "(max-width: 640px) 50vw, (max-width: 1020px) 33vw, 25vw"), "spur": [("referenzen", "Baustellen")],
         "title": "Erdsondenbohrung Referenzen | Eco Green Baustellen",
         "desc": "Baustellen von Eco Green: Erdsondenbohrungen für Einfamilienhäuser, Mehrfamilienhäuser und Neubauten im Kanton Zürich. Mit Kran, wenn die Zufahrt zu eng ist."}
    p = s["p"]
    zeilen = "".join(f"<tr><td data-label=\"Objekt\">{o}</td><td data-label=\"Region\">{ort}</td><td data-label=\"Ersetzt\">{alt}</td><td data-label=\"Sonden\" class=\"zahl\">{sonden}</td><td data-label=\"Besonderheit\">{notiz}</td></tr>"
                     for o, ort, alt, sonden, notiz in PROJEKTE)
    gal = "".join(foto(p, k, a, c, sizes="(max-width: 640px) 50vw, (max-width: 1020px) 33vw, 25vw", cls="auf", lazy=i > 3, prio=i == 0) for i, (k, a, c) in enumerate([
        ("garten", "Türkises Raupenbohrgerät im Garten eines Einfamilienhauses", "Garten eines Einfamilienhauses."),
        ("dorf", "Bohrgerät zwischen Bauernhaus und Wohnhaus", "Zwischen Bauernhaus und Wohnhaus."),
        ("feld", "Bohrgerät und Bagger am Siedlungsrand im Winter", "Siedlungsrand im Winter."),
        ("rot-grube", "Rotes Raupenbohrgerät neben einer Baugrube", "Neubau, vor dem Aushub."),
        ("herbst", "Bohrgerät neben einer Baugrube im Herbst", "Baugrube im Herbst."),
        ("mast", "Bohrmast von unten", "Der Bohrmast."),
        ("raupe", "Fuss des Bohrmasts im Bohrschlamm", "Bohrschlamm am Mastfuss."),
        ("rot-nah", "Hydraulik am roten Bohrgerät", "Hydraulik am roten Gerät."),
    ]))
    body = seitenkopf(s, "Unsere Baustellen.", "Alle Bilder auf dieser Website stammen von Baustellen von Eco Green. So sehen Erdsondenbohrungen im Kanton Zürich aus.") + f"""
<section class="sektion" aria-labelledby="gal-h">
 <div class="wrap">
  <div class="kopfzeile"><h2 id="gal-h">Geräte und Baustellen.</h2><p style="max-width:30em">Raupenbohrgeräte, die durch ein Gartentor passen. Und wenn nicht, über das Dach.</p></div>
  <div class="galerie">{gal}</div>
 </div>
</section>
<section class="sektion papier" aria-labelledby="proj-h">
 <div class="wrap">
  <div class="kopfzeile"><h2 id="proj-h">Typische Aufträge.</h2><p style="max-width:30em">Sondenzahl und Tiefe richten sich nach dem Haus. Diese Beispiele zeigen die Spannweite.</p></div>
  <div class="tabelle-rahmen auf"><table class="tabelle">
   <thead><tr><th scope="col">Objekt</th><th scope="col">Region</th><th scope="col">Ersetzt</th><th scope="col">Sonden</th><th scope="col">Besonderheit</th></tr></thead>
   <tbody>{zeilen}</tbody>
  </table></div>
 </div>
</section>
{schluss(p, "Ihr Haus als nächste Baustelle?")}"""
    return s, body


def seite_ueber():
    s = {"slug": "ueber-uns", "p": "", "ogbild": "og-ueber-uns", "preload": preload("bohrmeister", "(max-width: 900px) 100vw, 40vw"), "spur": [("ueber-uns", "Über uns")],
         "title": "Bohrfirma mit FWS-Gütesiegel in Regensdorf | Eco Green",
         "desc": "Eco Green GmbH ist eine Bohrfirma für Erdwärmesonden an der Pumpwerkstrasse 40 in Regensdorf. Mit FWS-Gütesiegel seit 2021 und eigenen Raupenbohrgeräten."}
    p = s["p"]
    body = seitenkopf(s, "", "", extra=f"""<div class="split">
  <div><h1>Bohrfirma aus dem Furttal.</h1><p class="lead">Eco Green GmbH bohrt Erdwärmesonden für Einfamilienhäuser, Mehrfamilienhäuser und Neubauten. Von Regensdorf aus fahren wir mit eigenen Geräten zu Baustellen im ganzen Kanton.</p></div>
  {foto(p, "bohrmeister", "Bohrmeister im grünen Eco-Green-Shirt am Bohrgerät", "Bohrmeister von Eco Green.", lazy=False, prio=True)}
 </div>""") + f"""
<section class="sektion" aria-labelledby="daten-h">
 <div class="wrap zwei">
  <h2 id="daten-h">Die Firma in Fakten.</h2>
  <dl class="daten">
   <div><dt>Firma</dt><dd>Eco Green GmbH</dd></div>
   <div><dt>Sitz</dt><dd>Pumpwerkstrasse 40, 8105 Regensdorf, seit 2020</dd></div>
   <div><dt>Handelsregister</dt><dd>Kanton Zürich, CHE-141.654.180</dd></div>
   <div><dt>Tätigkeit</dt><dd>Planung und Ausführung von Erdsondenbohrungen</dd></div>
   <div><dt>Gütesiegel</dt><dd>FWS-Gütesiegel für Erdwärmesonden-Bohrfirmen, auf der Liste seit Juni 2021, aktuell Stand Juli 2026</dd></div>
   <div><dt>Geräte</dt><dd>Eigene Raupenbohrgeräte, Transport bei Bedarf mit Kran</dd></div>
   <div><dt>Einsatzgebiet</dt><dd>{EINSATZ}</dd></div>
  </dl>
 </div>
</section>
<section class="sektion ocker-flaeche" aria-labelledby="siegel-h">
 <div class="wrap zwei">
  <div><h2 id="siegel-h">Eine von 45 Bohrfirmen mit Gütesiegel.</h2></div>
  <div>
   <p class="lead">45 Bohrfirmen in der Schweiz tragen das Gütesiegel der Fachvereinigung Wärmepumpen Schweiz. Eco Green ist seit 2021 dabei.</p>
   <p>Wer es trägt, verpflichtet sich auf Beratung der Bauherrschaft, umweltschonende Ausführung, Bohrungen nach dem Stand der Technik, hochwertiges Sondenmaterial und Sicherheit auf der Baustelle. Das AWEL empfiehlt Firmen mit diesem Siegel, und der Kanton verlangt es für den Förderbeitrag.</p>
   <div class="knopfreihe"><a class="knopf weiss" href="{FWS_PDF}" rel="noopener">Gütesiegelliste ansehen <span class="pfeil">↗</span></a></div>
  </div>
 </div>
</section>
<section class="sektion papier" aria-labelledby="leute-h">
 <div class="wrap zwei">
  <h2 id="leute-h">Geschäftsführung.</h2>
  <dl class="daten">
   <div><dt>Etiènne Spruijt</dt><dd>Inhaber und Vorsitzender der Geschäftsführung. Bohrungen und Geräte.</dd></div>
   <div><dt>Mahissa Ganz-Yasri</dt><dd>Geschäftsführerin. Offerten und Termine.</dd></div>
   <div><dt>Bohrteam</dt><dd>Eigenes Bohrpersonal auf jeder Baustelle.</dd></div>
  </dl>
 </div>
</section>
<section class="sektion raster" aria-labelledby="ort-h">
 <div class="wrap zwei">
  <div><h2 id="ort-h">Pumpwerk&shy;strasse 40, Regensdorf.</h2><p class="lead" style="margin-top:24px">Von hier sind Furttal, Zürcher Unterland und Limmattal schnell erreicht. Die Stadt Zürich auch.</p></div>
  <div class="kasten"><p class="label">Adresse</p><address style="font-style:normal;font-size:1.25rem;font-weight:650;margin:10px 0 20px">Eco Green GmbH<br>Pumpwerkstrasse 40<br>8105 Regensdorf</address><a class="textlink" href="{KARTE}" rel="noopener">Auf der Karte zeigen</a></div>
 </div>
</section>
{schluss(p)}"""
    return s, body


def seite_kontakt():
    s = {"slug": "kontakt", "p": "", "ogbild": "og-kontakt", "spur": [("kontakt", "Kontakt")],
         "title": "Erdsonde Offerte anfragen | Kontakt Eco Green Regensdorf",
         "desc": "Erstabklärung für Ihre Erdwärmesonde: rufen Sie an unter 044 400 20 20 oder schreiben Sie an info@eco-green.ch. Eco Green GmbH, Pumpwerkstrasse 40, Regensdorf."}
    p = s["p"]
    s["schema"] = [{"@type": "ContactPage", "url": BASIS + "kontakt", "about": {"@id": ORG_ID}}]
    body = seitenkopf(s, "Erstabklärung für Ihr Grundstück.", "Für die Erstabklärung brauchen wir fünf Angaben. Das Gespräch dauert zehn Minuten, die Einschätzung ist kostenlos.") + f"""
<section class="sektion" aria-label="Telefon und E-Mail">
 <div class="wrap">
  <div class="kontakt-gross auf">
   <a href="{TEL_LINK}"><span class="label">Telefon</span><b>{TEL}</b><span class="klein" style="display:block;margin-top:14px">{BUEROZEIT}</span></a>
   <a href="{MAILTO}"><span class="label">E-Mail mit Vorlage</span><b>{MAIL}</b><span class="klein" style="display:block;margin-top:14px">Antwort innert zwei Arbeitstagen</span></a>
  </div>
 </div>
</section>
<section class="sektion papier" aria-labelledby="brauchen-h">
 <div class="wrap zwei">
  <div><h2 id="brauchen-h">Das brauchen wir von Ihnen.</h2><p class="lead" style="margin-top:24px">Die E-Mail-Vorlage fragt genau das ab. Öffnet sich bei Ihnen kein Mailprogramm, kopieren Sie die Vorlage und schicken Sie sie an {MAIL}.</p><div class="knopfreihe"><button class="knopf hell kopieren" type="button" data-text="{esc(MAIL_TEXT)}">Vorlage kopieren</button></div><p class="klein kopiert" role="status"></p></div>
  <ol class="checkliste">
   <li><span><b>Adresse des Grundstücks.</b> Damit prüfen wir im Wärmenutzungsatlas, ob gebohrt werden darf.</span></li>
   <li><span><b>Heutige Heizung.</b> Öl, Gas oder Elektro, mit dem Baujahr der Heizung. Davon hängt der Förderbeitrag ab.</span></li>
   <li><span><b>Verbrauch pro Jahr.</b> Liter Öl, Kubikmeter Gas oder Kilowattstunden. Daraus rechnen wir die Sondenlänge.</span></li>
   <li><span><b>Baujahr und Wohnfläche des Hauses.</b> Eine grobe Angabe reicht.</span></li>
   <li><span><b>Telefonnummer.</b> Für den Rückruf und den Termin vor Ort.</span></li>
  </ol>
 </div>
</section>
<section class="sektion gruen-flaeche" aria-labelledby="adr-h">
 <div class="wrap zwei">
  <div><h2 id="adr-h">Büro in Regensdorf.</h2></div>
  <div>
   <address class="lead" style="font-style:normal">Eco Green GmbH<br>Pumpwerkstrasse 40<br>8105 Regensdorf</address>
   <p style="margin-top:20px">{BUEROZEIT}</p>
   <div class="knopfreihe"><a class="knopf" href="{KARTE}" rel="noopener">Route planen <span class="pfeil">↗</span></a></div>
  </div>
 </div>
</section>"""
    return s, body


def seite_impressum():
    s = {"slug": "impressum", "p": "", "spur": [("impressum", "Impressum")],
         "title": "Impressum | Eco Green GmbH, Erdwärmesonden Regensdorf",
         "desc": "Impressum der Website von Eco Green GmbH, Bohrfirma für Erdwärmesonden, Pumpwerkstrasse 40, 8105 Regensdorf. Handelsregister Kanton Zürich, CHE-141.654.180."}
    body = seitenkopf(s, "Impressum", "Angaben zur Betreiberin dieser Website.") + f"""
<section class="sektion"><div class="wrap recht">
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
</div></section>"""
    return s, body


def seite_datenschutz():
    s = {"slug": "datenschutz", "p": "", "spur": [("datenschutz", "Datenschutz")],
         "title": "Datenschutzerklärung | Eco Green GmbH, Regensdorf",
         "desc": "Datenschutzerklärung von Eco Green GmbH nach dem Schweizer Datenschutzgesetz (DSG). Keine Cookies, kein Tracking, Schriften lokal. Was wir speichern und warum."}
    body = seitenkopf(s, "Datenschutz", "Wie Eco Green mit Personendaten umgeht. Nach dem Bundesgesetz über den Datenschutz (DSG). Stand 21.10.2026.") + f"""
<section class="sektion"><div class="wrap recht">
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
</div></section>"""
    return s, body


def seite_404():
    s = {"slug": "404.html", "p": PFAD, "spur": [("404.html", "Nicht gefunden")],
         "title": "Seite nicht gefunden | Eco Green Erdwärmesonden",
         "desc": "Diese Seite gibt es nicht. Zurück zur Startseite von Eco Green, Bohrfirma für Erdwärmesonden in Regensdorf, oder direkt zu Leistungen, Ablauf und Kontakt."}
    p = PFAD
    body = f"""<section class="seitenkopf raster"><div class="wrap seitenkopf-in">
 <p class="mono">Fehler 404</p>
 <h1 style="margin-top:16px">404 Meter tief. Nichts gefunden.</h1>
 <p class="lead">Diese Seite gibt es nicht oder nicht mehr. Hier geht es weiter:</p>
 <div class="knopfreihe"><a class="knopf" href="{p}">Zur Startseite <span class="pfeil">→</span></a><a class="knopf hell" href="{p}kontakt">Kontakt</a><a class="knopf hell" href="{p}foerderung">Förderung</a></div>
</div></section>"""
    return s, body


SEITEN = [seite_start, seite_leistungen, seite_ablauf, seite_foerderung, seite_referenzen, seite_ueber,
          seite_kontakt, seite_impressum, seite_datenschutz, seite_404]

# ---------------------------------------------------------------- Nebendateien

def llms():
    return f"""# Eco Green GmbH

> Bohrfirma für Erdwärmesonden in Regensdorf, Kanton Zürich. Träger des FWS-Gütesiegels für Erdwärmesonden-Bohrfirmen (Liste Juni 2021 und Juli 2026). Sondenauslegung, Bewilligungsunterlagen, Erdsondenbohrung, Sondeneinbau, Druckprobe und Anbindung an die Wärmepumpe.

## Fakten
- Firma: Eco Green GmbH, UID CHE-141.654.180, Handelsregister Kanton Zürich
- Adresse: Pumpwerkstrasse 40, 8105 Regensdorf, Schweiz
- Telefon: {TEL}, E-Mail: {MAIL}
- Gütesiegel: FWS-Gütesiegel für Erdwärmesonden-Bohrfirmen, eine von 45 Firmen auf der Liste vom Juli 2026: {FWS_PDF}
- Einsatzgebiet: {EINSATZ}
- Förderung Kanton Zürich: Erdwärmepumpe bis 15 kW CHF 6'800, darüber CHF 420 pro zusätzliches kW. Zusatzbeitrag CHF 3'000 plus CHF 100 pro kW über 15 kW für Sonden ohne Frostschutzmittel oder mit vollständiger Regeneration. Gesuch vor der Bohrung, ersetzt Öl-, Gas- oder Elektroheizung in bestehendem Gebäude. Der Kanton verlangt eine Bohrfirma mit gültigem Gütesiegel.
- Bewilligung: gewässerschutzrechtliche Bewilligung des AWEL, eingereicht bei der Gemeinde. Unter 2,5 m Grenzabstand Zustimmung des Nachbarn.

## Seiten
- [Start]({BASIS}): Überblick, Ablauf in sechs Schritten, Förderung, Baustellenregeln, häufige Fragen
- [Leistungen]({BASIS}leistungen): Sondenauslegung bis Befüllung
- [Ablauf]({BASIS}ablauf): sechs Schritte, Bewilligung, Baustellenregeln
- [Förderung]({BASIS}foerderung): Beiträge, Bedingungen, Unterlagen, Rechner
- [Baustellen]({BASIS}referenzen): Projektbeispiele und Geräte
- [Über uns]({BASIS}ueber-uns): Firma, Gütesiegel, Personen
- [Kontakt]({BASIS}kontakt): Telefon, E-Mail, Angaben für die Erstabklärung
"""

def manifest():
    return json.dumps({"name": "Eco Green Erdwärmesonden", "short_name": "Eco Green", "lang": "de-CH",
                       "start_url": PFAD, "scope": PFAD, "display": "standalone",
                       "background_color": "#F2EEE3", "theme_color": "#29662F",
                       "icons": [{"src": PFAD + "img/icon-192.png", "sizes": "192x192", "type": "image/png"},
                                 {"src": PFAD + "img/icon-512.png", "sizes": "512x512", "type": "image/png"},
                                 {"src": PFAD + "img/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
                                 {"src": PFAD + "favicon.svg", "sizes": "any", "type": "image/svg+xml"}]},
                      ensure_ascii=False, indent=1)


def main():
    if OUT != HIER.parent / "docs":
        shutil.copytree(HIER.parent / "docs", OUT, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("*.html", "sitemap.xml", "robots.txt", "llms.txt", "site.webmanifest"))
    static = HIER / "static"
    for f in static.rglob("*"):
        if f.is_file():
            ziel = OUT / f.relative_to(static)
            ziel.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, ziel)
    urls = []
    for fn in SEITEN:
        s, body = fn()
        doc = head(s) + kopf(s) + body + fuss(s["p"])
        if s["slug"].endswith(".html"):
            ziel = OUT / s["slug"]
        else:
            ziel = OUT / ((s["slug"] or "index") + ".html")
            urls.append(s["slug"])
        ziel.parent.mkdir(parents=True, exist_ok=True)
        ziel.write_text(doc, encoding="utf-8")
        tl, dl = len(s["title"]), len(s["desc"])
        warn = "" if (45 <= tl <= 62 and 140 <= dl <= 165) else "  <-- Laenge pruefen"
        print(f"{s['slug'] or 'index'}: title {tl}, desc {dl}{warn}")
    prio = {"": "1.0", "kontakt": "0.8", "foerderung": "0.8", "leistungen": "0.8", "ablauf": "0.8"}
    sm = "".join(f"<url><loc>{BASIS}{u}</loc><lastmod>{STAND}</lastmod></url>" for u in urls)
    (OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>\n', encoding="utf-8")
    if VORSCHAU:
        robots = f"# Vorschau. Vor Livegang ersetzen durch: Allow: / und Sitemap-Zeile mit der echten Domain\nUser-agent: *\nDisallow: /\n\nSitemap: {BASIS}sitemap.xml\n"
    else:
        robots = f"User-agent: *\nAllow: /\n\nSitemap: {BASIS}sitemap.xml\n"
    (OUT / "robots.txt").write_text(robots, encoding="utf-8")
    (OUT / "llms.txt").write_text(llms(), encoding="utf-8")
    (OUT / "site.webmanifest").write_text(manifest(), encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")


if __name__ == "__main__":
    main()
