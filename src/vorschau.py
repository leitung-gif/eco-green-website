"""Lokale Vorschau der Eco-Green-Website, so wie sie auf Shopify unter / laeuft.

Aufruf:  python vorschau.py [port] [--entwurf]

Baut einen Live-Probebau (python bauen.py --live <temp>, PFAD /) und liefert ihn aus.
URLs ohne Endung (/pages/kontakt, /blogs/ratgeber/<handle>) werden auf .html aufgeloest,
unbekannte Adressen bekommen 404.html mit Status 404. Standardport 8653.
"""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit, unquote
import subprocess, sys, tempfile

HIER = Path(__file__).resolve().parent
ZIEL = Path(tempfile.gettempdir()) / "ecogreen-vorschau"
PORT = next((int(a) for a in sys.argv[1:] if a.isdigit()), 8653)
EXTRA = [a for a in sys.argv[1:] if a == "--entwurf"]


class Handler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, ".atom": "application/atom+xml",
                      ".webmanifest": "application/manifest+json", ".svg": "image/svg+xml", ".webp": "image/webp",
                      ".woff2": "font/woff2", ".txt": "text/plain; charset=utf-8", ".xml": "application/xml"}

    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(ZIEL), **k)

    def send_head(self):
        teile = urlsplit(self.path)
        pfad = unquote(teile.path)
        datei = ZIEL / pfad.lstrip("/")
        if pfad.endswith("/") and (datei / "index.html").is_file():
            self.path = pfad + "index.html"
        elif not datei.is_file() and Path(str(datei) + ".html").is_file():
            self.path = pfad + ".html"
        elif not datei.exists():
            inhalt = (ZIEL / "404.html").read_bytes()
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(inhalt)))
            self.end_headers()
            from io import BytesIO
            return BytesIO(inhalt)
        return super().send_head()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


if __name__ == "__main__":
    r = subprocess.run([sys.executable, str(HIER / "bauen.py"), "--live", str(ZIEL)] + EXTRA, cwd=HIER)
    if r.returncode:
        sys.exit(r.returncode)
    print(f"Vorschau: http://localhost:{PORT}/  (Ordner {ZIEL})", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
