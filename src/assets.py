"""Bilder, Logo als SVG, Favicons und OG-Bild fuer die Eco-Green-Website.

Quelle aller Fotos und Logos: recherche/roh/bilder (eco-green.ch, abgerufen 21.10.2026).
Aufruf: python assets.py   (schreibt nach ../docs/img und ../docs)
"""
from pathlib import Path
import io
import cv2
import numpy as np
from PIL import Image, ImageOps, ImageDraw, ImageFont, ImageFilter

HIER = Path(__file__).resolve().parent
ROH = HIER.parents[1] / "recherche" / "roh" / "bilder"
OUT = HIER.parent / "docs"
IMG = OUT / "img"
IMG.mkdir(parents=True, exist_ok=True)

GRUEN = (41, 102, 47)      # #29662F, Logo gemessen
TINTE = (20, 20, 15)
KALK = (242, 238, 227)
OCKER = (240, 178, 62)

# Fotos: Schluessel -> (Datei, Ausschnitt als Anteil links, oben, rechts, unten)
FOTOS = {
    "kran":       ("b_5.05.jpg", (0, 0, 1, 1)),
    "garten":     ("b_4.05.jpg", (0, 0, 1, 1)),
    "bohrmeister":("b_6.05.jpg", (0, 0, 1, 1)),
    "verteiler":  ("b_3.05.jpg", (0, 0, 1, 1)),
    "feld":       ("w_WhatsApp-Image-2022-02-16-at-06.21.58-21.jpg", (0, 0, 1, 1)),
    "feld2":      ("w_WhatsApp-Image-2022-02-16-at-06.21.58.jpg", (0, 0, 1, 1)),
    "raupe":      ("w_WhatsApp-Image-2022-02-16-at-06.21.54-2.jpg", (0, 0, 1, 1)),
    "rot-logo":   ("w_WhatsApp-Image-2022-02-16-at-06.22.09.jpg", (0, 0, 1, 1)),
    "rot-grube":  ("w_WhatsApp-Image-2022-02-16-at-06.22.07-4.jpg", (0, 0, 1, 1)),
    "rot-nah":    ("w_WhatsApp-Image-2022-02-16-at-06.22.07-2.jpg", (0, 0, 1, 1)),
    "mast":       ("w_WhatsApp-Image-2022-02-16-at-06.22.08-1.jpg", (0, 0, 1, 1)),
    "herbst":     ("w_WhatsApp-Image-2022-02-16-at-06.21.59.jpg", (0, 0, 1, 1)),
    "dorf":       ("WhatsApp-Image-2022-02-16-at-06.21.52-480x765.jpg", (0, 0, 1, 1)),
}
BREITEN = (480, 800, 1200)
GROSS = {"kran", "garten"}


def grau(im: Image.Image) -> Image.Image:
    """Farbfilter der Originale neutralisieren: Luminanz, sanfte Kurve, leichte Waerme."""
    g = ImageOps.grayscale(im)
    g = ImageOps.autocontrast(g, cutoff=(0.6, 0.4))
    lut = [int(255 * ((i / 255) ** 1.08)) for i in range(256)]
    g = g.point(lut)
    # leichte warme Tonung, damit das Grau zum Kalkgrund passt
    warm = ImageOps.colorize(g, black=(18, 18, 14), white=(246, 243, 235), mid=(128, 126, 119))
    return warm


def fotos():
    masse = {}
    for key, (datei, (l, o, r, u)) in FOTOS.items():
        im = Image.open(ROH / datei).convert("RGB")
        w, h = im.size
        im = im.crop((int(l * w), int(o * h), int(r * w), int(u * h)))
        im = grau(im).filter(ImageFilter.GaussianBlur(0.6))
        w, h = im.size
        breiten = BREITEN if key in GROSS else BREITEN[:2]
        for b in breiten:
            if b > w and b != BREITEN[0]:
                continue
            bb = min(b, w)
            hh = round(h * bb / w)
            k = im.resize((bb, hh), Image.LANCZOS)
            q = {480: 70, 800: 60, 1200: 52}[b]
            k = k.convert("L") if False else k
            k.save(IMG / f"{key}-{b}.webp", "WEBP", quality=q, method=6)
        masse[key] = (w, h, [b for b in breiten if b <= w or b == breiten[0]])
    return masse


