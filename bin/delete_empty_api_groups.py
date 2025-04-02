#!/usr/bin/env python
#
# Fix the API groups that were automatically created from their singleton configs but
# hold no actual useful configuration. These API groups block upgrading to Open Forms
# 3.0 otherwise, unless manually removed in the admin interface.
#


from __future__ import annotations

import sys
from pathlib import Path

import django
from django.db.models import Q

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))


def fix_api_groups():
    from openforms.contrib.objects_api.models import ObjectsAPIGroupConfig
    from openforms.registrations.contrib.zgw_apis.models import ZGWApiGroupConfig

    objects_api_groups = ObjectsAPIGroupConfig.objects.filter(
        objects_service__isnull=True,
        objecttypes_service__isnull=True,
        drc_service__isnull=True,
        catalogi_service__isnull=True,
    ).only("pk")
    if objects_api_groups:
        ids = [str(group.pk) for group in objects_api_groups]
        print(f"Deleting {len(ids)} Objects API Group(s) with IDS: {', '.join(ids)}")
    objects_api_groups.delete()

    zgw_api_groups = ZGWApiGroupConfig.objects.filter(
        zrc_service__isnull=True,
        drc_service__isnull=True,
        ztc_service__isnull=True,
    ).only("pk")
    if zgw_api_groups:
        ids = [str(group.pk) for group in zgw_api_groups]
        print(f"Deleting {len(ids)} ZGW API Group(s) with IDS: {', '.join(ids)}")
    zgw_api_groups.delete()


def main():
    from openforms.setup import setup_env

    setup_env()
    django.setup()
    fix_api_groups()


if __name__ == "__main__":
    main()
