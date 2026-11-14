import json
import os
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit


VERSION = "v1"
PORT = 8000


class DemoHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/":
            status = 200
            payload = {
                "message": "Hello from Python",
                "version": VERSION,
                "hostname": socket.gethostname(),
            }
        elif path == "/healthz":
            status = 200
            payload = {"status": "ok"}
        else:
            status = 404
            payload = {"error": "not found"}

        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    host = os.environ.get("BIND_HOST", "127.0.0.1")
    with ThreadingHTTPServer((host, PORT), DemoHandler) as server:
        print(f"Serving {VERSION} at http://{host}:{PORT}", flush=True)
        server.serve_forever()
