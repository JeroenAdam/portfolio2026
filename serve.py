"""Serve the portfolio locally WITHOUT caching, with SPA fallback.

The stock `python -m http.server` sends no Cache-Control header, so browsers
may reuse a stale index.html / data.json (heuristic caching). This server adds
`Cache-Control: no-store` so every reload shows the latest edits. Requests to
route URLs without a file extension (e.g. /blogs/foo) serve index.html, like
Netlify's _redirects does in production.

Usage:  python serve.py [port]   (default 8080)
"""
import functools
import http.server
import os
import sys

class NoStoreHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()

    def send_head(self):
        # SPA fallback: a URL without a file extension that doesn't exist on
        # disk is a route (e.g. /blogs/foo) -> serve the app, like Netlify
        # does with _redirects. send_error() never raises, so check upfront.
        last = self.path.split("?")[0].rstrip("/").split("/")[-1]
        if "." not in last and not os.path.exists(self.translate_path(self.path)):
            self.path = "/index.html"
        return super().send_head()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    handler = functools.partial(NoStoreHandler, directory=".")
    # threaded: one slow or half-open browser connection must not stall the
    # whole server (plain TCPServer serialized every request)
    class Server(http.server.ThreadingHTTPServer):
        daemon_threads = True
    with Server(("", port), handler) as httpd:
        print(f"Serving portfolio without caching on http://localhost:{port}")
        httpd.serve_forever()
