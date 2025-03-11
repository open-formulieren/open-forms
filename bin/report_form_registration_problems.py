#!/usr/bin/env python
from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

import django

import click
from tabulate import tabulate

if TYPE_CHECKING:
    from openforms.forms.models import FormRegistrationBackend

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))


def check_registration_backend(registration: FormRegistrationBackend) -> str | None:
    from openforms.registrations.contrib.objects_api.config import VersionChoices

    match (registration.backend, registration.options):
        case ("objects_api", dict() as options) if not options.get("version", None):
            return "'version' is missing"

        case (
            "objects_api",
            {"version": int() as version},
        ) if version == VersionChoices.V2:
            # `variables_mapping` should only be checked/added on V2 registrations
            variables_mapping = registration.options.get("variables_mapping", None)

            if variables_mapping is None:
                return "'variables_mapping' is missing"
            if type(variables_mapping) is not list:
                return "'variables_mapping' is't a list"


def report_problems(backends: Sequence[str]) -> bool:
    from openforms.forms.models import FormRegistrationBackend

    problems = []

    # Only fetch the backends we are going to check
    query_params = {"backend__in": backends} if backends else {}
    registration_backends = FormRegistrationBackend.objects.filter(
        **query_params
    ).iterator()
    for registration_backend in registration_backends:
        message = check_registration_backend(registration_backend)
        if message is None:
            continue

        problems.append(
            [
                registration_backend,
                registration_backend.name,
                registration_backend.backend,
                message,
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
                "Form registration",
                "Registration name",
                "Registration backend",
                "Problem",
            ),
        )
    )

    return False


def main(skip_setup=False, **kwargs) -> bool:
    from openforms.setup import setup_env

    if not skip_setup:
        setup_env()
        django.setup()

    return report_problems(**kwargs)


@click.command()
@click.option("--backend", multiple=True, help="Limit check to backend.")
def cli(backend: Sequence[str]):
    return main(
        backends=backend,
    )


if __name__ == "__main__":
    cli()
