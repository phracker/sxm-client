# -*- coding: utf-8 -*-

"""Console script for sxm."""
import logging
import sys

import click

from . import SiriusXMClient, run_http_server


@click.command()
@click.option(
    "--username",
    type=str,
    prompt=True,
    envvar="SXM_USERNAME",
    help="SiriuxXM username",
)
@click.option(
    "--password",
    type=str,
    prompt=True,
    hide_input=True,
    envvar="SXM_PASSWORD",
    help="SiriuxXM password",
)
@click.option(
    "-l",
    "--list-channels",
    "do_list",
    is_flag=True,
    help="List all avaiable SiriusXM channels",
)
@click.option(
    "-p",
    "--port",
    type=int,
    default=9999,
    help="Port to run SiriusXM server on",
)
@click.option(
    "-h",
    "--host",
    type=str,
    default="127.0.0.1",
    help="IP address to bind SiriusXM server to",
)
@click.option(
    "-r",
    "--region",
    type=click.Choice(["US", "CA"]),
    default="US",
    help="Sets the SiriusXM client's region",
)
def main(
    username: str,
    password: str,
    do_list: bool,
    port: int,
    host: str,
    region: str,
) -> int:
    """SiriusXM proxy command line application."""

    logging.basicConfig(level=logging.INFO)

    sxm = SiriusXMClient(username, password, region=region)
    if do_list:
        l1 = max(len(x.id) for x in sxm.channels)
        l2 = max(len(str(x.channel_number)) for x in sxm.channels)
        l3 = max(len(x.name) for x in sxm.channels)

        click.echo(
            "{} | {} | {}".format(
                "ID".ljust(l1), "Num".ljust(l2), "Name".ljust(l3)
            )
        )

        for channel in sxm.channels:
            cid = channel.id.ljust(l1)[:l1]
            cnum = str(channel.channel_number).ljust(l2)[:l2]
            cname = channel.name.ljust(l3)[:l3]
            click.echo("{} | {} | {}".format(cid, cnum, cname))
    else:
        run_http_server(sxm, port, ip=host)
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover, pylint: disable=E1120
