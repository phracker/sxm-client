import argparse

from .client import SiriusXMClient
from .http import run_sync_http_server

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
        run_sync_http_server(args['port'], sxm)
