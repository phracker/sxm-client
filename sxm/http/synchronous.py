import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from ..client import HLS_AES_KEY, SegmentRetrievalException

logger = logging.getLogger(__file__)


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
                segment_path = self.path[1:]
                try:
                    data = sxm.get_segment(segment_path)
                except SegmentRetrievalException:
                    sxm.reset_session()
                    sxm.authenticate()
                    data = sxm.get_segment(segment_path)

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


def run_sync_http_server(sxm, port, ip='0.0.0.0'):
    httpd = ThreadingHTTPServer((ip, port), make_sync_http_handler(sxm))
    try:
        logger.info(f'running SiriusXM proxy server on http://{ip}:{port}')
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
