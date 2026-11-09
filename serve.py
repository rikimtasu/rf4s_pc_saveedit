"""Serve the static editor on loopback. Save bytes never reach this server."""
from __future__ import annotations

import argparse
import errno
import mimetypes
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
import webbrowser
import sys

WEB = Path(__file__).resolve().parent / 'web'
mimetypes.add_type('text/javascript', '.js')
mimetypes.add_type('font/woff2', '.woff2')


class EditorHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # Windowed executables have no stderr; the standard logger would fail
        # before sending the requested static page.
        if sys.stderr is not None:
            super().log_message(format, *args)

    def do_GET(self):
        if not self.safe_request():
            return
        if self.empty_reference_module():
            return
        super().do_GET()

    def do_HEAD(self):
        if not self.safe_request():
            return
        if self.empty_reference_module(head=True):
            return
        super().do_HEAD()

    def empty_reference_module(self, head=False):
        modules = {'/local-game-data.js': 'LOCAL_GAME_DATA', '/local-save-reference.js': 'LOCAL_SAVE_REFERENCE', '/local-languages.js': 'LOCAL_LANGUAGES'}
        path = urlsplit(self.path).path
        if path not in modules or (WEB / path.lstrip('/')).is_file():
            return False
        body = f'export const {modules[path]} = null;\n'.encode('ascii')
        self.send_response(200)
        self.send_header('Content-Type', 'text/javascript; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        if not head:
            self.wfile.write(body)
        return True

    def safe_request(self):
        hosts = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
        if self.headers.get('Host') not in hosts:
            self.send_error(403, 'Loopback host only')
            return False
        path = unquote(urlsplit(self.path).path)
        target = (WEB / path.lstrip('/')).resolve()
        if '\\' in path or any(part == '..' for part in path.split('/')) or not target.is_relative_to(WEB):
            self.send_error(403, 'Path outside editor')
            return False
        return True

    def list_directory(self, path):
        self.send_error(403, 'Directory listing disabled')
        return None

    def end_headers(self):
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self' data:; connect-src 'none'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
        super().end_headers()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8764)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error('--port must be 0–65535')
    handler = partial(EditorHandler, directory=str(WEB))
    try:
        server = ThreadingHTTPServer(('127.0.0.1', args.port), handler)
    except OSError as error:
        if error.errno != errno.EADDRINUSE and getattr(error, 'winerror', None) != 10048:
            raise
        server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
    with server:
        url = f'http://127.0.0.1:{server.server_port}'
        print(f'Save editor: {url}', flush=True)
        print('Keep this window open. Press Ctrl+C to stop. No save data is sent to the server.', flush=True)
        if not args.no_browser:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
