#!/usr/bin/env python
from __future__ import annotations

import sys
from pathlib import Path

import django

import click
from tabulate import tabulate

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))


def check_zgw_groups() -> bool:
    from openforms.forms.models import FormRegistrationBackend
    from openforms.registrations.contrib.zgw_apis.models import ZgwConfig

    zgw_config = ZgwConfig.get_solo()
    if zgw_config is not None:
        default_group = zgw_config.default_zgw_api_group
    else:
        default_group = None

    problems: list[list[str]] = []

    for backend in FormRegistrationBackend.objects.filter(backend="zgw-create-zaak"):
        zgw_api_group = backend.options.get("zgw_api_group")
        if zgw_api_group is None and default_group is None:
            problems.append(
                [
                    backend.form.admin_name,
                    backend.name,
                    backend.key,
                    "No ZGW API group set and no default group available",
                ]
            )
            continue

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

    return check_zgw_groups()


@click.command()
def cli():
    return main()


if __name__ == "__main__":
    cli()