# ---------- Logo als Vektor ----------

def _pfade(maske: np.ndarray, eps: float) -> str:
    cnts, _ = cv2.findContours(maske, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    teile = []
    for c in cnts:
        if cv2.contourArea(c) < 6:
            continue
        a = cv2.approxPolyDP(c, eps, True)[:, 0, :]
        if len(a) < 3:
            continue
        teile.append("M" + " ".join(f"{x},{y}" for x, y in a) + "Z")
    return "".join(teile)


def logo_svg():
    # Wortmarke: 821x308 Original, 4-fach hochgerechnet und geglaettet
    src = Image.open(ROH / "logo_Ecogreen_1.png").convert("RGBA")
    f = 4
    big = src.resize((src.width * f, src.height * f), Image.LANCZOS)
    a = np.array(big).astype(int)
    alpha = a[:, :, 3]
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    gruen = ((g - r) > 25) & (alpha > 110)
    grau_ = ((g - r) <= 25) & (alpha > 110)

    def glatt(m):
        m = (m * 255).astype(np.uint8)
        m = cv2.GaussianBlur(m, (5, 5), 0)
        return (m > 127).astype(np.uint8) * 255

    pg = _pfade(glatt(gruen), 1.2)
    pa = _pfade(glatt(grau_), 1.2)
    W, H = big.size
    # enger Rahmen
    ys, xs = np.where(alpha > 110)
    x0, y0, x1, y1 = xs.min() - 4, ys.min() - 4, xs.max() + 4, ys.max() + 4
    vb = f"{x0} {y0} {x1 - x0} {y1 - y0}"
    def svg(c1, c2):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" role="img" aria-label="Eco Green">'
                f'<path fill="{c1}" fill-rule="evenodd" d="{pg}"/>'
                f'<path fill="{c2}" fill-rule="evenodd" d="{pa}"/></svg>')
    (IMG / "logo.svg").write_text(svg("#29662F", "#3E3E3E"), encoding="utf-8")
    (IMG / "logo-hell.svg").write_text(svg("#F2EEE3", "#F2EEE3"), encoding="utf-8")
    return (int(x1 - x0), int(y1 - y0))


