"""Local HTTP sink: browser POSTs text, we append to a file. Used for archiving
page text captured in the in-app browser (same pattern as the Discord scrape)."""
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0))
        with open(sys.argv[1], 'ab') as f:
            f.write(self.rfile.read(n))
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'content-type')
        self.end_headers()
    def log_message(self, *a): pass

HTTPServer(('127.0.0.1', 8792), H).serve_forever()
