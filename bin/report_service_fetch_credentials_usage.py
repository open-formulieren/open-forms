#!/usr/bin/env python
from __future__ import annotations

import sys
from pathlib import Path

import django

import click
from tabulate import tabulate

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))

SENSITIVE_HEADERS = {
    "authorization",
    "x-api-key",
    "api-key",
}


def report_problems(**kwargs) -> bool:
    from openforms.variables.models import ServiceFetchConfiguration

    problems: list[tuple[str, int, str]] = []

    for configuration in ServiceFetchConfiguration.objects.order_by("id"):
        headers_configured = {header.lower() for header in configuration.headers}
        sensitive_headers = headers_configured.intersection(SENSITIVE_HEADERS)
        if not sensitive_headers:
            continue

        problems.append(
            (
                configuration.name,
                configuration.pk,
                ", ".join(sorted(sensitive_headers)),
            )
        )

    if not problems:
        click.echo(click.style("No problems found.", fg="green"))
        return True

    click.echo(click.style("Found likely credentials in service fetches.", fg="red"))
    click.echo("")
    click.echo(
        "Credentials should be configured on the underlying service via Admin > "
        "Configuration > Services instead of directly on the service fetch config."
    )
    click.echo(
        tabulate(
            problems,
            headers=("Name", "ID", "Detected header(s)"),
        )
    )

    return False


def main(skip_setup=False, **kwargs) -> bool:
    from openforms.setup import setup_env

    if not skip_setup:
        setup_env()
        django.setup()

    return report_problems(**kwargs)


if __name__ == "__main__":
    main()
