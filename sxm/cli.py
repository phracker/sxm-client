# -*- coding: utf-8 -*-

"""Console script for sxm."""
import logging

import typer

from sxm import QualitySize, RegionChoice, SXMClient, run_http_server

OPTION_USERNAME = typer.Option(
    ..., "--username", "-U", help="SXM username", prompt=True, envvar="SXM_USERNAME"
)
OPTION_PASSWORD = typer.Option(
    ...,
    "--password",
    "-P",
    help="SXM password",
    prompt=True,
    hide_input=True,
    envvar="SXM_PASSWORD",
)
OPTION_LIST_CHANNELS = typer.Option(
    False, "--list-channels", "-l", help="List all available SXM channels and exit"
)
OPTION_PORT = typer.Option(
    9999, "--port", "-p", help="Port to run SXM server on", envvar="SXM_PORT"
)
OPTION_HOST = typer.Option(
    "127.0.0.1", "--host", "-h", help="IP to bind SXM server to", envvar="SXM_HOST"
)
OPTION_VERBOSE = typer.Option(
    False, "--verbose", "-v", help="Enable debug logging", envvar="SXM_DEBUG"
)
OPTION_REGION = typer.Option(
    RegionChoice.US,
    "--region",
    "-r",
    help="Sets the SXM client's region",
    envvar="SXM_REGION",
)
OPTION_QUALITY = typer.Option(
    QualitySize.LARGE_256k,
    "--quality",
    "-q",
    help="Sets stream qualuty.",
    envvar="SXM_REGION",
)
OPTION_PRECACHE = typer.Option(
    True,
    "--no-precache",
    "-n",
    help="Turn off precaching AAC chunks",
    envvar="SXM_PRECACHE",
)


def main(
    username: str = OPTION_USERNAME,
    password: str = OPTION_PASSWORD,
    do_list: bool = OPTION_LIST_CHANNELS,
    port: int = OPTION_PORT,
    host: str = OPTION_HOST,
    verbose: bool = OPTION_VERBOSE,
    region: RegionChoice = OPTION_REGION,
    quality: QualitySize = OPTION_QUALITY,
    precache: bool = OPTION_PRECACHE,
) -> int:
    """SXM proxy command line application."""

    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    sxm = SXMClient(username, password, region=region, quality=quality)
    if do_list:
        l1 = max(len(x.id) for x in sxm.channels)
        l2 = max(len(str(x.channel_number)) for x in sxm.channels)
        l3 = max(len(x.name) for x in sxm.channels)

        typer.echo(f"{'ID'.ljust(l1)} | {'Num'.ljust(l2)} | {'Name'.ljust(l3)}")
        for channel in sxm.channels:
            channel_id = channel.id.ljust(l1)[:l1]
            channel_num = str(channel.channel_number).ljust(l2)[:l2]
            channel_name = channel.name.ljust(l3)[:l3]
            typer.echo(f"{channel_id} | {channel_num} | {channel_name}")
    else:
        run_http_server(sxm, port, ip=host, precache=precache)
    return 0
