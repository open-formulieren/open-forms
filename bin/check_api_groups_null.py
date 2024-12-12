#!/usr/bin/env python
import sys
from pathlib import Path

import django

from tabulate import tabulate

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))


def check_for_null_services_in_api_groups():
    from openforms.contrib.objects_api.models import ObjectsAPIGroupConfig

    problems: list[tuple[str, int, str, str]] = []

    objects_groups = ObjectsAPIGroupConfig.objects.exclude(
        objects_service__isnull=False, objecttypes_service__isnull=False
    ).values_list("id", "name", "objects_service_id", "objecttypes_service_id")

    for pk, name, objects_service_id, objecttypes_service_id in objects_groups:
        problem = ("Objects API", pk, name)
        if objects_service_id is None:
            problems.append((*problem, "No objects service configured"))
        if objecttypes_service_id is None:
            problems.append((*problem, "No object types service configured"))

    if not problems:
        return False

    print(
        "Can't upgrade yet - some API group services are not properly configured yet."
    )
    print(
        "Go into the admin to fix their configuration, and then try to upgrade again."
    )
    tabulate(
        problems,
        headers=("API group type", "ID", "Name", "Problem"),
    )
    return True


def main(skip_setup=False) -> bool:
    from openforms.setup import setup_env

    if not skip_setup:
        setup_env()
        django.setup()

    return check_for_null_services_in_api_groups()


if __name__ == "__main__":
    main()
