# -*- coding: utf-8 -*-
"""Module entrypoint for sxm."""

import typer
from dotenv import load_dotenv

from sxm.cli import main


def start():
    """Wrapper around typer entrypoint"""
    load_dotenv()

    typer.run(main)


if __name__ == "__main__":
    start()
