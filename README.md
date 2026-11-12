# Eco Green Website

Vorschau der neuen Website von Eco Green GmbH, Regensdorf. Gestaltung und Umsetzung: Lorien Group, Aarau.

Vorschau: https://leitung-gif.github.io/eco-green-website/

## Aufbau

- `src/bauen.py` erzeugt alle Seiten, Ratgeber, Atom-Feed, `sitemap.xml`, `robots.txt`, `llms.txt` und `site.webmanifest` nach `docs/`.
- `src/ratgeber/NN-handle.html` sind die Ratgeber-Artikel (Meta-JSON im Kopf, HTML-Körper). Das Format steht in `lies_artikel()` und wird beim Bauen hart geprüft.
- `src/assets.py` enthält Bilder, Logo, Favicons und OG-Bilder. Nicht mehr ganz laufen lassen, das kodiert alle Bilder neu. OG-Bilder der Artikel erzeugt `bauen.py` selbst, nur wenn eines fehlt oder Titel oder Foto geändert haben (`src/og-ratgeber.json`).
- `src/static/` enthält CSS, JavaScript und die lokalen Schriften.
- `src/pruefen.py` prüft interne Links, Dateien, JSON-LD, Sitemap, Feed und `data-shopify`.
- `src/vorschau.py` startet eine lokale Vorschau wie auf Shopify (Pfad `/`, URLs ohne Endung, 404 mit Status 404).
- GitHub Pages liefert den Ordner `docs/` aus.

## URL-Aufbau wie auf Shopify

| Adresse | Datei |
|---|---|
| `/` | `docs/index.html` |
| `/pages/<handle>` | `docs/pages/<handle>.html` |
| `/blogs/ratgeber` | `docs/blogs/ratgeber.html` |
| `/blogs/ratgeber/<handle>` | `docs/blogs/ratgeber/<handle>.html` |
| `/blogs/ratgeber.atom` | `docs/blogs/ratgeber.atom` |

Alle internen Links sind absolut mit `PFAD` (Vorschau `/eco-green-website/`, live `/`) und ohne Dateiendung. Sie laufen über `link()` und `asset()` in `bauen.py`.

## Aufrufe

```
cd src
python bauen.py                          # Vorschau nach docs
python bauen.py --entwurf                # dasselbe, Verweise auf noch fehlende Artikel nur als Warnung
python bauen.py --live <ordner>          # Probebau für den Livegang
python bauen.py --ziel <ordner> --ratgeber <ordner>   # Test mit anderen Artikeln, nie nach docs
python bauen.py --shopify [<ordner>]     # Export, Standard ../../shopify-uebertragung
python pruefen.py [<ordner> --live]      # Links, JSON-LD, Sitemap
python vorschau.py [port]                # lokale Vorschau, Standard 8653
```

## Vor Livegang

Die Vorschau ist absichtlich gesperrt: `meta robots` auf `noindex, nofollow`, `robots.txt` mit `Disallow: /`, Canonical, OG und Sitemap auf der github.io-Adresse. Die Website zieht auf Shopify um. Ablauf, Weiterleitungen und Prüfungen stehen in `shopify-uebertragung/UEBERTRAGUNG.md` (erzeugt mit `--shopify`).
