"""
60KiB JSON file without indentation/formatting, containing (nearly) all form
components.
"""

from __future__ import annotations

import gc
import json
import timeit
from collections.abc import Sequence
from pathlib import Path
from statistics import mean
from typing import Any

from django.conf import settings
from django.core.management import BaseCommand

import msgspec

from formio_types import AnyComponent, FormioConfiguration
from formio_types.datetime import FormioDateTime

SOURCE_FILE = Path(settings.MEDIA_ROOT) / "formdef.json"

NUMBER = 200
REPEATS = 5

DO_GC = False


class Command(BaseCommand):
    help = "Load form definitions from disk."

    def add_arguments(self, parser) -> None:
        parser.add_argument("impl", choices=("stdlib", "msgspec"))

    def handle(self, **options):
        json_bytes = SOURCE_FILE.read_bytes()

        match options["impl"]:
            case "stdlib":
                callback = plain_json_to_dict
            case "msgspec":
                callback = with_msgspec
            case _:
                raise ValueError("Invalid implmentation option")

        times = _time_callback(
            callback, json_bytes, number=NUMBER, repeat=REPEATS, do_gc=DO_GC
        )
        best = min(times)
        avg = mean(times)
        self.stdout.write(
            f"{options['impl']}  best={best / NUMBER:.6f}s/op  avg={avg / NUMBER:.6f}s/op  "
            f"(best run total={best:.6f}s; repeats={REPEATS})"
        )


def _time_callback(
    callback, json_bytes: bytes, *, number: int, repeat: int, do_gc: bool
) -> list[float]:
    # Use a closure so timeit measures the same statement each run.
    def stmt():
        callback(json_bytes)

    if do_gc:
        # Run gc before each repeat to reduce variance.
        timer = timeit.Timer(
            lambda: (gc.collect(), stmt())[1]  # collect then run
        )
    else:
        timer = timeit.Timer(stmt)

    return timer.repeat(repeat=repeat, number=number)


def plain_json_to_dict(file_content: bytes) -> Sequence[dict]:
    return json.loads(file_content)["components"]


def with_msgspec(file_content: bytes) -> Sequence[AnyComponent]:
    result = msgspec.json.decode(
        file_content, type=FormioConfiguration, dec_hook=fixup_component_properties
    )
    return result.components


def fixup_component_properties(type_: type, obj: Any):
    if type_ is FormioDateTime and isinstance(obj, str):
        return FormioDateTime.fromstr(obj)

    return obj
