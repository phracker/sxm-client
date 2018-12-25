# -*- coding: utf-8 -*-

"""Console script for sxm."""
import sys

import click

from . import SiriusXMClient, run_sync_http_server


@click.command()
@click.option('--username', prompt=True)
@click.option('--password', prompt=True, hide_input=True)
@click.option('-l', '--list', 'do_list', is_flag=True)
@click.option('-p', '--port', type=int, default=9999)
def main(username, password, do_list, port):
    """SiriusXM proxy command line application."""

    sxm = SiriusXMClient(username, password)
    if do_list:
        l1 = max(len(x.get('channelId', '')) for x in sxm.channels)
        l2 = max(len(str(x.get('siriusChannelNumber', 0))) for x in sxm.channels)
        l3 = max(len(x.get('name', '')) for x in sxm.channels)

        click.echo('{} | {} | {}'.format('ID'.ljust(l1), 'Num'.ljust(l2), 'Name'.ljust(l3)))

        for channel in sxm.channels:
            cid = channel.get('channelId', '').ljust(l1)[:l1]
            cnum = str(channel.get('siriusChannelNumber', '??')).ljust(l2)[:l2]
            cname = channel.get('name', '??').ljust(l3)[:l3]
            click.echo('{} | {} | {}'.format(cid, cnum, cname))
    else:
        run_sync_http_server(port, sxm)
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
