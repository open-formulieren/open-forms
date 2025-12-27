"""
Management command to validate formio_structs definitions against real database
content.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from django.core.management import BaseCommand

import msgspec

from formio_types import AnyComponent
from formio_types.date import FormioDate
from formio_types.datetime import FormioDateTime

from ...models import FormDefinition


class Command(BaseCommand):
    help = "Load form definitions from the DB as formio structs."

    def handle(self, **options):
        for fd in FormDefinition.objects.all().iterator():
            components = fd.configuration["components"]
            try:
                msgspec.convert(
                    components,
                    type=Sequence[AnyComponent],
                    dec_hook=fixup_component_properties,
                )
            except Exception as exc:
                print(exc)
                breakpoint()
                raise


def fixup_component_properties(type_: type, obj: Any):
    # sometimes an ISO-8601 date, sometimes an ISO-8601 datetime...
    if type_ is FormioDate and isinstance(obj, str):
        return FormioDate.fromstr(obj)

    if type_ is FormioDateTime and isinstance(obj, str):
        return FormioDateTime.fromstr(obj)

    return obj
