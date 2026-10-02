"""Local-only HTTP adapter. No persistence, subprocesses or external services."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from .core import ROOT, Invalid, loads, validate_requirements, build_flowsheet, calculate

MAX_BODY = 131072
OPERATIONS = {'validate-requirements': validate_requirements, 'build-flowsheet': build_flowsheet, 'calculate': calculate}


class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def log_message(self, *_args):
        pass  # Do not log submitted engineering data.

    def reply(self, status, body):
        data = json.dumps(body, allow_nan=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def reject(self, status, message, code):
        self.reply(status, Invalid(message, code=code).payload)

    def do_GET(self):
        if self.path == '/health':
            self.reply(200, {'status': 'ok', 'engine_version': '1.0.0'})
        elif self.path == '/v1/reference':
            self.reply(200, loads((ROOT / 'contracts/examples/requirements.json').read_text()))
        else:
            self.reject(404, 'Unknown endpoint', 'NOT_FOUND')

    def do_POST(self):
        operation = self.path.removeprefix('/v1/') if self.path.startswith('/v1/') else ''
        if operation not in OPERATIONS:
            return self.reject(404, 'Unknown endpoint', 'NOT_FOUND')
        if self.headers.get('Content-Type', '').split(';')[0].strip() != 'application/json':
            return self.reject(415, 'Use application/json', 'CONTENT_TYPE')
        if self.headers.get('Transfer-Encoding'):
            return self.reject(400, 'Use a fixed Content-Length', 'INVALID_LENGTH')
        try:
            size = int(self.headers.get('Content-Length', '-1'))
        except ValueError:
            size = -1
        if size < 0:
            return self.reject(400, 'Content-Length required', 'INVALID_LENGTH')
        if size > MAX_BODY:
            return self.reject(413, 'Request body too large', 'BODY_TOO_LARGE')
        try:
            raw = self.rfile.read(size)
            if len(raw) != size: raise Invalid('Incomplete request body')
            document = loads(raw.decode('utf-8'))
            self.reply(200, OPERATIONS[operation](document))
        except Invalid as error:
            self.reply(422, error.payload)
        except (UnicodeError, RecursionError):
            self.reject(400, 'Invalid JSON encoding or nesting', 'INVALID_JSON')
        except TimeoutError:
            self.reject(408, 'Request timed out', 'TIMEOUT')
        except Exception:
            self.reject(500, 'Engine calculation could not complete', 'ENGINE_ERROR')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8001)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'RIOGINEER Engine: http://127.0.0.1:{server.server_port}', flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()


if __name__ == '__main__': main()
