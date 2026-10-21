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
<meta name="theme-color" content="#FFFFFF" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#12301A" media="(prefers-color-scheme: dark)">
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
{pre}<link rel="stylesheet" href="{p}site.css?v=3">
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
    mnav = "".join(a(u, n).replace(f">{n}</a>", f"><span>{n}</span><span class=\"mono\">{i + 1:02d}</span></a>")
                   for i, (u, n) in enumerate([("", "Start")] + NAV))
    start = p if p else "./"
    return f"""<header class="kopf">
 <div class="wrap kopf-in">
  <a class="marke" href="{start}" aria-label="Eco Green, zur Startseite"><img src="{p}img/logo.svg" width="150" height="56" alt="Eco Green"></a>
  <nav class="nav" aria-label="Hauptnavigation">{nav}</nav>
  <a class="knopf" href="{p}kontakt">Offerte anfragen</a>
  <button class="menuknopf" type="button" aria-expanded="false" aria-controls="menue">Menü</button>
 </div>
</header>
<div class="menue" id="menue" aria-hidden="true" inert>
 <div class="menue-kopf"><img src="{p}img/logo-hell.svg" width="130" height="48" alt="Eco Green"><button class="menue-zu" type="button">Schliessen</button></div>
 <nav aria-label="Menü">{mnav}</nav>
 <div class="knopfreihe"><a class="knopf" href="{p}kontakt">Offerte anfragen</a><a class="knopf zwei" href="{TEL_LINK}">{TEL}</a></div>
</div>
<main id="inhalt">
"""

def schluss(p, titel="Prüfen wir Ihr Grundstück.", text=None):
    text = text or "Schicken Sie uns Adresse und heutige Heizung. Wir klären, ob gebohrt werden darf, und melden uns mit einer ersten Einschätzung zu Sonde, Ablauf und Förderbeitrag. Kostenlos."
    return f"""<section class="sektion marke-flaeche schluss" aria-labelledby="schluss-titel">
 <div class="wrap raster">
  <h2 id="schluss-titel">{titel}</h2>
  <div class="schluss-text">
   <p class="lead">{text}</p>
   <div class="knopfreihe"><a class="knopf" href="{p}kontakt">Offerte anfragen</a><a class="knopf zwei" href="{TEL_LINK}">{TEL} anrufen</a></div>
   <p class="klein" style="margin-top:16px">Telefon {BUEROZEIT}</p>
  </div>
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
    <a class="marke" href="{start}"><img src="{p}img/logo-hell.svg" width="160" height="60" alt="Eco Green, zur Startseite" loading="lazy"></a>
    <p>Erdsondenbohrungen für Wärmepumpen<br>im Kanton Zürich.</p>
    <a class="fuss-siegel" href="{FWS_PDF}" rel="noopener">FWS-Gütesiegel seit 2021</a>
   </div>
   <div><h2>Seiten</h2><ul>{links}</ul></div>
   <div><h2>Kontakt</h2><ul><li><a href="{TEL_LINK}">{TEL}</a></li><li><a href="mailto:{MAIL}">{MAIL}</a></li><li><a href="{KARTE}" rel="noopener">Pumpwerkstrasse 40<br>8105 Regensdorf</a></li></ul></div>
   <div><h2>Rechtliches</h2><ul><li><a href="{p}impressum">Impressum</a></li><li><a href="{p}datenschutz">Datenschutz</a></li></ul></div>
  </div>
  <div class="fuss-unten"><span>© 2026 Eco Green GmbH, Regensdorf</span><span>CHE-141.654.180</span></div>
 </div>
</footer>
<nav class="leiste" aria-label="Schnellkontakt"><a class="knopf zwei" href="{TEL_LINK}">Anrufen</a><a class="knopf" href="{p}kontakt">Offerte anfragen</a></nav>
<script src="{p}site.js?v=3" defer></script>
</body>
</html>
"""

def seitenkopf(s, h1, lead, bildteil=""):
    p = s["p"]
    spur = [("", "Start")] + s["spur"]
    li = []
    for i, (u, n) in enumerate(spur):
        if i == len(spur) - 1:
            li.append(f'<li aria-current="page">{n}</li>')
        else:
            li.append(f'<li><a href="{(p + u) or "./"}">{n}</a></li>')
    textspan = "seitenkopf-text"
    return f"""<section class="seitenkopf">
 <div class="wrap raster">
  <nav class="brot-nav" aria-label="Brotkrumen" style="grid-column:1/-1"><ol class="brot">{''.join(li)}</ol></nav>
  <div class="{textspan}"><h1>{h1}</h1><p class="lead">{lead}</p></div>
  {f'<div class="seitenkopf-bild">{bildteil}</div>' if bildteil else ''}
 </div>
</section>
"""

