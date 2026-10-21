# Eco Green Website

Vorschau der neuen Website von Eco Green GmbH, Regensdorf. Gestaltung und Umsetzung: Lorien Group, Aarau.

Vorschau: https://leitung-gif.github.io/eco-green-website/

## Aufbau

- `src/assets.py` erzeugt Bilder, Logo als SVG, Favicons und OG-Bilder nach `docs/`. Braucht die Originale aus dem Projektordner (`recherche/roh/bilder`), die nicht im Repo liegen.
- `src/bauen.py` erzeugt alle Seiten, `sitemap.xml`, `robots.txt`, `llms.txt` und `site.webmanifest` nach `docs/`.
- `src/static/` enthält CSS, JavaScript und die lokalen Schriften.
- GitHub Pages liefert den Ordner `docs/` aus.

```
cd src
python bauen.py
```

## Vor Livegang entfernen

Die Vorschau ist absichtlich gesperrt:

- `meta robots` steht auf `noindex, nofollow`.
- `robots.txt` enthält `Disallow: /`.
- Canonical, OG und Sitemap zeigen auf die github.io-Adresse.

Für den Livegang `BASIS` in `src/bauen.py` auf `https://eco-green.ch/` und `VORSCHAU = False` setzen. Probe ohne Änderung: `python bauen.py --live <ordner>`. Danach Datenschutz an den neuen Host anpassen, alte URLs per 301 umleiten, Search Console und Bing einrichten.
