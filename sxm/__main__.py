# -*- coding: utf-8 -*-

import typer
from dotenv import load_dotenv

from sxm.cli import main


def start():
    load_dotenv()

    typer.run(main)


if __name__ == "__main__":
    start()
