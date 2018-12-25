from http.server import BaseHTTPRequestHandler, HTTPServer

from ..client import HLS_AES_KEY


def make_sync_http_handler(sxm):
    class SiriusHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.endswith('.m3u8'):
                data = sxm.get_playlist(self.path.rsplit('/', 1)[1][:-5])
                if data:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/x-mpegURL')
                    self.end_headers()
                    self.wfile.write(bytes(data, 'utf-8'))
                else:
                    self.send_response(500)
                    self.end_headers()
            elif self.path.endswith('.aac'):
                data = sxm.get_segment(self.path[1:])
                if data:
                    self.send_response(200)
                    self.send_header('Content-Type', 'audio/x-aac')
                    self.end_headers()
                    self.wfile.write(data)
                else:
                    self.send_response(500)
                    self.end_headers()
            elif self.path.endswith('/key/1'):
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(HLS_AES_KEY)
            else:
                self.send_response(500)
                self.end_headers()
    return SiriusHandler


def run_sync_http_server(port, sxm):
    httpd = HTTPServer(('', port), make_sync_http_handler(sxm))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
