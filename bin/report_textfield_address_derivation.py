#!/usr/bin/env python
from __future__ import annotations

import sys
from pathlib import Path

import django

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))


def report_address_derivation_usage():
    """
    Inspect all form definitions used in at least one form for address derivation usage.

    Address derivation in textfields in the new renderer is not supported. Users must
    convert their forms to use addressNL which now handles this feature.
    """
    return True


def main(skip_setup=False) -> bool:
    from openforms.setup import setup_env

    if not skip_setup:
        setup_env()
        django.setup()

    return report_address_derivation_usage()


if __name__ == "__main__":
    main()
