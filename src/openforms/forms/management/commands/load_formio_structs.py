"""
Management command to validate formio_structs definitions against real database
content.
"""

from __future__ import annotations

from collections.abc import Sequence

from django.core.management import BaseCommand

import msgspec

from formio_types import AnyComponent

from ...models import FormDefinition


class Command(BaseCommand):
    help = "Load form definitions from the DB as formio structs."

    def handle(self, **options):
        for fd in FormDefinition.objects.all().iterator():
            components = fd.configuration["components"]
            msgspec.convert(components, type=Sequence[AnyComponent])
