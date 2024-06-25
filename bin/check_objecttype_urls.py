#!/usr/bin/env python
from __future__ import annotations

import sys
from pathlib import Path
from uuid import UUID

import django

import click

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))


def check_objecttype_urls() -> bool:
    from openforms.forms.models import FormRegistrationBackend

    for backend in FormRegistrationBackend.objects.filter(backend="objects_api"):
        objecttype_url = backend.options.get("objecttype")
        if not objecttype_url:
            click.echo(
                click.style(
                    f"No Objecttype URL present for backend {backend.name!r} (key: {backend.key!r})",
                    fg="red",
                )
            )
            return False

        try:
            UUID(objecttype_url.rsplit("/", 1)[1])
        except (IndexError, ValueError):
            click.echo(
                click.style(
                    f"{objecttype_url} is invalid for {backend.name!r} (key: {backend.key!r})",
                    fg="red",
                )
            )
            return False

    return True


def main(skip_setup: bool = False) -> bool:
    from openforms.setup import setup_env

    if not skip_setup:
        setup_env()
        django.setup()

    return check_objecttype_urls()


@click.command()
def cli():
    return main()


if __name__ == "__main__":
    cli()
