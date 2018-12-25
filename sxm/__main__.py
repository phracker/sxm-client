import argparse
import base64
from http.server import BaseHTTPRequestHandler, HTTPServer

from .client import SiriusXMClient


def make_sirius_handler(sxm):
    class SiriusHandler(BaseHTTPRequestHandler):
        HLS_AES_KEY = base64.b64decode('0Nsco7MAgxowGvkUT8aYag==')

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
                self.wfile.write(self.HLS_AES_KEY)
            else:
                self.send_response(500)
                self.end_headers()
    return SiriusHandler


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='SiriusXM proxy')
    parser.add_argument('username')
    parser.add_argument('password')
    parser.add_argument('-l', '--list', required=False,
                        action='store_true', default=False)
    parser.add_argument('-p', '--port', required=False,
                        default=9999, type=int)
    args = vars(parser.parse_args())

    sxm = SiriusXMClient(args['username'], args['password'])

    if args['list']:
        l1 = max(len(x.get('channelId', '')) for x in sxm.channels)
        l2 = max(len(str(x.get('siriusChannelNumber', 0))) for x in sxm.channels)
        l3 = max(len(x.get('name', '')) for x in sxm.channels)

        print('{} | {} | {}'.format('ID'.ljust(l1), 'Num'.ljust(l2), 'Name'.ljust(l3)))

        for channel in sxm.channels:
            cid = channel.get('channelId', '').ljust(l1)[:l1]
            cnum = str(channel.get('siriusChannelNumber', '??')).ljust(l2)[:l2]
            cname = channel.get('name', '??').ljust(l3)[:l3]
            print('{} | {} | {}'.format(cid, cnum, cname))
    else:
        httpd = HTTPServer(('', args['port']), make_sirius_handler(sxm))
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        httpd.server_close()
