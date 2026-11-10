import http.client
import importlib.util
from pathlib import Path
import threading
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('editor_server', ROOT / 'serve.py')
editor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(editor)


class QuietHandler(editor.EditorHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(editor.WEB), **kwargs)

    def log_message(self, *args):
        pass


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = editor.ThreadingHTTPServer(('127.0.0.1', 0), QuietHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, path, method='GET', host=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port)
        headers = {'Host': host} if host else {}
        connection.request(method, path, headers=headers)
        response = connection.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        connection.close()
        return result

    def test_editor_and_local_assets(self):
        status, headers, body = self.request('/')
        self.assertEqual(status, 200)
        self.assertIn(b'Save editor', body)
        for path in ['/app.js', '/save-core.js', '/extended-core.js', '/extended-ui.js', '/save-reference.js', '/progress-core.js', '/save-metadata.js', '/styles.css', '/assets/fonts/NotoSans.ttf', '/assets/fonts/NotoSansCJKsc-Medium.otf', '/assets/fonts/tabler-icons.woff2', '/help.html', '/game-reference.js', '/game-schema.js', '/local-game-data.js', '/local-save-reference.js']:
            self.assertEqual(self.request(path)[0], 200, path)
        self.assertIn('text/javascript', self.request('/app.js')[1]['Content-type'])

    def test_no_directory_listing_or_workspace_access(self):
        for path in ['/assets/', '/../Visual.md', '/%2e%2e/Visual.md', '/..%5cVisual.md']:
            self.assertEqual(self.request(path)[0], 403, path)
        self.assertEqual(self.request('/Visual.md')[0], 404)
        self.assertEqual(self.request('/vendor/rf4-modkit/save.py')[0], 404)

    def test_no_save_upload_endpoint(self):
        self.assertEqual(self.request('/', method='POST')[0], 501)

    def test_no_mod_builder_routes(self):
        for path in ['/venti.html', '/venti.js', '/venti-core.js']:
            self.assertEqual(self.request(path)[0], 404)

    def test_missing_personal_reference_data_does_not_block_the_editor(self):
        with patch.object(editor.Path, 'is_file', return_value=False):
            status, headers, body = self.request('/local-game-data.js')
        self.assertEqual(status, 200)
        self.assertIn(b'LOCAL_GAME_DATA = null', body)
        self.assertIn('text/javascript', headers['Content-Type'])
        with patch.object(editor.Path, 'is_file', return_value=False):
            status, _, body = self.request('/local-save-reference.js')
        self.assertEqual(status, 200)
        self.assertIn(b'LOCAL_SAVE_REFERENCE = null', body)
        with patch.object(editor.Path, 'is_file', return_value=False):
            status, _, body = self.request('/local-languages.js')
        self.assertEqual(status, 200)
        self.assertIn(b'LOCAL_LANGUAGES = null', body)

    def test_windowed_runtime_has_no_stderr_and_still_serves_pages(self):
        with patch.object(QuietHandler, 'log_message', editor.EditorHandler.log_message), patch.object(editor.sys, 'stderr', None):
            status, _, body = self.request('/')
        self.assertEqual(status, 200)
        self.assertIn(b'Save editor', body)

    def test_relocated_public_assets_without_personal_reference_modules(self):
        with tempfile.TemporaryDirectory(prefix='editor with spaces ', dir=ROOT) as folder:
            destination = Path(folder) / 'web'
            shutil.copytree(editor.WEB, destination, ignore=shutil.ignore_patterns('local-game-data.js', 'local-save-reference.js', 'local-languages.js'))
            with patch.object(editor, 'WEB', destination):
                self.assertEqual(self.request('/')[0], 200)
                self.assertEqual(self.request('/extended-ui.js')[0], 200)
                self.assertIn(b'LOCAL_GAME_DATA = null', self.request('/local-game-data.js')[2])
                self.assertIn(b'LOCAL_SAVE_REFERENCE = null', self.request('/local-save-reference.js')[2])
                self.assertIn(b'LOCAL_LANGUAGES = null', self.request('/local-languages.js')[2])

    def test_loopback_host_guard(self):
        self.assertEqual(self.request('/', host='attacker.invalid')[0], 403)
        self.assertEqual(self.request('/', host=f'localhost:{self.server.server_port}')[0], 200)

    def test_security_headers_and_head(self):
        status, headers, body = self.request('/', method='HEAD')
        self.assertEqual(status, 200)
        self.assertEqual(body, b'')
        self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
        self.assertIn("connect-src 'none'", headers['Content-Security-Policy'])
        self.assertEqual(headers['Cache-Control'], 'no-store')


if __name__ == '__main__':
    unittest.main()