def bildmarke():
    """Weisses Blattpaar auf gruenem Quadrat, als Vektor fuer das Favicon."""
    src = Image.open(ROH / "logo-eco-green.png").convert("RGBA")
    s = src.resize((1024, 1024), Image.LANCZOS)
    a = np.array(s).astype(int)
    weiss = (a[:, :, 0] > 200) & (a[:, :, 1] > 200) & (a[:, :, 2] > 200) & (a[:, :, 3] > 128)
    m = cv2.GaussianBlur((weiss * 255).astype(np.uint8), (5, 5), 0)
    m = ((m > 127) * 255).astype(np.uint8)
    p = _pfade(m, 1.6)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">'
           '<style>@media (prefers-color-scheme:dark){.g{fill:#3C8C44}}</style>'
           '<rect class="g" width="1024" height="1024" fill="#26672F"/>'
           f'<path fill="#fff" fill-rule="evenodd" d="{p}"/></svg>')
    (OUT / "favicon.svg").write_text(svg, encoding="utf-8")
    # Raster aus dem Original (sauberer als aus dem Pfad)
    q = src.convert("RGB")
    for n, px in (("apple-touch-icon.png", 180), ("icon-192.png", 192), ("icon-512.png", 512)):
        q.resize((px, px), Image.LANCZOS).save(OUT / n if n.startswith("apple") else IMG / n, optimize=True)
    q.resize((48, 48), Image.LANCZOS).save(OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    # maskable: Blattpaar auf 62 Prozent verkleinert, voller gruener Grund
    m = Image.new("RGB", (512, 512), (38, 103, 47))
    k = q.resize((318, 318), Image.LANCZOS)
    m.paste(k, (97, 97))
    m.save(IMG / "icon-maskable-512.png", optimize=True)
    return q


def og_bild(name="og", z1="Wir bohren", z2="nach Wärme.", fotokey="b_5.05.jpg", oben=0.35):
    W, H = 1200, 630
    im = Image.new("RGB", (W, H), KALK)
    d = ImageDraw.Draw(im)
    foto = grau(Image.open(ROH / fotokey).convert("RGB"))
    fw, fh = 470, 630
    foto = ImageOps.fit(foto, (fw, fh), Image.LANCZOS, centering=(0.5, oben))
    im.paste(foto, (W - fw, 0))
    d.rectangle([W - fw - 6, 0, W - fw, H], fill=TINTE)
    ttf = HIER / "schibsted.ttf"
    def schrift(px, wght):
        f = ImageFont.truetype(str(ttf), px)
        try:
            f.set_variation_by_axes([wght])
        except Exception:
            pass
        return f
    mono = ImageFont.truetype(str(HIER / "plexmono500.ttf"), 24)
    # Logo-Raster
    logo = Image.open(ROH / "logo_Ecogreen_1.png").convert("RGBA")
    logo.thumbnail((250, 100), Image.LANCZOS)
    im.paste(logo, (64, 56), logo)
    d.text((64, 200), "ERDWÄRMESONDEN · REGENSDORF ZH", font=mono, fill=TINTE)
    px = 88
    while px > 50:
        t = schrift(px, 850)
        if max(d.textlength(z1, font=t), d.textlength(z2, font=t)) <= 640:
            break
        px -= 4
    d.text((60, 240), z1, font=t, fill=TINTE)
    d.text((60, 240 + int(px * 1.09)), z2, font=t, fill=GRUEN)
    # Siegel-Kasten mit hartem Schatten
    x, y, w, h = 64, 488, 520, 78
    d.rectangle([x + 8, y + 8, x + w + 8, y + h + 8], fill=TINTE)
    d.rectangle([x, y, x + w, y + h], fill=OCKER, outline=TINTE, width=4)
    d.text((x + 22, y + 24), "FWS-GÜTESIEGEL FÜR BOHRFIRMEN", font=mono, fill=TINTE)
    d.rectangle([0, 0, W - 1, H - 1], outline=TINTE, width=6)
    im.save(IMG / f"{name}.jpg", "JPEG", quality=86, optimize=True, progressive=True)


if __name__ == "__main__":
    m = fotos()
    lw = logo_svg()
    bildmarke()
    og_bild()
    for n, a, b, f, o in [
        ("og-leistungen", "Alles bis zur", "Hauswand.", "b_4.05.jpg", 0.4),
        ("og-ablauf", "Sechs Schritte", "bis zur Wärme.", "w_WhatsApp-Image-2022-02-16-at-06.21.58.jpg", 0.5),
        ("og-foerderung", "CHF 6'800", "vom Kanton.", "b_3.05.jpg", 0.5),
        ("og-referenzen", "Gebohrt,", "nicht gerendert.", "w_WhatsApp-Image-2022-02-16-at-06.21.58-21.jpg", 0.5),
        ("og-ueber-uns", "Bohrfirma aus", "dem Furttal.", "w_WhatsApp-Image-2022-02-16-at-06.22.09.jpg", 0.5),
        ("og-kontakt", "Rufen Sie an.", "044 400 20 20", "b_6.05.jpg", 0.4),
    ]:
        og_bild(n, a, b, f, o)
    import json
    (HIER / "bilder.json").write_text(json.dumps({"fotos": m, "logo": lw}, indent=1), encoding="utf-8")
    print(json.dumps(m)); print("logo", lw)
