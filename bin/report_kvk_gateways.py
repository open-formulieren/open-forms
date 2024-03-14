#!/usr/bin/env python
import sys
from pathlib import Path

import django

from tabulate import tabulate

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))

DEFAULT_API_ROOT_URL = "https://api.kvk.nl/"


def report_problems() -> bool:
    from openforms.contrib.kvk.models import KVKConfig

    config = KVKConfig.get_solo()

    assert isinstance(config, KVKConfig)
    assert hasattr(config, "_service") and hasattr(
        config, "_profiles"
    ), "This script is meant for detecting problems in v2.3.x"

    problems = []
    if (service := config._service) and not service.api_root.startswith(
        DEFAULT_API_ROOT_URL
    ):
        problems.append([service.label, service.api_root])

    if (profiles := config._profiles) and not profiles.api_root.startswith(
        DEFAULT_API_ROOT_URL
    ):
        problems.append([profiles.label, profiles.api_root])

    if not problems:
        print("No KVK services (using gateways) found.")
        return True

    print("Found KVK services using gateways.")
    print("")
    print(
        tabulate(
            problems,
            headers=("Service", "API root url"),
        )
    )

    return False


def main(skip_setup=False) -> bool:
    from openforms.setup import setup_env

    if not skip_setup:
        setup_env()
        django.setup()

    return report_problems()


if __name__ == "__main__":
    main()
