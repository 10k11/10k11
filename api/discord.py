import os, sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".github", "scripts"))
from discord_card import build


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            svg = build().encode("utf-8")
            code = 200
        except Exception as e:
            svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="460" height="40"><text x="10" y="25" fill="red">{type(e).__name__}</text></svg>'.encode()
            code = 200
        self.send_response(code)
        self.send_header("Content-Type", "image/svg+xml; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate, max-age=0")
        self.end_headers()
        self.wfile.write(svg)
