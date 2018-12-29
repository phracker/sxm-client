# -*- coding: utf-8 -*-

"""Console script for sxm."""
import logging
import sys

import click

from . import SiriusXMClient, run_sync_http_server


@click.command()
@click.option('--username', type=str, prompt=True)
@click.option('--password', type=str, prompt=True, hide_input=True)
@click.option('-l', '--list', 'do_list', is_flag=True)
@click.option('-p', '--port', type=int, default=9999)
@click.option('-h', '--host', type=str, default='127.0.0.1')
def main(username: str, password: str,
         do_list: bool, port: int, host: str) -> int:
    """SiriusXM proxy command line application."""

    logging.basicConfig(level=logging.INFO)

    sxm = SiriusXMClient(username, password)
    if do_list:
        l1 = max(len(x.id) for x in sxm.channels)
        l2 = max(len(str(x.channel_number)) for x in sxm.channels)
        l3 = max(len(x.name) for x in sxm.channels)

        click.echo('{} | {} | {}'.format('ID'.ljust(l1), 'Num'.ljust(l2), 'Name'.ljust(l3)))

        for channel in sxm.channels:
            cid = channel.id.ljust(l1)[:l1]
            cnum = str(channel.channel_number).ljust(l2)[:l2]
            cname = channel.name.ljust(l3)[:l3]
            click.echo('{} | {} | {}'.format(cid, cnum, cname))
    else:
        run_sync_http_server(sxm, port, ip=host)
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
