#!/usr/bin/env python
from __future__ import annotations

import sys
from pathlib import Path
from uuid import UUID

import django

import click
from tabulate import tabulate

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))


def check_objecttype_urls() -> bool:
    from openforms.forms.models import FormRegistrationBackend

    problems: list[list[str]] = []

    for backend in FormRegistrationBackend.objects.filter(backend="objects_api"):
        objecttype_url = backend.options.get("objecttype")
        if not objecttype_url:
            problems.append(
                [
                    backend.form.admin_name,
                    backend.name,
                    backend.key,
                    "No objecttype URL present",
                ]
            )
            continue

        try:
            UUID(objecttype_url.rsplit("/", 1)[1])
        except (IndexError, ValueError):
            problems.append(
                [
                    backend.form.admin_name,
                    backend.name,
                    backend.key,
                    f"Invalid objecttype URL: {objecttype_url}",
                ]
            )

    if not problems:
        click.echo(click.style("No problems found.", fg="green"))
        return True

    click.echo(click.style("Found problems in form registration backends.", fg="red"))
    click.echo("")
    click.echo(
        tabulate(
            problems,
            headers=(
                "Form",
                "Registration backend name",
                "Regisration backend key",
                "Problem",
            ),
        )
    )

    return False


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
