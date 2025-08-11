#!/usr/bin/env python

from __future__ import annotations

import sys
from pathlib import Path

import django
from django.urls import reverse

import click
from tabulate import tabulate

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))


def report_duplicate_merchants() -> dict[str, list[int]]:
    from openforms.payments.contrib.ogone.models import OgoneMerchant

    merchant_data = {
        id: pspid.strip().lower()
        for id, pspid in OgoneMerchant.objects.values_list("id", "pspid")
    }
    merchant_mapping: dict[str, list[int]] = {}

    for merchant_id, merchant_pspid in merchant_data.items():
        pspid = merchant_pspid.strip().lower()

        if list(merchant_data.values()).count(pspid) == 1:
            continue

        merchant_mapping.setdefault(pspid, [])
        merchant_mapping[pspid].append(merchant_id)

    return dict(sorted(merchant_mapping.items(), key=lambda item: item[0]))


def main(**kwargs) -> bool:
    from openforms.setup import setup_env

    setup_env()
    django.setup()

    duplicates = report_duplicate_merchants(**kwargs)

    if not duplicates:
        click.echo(click.style("No merchant duplicates found.", fg="green"))
        return True

    click.echo(click.style("Found duplicate merchants.", fg="red"))
    click.echo("")
    click.echo(
        tabulate(
            [
                (
                    pspid,
                    merchant_id,
                    reverse(
                        "admin:payments_ogone_ogonemerchant_change",
                        args=(merchant_id,),
                    ),
                )
                for pspid, merchant_ids in duplicates.items()
                for merchant_id in merchant_ids
            ],
            headers=(
                "PSPID",
                "Merchant ID",
                "Admin URL",
            ),
        )
    )

    return False


@click.command()
def cli() -> bool:
    return main()


if __name__ == "__main__":
    cli()
