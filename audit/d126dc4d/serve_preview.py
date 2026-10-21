#!/usr/bin/env python3
"""Serve a Pages checkout for browser QA without exposing hidden repo files."""
import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit


class SafeHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        pieces = Path(unquote(urlsplit(self.path).path)).parts
        if any(part.startswith(".") for part in pieces):
            self.send_error(404)
            return
        super().do_GET()

    def do_HEAD(self):
        pieces = Path(unquote(urlsplit(self.path).path)).parts
        if any(part.startswith(".") for part in pieces):
            self.send_error(404)
            return
        super().do_HEAD()

    def list_directory(self, path):
        self.send_error(404, "Directory listings are disabled")
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", default=".")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    root = Path(args.directory).resolve()
    factory = lambda *a, **kw: SafeHandler(*a, directory=str(root), **kw)
    server = ThreadingHTTPServer(("0.0.0.0", args.port), factory)
    print(f"Pages preview on 0.0.0.0:{args.port}, directory {root}", flush=True)
    server.serve_forever()
