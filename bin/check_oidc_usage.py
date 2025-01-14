#!/usr/bin/env python
import sys
from pathlib import Path

import django

from tabulate import tabulate

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))


def check_oidc_usage():
    from django.conf import settings

    from mozilla_django_oidc_db.models import OpenIDConnectConfig

    from openforms.authentication.contrib.digid_eherkenning_oidc.models import (
        OFDigiDConfig,
        OFDigiDMachtigenConfig,
        OFEHerkenningBewindvoeringConfig,
        OFEHerkenningConfig,
    )
    from openforms.authentication.contrib.org_oidc.models import OrgOpenIDConnectConfig

    USE_LEGACY_OIDC_ENDPOINTS = (
        settings.OIDC_AUTHENTICATION_CALLBACK_URL
        == "legacy_oidc:oidc_authentication_callback"
    )

    problems: list[tuple[str, str]] = []

    # check admin OIDC first
    if USE_LEGACY_OIDC_ENDPOINTS:
        config = OpenIDConnectConfig.objects.first()
        if config and config.enabled:
            problems.append(("Admin OIDC", "Currently uses legacy callback endpoint."))

    if settings.USE_LEGACY_DIGID_EH_OIDC_ENDPOINTS:
        for model in (
            OFDigiDConfig,
            OFDigiDMachtigenConfig,
            OFEHerkenningConfig,
            OFEHerkenningBewindvoeringConfig,
        ):
            config = model.objects.first()
            if config and config.enabled:
                problems.append(
                    (
                        str(model._meta.verbose_name),
                        "Currently uses legacy callback endpoint.",
                    )
                )

    if settings.USE_LEGACY_ORG_OIDC_ENDPOINTS:
        config = OrgOpenIDConnectConfig.objects.first()
        if config and config.enabled:
            problems.append(
                (
                    str(OrgOpenIDConnectConfig._meta.verbose_name),
                    "Currently uses legacy callback endpoint.",
                )
            )

    if not problems:
        return True

    print("Some OIDC configuration appears to use the legacy callback URLs.")
    print(
        "Warning: On Open Forms 3.0, these will no longer use the legacy URLs by default."
    )
    print(
        tabulate(
            problems,
            headers=("Config", "Status"),
        )
    )
    return False


def main(skip_setup=False) -> bool:
    from openforms.setup import setup_env

    if not skip_setup:
        setup_env()
        django.setup()

    return check_oidc_usage()


if __name__ == "__main__":
    main()