def faq_schema(liste):
    return {"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub("<[^>]+>", "", a)}} for q, a in liste]}

def faq_html(liste):
    return "".join(f'<details><summary>{q}</summary><div class="antwort">{a}</div></details>' for q, a in liste)

# ---------------------------------------------------------------- Inhalte

FAQ = [
    ("Wie laut ist eine Erdsondenbohrung?",
     "<p>Laut, aber planbar. Bohrgerät und Kompressor hört man in der Nachbarschaft. Wir bohren Montag bis Freitag zu festen Zeiten, nie am Wochenende, und informieren Ihre Nachbarn eine Woche vorher schriftlich.</p>"),
    ("Wie lange dauert das?",
     "<p>Die Bohrung selbst dauert pro Sonde meist ein bis zwei Tage, dazu ein Tag für Auf- und Abbau. Von der ersten Anfrage bis zur Übergabe vergehen meist zwei bis drei Monate. Die meiste Zeit braucht die Bewilligung.</p>"),
    ("Was passiert mit meinem Garten?",
     "<p>Das Raupengerät fährt auf Platten, damit Rasen und Zufahrt geschützt bleiben. Bohrschlamm fangen wir in Mulden auf. Nach der Arbeit bleibt nur ein kleiner Schacht mit dem Sondenkopf. Ist die Zufahrt zu eng, hebt ein Kran das Gerät über das Haus.</p>"),
    ("Was kostet eine Erdsonde?",
     "<p>Der Preis richtet sich nach den Sondenmetern, und die rechnen wir für Ihr Haus. Nach der Abklärung erhalten Sie eine feste Offerte mit allem, was zur Sonde gehört: Bohrung, Sonde, Verfüllung, Anschluss bis in den Heizraum. Beim Ersatz einer Öl-, Gas- oder Elektroheizung zahlt der Kanton Zürich ab CHF 6'800 daran.</p>"),
    ("Darf auf meinem Grundstück gebohrt werden?",
     "<p>Das zeigt der Wärmenutzungsatlas des Kantons Zürich für jede Parzelle. Wir prüfen das vor der Offerte. Liegt eine Sonde näher als 2,5 Meter an der Grundstücksgrenze, braucht es die Zustimmung Ihres Nachbarn.</p>"),
    ("Wie tief wird gebohrt?",
     "<p>Ein Einfamilienhaus braucht oft eine oder zwei Sonden von 150 bis 250 Metern. Wie viele und wie tief, berechnen wir aus Wärmebedarf und Untergrund. Im Kanton Zürich reichen Erdwärmesonden meist bis höchstens 500 Meter.</p>"),
    ("Wer reicht die Bewilligung ein?",
     "<p>Jede Erdwärmesonde braucht eine gewässerschutzrechtliche Bewilligung des AWEL. Eingereicht wird bei der Baubehörde Ihrer Gemeinde, auch über eBaugesucheZH. Wir stellen die Unterlagen für Sie zusammen.</p>"),
    ("Was bedeutet das FWS-Gütesiegel?",
     "<p>Die Fachvereinigung Wärmepumpen Schweiz vergibt es an Bohrfirmen, die Beratung, Sondenmaterial, Ausführung und Sicherheit nach ihren Vorgaben erfüllen. Das AWEL empfiehlt solche Firmen. Für den Förderbeitrag verlangt der Kanton eine Bohrfirma mit gültigem Gütesiegel.</p>"),
]

SCHRITTE = [
    ("Abklärung", "1 bis 3 Arbeitstage",
     "Wir prüfen im Wärmenutzungsatlas, ob auf Ihrer Parzelle gebohrt werden darf, und schätzen Anzahl und Tiefe der Sonden."),
    ("Offerte", "nach der Abklärung",
     "Sie erhalten eine feste Offerte für Bohrung und Anschluss. Damit reichen Sie das Fördergesuch beim Kanton ein."),
    ("Bewilligung", "4 bis 8 Wochen",
     "Das Gesuch geht über Ihre Gemeinde an das AWEL. Wir stellen die Unterlagen zusammen. Gebohrt wird erst, wenn Bewilligung und Fördergesuch stehen."),
    ("Bohrung und Einbau", "1 bis 2 Tage pro Sonde",
     "Wir bohren, bauen die Sonde ein und verfüllen das Bohrloch dicht. Ihre Nachbarn wissen eine Woche vorher Bescheid."),
    ("Anschluss", "1 bis 2 Tage",
     "Druckprobe jeder Sonde, Leitungen bis in den Heizraum, Befüllung mit Wärmeträgerflüssigkeit."),
    ("Übergabe", "mit der Schlussrechnung",
     "Sie erhalten Bohrprotokoll und Rechnung für die Auszahlung des Förderbeitrags. Ihr Installateur schliesst die Wärmepumpe an."),
]

LEISTUNGEN = [
    ("Sondenauslegung", "Wir berechnen aus Wärmebedarf und Untergrund, wie viele Sonden Ihr Haus braucht und wie tief sie gehen. Zu kurz kühlt der Boden über die Jahre aus. Zu lang zahlen Sie Meter, die Sie nicht brauchen.", None),
    ("Bewilligungs&shy;unterlagen", "Für das gewässerschutzrechtliche Gesuch stellen wir zusammen, was die Gemeinde verlangt: Situationsplan mit Sondenstandort, Sondenlänge, Angaben zur Wärmepumpe. Sie unterschreiben und reichen ein.", None),
    ("Erdsonden&shy;bohrung", "Mit eigenen Raupenbohrgeräten und eigenem Bohrteam, an dem Tag, der in der Offerte steht. Ist die Zufahrt zu eng, hebt ein Kran das Gerät über das Haus.", "garten"),
    ("Sondeneinbau und Verfüllung", "Wir bauen die Sonde ein und verfüllen das Bohrloch von unten nach oben dicht. So fliesst kein Wasser zwischen den Bodenschichten, und die Sonde bleibt Jahrzehnte im Boden.", None),
    ("Druckprobe und Anbindung", "Jede Sonde wird mit Druck geprüft und im Protokoll festgehalten. Danach verlegen wir die Verbindungsleitungen zum Haus und setzen den Verteiler im Heizraum.", "verteiler"),
    ("Befüllung und Übergabe", "Wir füllen Sonde und Leitungen mit Wärmeträgerflüssigkeit und übergeben die Anlage an Ihren Heizungsinstallateur. Bohrprotokoll und Rechnung für das Fördergesuch erhalten Sie mit.", None),
]
KURZ = {  # Kurzfassung fuer die Startseite
    "Sondenauslegung": "Anzahl und Tiefe der Sonden, gerechnet für Ihr Haus.",
    "Bewilligungs&shy;unterlagen": "Situationsplan und Angaben für das Gesuch an die Gemeinde.",
    "Erdsonden&shy;bohrung": "Mit eigenen Raupenbohrgeräten, wenn nötig per Kran über das Haus.",
    "Sondeneinbau und Verfüllung": "Dicht verfüllt, damit das Grundwasser geschützt bleibt.",
    "Druckprobe und Anbindung": "Mit Druck geprüft und bis in den Heizraum verlegt.",
    "Befüllung und Übergabe": "Betriebsbereit an Ihren Installateur übergeben.",
}

def rechner_html(eid="rechner"):
    return f"""<div class="rechner" id="{eid}">
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
    return f"""<svg class="schema" viewBox="0 0 400 690" role="img" aria-label="Schema einer Erdwärmesonde: Haus mit Wärmepumpe, darunter eine Sonde bis rund 220 Meter Tiefe. Ab 15 Metern hat der Boden rund 10 Grad, in 200 Metern rund 15 Grad.">
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
 <circle cx="228" cy="{Y0 + 15 * K:.0f}" r="5" fill="#121712"/><text x="16" y="{Y0 + 20 * K:.0f}">15 m: rund 10 °C</text>
 <circle cx="228" cy="{Y0 + 200 * K:.0f}" r="5" fill="#121712"/><text x="16" y="{Y0 + 205 * K:.0f}">200 m: rund 15 °C</text>
 <text x="16" y="{Y0 + 110 * K:.0f}" fill="#4A5348">Kies, Sand, Fels</text>
</g>
</svg>"""


def seite_start():
    s = {"slug": "", "p": "", "spur": [],
         "title": "Erdsondenbohrung Zürich | Eco Green, Regensdorf",
         "og": "Eco Green: Erdwärmesonden für Ihre Wärmepumpe",
         "desc": "Erdsondenbohrungen für Wärmepumpen im Kanton Zürich. Bohrfirma mit FWS-Gütesiegel aus Regensdorf, von der Abklärung bis zur fertigen Sonde. Offerte anfragen.",
         "preload": preload("garten", "(max-width: 900px) 100vw, 40vw")}
    s["schema"] = [{"@type": "WebSite", "@id": BASIS + "#website", "url": BASIS, "name": "Eco Green", "inLanguage": "de-CH", "publisher": {"@id": ORG_ID}},
                   faq_schema(FAQ)]
    p = ""
    leist = "".join(f'<article><div><h3>{t}</h3><p>{KURZ[t]}</p></div></article>'
                    for i, (t, _x, _b) in enumerate(LEISTUNGEN))
    schritte = "".join(f'<li class="schritt"><div class="kopfnr"><span>{i + 1:02d}</span><span class="mono">{dauer}</span></div><h3>{t}</h3><p>{x}</p></li>'
                       for i, (t, dauer, x) in enumerate(SCHRITTE))
    bilder = "".join(foto(p, k, a, c, sizes="(max-width: 900px) 100vw, 33vw") for k, a, c in [
        ("kran", "Ein Kran hebt ein Raupenbohrgerät über ein Wohnhaus", "Zufahrt zu eng: das Gerät kommt per Kran."),
        ("bohrmeister", "Bohrmeister im Eco-Green-Shirt am Bohrgerät", "Eigenes Bohrteam auf jeder Baustelle."),
        ("verteiler", "Zwei Sondenrohre mit Manometern während der Druckprobe", "Druckprobe an zwei Sonden."),
    ])
    body = f"""<section class="hero" aria-labelledby="h1">
 <div class="wrap raster">
  <div class="hero-text">
   <span class="label">Bohrfirma aus Regensdorf ZH</span>
   <h1 id="h1">Erdwärmesonden für Ihre Wärmepumpe.</h1>
   <p class="lead">Eco Green bohrt Erdwärmesonden für Ein- und Mehrfamilienhäuser im Kanton Zürich. Von der Abklärung bis zur angeschlossenen Sonde, mit eigenen Geräten und eigenem Bohrteam.</p>
   <div class="knopfreihe"><a class="knopf" href="kontakt">Offerte anfragen</a><a class="knopf zwei" href="{TEL_LINK}">{TEL}</a></div>
  </div>
  <div class="hero-bild">{foto(p, "garten", "Raupenbohrgerät von Eco Green bohrt im Garten eines Einfamilienhauses", "Bohrung im Garten eines Einfamilienhauses.", lazy=False, prio=True)}</div>
  <ul class="belege">
    <li><a href="{FWS_PDF}" rel="noopener"><b>FWS-Gütesiegel</b>Eine von 45 Bohrfirmen der Schweiz</a></li>
    <li><a href="#foerderung"><b>Förderbeitrag</b>ab CHF 6'800 vom Kanton</a></li>
    <li><b>Einsatzgebiet</b>{EINSATZ}</li>
    <li><b>Bewilligung</b>Unterlagen für Gemeinde und AWEL von uns</li>
  </ul>
 </div>
</section>

<section class="sektion hell" aria-labelledby="problem-h">
 <div class="wrap raster">
  <div class="kopfzeile">
   <div><span class="label">Heizungsersatz</span><h2 id="problem-h">Ihre Öl- oder Gasheizung muss ersetzt werden?</h2></div>
   <div><p class="lead">Im Kanton Zürich darf eine fossile Heizung in einem bestehenden Haus seit 01.09.2022 grundsätzlich nur noch durch ein erneuerbares System ersetzt werden. Im ersten Jahr wurden über 98 Prozent der ersetzten fossilen Heizungen durch klimaneutrale ersetzt.</p>
   <p class="lead">Öl und Gas kosten jedes Jahr. Die Wärme aus dem Boden kostet nichts, Sie bezahlen nur den Strom für die Pumpe.</p></div>
  </div>
  <p class="quelle" style="grid-column:1/-1">Quelle: <a href="{ZH_ENERGIE}" rel="noopener">Kanton Zürich, Bauvorschriften Gebäude und Energie</a>.</p>
 </div>
</section>

<section class="sektion" aria-labelledby="prinzip-h">
 <div class="wrap raster">
  <div class="prinzip-bild">{schema_svg()}</div>
  <div class="prinzip-text">
   <span class="label">So funktioniert Erdwärme</span>
   <h2 id="prinzip-h">Der Boden heizt Ihr Haus.</h2>
   <ol class="teile" style="margin-top:32px">
    <li><div><h3>Erdwärmesonde</h3><p>Ein Rohr in einem Bohrloch von 150 bis 250 Metern. Eine Flüssigkeit zirkuliert darin und nimmt die Wärme des Bodens auf.</p></div></li>
    <li><div><h3>Wärmepumpe</h3><p>Sie hebt die Temperatur auf das Niveau Ihrer Heizung. Rund drei Viertel der Wärme stammen aus dem Boden, der Rest ist Strom.</p></div></li>
    <li><div><h3>Heizung und Warmwasser</h3><p>Bodenheizung oder Radiatoren werden versorgt wie bisher. Im Sommer kann die Sonde das Haus leicht kühlen.</p></div></li>
   </ol>
   <a class="weiter" href="kontakt">Grundstück prüfen lassen</a>
  </div>
 </div>
</section>

<section class="sektion hell" aria-labelledby="leist-h">
 <div class="wrap raster">
  <div class="kopfzeile">
   <div><span class="label">Leistungen</span><h2 id="leist-h">Alles bis zur Sonde im Heizraum.</h2></div>
   <p>Die Wärmepumpe liefert Ihr Heizungsinstallateur. Alles, was im Boden liegt und zur Sonde gehört, machen wir.</p>
  </div>
  <div class="leistungen">{leist}</div>
  <div style="grid-column:1/-1"><a class="weiter" href="leistungen">Alle Leistungen im Detail</a></div>
 </div>
</section>

<section class="sektion" aria-labelledby="ablauf-h">
 <div class="wrap raster">
  <div class="kopfzeile">
   <div><span class="label">Ablauf</span><h2 id="ablauf-h">In sechs Schritten zur Erdwärme.</h2></div>
   <p>Von der ersten Anfrage bis zur Übergabe vergehen meist zwei bis drei Monate. Die Bohrung selbst dauert wenige Tage.</p>
  </div>
  <ol class="schritte">{schritte}</ol>
  <div style="grid-column:1/-1"><a class="weiter" href="ablauf">Ablauf im Detail</a></div>
 </div>
</section>

<section class="sektion dunkel" aria-labelledby="vertrauen-h">
 <div class="wrap raster">
  <div class="siegel">
   <span class="label">FWS-Gütesiegel</span>
   <h2 id="vertrauen-h"><span class="gross">Eine von 45</span>Bohrfirmen in der Schweiz mit Gütesiegel.</h2>
   <p style="margin-top:24px">Das AWEL empfiehlt Bauherrschaften eine Bohrfirma mit diesem Siegel. Für den Förderbeitrag verlangt es der Kanton.</p>
   <a class="weiter" href="{FWS_PDF}" rel="noopener">Gütesiegelliste ansehen</a>
  </div>
  <div class="vertrauen-daten">
   <dl class="daten">
    <div><dt>Sitz</dt><dd>Pumpwerkstrasse 40, Regensdorf, seit 2020</dd></div>
    <div><dt>Gütesiegel</dt><dd>Seit Juni 2021 auf der Liste der FWS</dd></div>
    <div><dt>Geräte</dt><dd>Eigene Raupenbohrgeräte und eigenes Bohrteam</dd></div>
    <div><dt>Baustelle</dt><dd>Feste Arbeitszeiten, Nachbarn eine Woche vorher informiert, Rasen mit Platten geschützt</dd></div>
    <div><dt>Ansprechperson</dt><dd>Eine Person für die ganze Baustelle, mit direkter Nummer</dd></div>
   </dl>
  </div>
  <div class="bildreihe">{bilder}</div>
  <div style="grid-column:1/-1"><a class="weiter" href="referenzen">Baustellen ansehen</a></div>
 </div>
</section>

<section class="sektion" id="foerderung" aria-labelledby="foerder-h">
 <div class="wrap raster">
  <div class="foerder-text">
   <span class="label">Förderung</span>
   <h2 id="foerder-h">Der Kanton Zürich zahlt mit.</h2>
   <p class="lead" style="margin-top:24px">CHF 6'800 an eine Erdwärmepumpe bis 15 kW, die eine Öl-, Gas- oder Elektroheizung ersetzt. Darüber kommen CHF 420 pro kW dazu.</p>
   <p>Wichtig: Das Gesuch muss vor der Bohrung eingereicht sein. Und es verlangt eine Bohrfirma mit gültigem Gütesiegel. Beides klären wir mit Ihnen vor dem ersten Bohrtag.</p>
   <a class="weiter" href="foerderung">Bedingungen und Unterlagen</a>
   <p class="quelle">Quelle: Kanton Zürich, <a href="{ZH_FOERDER_PDF}" rel="noopener">Förderprogramm Heizung ersetzen</a>. Das Programm läuft <a href="{ZH_2026}" rel="noopener">2026 unverändert</a> weiter.</p>
  </div>
  {rechner_html()}
 </div>
</section>

<section class="sektion hell" aria-labelledby="faq-h">
 <div class="wrap raster">
  <div class="faq-kopf"><span class="label">Fragen</span><h2 id="faq-h">Fragen vor der Bohrung.</h2><p style="margin-top:24px">Ihre Frage fehlt? <a href="{TEL_LINK}">{TEL}</a></p></div>
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
    s["schema"] = [{"@type": "Service", "name": t.replace("&shy;", ""), "description": x, "serviceType": "Erdwärmesonde", "provider": {"@id": ORG_ID},
                    "areaServed": {"@type": "AdministrativeArea", "name": "Kanton Zürich"}} for t, x, _b in LEISTUNGEN]
    reihen = ""
    for i, (t, x, b) in enumerate(LEISTUNGEN):
        rechts = ""
        if b:
            alt = {"garten": "Raupenbohrgerät bohrt im Garten eines Einfamilienhauses", "verteiler": "Sondenverteiler mit zwei Manometern"}[b]
            rechts = f'<div class="bild">{foto(p, b, alt, sizes="(max-width: 900px) 100vw, 33vw")}</div>'
        reihen += f'<article class="leistung"><span class="nr">{i + 1:02d}</span><div class="inhalt"><h2>{t}</h2><p>{x}</p></div>{rechts}</article>'
    body = seitenkopf(s, "Alles, was zur Erdsonde gehört.", "Eco Green bohrt Erdwärmesonden und schliesst sie bis in den Heizraum an. Sie haben eine Ansprechperson vom ersten Anruf bis zum Bohrprotokoll.") + f"""
<section class="sektion"><div class="wrap raster">{reihen}</div></section>
<section class="sektion dunkel" aria-labelledby="inst-h">
 <div class="wrap raster">
  <div class="links"><span class="label">Für Installateure und Planer</span><h2 id="inst-h">Sie planen die Wärmepumpe, wir liefern die Sonde.</h2></div>
  <div class="rechts">
   <p class="lead">Für Anlagen bis 15 kW verlangt der Kanton das Wärmepumpen-System-Modul, für die Förderung eine Bohrfirma mit Gütesiegel. Sondenlänge, Druckprotokoll und Bohrprotokoll erhalten Sie so, wie Ihr Dossier sie braucht.</p>
   <p>Sie erhalten einen festen Bohrtermin und eine Ansprechperson, die auch Ihren Bauleiter kennt.</p>
   <div class="knopfreihe"><a class="knopf" href="mailto:{MAIL}?subject={quote('Anfrage Installateur: Erdsonde')}">Projekt anfragen</a></div>
  </div>
 </div>
</section>
<section class="sektion hell" aria-labelledby="nicht-h">
 <div class="wrap raster">
  <div class="links"><h2 id="nicht-h">Was nicht zu uns gehört.</h2></div>
  <div class="rechts">
   <p class="lead">Die Wärmepumpe selbst liefert und montiert Ihr Heizungsinstallateur. Wir arbeiten mit ihm zusammen und übergeben ihm die befüllte Sonde.</p>
   <p>Haben Sie noch keinen Installateur, nennen wir Ihnen Betriebe aus der Region, mit denen wir schon gebaut haben.</p>
  </div>
 </div>
</section>
{schluss(p, "Wie viele Meter braucht Ihr Haus?", "Schicken Sie uns Adresse und heutigen Verbrauch. Sie erhalten eine erste Einschätzung zu Anzahl und Länge der Sonden. Kostenlos.")}"""
    return s, body


def seite_ablauf():
    s = {"slug": "ablauf", "p": "", "ogbild": "og-ablauf", "preload": preload("feld2", "(max-width: 900px) 100vw, 33vw"), "spur": [("ablauf", "Ablauf")],
         "title": "Erdsonde Bewilligung Zürich: Ablauf | Eco Green",
         "desc": "Von der Abklärung im Wärmenutzungsatlas bis zur Übergabe: so läuft eine Erdsondenbohrung im Kanton Zürich ab. Mit Bewilligung, Förderung und Baustellenregeln."}
    p = s["p"]
    sie = [
        "Sie schicken uns die fünf Angaben aus der E-Mail-Vorlage. Fotos vom Heizraum helfen.",
        "Sie entscheiden und reichen mit der Offerte das Fördergesuch auf der Gesuchplattform des Kantons ein.",
        "Sie unterschreiben das Bewilligungsgesuch und reichen es bei der Gemeinde ein.",
        "Sie sorgen für Strom und Wasser auf dem Grundstück und eine freie Zufahrt.",
        "Sie stimmen den Anschlusstermin mit Ihrem Heizungsinstallateur ab.",
        "Sie reichen Bohrprotokoll und Rechnung mit den Unterlagen der Wärmepumpe beim Kanton ein.",
    ]
    wir = [
        "Wir prüfen im Wärmenutzungsatlas, ob gebohrt werden darf, und schätzen Anzahl und Tiefe der Sonden.",
        "Wir erstellen die Offerte und liefern den Nachweis unseres Gütesiegels für das Fördergesuch.",
        "Wir stellen Situationsplan, Sondenlänge und Angaben zur Wärmepumpe für das Gesuch zusammen.",
        "Wir informieren Ihre Nachbarn, bohren, bauen die Sonde ein und verfüllen das Bohrloch. Bohrschlamm fangen wir auf.",
        "Wir prüfen jede Sonde mit Druck, verlegen die Leitungen bis in den Heizraum und füllen das System.",
        "Wir übergeben Protokolle und Rechnung. Danach räumen wir die Baustelle.",
    ]
    phasen = "".join(
        f'<article class="phase"><div class="phase-kopf"><span class="nr">{i + 1:02d}</span><h2>{t}</h2><span class="mono">{dauer}</span></div>'
        f'<div class="phase-sie"><h3>Was Sie tun</h3><p>{sie[i]}</p></div><div class="phase-wir"><h3>Was wir tun</h3><p>{wir[i]}</p></div></article>'
        for i, (t, dauer, _x) in enumerate(SCHRITTE))
    body = seitenkopf(s, "Ablauf einer Erdsondenbohrung.", "Von der ersten Anfrage bis zur Übergabe vergehen meist zwei bis drei Monate. Die meiste Zeit braucht die Bewilligung. Die Bohrung selbst dauert wenige Tage.",
                      foto(p, "feld2", "Bohrgerät mit Bagger auf einer Wiese am Dorfrand", "Bohrung am Dorfrand im Winter.", lazy=False, prio=True, sizes="(max-width: 900px) 100vw, 33vw")) + f"""
<section class="sektion"><div class="wrap raster">{phasen}</div></section>
<section class="sektion hell" aria-labelledby="bew-h">
 <div class="wrap raster">
  <div class="links">
   <span class="label">Bewilligung</span>
   <h2 id="bew-h">Was der Kanton verlangt.</h2>
   <ul class="punkte" style="margin-top:32px">
    <li>Jede Erdwärmesonde braucht eine gewässerschutzrechtliche Bewilligung des AWEL.</li>
    <li>Eingereicht wird bei der Baubehörde der Gemeinde, auch über eBaugesucheZH.</li>
    <li>Der Wärmenutzungsatlas zeigt für jede Parzelle, ob Sonden zulässig sind.</li>
    <li>Unter 2,5 Meter Abstand zur Grenze braucht es die Zustimmung des Nachbarn.</li>
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
    <li>Bohrschlamm und Bohrwasser fangen wir in Mulden auf. Nichts läuft in die Kanalisation.</li>
    <li>Sie haben eine Ansprechperson mit direkter Handynummer.</li>
   </ul>
  </div>
 </div>
</section>
{schluss(p)}"""
    return s, body


FOERDER_FAQ = [
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
    body = seitenkopf(s, "Förderbeitrag Kanton Zürich.", "Der Kanton fördert den Ersatz von Öl-, Gas- und Elektroheizungen durch eine Erdwärmepumpe. Das Gesuch muss eingereicht sein, bevor wir bohren.") + f"""
<section class="sektion" aria-labelledby="rechner-h">
 <div class="wrap raster">
  <div class="foerder-text">
   <h2 id="rechner-h">Was der Kanton an Ihre Anlage zahlt.</h2>
   <p class="lead" style="margin-top:24px">Bis 15 kW Heizleistung CHF 6'800, darüber CHF 420 pro kW. Für Sonden ohne Frostschutzmittel oder mit Regeneration kommt ein Zusatzbeitrag dazu.</p>
   <p class="quelle">Sätze: Kanton Zürich, <a href="{ZH_FOERDER_PDF}" rel="noopener">Förderprogramm Heizung ersetzen</a>, Sole-Wasser-Wärmepumpe. <a href="{ZH_2026}" rel="noopener">Programm 2026 unverändert.</a></p>
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
    <li>Das Gebäude besteht schon. Neubauten fördert der Kanton nicht.</li>
    <li>Die Wärmepumpe ist die Hauptheizung und liefert mindestens 50 Prozent der Wärme.</li>
    <li>Bis 15 kW: Anlagezertifikat Wärmepumpen-System-Modul (WPSM).</li>
    <li>Die Bohrfirma hat ein gültiges Gütesiegel.</li>
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
   <p class="lead">Eine Öl- oder Gasheizung in einem bestehenden Haus darf seit 01.09.2022 grundsätzlich nur noch durch ein erneuerbares System ersetzt werden.</p>
   <p>Eine Ausnahme gilt, wenn die erneuerbare Lösung über die ganze Lebensdauer mehr als 5 Prozent teurer ist. Im ersten Jahr wurden über 98 Prozent der ersetzten fossilen Heizungen durch klimaneutrale Systeme ersetzt.</p>
   <p class="quelle">Quelle: <a href="{ZH_ENERGIE}" rel="noopener">Kanton Zürich, Bauvorschriften Gebäude und Energie</a></p>
  </div>
 </div>
</section>
<section class="sektion" aria-labelledby="ffaq-h">
 <div class="wrap raster">
  <div class="faq-kopf"><h2 id="ffaq-h">Fragen zur Förderung.</h2></div>
  <div class="faq">{faq_html(FOERDER_FAQ)}</div>
 </div>
</section>
{schluss(p, "Offerte und Siegelnachweis von uns.", "Sie erhalten von uns die Offerte für die Bohrung und den Nachweis unseres Gütesiegels. Damit ist Ihr Gesuch vollständig, bevor das Gerät kommt.")}"""
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
    s = {"slug": "referenzen", "p": "", "ogbild": "og-referenzen", "preload": preload("garten", "(max-width: 900px) 50vw, 25vw"), "spur": [("referenzen", "Baustellen")],
         "title": "Erdsondenbohrung Referenzen | Eco Green Baustellen",
         "desc": "Baustellen von Eco Green: Erdsondenbohrungen für Einfamilienhäuser, Mehrfamilienhäuser und Neubauten im Kanton Zürich. Mit Kran, wenn die Zufahrt zu eng ist."}
    p = s["p"]
    zeilen = "".join(f'<tr><td data-label="Objekt">{o}</td><td data-label="Region">{ort}</td><td data-label="Ersetzt">{alt}</td><td data-label="Sonden" class="zahl">{sonden}</td><td data-label="Besonderheit">{notiz}</td></tr>'
                     for o, ort, alt, sonden, notiz in PROJEKTE)
    gal = "".join(foto(p, k, a, c, sizes="(max-width: 900px) 50vw, 25vw", lazy=i > 3, prio=i == 0) for i, (k, a, c) in enumerate([
        ("garten", "Türkises Raupenbohrgerät im Garten eines Einfamilienhauses", "Garten eines Einfamilienhauses."),
        ("dorf", "Bohrgerät zwischen Bauernhaus und Wohnhaus", "Zwischen Bauernhaus und Wohnhaus."),
        ("feld", "Bohrgerät und Bagger am Siedlungsrand im Winter", "Siedlungsrand im Winter."),
        ("rot-grube", "Rotes Raupenbohrgerät neben einer Baugrube", "Neubau, vor dem Aushub."),
        ("herbst", "Bohrgerät neben einer Baugrube im Herbst", "Baugrube im Herbst."),
        ("mast", "Bohrmast von unten", "Der Bohrmast."),
        ("raupe", "Fuss des Bohrmasts im Bohrschlamm", "Bohrschlamm am Mastfuss."),
        ("rot-nah", "Hydraulik am roten Bohrgerät", "Hydraulik am roten Gerät."),
    ]))
    body = seitenkopf(s, "Baustellen.", "Alle Bilder auf dieser Website stammen von Baustellen von Eco Green. So sehen Erdsondenbohrungen im Kanton Zürich aus.") + f"""
<section class="sektion" aria-labelledby="gal-h">
 <div class="wrap raster">
  <h2 id="gal-h" class="sr">Fotos von Baustellen</h2>
  <div class="galerie">{gal}</div>
 </div>
</section>
<section class="sektion hell" aria-labelledby="proj-h">
 <div class="wrap raster">
  <div class="kopfzeile"><div><h2 id="proj-h">Typische Aufträge.</h2></div><p>Sondenzahl und Tiefe richten sich nach dem Haus. Diese Beispiele zeigen die Spannweite.</p></div>
  <div class="tabelle-rahmen"><table class="tabelle">
   <thead><tr><th scope="col">Objekt</th><th scope="col">Region</th><th scope="col">Ersetzt</th><th scope="col">Sonden</th><th scope="col">Besonderheit</th></tr></thead>
   <tbody>{zeilen}</tbody>
  </table></div>
 </div>
</section>
{schluss(p, "Ihr Haus als nächste Baustelle?")}"""
    return s, body


def seite_ueber():
    s = {"slug": "ueber-uns", "p": "", "ogbild": "og-ueber-uns", "preload": preload("bohrmeister", "(max-width: 900px) 100vw, 33vw"), "spur": [("ueber-uns", "Über uns")],
         "title": "Bohrfirma mit FWS-Gütesiegel in Regensdorf | Eco Green",
         "desc": "Eco Green GmbH ist eine Bohrfirma für Erdwärmesonden an der Pumpwerkstrasse 40 in Regensdorf. Mit FWS-Gütesiegel seit 2021 und eigenen Raupenbohrgeräten."}
    p = s["p"]
    body = seitenkopf(s, "Bohrfirma aus dem Furttal.", "Eco Green GmbH bohrt Erdwärmesonden für Einfamilienhäuser, Mehrfamilienhäuser und Neubauten. Von Regensdorf aus fahren wir mit eigenen Geräten zu Baustellen im ganzen Kanton.",
                      foto(p, "bohrmeister", "Bohrmeister im grünen Eco-Green-Shirt am Bohrgerät", "Bohrmeister von Eco Green.", lazy=False, prio=True, sizes="(max-width: 900px) 100vw, 33vw")) + f"""
<section class="sektion" aria-labelledby="daten-h">
 <div class="wrap raster">
  <div class="links"><h2 id="daten-h">Die Firma in Fakten.</h2></div>
  <div class="rechts">
   <dl class="daten">
    <div><dt>Firma</dt><dd>Eco Green GmbH</dd></div>
    <div><dt>Sitz</dt><dd>Pumpwerkstrasse 40, 8105 Regensdorf, seit 2020</dd></div>
    <div><dt>Handelsregister</dt><dd>Kanton Zürich, CHE-141.654.180</dd></div>
    <div><dt>Tätigkeit</dt><dd>Planung und Ausführung von Erdsondenbohrungen</dd></div>
    <div><dt>Gütesiegel</dt><dd>FWS-Gütesiegel für Erdwärmesonden-Bohrfirmen, seit Juni 2021 auf der Liste</dd></div>
    <div><dt>Geräte</dt><dd>Eigene Raupenbohrgeräte, Transport bei Bedarf mit Kran</dd></div>
    <div><dt>Einsatzgebiet</dt><dd>{EINSATZ}</dd></div>
   </dl>
  </div>
 </div>
</section>
<section class="sektion dunkel" aria-labelledby="siegel-h">
 <div class="wrap raster">
  <div class="links"><span class="label">FWS-Gütesiegel</span><h2 id="siegel-h">Eine von 45 Bohrfirmen mit Gütesiegel.</h2></div>
  <div class="rechts">
   <p class="lead">45 Bohrfirmen in der Schweiz tragen das Gütesiegel der Fachvereinigung Wärmepumpen Schweiz. Eco Green ist seit 2021 dabei.</p>
   <p>Wer es trägt, verpflichtet sich auf Beratung der Bauherrschaft, umweltschonende Ausführung, Bohrungen nach dem Stand der Technik, hochwertiges Sondenmaterial und Sicherheit auf der Baustelle. Das AWEL empfiehlt Firmen mit diesem Siegel, und der Kanton verlangt es für den Förderbeitrag.</p>
   <div class="knopfreihe"><a class="knopf zwei" href="{FWS_PDF}" rel="noopener">Gütesiegelliste ansehen</a></div>
  </div>
 </div>
</section>
<section class="sektion" aria-labelledby="leute-h">
 <div class="wrap raster">
  <div class="links"><h2 id="leute-h">Geschäftsführung.</h2></div>
  <div class="rechts">
   <dl class="daten">
    <div><dt>Etiènne Spruijt</dt><dd>Inhaber und Vorsitzender der Geschäftsführung. Bohrungen und Geräte.</dd></div>
    <div><dt>Mahissa Ganz-Yasri</dt><dd>Geschäftsführerin. Offerten und Termine.</dd></div>
    <div><dt>Bohrteam</dt><dd>Eigenes Bohrpersonal auf jeder Baustelle.</dd></div>
   </dl>
  </div>
 </div>
</section>
<section class="sektion hell" aria-labelledby="ort-h">
 <div class="wrap raster">
  <div class="links"><h2 id="ort-h">Pumpwerk&shy;strasse 40, Regensdorf.</h2></div>
  <div class="rechts">
   <p class="lead">Von hier sind Furttal, Zürcher Unterland und Limmattal schnell erreicht. Die Stadt Zürich auch.</p>
   <address style="font-style:normal;margin-top:24px">Eco Green GmbH<br>Pumpwerkstrasse 40<br>8105 Regensdorf</address>
   <a class="weiter" href="{KARTE}" rel="noopener">Auf der Karte zeigen</a>
  </div>
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
    body = seitenkopf(s, "Offerte anfragen.", "Für die Erstabklärung brauchen wir fünf Angaben. Das Gespräch dauert zehn Minuten, die Einschätzung ist kostenlos.") + f"""
<section class="sektion" aria-label="Telefon und E-Mail">
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
    <li><span><b>Verbrauch pro Jahr.</b> Liter Öl, Kubikmeter Gas oder Kilowattstunden. Daraus rechnen wir die Sondenlänge.</span></li>
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
   <p style="margin-top:16px">{BUEROZEIT}</p>
   <div class="knopfreihe"><a class="knopf" href="{KARTE}" rel="noopener">Route planen</a></div>
  </div>
 </div>
</section>"""
    return s, body


def seite_impressum():
    s = {"slug": "impressum", "p": "", "spur": [("impressum", "Impressum")],
         "title": "Impressum | Eco Green GmbH, Erdwärmesonden Regensdorf",
         "desc": "Impressum der Website von Eco Green GmbH, Bohrfirma für Erdwärmesonden, Pumpwerkstrasse 40, 8105 Regensdorf. Handelsregister Kanton Zürich, CHE-141.654.180."}
    body = seitenkopf(s, "Impressum.", "Angaben zur Betreiberin dieser Website.") + f"""
<section class="sektion"><div class="wrap raster"><div class="recht">
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
    s = {"slug": "datenschutz", "p": "", "spur": [("datenschutz", "Datenschutz")],
         "title": "Datenschutzerklärung | Eco Green GmbH, Regensdorf",
         "desc": "Datenschutzerklärung von Eco Green GmbH nach dem Schweizer Datenschutzgesetz (DSG). Keine Cookies, kein Tracking, Schriften lokal. Was wir speichern und warum."}
    body = seitenkopf(s, "Datenschutz.", "Wie Eco Green mit Personendaten umgeht. Nach dem Bundesgesetz über den Datenschutz (DSG). Stand 21.10.2026.") + f"""
<section class="sektion"><div class="wrap raster"><div class="recht">
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
    s = {"slug": "404.html", "p": PFAD, "spur": [("404.html", "Nicht gefunden")],
         "title": "Seite nicht gefunden | Eco Green Erdwärmesonden",
         "desc": "Diese Seite gibt es nicht. Zurück zur Startseite von Eco Green, Bohrfirma für Erdwärmesonden in Regensdorf, oder direkt zu Leistungen, Ablauf und Kontakt."}
    p = PFAD
    body = f"""<section class="seitenkopf"><div class="wrap raster"><div class="seitenkopf-text">
 <span class="label">Fehler 404</span>
 <h1>404 Meter tief. Nichts gefunden.</h1>
 <p class="lead" style="margin-top:24px">Diese Seite gibt es nicht oder nicht mehr.</p>
 <div class="knopfreihe"><a class="knopf" href="{p}">Zur Startseite</a><a class="knopf zwei" href="{p}kontakt">Offerte anfragen</a></div>
</div></div></section>"""
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
                       "background_color": "#FFFFFF", "theme_color": "#29662F",
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
