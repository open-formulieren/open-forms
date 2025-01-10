#!/usr/bin/env python
import sys
from pathlib import Path

import django

from tabulate import tabulate

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))


def check_for_null_services_in_api_groups():
    from openforms.contrib.objects_api.models import ObjectsAPIGroupConfig
    from openforms.registrations.contrib.zgw_apis.models import ZGWApiGroupConfig

    problems: list[tuple[str, int, str, str]] = []

    objects_groups = ObjectsAPIGroupConfig.objects.exclude(
        objects_service__isnull=False,
        objecttypes_service__isnull=False,
    ).values_list("id", "name", "objects_service_id", "objecttypes_service_id")

    for pk, name, objects_service_id, objecttypes_service_id in objects_groups:
        problem = ("Objects API", pk, name)
        if objects_service_id is None:
            problems.append((*problem, "No objects service configured"))
        if objecttypes_service_id is None:
            problems.append((*problem, "No object types service configured"))

    zgw_groups = ZGWApiGroupConfig.objects.exclude(
        zrc_service__isnull=False,
        drc_service__isnull=False,
        ztc_service__isnull=False,
    ).values_list(
        "id",
        "name",
        "zrc_service_id",
        "drc_service_id",
        "ztc_service_id",
    )
    for pk, name, zrc_service_id, drc_service_id, ztc_service_id in zgw_groups:
        problem = ("ZGW APIs", pk, name)
        if zrc_service_id is None:
            problems.append((*problem, "No Zaken API service configured"))
        if drc_service_id is None:
            problems.append((*problem, "No Documenten API service configured"))
        if ztc_service_id is None:
            problems.append((*problem, "No Catalogi API service configured"))

    if not problems:
        return True

    print(
        "Can't upgrade yet - some API group services are not properly configured yet."
    )
    print(
        "Go into the admin to fix their configuration, and then try to upgrade again."
    )
    print(
        tabulate(
            problems,
            headers=("API group type", "ID", "Name", "Problem"),
        )
    )
    return False


def main(skip_setup=False) -> bool:
    from openforms.setup import setup_env

    if not skip_setup:
        setup_env()
        django.setup()

    return check_for_null_services_in_api_groups()


if __name__ == "__main__":
    main()
